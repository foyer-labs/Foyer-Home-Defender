"""The decision engine: ``decide(snapshot, event, config, now) -> Decision``.

A pure function (INV-1). It performs no I/O, reads no clock or random source it
was not handed, and touches no Home Assistant state. The runtime stores the
Decision's state and hands its actions to an executor; the simulator will call
this same function with a fabricated snapshot and clock and never execute it.

One call runs in a fixed order, so that the result depends only on its inputs:

1. timers that fell due by ``now`` are processed, whatever the event;
2. the event's entity change, if any, is applied to the world;
3. zones whose trigger became active (or fired, for event zones) act;
4. the event itself is handled;
5. bypassed zones that have closed rejoin;
6. faults are reconciled, and each new one is announced once.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from .models import (
    CUSTOM_BYPASS,
    ActionIntent,
    AreaRuntime,
    AreaState,
    ArmAreaRequest,
    ArmModeRequest,
    ArmPolicy,
    ArmRequest,
    BypassReason,
    Channel,
    Decision,
    DisarmRequest,
    EntityState,
    EntryMode,
    Event,
    FoyerConfig,
    KeyCommand,
    KeyRelease,
    Moment,
    Occurrence,
    Operation,
    Reason,
    RuntimeState,
    Scenario,
    Startup,
    SystemSnapshot,
    Tick,
    Timer,
    TimerKind,
    Zone,
    ZoneStateChanged,
)
from .triggers import fault_cause, fires_momentarily, is_active, supervision_due

KEY_ZONE_CHANNEL = "key_zone"


def decide(
    snapshot: SystemSnapshot,
    event: Event,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    """Return what should happen in response to ``event``. Executes nothing."""
    run = _Run(snapshot, config, now)
    run.process_due_timers()

    changed: str | None = None
    if isinstance(event, ZoneStateChanged):
        changed = event.entity_id
        run.entities[event.entity_id] = event.new
    run.process_zone_changes(snapshot, changed)

    outcome = _ACCEPTED
    if isinstance(event, ArmRequest):
        outcome = run.arm_scenario(
            config.scenario(event.scenario_id),
            event.code,
            event.channel,
            force=event.force,
        )
    elif isinstance(event, ArmModeRequest):
        outcome = run.arm_mode(event)
    elif isinstance(event, ArmAreaRequest):
        outcome = run.arm_area(event)
    elif isinstance(event, DisarmRequest):
        outcome = run.disarm(event.area_ids, event.code, event.channel)
    elif isinstance(event, Startup):
        run.occur(
            Moment.HA_RESTARTED,
            detail={
                "down_since": event.down_since.isoformat() if event.down_since else "",
                "up_at": now.isoformat(),
            },
        )
    elif not isinstance(event, ZoneStateChanged | Tick):
        raise TypeError(f"unsupported event: {event!r}")

    run.rejoin_closed_bypasses()
    if not snapshot.settling or isinstance(event, Startup):
        run.reconcile_faults()
    return run.decision(outcome)


# --- read models, pure as well -----------------------------------------------------


def arm_blockers(
    snapshot: SystemSnapshot,
    config: FoyerConfig,
    area_ids: tuple[str, ...] | frozenset[str],
    now: datetime,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(faulted, open) zones that would block arming these areas right now."""
    run = _Run(snapshot, config, now)
    faulted, open_ = run.blockers(area_ids)
    return tuple(z.id for z in faulted), tuple(z.id for z in open_)


def zone_fault(
    snapshot: SystemSnapshot, config: FoyerConfig, zone: Zone, now: datetime
) -> str | None:
    return fault_cause(zone, snapshot.entity(zone.entity_id), now)


def master_state(
    state: RuntimeState, config: FoyerConfig
) -> tuple[AreaState, str | None]:
    """The derived master panel (SPEC §13): never an independent state holder.

    Triggered if any area is; else entry; else arming; else armed if **any**
    area is armed — a partially armed house is not a disarmed house. When
    armed, the mode is the active scenario's, but only while exactly its
    areas are armed; anything else is reported as armed_custom_bypass
    (decision 10, 2026-09-14).
    """
    states = {a.id: state.area(a.id).state for a in config.areas}
    for candidate in (AreaState.TRIGGERED, AreaState.ENTRY, AreaState.ARMING):
        if candidate in states.values():
            return candidate, None
    armed = {a for a, s in states.items() if s is AreaState.ARMED}
    if not armed:
        return AreaState.DISARMED, None
    scenario = config.scenario(state.active_scenario_id)
    if scenario is not None and armed == set(scenario.areas):
        return AreaState.ARMED, scenario.ha_master_state
    return AreaState.ARMED, CUSTOM_BYPASS


def next_wakeup(
    snapshot: SystemSnapshot, config: FoyerConfig, now: datetime
) -> datetime | None:
    """When the scheduler must next send a Tick: a timer or a supervision lapse."""
    dues: list[datetime] = [
        rt.timer.due for rt in snapshot.state.areas.values() if rt.timer is not None
    ]
    for zone in config.zones:
        if not zone.enabled:
            continue
        due = supervision_due(zone, snapshot.entity(zone.entity_id))
        # A lapse already past has been, or is being, handled by its own Tick.
        if due is not None and due > now:
            # Strictly after the window, matching supervision_lapsed().
            dues.append(due + timedelta(microseconds=1))
    return min(dues, default=None)


# --- one decide() call -------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Outcome:
    accepted: bool
    reason: Reason | None = None
    blocking: tuple[str, ...] = ()


_ACCEPTED = _Outcome(accepted=True)


def _reject(reason: Reason, blocking: tuple[str, ...] = ()) -> _Outcome:
    return _Outcome(accepted=False, reason=reason, blocking=blocking)


class _Run:
    """Working state for one decide() call. Mutable locals, pure overall."""

    def __init__(self, snapshot: SystemSnapshot, config: FoyerConfig, now: datetime):
        self.config = config
        self.now = now
        state = snapshot.state
        self.areas: dict[str, AreaRuntime] = {
            a.id: state.area(a.id) for a in config.areas
        }
        self.active_scenario_id = (
            state.active_scenario_id
            if config.scenario(state.active_scenario_id)
            else None
        )
        zone_ids = {z.id for z in config.zones}
        self.bypassed = {z: r for z, r in state.bypassed.items() if z in zone_ids}
        self.active = set(state.active_zones & zone_ids)
        self.faults = frozenset(state.faults & zone_ids)
        self.entities: dict[str, EntityState] = dict(snapshot.entities)
        self.occurrences: list[Occurrence] = []
        self.new_bypasses: list[str] = []

    # --- world ----------------------------------------------------------------

    def entity(self, zone: Zone) -> EntityState:
        return self.entities.get(zone.entity_id) or EntityState(state=None)

    def fault(self, zone: Zone) -> str | None:
        return fault_cause(zone, self.entity(zone), self.now)

    def is_open(self, zone: Zone) -> bool:
        return zone.channel is Channel.INTRUSION and zone.id in self.active

    def occur(self, moment: Moment, **kwargs) -> None:
        self.occurrences.append(Occurrence(moment=moment, **kwargs))

    def set_area(self, area_id: str, **changes) -> AreaRuntime:
        self.areas[area_id] = replace(self.areas[area_id], **changes)
        return self.areas[area_id]

    # --- timers ---------------------------------------------------------------

    def process_due_timers(self) -> None:
        """Handle every timer due by now, earliest first.

        A timer that fell due while Home Assistant was down fires on restore:
        an entry delay that ran out with nobody disarming is an alarm, however
        late we learn of it. Its consequences start now, not in the past.
        """
        for _ in range(4 * len(self.areas) + 1):  # each area: at most exit→hold→…
            due = [
                (rt.timer.due, area_id)
                for area_id, rt in self.areas.items()
                if rt.timer is not None and rt.timer.due <= self.now
            ]
            if not due:
                return
            _, area_id = min(due)
            timer = self.areas[area_id].timer
            assert timer is not None
            if timer.kind in (TimerKind.EXIT, TimerKind.HOLD):
                self.complete_exit(area_id)
            elif timer.kind is TimerKind.ENTRY:
                self.entry_expired(area_id)
            else:
                self.siren_cutoff(area_id)

    def entry_expired(self, area_id: str) -> None:
        rt = self.areas[area_id]
        zone = self.config.zone(rt.causes[0]) if rt.causes else None
        self.trigger(area_id, zone, detail={"cause": "entry_expired"})

    def siren_cutoff(self, area_id: str) -> None:
        """Sounders stop; the area goes back to where it was (decision 3).

        Alarm memory stays until a disarm, whatever the area returns to.
        """
        rt = self.areas[area_id]
        self.occur(
            Moment.SIREN_CUTOFF,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=rt.causes,
        )
        resume = rt.resume or AreaState.ARMED
        if resume is AreaState.DISARMED:
            self.set_area(
                area_id,
                state=AreaState.DISARMED,
                scenario_id=None,
                timer=None,
                resume=None,
                resume_timer=None,
                channel=None,
            )
            self.refresh_active_scenario()
        elif resume is AreaState.ARMING:
            timer = rt.resume_timer or Timer(TimerKind.EXIT, self.now)
            self.set_area(
                area_id,
                state=AreaState.ARMING,
                timer=timer,
                resume=None,
                resume_timer=None,
            )
        else:
            self.set_area(
                area_id,
                state=AreaState.ARMED,
                timer=None,
                resume=None,
                resume_timer=None,
            )

    # --- zones ----------------------------------------------------------------

    def process_zone_changes(
        self, before: SystemSnapshot, changed_entity: str | None
    ) -> None:
        """Act on every zone whose trigger became active or fired.

        Level triggers are recomputed for every zone on every call, not only
        the entity in the event: at startup, a door opened while Home Assistant
        was down shows up here as a newly active zone.
        """
        previous = set(self.active)
        self.active = {
            z.id
            for z in self.config.zones
            if z.enabled and is_active(z, self.entity(z), z.id in previous)
        }
        for zone in self.config.zones:
            if not zone.enabled:
                continue
            fired = zone.entity_id == changed_entity and fires_momentarily(
                zone, before.entity(zone.entity_id), self.entity(zone)
            )
            if fired or (zone.id in self.active and zone.id not in previous):
                self.zone_activated(zone)
            elif zone.id in previous and zone.id not in self.active:
                self.zone_deactivated(zone)

    def zone_activated(self, zone: Zone) -> None:
        if zone.channel is Channel.KEY:
            if zone.key is not None:
                self.key_command(zone, zone.key.on_activate)
            return
        if zone.channel is not Channel.INTRUSION or zone.id in self.bypassed:
            return
        rt = self.areas.get(zone.area_id)
        if rt is None:
            return
        if zone.always_on or rt.state is AreaState.TRIGGERED:
            self.trigger(zone.area_id, zone)
        elif rt.state is AreaState.ARMED:
            if zone.entry_mode is EntryMode.DELAYED:
                self.start_entry(zone.area_id, zone)
            else:
                # A follower with no entry window running is instant (§5.2).
                self.trigger(zone.area_id, zone)
        elif rt.state is AreaState.ENTRY:
            if zone.entry_mode is EntryMode.INSTANT:
                # The entry delay protects the entry route, not other zones.
                self.trigger(zone.area_id, zone)
            else:
                # Delayed or follower inside the entry window: it inherits the
                # time that remains, it does not restart it.
                self.set_area(zone.area_id, causes=(*rt.causes, zone.id))
        # Disarmed or arming: not monitored. Chime is part 2.

    def zone_deactivated(self, zone: Zone) -> None:
        if zone.channel is Channel.KEY:
            if zone.key is not None and zone.key.on_deactivate is KeyRelease.DISARM:
                self.key_command(zone, KeyCommand.DISARM)
            return
        rt = self.areas.get(zone.area_id)
        if (
            rt is not None
            and rt.state is AreaState.ARMING
            and rt.timer is not None
            and rt.timer.kind is TimerKind.HOLD
            and zone.arm_policy is ArmPolicy.ARM_AFTER_CLOSING
        ):
            # The patio door has been pulled shut: arming completes now.
            self.complete_exit(zone.area_id)

    def key_command(self, zone: Zone, command: KeyCommand) -> None:
        """A key zone acts as a user would, on every area (decision 13)."""
        assert zone.key is not None
        if command is KeyCommand.TOGGLE:
            armed = any(
                rt.state is not AreaState.DISARMED for rt in self.areas.values()
            )
            command = KeyCommand.DISARM if armed else KeyCommand.ARM
        if command is KeyCommand.DISARM:
            outcome = self.disarm(None, None, KEY_ZONE_CHANNEL)
            if outcome.reason is Reason.INVALID_STATE:
                return  # nothing was armed: a key turned twice is not a failure
        else:
            outcome = self.arm_scenario(
                self.config.scenario(zone.key.scenario_id),
                None,
                KEY_ZONE_CHANNEL,
                force=False,
            )
        if not outcome.accepted:
            self.occur(
                Moment.ARM_FAILED,
                area_id=zone.area_id,
                zone_id=zone.id,
                scenario_id=zone.key.scenario_id,
                zone_ids=outcome.blocking,
                channel=KEY_ZONE_CHANNEL,
                detail={"reason": outcome.reason.value if outcome.reason else ""},
            )

    def rejoin_closed_bypasses(self) -> None:
        """Bypassed zones rejoin automatically once seen closed (§5.4)."""
        for zone_id, reason in list(self.bypassed.items()):
            zone = self.config.zone(zone_id)
            if zone is None:
                continue
            if zone.id not in self.active and self.fault(zone) is None:
                del self.bypassed[zone_id]
                self.occur(
                    Moment.ZONE_REJOINED,
                    area_id=zone.area_id,
                    zone_id=zone.id,
                    detail={"bypass": reason.value},
                )

    def reconcile_faults(self) -> None:
        """Announce each new fault once (INV-4); forget faults that cleared."""
        current: dict[str, str] = {}
        for zone in self.config.zones:
            if zone.enabled and (cause := self.fault(zone)) is not None:
                current[zone.id] = cause
        for zone_id, cause in current.items():
            if zone_id not in self.faults:
                zone = self.config.zone(zone_id)
                assert zone is not None
                self.occur(
                    Moment.ZONE_FAULT,
                    area_id=zone.area_id,
                    zone_id=zone_id,
                    detail={"cause": cause},
                )
        self.faults = frozenset(current)

    # --- alarm transitions ------------------------------------------------------

    def trigger(
        self, area_id: str, zone: Zone | None, detail: dict[str, str] | None = None
    ) -> None:
        rt = self.areas[area_id]
        zone_id = zone.id if zone else None
        if rt.state is AreaState.TRIGGERED:
            if zone_id and zone_id not in rt.causes:
                self.set_area(area_id, causes=(*rt.causes, zone_id))
            return
        if rt.state is AreaState.DISARMED:
            resume = AreaState.DISARMED
        elif rt.state is AreaState.ARMING:
            resume = AreaState.ARMING
        else:
            resume = AreaState.ARMED
        scenario = self.config.scenario(rt.scenario_id)
        siren = self.config.siren_duration(scenario)
        causes = rt.causes if rt.state is AreaState.ENTRY else ()
        if zone_id and zone_id not in causes:
            causes = (*causes, zone_id)
        self.set_area(
            area_id,
            state=AreaState.TRIGGERED,
            timer=Timer(TimerKind.SIREN, self.now + timedelta(seconds=siren)),
            memory=True,
            resume=resume,
            resume_timer=rt.timer if resume is AreaState.ARMING else None,
            causes=causes,
        )
        self.occur(
            Moment.TRIGGERED,
            area_id=area_id,
            zone_id=zone_id,
            scenario_id=rt.scenario_id,
            detail={"kind": zone.alarm_kind.value if zone else "", **(detail or {})},
        )

    def start_entry(self, area_id: str, zone: Zone) -> None:
        delay = self.config.entry_delay(zone)
        if delay <= 0:
            self.trigger(area_id, zone)
            return
        rt = self.set_area(
            area_id,
            state=AreaState.ENTRY,
            timer=Timer(TimerKind.ENTRY, self.now + timedelta(seconds=delay)),
            causes=(zone.id,),
        )
        self.occur(
            Moment.ENTRY_STARTED,
            area_id=area_id,
            zone_id=zone.id,
            scenario_id=rt.scenario_id,
            detail={"seconds": str(delay)},
        )

    # --- arming ---------------------------------------------------------------

    def blockers(
        self, area_ids: tuple[str, ...] | frozenset[str]
    ) -> tuple[list[Zone], list[Zone]]:
        """Zones that stop arming (SPEC §5.4): faults first, then open `block`."""
        zones = [z for z in self.config.zones_in(area_ids) if z.id not in self.bypassed]
        faulted = [
            z
            for z in zones
            if not z.allow_arm_when_faulted and self.fault(z) is not None
        ]
        open_ = [
            z
            for z in zones
            if z not in faulted and z.arm_policy is ArmPolicy.BLOCK and self.is_open(z)
        ]
        return faulted, open_

    def check_code(self, operation: Operation) -> Reason | None:
        """Enforce the code policy server-side (INV-2).

        There are no users before Phase 2 and so no code that could be verified.
        If the policy requires one, the request is refused whatever was supplied:
        the engine fails closed rather than accept something it cannot check.
        """
        if self.config.code_policy.requires_code(operation):
            return Reason.CODE_REQUIRED
        return None

    def check_arming(
        self, area_ids: tuple[str, ...], force: bool
    ) -> tuple[_Outcome, list[Zone]]:
        """Preconditions (§5.4). Returns the zones a forced arm will bypass."""
        faulted, open_ = self.blockers(area_ids)
        if not faulted and not open_:
            return _ACCEPTED, []
        if not force:
            if faulted:
                return _reject(Reason.ZONE_FAULT, tuple(z.id for z in faulted)), []
            return _reject(Reason.ZONE_OPEN, tuple(z.id for z in open_)), []
        stuck = tuple(z.id for z in faulted + open_ if not z.bypassable)
        if stuck:
            return _reject(Reason.ZONE_NOT_BYPASSABLE, stuck), []
        return _ACCEPTED, faulted + open_

    def begin_arming(
        self,
        area_ids: tuple[str, ...],
        scenario: Scenario | None,
        channel: str,
        force: bool,
        to_bypass: list[Zone],
    ) -> None:
        if force:
            self.occur(
                Moment.FORCED_ARM,
                scenario_id=scenario.id if scenario else None,
                area_id=area_ids[0] if scenario is None else None,
                zone_ids=tuple(z.id for z in to_bypass),
                channel=channel,
            )
        self.bypass(to_bypass, BypassReason.FORCED)
        for area_id in area_ids:
            area = self.config.area(area_id)
            assert area is not None
            delay = self.config.exit_delay(area, scenario)
            self.set_area(
                area_id,
                state=AreaState.ARMING,
                scenario_id=scenario.id if scenario else None,
                timer=Timer(TimerKind.EXIT, self.now + timedelta(seconds=delay)),
                forced=force,
                channel=channel,
                causes=(),
            )
            if delay <= 0:
                # With no exit delay `arming` is skipped (§5.2), unless an
                # arm_after_closing zone is still open and holds it.
                self.complete_exit(area_id)

    def complete_exit(self, area_id: str) -> None:
        """The exit delay is over, or a held zone closed (§5.2, decision 4)."""
        rt = self.areas[area_id]
        anchor = self.now
        if rt.timer is not None:
            anchor = rt.timer.anchor or min(rt.timer.due, self.now)
        faulted, block_open = self.blockers((area_id,))
        zones = [
            z for z in self.config.zones_in((area_id,)) if z.id not in self.bypassed
        ]
        after_closing = [
            z
            for z in zones
            if z.arm_policy is ArmPolicy.ARM_AFTER_CLOSING and self.is_open(z)
        ]
        if faulted or block_open:
            blocking = faulted + block_open
            if not rt.forced or any(not z.bypassable for z in blocking):
                reason = Reason.ZONE_FAULT if faulted else Reason.ZONE_OPEN
                self.arming_failed(area_id, blocking, reason)
                return
            self.bypass(blocking, BypassReason.FORCED)
        if after_closing:
            cap = min(self.config.arm_hold_timeout(z) for z in after_closing)
            cap_due = anchor + timedelta(seconds=cap)
            if self.now < cap_due:
                self.set_area(
                    area_id, timer=Timer(TimerKind.HOLD, cap_due, anchor=anchor)
                )
                return
            if not rt.forced or any(not z.bypassable for z in after_closing):
                self.arming_failed(area_id, after_closing, Reason.ARM_HOLD_EXPIRED)
                return
            self.bypass(after_closing, BypassReason.FORCED)
        self.bypass(
            [
                z
                for z in zones
                if z.arm_policy is ArmPolicy.AUTO_BYPASS
                and self.is_open(z)
                and z.id not in self.bypassed
            ],
            BypassReason.AUTO,
        )
        rt = self.set_area(area_id, state=AreaState.ARMED, timer=None, forced=False)
        self.occur(
            Moment.ARMED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            channel=rt.channel,
        )

    def arming_failed(self, area_id: str, zones: list[Zone], reason: Reason) -> None:
        rt = self.areas[area_id]
        self.occur(
            Moment.ARM_FAILED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=tuple(z.id for z in zones),
            channel=rt.channel,
            detail={"reason": reason.value},
        )
        self.clear_area(area_id)

    def bypass(self, zones: list[Zone], reason: BypassReason) -> None:
        for zone in zones:
            if zone.id in self.bypassed:
                continue
            self.bypassed[zone.id] = reason
            self.new_bypasses.append(zone.id)
            self.occur(
                Moment.ZONE_BYPASSED,
                area_id=zone.area_id,
                zone_id=zone.id,
                detail={"bypass": reason.value},
            )

    def arm_scenario(
        self, scenario: Scenario | None, code: str | None, channel: str, *, force: bool
    ) -> _Outcome:
        """Arm a scenario, or switch to it while armed (decisions 7 and 9).

        Areas of the new scenario not yet armed go through their exit delay;
        areas already armed stay armed and now belong to it; areas armed by the
        previous scenario and absent from this one are disarmed. Areas armed on
        their own, outside any scenario, are left exactly as they are.
        """
        if scenario is None:
            return _reject(Reason.UNKNOWN_SCENARIO)
        current = self.active_scenario_id
        target = [a for a in scenario.areas if a in self.areas]
        leaving = [
            a
            for a, rt in self.areas.items()
            if current is not None
            and rt.scenario_id == current
            and rt.state is not AreaState.DISARMED
            and a not in target
        ]
        in_alarm = [
            a
            for a in (*target, *leaving)
            if self.areas[a].state in (AreaState.ENTRY, AreaState.TRIGGERED)
        ]
        if in_alarm:
            # Switching must never silence an alarm without a disarm.
            return _reject(Reason.ALARM_IN_PROGRESS)
        to_arm = tuple(a for a in target if self.areas[a].state is AreaState.DISARMED)
        if current == scenario.id and not to_arm:
            return _reject(Reason.INVALID_STATE)

        switching = current is not None and current != scenario.id
        for operation in (
            Operation.ARM,
            *((Operation.CHANGE_SCENARIO,) if switching else ()),
            *((Operation.FORCE_ARM,) if force else ()),
        ):
            if (reason := self.check_code(operation)) is not None:
                return _reject(reason)
        outcome, to_bypass = self.check_arming(to_arm, force)
        if not outcome.accepted:
            return outcome

        for area_id in leaving:
            self.disarm_area(area_id, channel)
        for area_id in target:
            if area_id not in to_arm:
                self.set_area(area_id, scenario_id=scenario.id)
        self.active_scenario_id = scenario.id
        self.begin_arming(to_arm, scenario, channel, force, to_bypass)
        return _ACCEPTED

    def arm_mode(self, event: ArmModeRequest) -> _Outcome:
        """The master panel arms the one scenario with this mode (decision 8)."""
        matches = [s for s in self.config.scenarios if s.ha_master_state == event.mode]
        if not matches:
            return _reject(Reason.NO_SCENARIO_FOR_MODE)
        if len(matches) > 1:
            return _reject(Reason.AMBIGUOUS_MODE)
        return self.arm_scenario(
            matches[0], event.code, event.channel, force=event.force
        )

    def arm_area(self, event: ArmAreaRequest) -> _Outcome:
        """One area on its own, outside any scenario (decision 5)."""
        if self.config.area(event.area_id) is None:
            return _reject(Reason.UNKNOWN_AREA)
        if self.areas[event.area_id].state is not AreaState.DISARMED:
            return _reject(Reason.INVALID_STATE)
        for operation in (
            Operation.ARM,
            *((Operation.FORCE_ARM,) if event.force else ()),
        ):
            if (reason := self.check_code(operation)) is not None:
                return _reject(reason)
        outcome, to_bypass = self.check_arming((event.area_id,), event.force)
        if not outcome.accepted:
            return outcome
        self.begin_arming((event.area_id,), None, event.channel, event.force, to_bypass)
        return _ACCEPTED

    # --- disarming --------------------------------------------------------------

    def disarm(
        self, area_ids: tuple[str, ...] | None, code: str | None, channel: str
    ) -> _Outcome:
        if area_ids is not None and any(a not in self.areas for a in area_ids):
            return _reject(Reason.UNKNOWN_AREA)
        candidates = area_ids if area_ids is not None else tuple(self.areas)
        # An area holding alarm memory can be disarmed to clear it (decision 3).
        targets = [
            a
            for a in candidates
            if self.areas[a].state is not AreaState.DISARMED or self.areas[a].memory
        ]
        if not targets:
            return _reject(Reason.INVALID_STATE)
        if (reason := self.check_code(Operation.DISARM)) is not None:
            return _reject(reason)
        for area_id in targets:
            self.disarm_area(area_id, channel)
        return _ACCEPTED

    def disarm_area(self, area_id: str, channel: str | None) -> None:
        rt = self.areas[area_id]
        self.occur(
            Moment.DISARMED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=rt.causes if rt.memory else (),
            channel=channel,
            detail={"from": rt.state.value},
        )
        self.clear_area(area_id)

    def clear_area(self, area_id: str) -> None:
        """Back to a plain disarmed area: no timer, no memory, no bypasses."""
        self.areas[area_id] = AreaRuntime()
        for zone in self.config.zones_in((area_id,)):
            self.bypassed.pop(zone.id, None)
        self.refresh_active_scenario()

    def refresh_active_scenario(self) -> None:
        """The scenario ends when nothing it armed is still armed."""
        if self.active_scenario_id is None:
            return
        if not any(
            rt.scenario_id == self.active_scenario_id
            and rt.state is not AreaState.DISARMED
            for rt in self.areas.values()
        ):
            self.active_scenario_id = None

    # --- result -----------------------------------------------------------------

    def decision(self, outcome: _Outcome) -> Decision:
        state = RuntimeState(
            areas=self.areas,
            active_scenario_id=self.active_scenario_id,
            bypassed=self.bypassed,
            active_zones=frozenset(self.active),
            faults=self.faults,
        )
        occurrences = tuple(self.occurrences)
        return Decision(
            at=self.now,
            accepted=outcome.accepted,
            state=state,
            reason=outcome.reason,
            blocking_zones=outcome.blocking,
            bypassed_zones=tuple(self.new_bypasses),
            occurrences=occurrences,
            actions=_intents(self.config, occurrences),
        )


# --- actions -----------------------------------------------------------------------


def _names(ids: list[str | None], lookup: dict[str, str]) -> str:
    seen: list[str] = []
    for item in ids:
        if item and (name := lookup.get(item, item)) not in seen:
            seen.append(name)
    return ", ".join(seen)


def _intents(
    config: FoyerConfig, occurrences: tuple[Occurrence, ...]
) -> tuple[ActionIntent, ...]:
    """One intent per action and moment: three areas arming together send one
    notification that names all three, not three notifications."""
    areas = {a.id: a.name for a in config.areas}
    zones = {z.id: z.name for z in config.zones}
    scenarios = {s.id: s.name for s in config.scenarios}
    moments = list(dict.fromkeys(o.moment for o in occurrences))
    intents: list[ActionIntent] = []
    for action in config.actions:
        for moment in moments:
            if moment not in action.moments:
                continue
            group = [o for o in occurrences if o.moment is moment]
            zone_ids = [o.zone_id for o in group] + [
                z for o in group for z in o.zone_ids
            ]
            scenario = _names([o.scenario_id for o in group], scenarios)
            intents.append(
                ActionIntent(
                    action_id=action.id,
                    kind="notification",
                    moment=moment,
                    variant="area" if moment is Moment.ARMED and not scenario else None,
                    placeholders={
                        "area": _names([o.area_id for o in group], areas),
                        "scenario": scenario,
                        "zone": _names([o.zone_id for o in group], zones),
                        "zones": _names(zone_ids, zones),
                    },
                )
            )
    return tuple(intents)
