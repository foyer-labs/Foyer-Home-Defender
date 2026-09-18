"""The decision engine: ``decide(snapshot, event, config, now) -> Decision``.

A pure function (INV-1). It performs no I/O, reads no clock or random source it
was not handed, and touches no Home Assistant state. The runtime stores the
Decision's state and hands its actions to an executor; the simulator will call
this same function with a fabricated snapshot and clock and never execute it.

One call runs in a fixed order, so that the result depends only on its inputs:

1. verification windows that ran out by ``now`` are emptied;
2. timers that fell due by ``now`` are processed, whatever the event;
3. the event's entity change, if any, is applied to the world;
4. zones whose trigger became active (or fired, for event zones) act;
5. the event itself is handled;
6. bypassed zones that have closed rejoin;
7. faults are reconciled, and each new one is announced once;
8. the incident closes if it is acknowledged and every area it touched
   has settled.

Three machines share the call and never touch each other's state: the areas
(intrusion, §5), the technical channel (§5.5) and the incident (§5.6), which
records what the areas did but decides nothing for them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from . import authz
from .models import (
    CUSTOM_BYPASS,
    AcknowledgeIncident,
    Acknowledgement,
    AcknowledgeTechnical,
    ActionIntent,
    Activation,
    Actor,
    AreaRuntime,
    AreaState,
    ArmAreaRequest,
    ArmingDevice,
    ArmModeRequest,
    ArmPolicy,
    ArmRequest,
    BypassReason,
    BypassZone,
    Channel,
    CodeResult,
    Contributor,
    Decision,
    DisarmRequest,
    EntityState,
    EntryMode,
    Event,
    FoyerConfig,
    Incident,
    KeyCommand,
    KeyRelease,
    Lockout,
    Moment,
    Occurrence,
    Operation,
    Reason,
    RuntimeState,
    Scenario,
    SetChime,
    Startup,
    SystemSnapshot,
    TechnicalAlarm,
    Tick,
    Timer,
    TimerKind,
    Zone,
    ZoneStateChanged,
)
from .response import (
    PlanContext,
    audible_targets,
    chime_suppressed,
    effective_profile,
    plan_occurrences,
    resume,
    revert_intent,
    without,
)
from .triggers import (
    fault_cause,
    fires_momentarily,
    is_active,
    is_unavailable,
    scanned,
    supervision_due,
)
from .verification import Verification, all_windows, counter_of, groups

KEY_ZONE_CHANNEL = "key_zone"

# What an intrusion zone's activation does to its area right now (§5.2).
_TRIGGER = "trigger"
_START_ENTRY = "start_entry"
_INHERIT_ENTRY = "inherit_entry"
_JOIN_ENTRY = "join_entry"

# Occurrences that never carry an incident id, even in an incident's area:
# the technical channel never joins an intrusion incident (§5.5), and a
# chime or a restart is not part of one.
_NOT_INCIDENT = frozenset(
    {
        Moment.TECHNICAL_RAISED,
        Moment.TECHNICAL_ACKNOWLEDGED,
        Moment.TECHNICAL_CLEARED,
        Moment.CHIME,
        Moment.CHIME_SWITCHED,
        Moment.HA_RESTARTED,
    }
)


def decide(
    snapshot: SystemSnapshot,
    event: Event,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    """Return what should happen in response to ``event``. Executes nothing."""
    run = _Run(snapshot, config, now)
    run.actor = getattr(event, "actor", Actor())
    run.expire_windows()
    run.expire_bypasses()
    run.expire_running()
    run.process_due_timers()

    changed: str | None = None
    if isinstance(event, ZoneStateChanged):
        changed = event.entity_id
        run.entities[event.entity_id] = event.new
    run.process_zone_changes(snapshot, changed)
    run.process_device_scans(snapshot, changed)

    outcome = _ACCEPTED
    if isinstance(event, ArmRequest):
        outcome = run.arm_scenario(
            config.scenario(event.scenario_id), force=event.force
        )
    elif isinstance(event, ArmModeRequest):
        outcome = run.arm_mode(event)
    elif isinstance(event, ArmAreaRequest):
        outcome = run.arm_area(event)
    elif isinstance(event, DisarmRequest):
        outcome = run.disarm(event.area_ids)
    elif isinstance(event, AcknowledgeIncident):
        outcome = run.acknowledge_incident()
    elif isinstance(event, AcknowledgeTechnical):
        outcome = run.acknowledge_technical()
    elif isinstance(event, BypassZone):
        outcome = run.bypass_zone(event)
    elif isinstance(event, SetChime):
        run.set_chime(event.enabled)
    elif isinstance(event, Startup):
        # How long the gap was, measured rather than described: the log grades
        # a configuration reload and an hour with the integration disabled
        # differently, and only the number can tell them apart.
        gap = (
            int((now - event.down_since).total_seconds()) if event.down_since else None
        )
        run.occur(
            Moment.HA_RESTARTED,
            detail={
                "down_since": event.down_since.isoformat() if event.down_since else "",
                "up_at": now.isoformat(),
                "cause": event.cause,
                "gap_seconds": str(max(0, gap)) if gap is not None else "",
            },
        )
    elif not isinstance(event, ZoneStateChanged | Tick):
        raise TypeError(f"unsupported event: {event!r}")

    run.rejoin_closed_bypasses()
    if not snapshot.settling or isinstance(event, Startup):
        run.reconcile_faults()
    run.close_incident_if_settled()
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
    """When the scheduler must next send a Tick: a timer, a verification window
    running out, or a supervision lapse."""
    state = snapshot.state
    dues: list[datetime] = [
        rt.timer.due for rt in state.areas.values() if rt.timer is not None
    ]
    # Timed bypasses, sequences held by a delay, and auto-reverts are timers
    # like any other: data in the state, one wake-up (part 3 decision 5).
    dues.extend(state.bypass_until.values())
    dues.extend(run.due for run in state.pending_runs)
    dues.extend(r.until for r in state.running if r.until is not None)
    windows = all_windows(config)
    for key, activations in state.windows.items():
        if (window := windows.get(key)) is not None:
            dues.extend(window.expires_at(a) for a in activations)
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
        self.snapshot = snapshot
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
        self.seen = set(state.seen_zones & zone_ids)
        self.seen_devices = set(state.seen_devices & {d.id for d in config.devices})
        self.faults = frozenset(state.faults & zone_ids)
        self.entities: dict[str, EntityState] = dict(snapshot.entities)
        self.timezone = snapshot.timezone
        self.occurrences: list[Occurrence] = []
        self.new_bypasses: list[str] = []
        # Who is asking. decide() fills it from the event; a timer or a zone
        # opening has no actor, and the default one identifies nobody.
        self.actor = Actor()
        # Failed code attempts, per channel and device (§8.4). Persisted with
        # everything else, because a lockout a restart clears is an invitation
        # to restart Home Assistant.
        self.lockouts: dict[str, Lockout] = dict(state.lockouts)
        # The technical channel: never read or written by the area machine.
        self.technical: dict[str, TechnicalAlarm] = {
            z: a for z, a in state.technical.items() if z in zone_ids
        }
        self.incident: Incident | None = state.incident
        self.incident_seq = state.incident_seq
        self.chime_enabled = state.chime_enabled
        # Manual bypasses with a duration (part 3 decision 10) and the profile
        # machinery: sequences held by a delay, and what is still switched on.
        self.bypass_until = {
            z: due for z, due in state.bypass_until.items() if z in self.bypassed
        }
        self.pending_runs = list(state.pending_runs)
        self.running = list(state.running)
        self.run_seq = state.run_seq
        # Intents that no occurrence produces: switching off what an action
        # switched on, and resuming a sequence a delay held back.
        self.extra: list[ActionIntent] = []
        # Verification windows (§4.8): one engine for groups, cross-zone pairs
        # and trigger counts. A window whose setting is gone is dropped.
        self.verifications: dict[str, Verification] = all_windows(config)
        self.group_of: dict[str, Verification] = {
            member: group for group in groups(config) for member in group.members
        }
        self.windows: dict[str, tuple[Activation, ...]] = {}
        for key, activations in state.windows.items():
            kept = tuple(a for a in activations if a.zone_id in zone_ids)
            if key in self.verifications and kept:
                self.windows[key] = kept

    # --- world ----------------------------------------------------------------

    def entity(self, zone: Zone) -> EntityState:
        return self.entity_state(zone.entity_id)

    def entity_state(self, entity_id: str) -> EntityState:
        return self.entities.get(entity_id) or EntityState(state=None)

    def fault(self, zone: Zone) -> str | None:
        return fault_cause(zone, self.entity(zone), self.now)

    def is_open(self, zone: Zone) -> bool:
        return zone.channel is Channel.INTRUSION and zone.id in self.active

    def occur(self, moment: Moment, **kwargs) -> None:
        """Record an occurrence, tagged with the open incident when related.

        An occurrence belongs to the incident when it happens in an area the
        incident touched (§5.6: the id goes on every related log row), except
        the technical channel's, which never joins one (§5.5).
        """
        incident = self.incident
        if (
            incident is not None
            and "incident_id" not in kwargs
            and moment not in _NOT_INCIDENT
            and (
                moment.value.startswith("incident_")
                or kwargs.get("area_id") in incident.area_ids
            )
        ):
            kwargs["incident_id"] = incident.id
        # Who did it, on everything this request caused. An occurrence raised
        # by a timer or by a door opening carries another channel, or none,
        # and is left alone: nobody asked for it.
        actor = self.actor
        if kwargs.get("user_id") and "user_name" not in kwargs:
            named = self.config.user(kwargs["user_id"])
            kwargs["user_name"] = named.name if named else None
        if kwargs.get("channel") == actor.channel and "user_id" not in kwargs:
            if actor.user_id is not None:
                kwargs["user_id"] = actor.user_id
                user = self.config.user(actor.user_id)
                kwargs["user_name"] = user.name if user else None
            if actor.device_id is not None:
                kwargs["device_id"] = actor.device_id
        self.occurrences.append(Occurrence(moment=moment, **kwargs))

    @property
    def channel(self) -> str:
        return self.actor.channel

    def set_area(self, area_id: str, **changes) -> AreaRuntime:
        self.areas[area_id] = replace(self.areas[area_id], **changes)
        return self.areas[area_id]

    # --- verification windows (§4.2, §4.8) ----------------------------------------

    def expire_windows(self) -> None:
        """Activations older than their window no longer count."""
        for key, activations in list(self.windows.items()):
            window = self.verifications[key]
            kept = tuple(a for a in activations if not window.expired(a, self.now))
            if len(kept) == len(activations):
                continue
            if kept:
                self.windows[key] = kept
            else:
                del self.windows[key]
            gone = tuple(dict.fromkeys(a.zone_id for a in activations if a not in kept))
            self.occur(
                Moment.VERIFICATION_EXPIRED,
                area_id=window.area_id,
                zone_ids=gone,
                group_id=window.group_id,
                detail=_window_detail(window, kept),
            )

    def record(self, window: Verification, zone: Zone) -> tuple[Activation, ...] | None:
        """Add an activation; return the window's activations if it is now
        satisfied (and empty it), None if it is still short of its threshold."""
        activations = (
            *self.windows.get(window.key, ()),
            Activation(zone.id, self.now, held=window.suppress),
        )
        satisfied = window.count(activations) >= window.n
        if satisfied:
            self.windows.pop(window.key, None)
        else:
            self.windows[window.key] = activations
        self.occur(
            Moment.VERIFICATION_SATISFIED if satisfied else Moment.VERIFICATION_PENDING,
            area_id=window.area_id,
            zone_id=zone.id,
            zone_ids=tuple(dict.fromkeys(a.zone_id for a in activations)),
            group_id=window.group_id,
            detail=_window_detail(window, activations),
        )
        return activations if satisfied else None

    def verify(self, zone: Zone) -> tuple[bool, str | None]:
        """Whether an activation that would trigger may act now (§4.2, §4.8).

        The zone's own trigger count comes first: below it the zone does
        nothing. Then its group: a member acts on its own unless the group
        suppresses members; when the group is satisfied, members it held back
        fire too. Returns (act, group id for the record).
        """
        counter = counter_of(zone)
        if counter is not None and self.record(counter, zone) is None:
            return False, None
        group = self.group_of.get(zone.id)
        if group is None:
            return True, None
        activations = self.record(group, zone)
        if activations is None:
            return not group.suppress, group.group_id
        held = dict.fromkeys(a.zone_id for a in activations if a.held)
        held.pop(zone.id, None)
        for held_id in held:
            member = self.config.zone(held_id)
            if member is None or member.id in self.bypassed:
                continue
            rt = self.areas.get(member.area_id)
            if rt is not None and self.effect(member, rt) is not None:
                self.trigger(member.area_id, member, group_id=group.group_id)
        return True, group.group_id

    def forget_activations(self, area_id: str) -> None:
        """An area that stops monitoring drops its zones' pending activations:
        an activation counts only while its area watches the zone. 24h zones
        are watched whatever the area does, so theirs stay."""
        watched = {
            z.id for z in self.config.zones if z.area_id == area_id and not z.always_on
        }
        for key, activations in list(self.windows.items()):
            kept = tuple(a for a in activations if a.zone_id not in watched)
            if not kept:
                del self.windows[key]
            elif len(kept) != len(activations):
                self.windows[key] = kept

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
        self.stop_running(area_id, Moment.SIREN_CUTOFF)
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

        A zone never read before only records its baseline: its first readable
        value is not a change. Without this, saving a new key zone whose switch
        is already on would arm the house.
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
            if zone.id not in self.seen:
                if not is_unavailable(self.entity(zone)):
                    self.seen.add(zone.id)
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
        if zone.channel is Channel.TECHNICAL:
            # Live whatever the areas are doing, bypass or not (§5.5).
            self.technical_raised(zone)
            return
        if zone.channel is not Channel.INTRUSION or zone.id in self.bypassed:
            return
        rt = self.areas.get(zone.area_id)
        if rt is None:
            return
        effect = self.effect(zone, rt)
        if effect is None:
            self.chime(zone, rt)
        elif effect is _TRIGGER:
            act, group_id = self.verify(zone)
            if act:
                self.trigger(zone.area_id, zone, group_id=group_id)
        elif effect is _START_ENTRY:
            self.start_entry(zone.area_id, zone)
        elif effect is _INHERIT_ENTRY:
            inherited = self.followed_window(zone)
            assert inherited is not None
            self.inherit_entry(zone.area_id, zone, *inherited)
        else:
            # Delayed or follower inside the entry window: it inherits the
            # time that remains, it does not restart it.
            self.set_area(zone.area_id, causes=(*rt.causes, zone.id))

    def effect(self, zone: Zone, rt: AreaRuntime) -> str | None:
        """What an intrusion zone's activation does to its area now (§5.2).

        None when the area does not monitor the zone (disarmed or arming).
        Only ``_TRIGGER`` is an alarm at once, and only it goes through
        verification: an activation the entry delay absorbs acts normally
        and never counts towards a group or a trigger count, so coming home
        can never satisfy one (part 2 decisions 6 and 12).
        """
        if zone.always_on or rt.state is AreaState.TRIGGERED:
            return _TRIGGER
        if rt.state is AreaState.ARMED:
            if zone.entry_mode is EntryMode.DELAYED:
                return _START_ENTRY if self.config.entry_delay(zone) > 0 else _TRIGGER
            if zone.entry_mode is EntryMode.FOLLOWER and self.followed_window(zone):
                return _INHERIT_ENTRY
            # A follower with no entry window to inherit is instant (§5.2).
            return _TRIGGER
        if rt.state is AreaState.ENTRY:
            # The entry delay protects the entry route, not other zones.
            return _TRIGGER if zone.entry_mode is EntryMode.INSTANT else _JOIN_ENTRY
        return None

    def chime(self, zone: Zone, rt: AreaRuntime) -> None:
        """A zone opened where nothing watches it (§6.6).

        "Not monitored" is read per area, however it came to be armed or not
        (decision 4 allows one area armed on its own). An area counting down
        its exit delay chimes only if the user chose so (part 2 decision 7).
        """
        settings = self.config.chime
        if not zone.chime or not self.chime_enabled or not settings.targets:
            return
        if rt.state is AreaState.ARMING and not settings.during_exit:
            return
        if chime_suppressed(self.config, zone):
            return
        # Each target may have quiet hours of its own (part 3 decision 8): the
        # chime happens if at least one target can still hear it.
        targets = audible_targets(settings, self.now, self.timezone)
        if not targets:
            return
        self.occur(
            Moment.CHIME,
            area_id=zone.area_id,
            zone_id=zone.id,
            detail={"targets": ",".join(targets)},
        )

    def set_chime(self, enabled: bool) -> None:
        if enabled != self.chime_enabled:
            self.chime_enabled = enabled
            self.occur(
                Moment.CHIME_SWITCHED,
                channel=self.channel,
                detail={"enabled": "true" if enabled else "false"},
            )

    # --- technical channel (§5.5) ------------------------------------------------

    def technical_raised(self, zone: Zone) -> None:
        """A technical zone fired. Its alarm stands until acknowledged and back
        to normal; a repeat before then is announced again, not reset."""
        alarm = self.technical.get(zone.id)
        if alarm is None or alarm.acknowledged:
            self.technical[zone.id] = TechnicalAlarm(since=self.now)
        self.occur(
            Moment.TECHNICAL_RAISED,
            area_id=zone.area_id,
            zone_id=zone.id,
            detail={"repeat": "true"} if alarm is not None else {},
        )

    def technical_normal(self, zone: Zone) -> None:
        """Back to normal: that clears the alarm only once acknowledged."""
        alarm = self.technical.get(zone.id)
        if alarm is not None and alarm.acknowledged:
            self.clear_technical(zone.id)

    def clear_technical(self, zone_id: str) -> None:
        del self.technical[zone_id]
        zone = self.config.zone(zone_id)
        self.occur(
            Moment.TECHNICAL_CLEARED,
            area_id=zone.area_id if zone else None,
            zone_id=zone_id,
        )

    def acknowledge_technical(self) -> _Outcome:
        """One acknowledgement for every technical alarm pending now (part 2
        decision 11). Disarming has no authority here: only this clears it."""
        pending = [z for z, alarm in self.technical.items() if not alarm.acknowledged]
        if not pending:
            return _reject(Reason.NOTHING_TO_ACKNOWLEDGE)
        if (reason := self.authorize(Operation.ACKNOWLEDGE)) is not None:
            return _reject(reason)
        for zone_id in pending:
            self.technical[zone_id] = replace(
                self.technical[zone_id],
                acknowledged_at=self.now,
                acknowledged_channel=self.channel,
            )
        self.occur(
            Moment.TECHNICAL_ACKNOWLEDGED, zone_ids=tuple(pending), channel=self.channel
        )
        for zone_id in pending:
            if zone_id not in self.active:
                self.clear_technical(zone_id)
        return _ACCEPTED

    def zone_deactivated(self, zone: Zone) -> None:
        if zone.channel is Channel.KEY:
            if zone.key is not None and zone.key.on_deactivate is KeyRelease.DISARM:
                self.key_command(zone, KeyCommand.DISARM)
            return
        if zone.channel is Channel.TECHNICAL:
            self.technical_normal(zone)
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

    # --- arming devices (§9.3) -------------------------------------------------

    def process_device_scans(
        self, before: SystemSnapshot, changed_entity: str | None
    ) -> None:
        """A tag was presented, or a remote's button was pressed.

        A scan is momentary, exactly as an event zone's trigger is (§4.4), and
        it is read with the same three rules: only the entity that changed can
        have been scanned, a change out of ``unavailable`` is Home Assistant
        restoring the last scan at startup rather than a new one, and the
        first readable value of a device never seen before is its baseline —
        otherwise adding a tag whose entity already carries last week's
        timestamp would arm the house the moment it is saved.
        """
        for device in self.config.devices:
            if not device.enabled or not device.entity_id:
                continue
            entity = self.entity_state(device.entity_id)
            if device.id not in self.seen_devices:
                if not is_unavailable(entity):
                    self.seen_devices.add(device.id)
                continue
            if device.entity_id != changed_entity:
                continue
            if not scanned(device, before.entity(device.entity_id), entity):
                continue
            self.device_command(device)

    def device_command(self, device: ArmingDevice) -> None:
        """A token acts as its owner would (§9.3, part 2 decision 2).

        Possession is the credential: no code can travel on a tag, so the code
        policy of §8.2 cannot reach it — which is the plain fact §9.3 states
        and the panel repeats where the tag is configured. What does reach it
        is everything else about the person it names: their permissions, their
        validity window, the areas and scenarios they are allowed.
        """
        previous, self.actor = (
            self.actor,
            Actor(
                user_id=device.user_id,
                channel=device.channel,
                device_id=device.id,
                identified=True,
                token=True,
            ),
        )
        try:
            self.device_act(device)
        finally:
            self.actor = previous

    def device_act(self, device: ArmingDevice) -> None:
        command = device.command
        if command is KeyCommand.TOGGLE:
            armed = any(
                rt.state is not AreaState.DISARMED for rt in self.areas.values()
            )
            command = KeyCommand.DISARM if armed else KeyCommand.ARM
        if command is KeyCommand.DISARM:
            outcome = self.disarm(None)
            if outcome.reason is Reason.INVALID_STATE:
                return  # nothing was armed: a tag presented twice is not a failure
        else:
            outcome = self.arm_scenario(
                self.config.scenario(device.scenario_id), force=False
            )
        if not outcome.accepted:
            # Never silent: a tag that did nothing must say why, or the person
            # walks away believing the house is armed (§4.7 says the same of a
            # key, and for the same reason).
            self.occur(
                Moment.ARM_FAILED,
                scenario_id=device.scenario_id,
                zone_ids=outcome.blocking,
                channel=device.channel,
                detail={"reason": outcome.reason.value if outcome.reason else ""},
            )

    def key_command(self, zone: Zone, command: KeyCommand) -> None:
        """A key zone acts as a user would, on every area (decision 13)."""
        assert zone.key is not None
        # The key is the credential: a key switch carries no code, so the
        # policy of §8.2 cannot reach it — exactly as §9.3 says of an NFC tag.
        # What it does carry is the identity configured on the zone, so the
        # log can say whose key was turned, and that user's permissions and
        # validity window still decide whether the turn is accepted.
        previous, self.actor = (
            self.actor,
            Actor(
                user_id=zone.key.user_id,
                channel=KEY_ZONE_CHANNEL,
                identified=zone.key.user_id is not None,
                token=True,
            ),
        )
        try:
            self.key_act(zone, command)
        finally:
            self.actor = previous

    def key_act(self, zone: Zone, command: KeyCommand) -> None:
        assert zone.key is not None
        if command is KeyCommand.TOGGLE:
            armed = any(
                rt.state is not AreaState.DISARMED for rt in self.areas.values()
            )
            command = KeyCommand.DISARM if armed else KeyCommand.ARM
        if command is KeyCommand.DISARM:
            outcome = self.disarm(None)
            if outcome.reason is Reason.INVALID_STATE:
                return  # nothing was armed: a key turned twice is not a failure
        else:
            outcome = self.arm_scenario(
                self.config.scenario(zone.key.scenario_id), force=False
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

    def expire_bypasses(self) -> None:
        """A timed manual bypass ends on its own, with a notification: a zone
        excluded and forgotten is the window somebody comes through (§16)."""
        for zone_id, due in sorted(self.bypass_until.items(), key=lambda i: i[1]):
            if due > self.now:
                continue
            del self.bypass_until[zone_id]
            self.bypassed.pop(zone_id, None)
            zone = self.config.zone(zone_id)
            self.occur(
                Moment.ZONE_REJOINED,
                area_id=zone.area_id if zone else None,
                zone_id=zone_id,
                detail={"bypass": BypassReason.MANUAL.value, "cause": "expired"},
            )

    def expire_running(self) -> None:
        """Switch off what an action switched on, when its time is up (§6.2)."""
        done = [r for r in self.running if r.until is not None and r.until <= self.now]
        for running in done:
            self.extra.append(revert_intent(running, Moment.SIREN_CUTOFF))
        self.running = list(without(self.running, done))

    def stop_running(self, area_id: str, moment: Moment) -> None:
        """Stop this area's sounders, and the incident's if it shares one."""
        incident = self.incident
        in_incident = incident is not None and area_id in incident.area_ids
        stopped = [
            r
            for r in self.running
            if r.area_id == area_id
            or (in_incident and incident is not None and r.incident_id == incident.id)
        ]
        for running in stopped:
            self.extra.append(revert_intent(running, moment))
        self.running = list(without(self.running, stopped))

    def bypass_zone(self, event: BypassZone) -> _Outcome:
        """Exclude a zone by hand, or let it back in (SPEC §5.4, §16).

        Excluding a zone needs a code by default (§8.2): it is the one action
        that leaves a chosen part of the house unwatched while the rest is
        armed.
        """
        zone = self.config.zone(event.zone_id)
        if zone is None or not zone.enabled:
            return _reject(Reason.UNKNOWN_ZONE)
        if event.bypass and not zone.bypassable:
            return _reject(Reason.ZONE_NOT_BYPASSABLE, (zone.id,))
        already = self.bypassed.get(zone.id)
        if event.bypass == (already is not None) and (
            not event.bypass or already is BypassReason.MANUAL
        ):
            return _reject(Reason.INVALID_STATE, (zone.id,))
        if (
            reason := self.authorize(Operation.BYPASS_ZONE, area_ids=(zone.area_id,))
        ) is not None:
            return _reject(reason)
        if not event.bypass:
            del self.bypassed[zone.id]
            self.bypass_until.pop(zone.id, None)
            self.occur(
                Moment.ZONE_REJOINED,
                area_id=zone.area_id,
                zone_id=zone.id,
                channel=self.channel,
                detail={"bypass": BypassReason.MANUAL.value, "cause": "manual"},
            )
            return _ACCEPTED
        self.bypassed[zone.id] = BypassReason.MANUAL
        self.new_bypasses.append(zone.id)
        detail = {"bypass": BypassReason.MANUAL.value}
        if event.seconds:
            self.bypass_until[zone.id] = self.now + timedelta(seconds=event.seconds)
            detail["seconds"] = str(event.seconds)
        else:
            self.bypass_until.pop(zone.id, None)
        self.occur(
            Moment.ZONE_BYPASSED,
            area_id=zone.area_id,
            zone_id=zone.id,
            channel=self.channel,
            detail=detail,
        )
        return _ACCEPTED

    def rejoin_closed_bypasses(self) -> None:
        """Bypassed zones rejoin automatically once seen closed (§5.4)."""
        for zone_id, reason in list(self.bypassed.items()):
            zone = self.config.zone(zone_id)
            if zone is None or reason is BypassReason.MANUAL:
                # A manual exclusion is deliberate: closing the window is
                # precisely why it was excluded (part 3 decision 10).
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
        self,
        area_id: str,
        zone: Zone | None,
        detail: dict[str, str] | None = None,
        group_id: str | None = None,
    ) -> None:
        rt = self.areas[area_id]
        zone_id = zone.id if zone else None
        if rt.state is AreaState.TRIGGERED:
            if zone_id and zone_id not in rt.causes:
                self.set_area(area_id, causes=(*rt.causes, zone_id))
                # Joins the incident: the zone is added, nothing restarts.
                self.announce_incident(
                    area_id, *self.join_incident(area_id, (zone_id,), group_id)
                )
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
        # The incident exists before the occurrence, so the trigger carries
        # its id; the entry route that led here contributes too.
        joined = self.join_incident(area_id, causes, group_id, group_zone=zone_id)
        self.occur(
            Moment.TRIGGERED,
            area_id=area_id,
            zone_id=zone_id,
            scenario_id=rt.scenario_id,
            group_id=group_id,
            detail={"kind": zone.alarm_kind.value if zone else "", **(detail or {})},
        )
        self.announce_incident(area_id, *joined)

    # --- incidents (§5.6) -----------------------------------------------------------

    def join_incident(
        self,
        area_id: str,
        zone_ids: tuple[str, ...],
        group_id: str | None,
        group_zone: str | None = None,
    ) -> tuple[bool, tuple[str, ...]]:
        """Open the incident, or add to it. Returns (opened, new zones).

        The first intrusion trigger opens it; every later one joins it. A zone
        joining after an acknowledgement clears it: someone who acknowledged
        what looked like the cat must hear that a second zone went (part 2
        decision 8). The history of acknowledgements is kept.
        """
        opened = self.incident is None
        if self.incident is None:
            self.incident_seq += 1
            self.incident = Incident(
                id=f"{self.now:%Y%m%d-%H%M%S}-{self.incident_seq}",
                opened_at=self.now,
            )
        incident = self.incident
        known = {(c.area_id, c.zone_id) for c in incident.contributors}
        new = []
        for zone_id in zone_ids or (None,):
            if (area_id, zone_id) in known:
                continue
            of_group = group_id if group_zone is None or zone_id == group_zone else None
            # The profile this zone answered with, recorded as it joins: Phase
            # 4's escalation takes the highest-severity contributor (§5.6), and
            # by then the configuration may have changed.
            profile = effective_profile(
                self.config,
                area_id=area_id,
                zone_id=zone_id,
                group_id=of_group,
                scenario_id=self.areas[area_id].scenario_id
                if area_id in self.areas
                else None,
                moment=Moment.TRIGGERED,
            )
            new.append(
                Contributor(
                    area_id=area_id,
                    zone_id=zone_id,
                    at=self.now,
                    group_id=of_group,
                    profile_id=profile.id if profile else None,
                    severity=profile.severity if profile else None,
                )
            )
        if new:
            self.incident = replace(
                incident,
                contributors=(*incident.contributors, *new),
                acknowledged=False,
            )
        return opened, tuple(c.zone_id for c in new if c.zone_id is not None)

    def announce_incident(
        self, area_id: str, opened: bool, new_zones: tuple[str, ...]
    ) -> None:
        incident = self.incident
        assert incident is not None
        if opened:
            self.occur(
                Moment.INCIDENT_OPENED, area_id=area_id, zone_ids=incident.zone_ids
            )
        elif new_zones:
            self.occur(
                Moment.INCIDENT_JOINED,
                area_id=area_id,
                zone_ids=new_zones,
                detail={"incident_zones": ",".join(incident.zone_ids)},
            )

    def acknowledge(self, channel: str | None, via: str) -> None:
        incident = self.incident
        assert incident is not None
        self.incident = replace(
            incident,
            acknowledged=True,
            acknowledgements=(
                *incident.acknowledgements,
                Acknowledgement(at=self.now, channel=channel, via=via),
            ),
        )
        self.occur(
            Moment.INCIDENT_ACKNOWLEDGED,
            zone_ids=incident.zone_ids,
            channel=channel,
            detail={"via": via},
        )

    def acknowledge_incident(self) -> _Outcome:
        """One acknowledgement acknowledges the whole incident (§5.6)."""
        if self.incident is None or self.incident.acknowledged:
            return _reject(Reason.NOTHING_TO_ACKNOWLEDGE)
        if (reason := self.authorize(Operation.ACKNOWLEDGE)) is not None:
            return _reject(reason)
        self.acknowledge(self.channel, "acknowledge")
        return _ACCEPTED

    def close_incident_if_settled(self) -> None:
        """Closed once acknowledged and every area it touched is disarmed or
        back to armed; a trigger after that opens a new incident (§5.6)."""
        incident = self.incident
        if incident is None or not incident.acknowledged:
            return
        settled = (AreaState.DISARMED, AreaState.ARMED)
        if all(
            self.areas.get(a, AreaRuntime()).state in settled for a in incident.area_ids
        ):
            self.occur(Moment.INCIDENT_CLOSED, zone_ids=incident.zone_ids)
            self.incident = None

    def followed_window(self, zone: Zone) -> tuple[Timer, str] | None:
        """The running entry window, in another area, of a zone this follows.

        With several, the one that ends first: it is when the alarm would sound
        anyway, and inheriting a later one would lengthen the delay (decision 47).
        """
        windows = [
            (rt.timer, followed)
            for rt in self.areas.values()
            if rt.state is AreaState.ENTRY
            and rt.timer is not None
            and rt.timer.kind is TimerKind.ENTRY
            for followed in zone.follows
            if followed in rt.causes
        ]
        return min(windows, key=lambda w: w[0].due, default=None)

    def inherit_entry(
        self, area_id: str, zone: Zone, timer: Timer, source: str
    ) -> None:
        """The walk from the front door into the hall: same deadline, no restart."""
        rt = self.set_area(
            area_id,
            state=AreaState.ENTRY,
            timer=Timer(TimerKind.ENTRY, timer.due),
            causes=(zone.id,),
        )
        self.occur(
            Moment.ENTRY_STARTED,
            area_id=area_id,
            zone_id=zone.id,
            scenario_id=rt.scenario_id,
            detail={
                "inherited_from": source,
                "seconds": str(max(0, int((timer.due - self.now).total_seconds()))),
            },
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

    def authorize(
        self,
        operation: Operation,
        *,
        area_ids: tuple[str, ...] = (),
        scenario: Scenario | None = None,
    ) -> Reason | None:
        """Everything identity has to say about one request (§8.2-§8.4).

        Enforced here and only here (INV-2): the card and the panel transmit,
        the backend decides. The order matters — a channel already locked is
        answered without another attempt counting against it, a wrong code is
        an attempt and counts, a missing code is not an attempt at all.
        """
        actor = self.actor
        if (until := authz.locked_until(self.lockouts, actor, self.now)) is not None:
            self.occur(
                Moment.CODE_REJECTED,
                channel=actor.channel,
                detail={
                    "operation": operation.value,
                    "reason": Reason.LOCKED_OUT.value,
                    "until": until.isoformat(),
                },
            )
            return Reason.LOCKED_OUT
        if actor.code is CodeResult.INVALID:
            self.code_failed(operation)
            return Reason.BAD_CODE
        if (
            reason := authz.check_user(
                self.config,
                actor,
                operation,
                self.now,
                area_ids=area_ids,
                scenario=scenario,
            )
        ) is not None:
            self.occur(
                Moment.CODE_REJECTED,
                channel=actor.channel,
                detail={"operation": operation.value, "reason": reason.value},
            )
            return reason
        areas = tuple(
            area for area in (self.config.area(a) for a in area_ids) if area is not None
        )
        if (
            not actor.token
            and authz.code_required(
                self.config,
                operation,
                now=self.now,
                areas=areas,
                scenario=scenario,
                user=self.config.user(actor.user_id),
                identified=actor.identified,
                channel=actor.channel,
            )
            and not actor.code_verified
        ):
            return Reason.CODE_REQUIRED
        if actor.code_verified:
            # A correct code ends the run of failures on this channel. It does
            # not end a lockout already in force: that is what waiting is for.
            key = authz.lockout_key(actor)
            cleared = authz.clear_failures(self.lockouts.get(key))
            if cleared is None:
                self.lockouts.pop(key, None)
            else:
                self.lockouts[key] = cleared
        return None

    def code_failed(self, operation: Operation) -> None:
        """A wrong code: count it, and shut the channel if it is one too many.

        The admin path is counted like any other and never locked (§8.4), so
        the attempt is still visible in the log and nobody can shut themselves
        out of their own house.
        """
        actor = self.actor
        security = self.config.settings.security
        key = authz.lockout_key(actor)
        lock, locked = authz.register_failure(
            self.lockouts.get(key),
            self.now,
            failures=security.lockout_failures,
            window=security.lockout_window,
            duration=security.lockout_duration,
        )
        if actor.is_admin:
            lock = replace(lock, until=None, strikes=0, locked_at=None)
            locked = False
        self.lockouts[key] = lock
        self.occur(
            Moment.CODE_REJECTED,
            channel=actor.channel,
            detail={"operation": operation.value, "reason": Reason.BAD_CODE.value},
        )
        if locked and lock.until is not None:
            # A tamper attempt on a keypad is a genuine alarm signal, so this
            # is a moment a response profile can answer (§6.1, §8.4).
            self.occur(
                Moment.LOCKOUT,
                channel=actor.channel,
                detail={
                    "until": lock.until.isoformat(),
                    "seconds": str(int((lock.until - self.now).total_seconds())),
                    "strike": str(lock.strikes),
                },
            )

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
        force: bool,
        to_bypass: list[Zone],
    ) -> None:
        channel = self.channel
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
                user_id=self.actor.user_id,
                device_id=self.actor.device_id,
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
            user_id=rt.user_id,
            device_id=rt.device_id,
        )

    def arming_failed(self, area_id: str, zones: list[Zone], reason: Reason) -> None:
        rt = self.areas[area_id]
        self.occur(
            Moment.ARM_FAILED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=tuple(z.id for z in zones),
            channel=rt.channel,
            user_id=rt.user_id,
            device_id=rt.device_id,
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

    def arm_scenario(self, scenario: Scenario | None, *, force: bool) -> _Outcome:
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
        for operation, areas in (
            (Operation.ARM, to_arm),
            # A switch also disarms what only the old scenario armed, so the
            # areas it leaves behind have their say in the policy too.
            *(((Operation.CHANGE_SCENARIO, (*to_arm, *leaving)),) if switching else ()),
            *(((Operation.FORCE_ARM, to_arm),) if force else ()),
        ):
            reason = self.authorize(operation, area_ids=tuple(areas), scenario=scenario)
            if reason is not None:
                return _reject(reason)
        outcome, to_bypass = self.check_arming(to_arm, force)
        if not outcome.accepted:
            return outcome

        for area_id in leaving:
            self.disarm_area(area_id, self.channel)
        for area_id in target:
            if area_id not in to_arm:
                self.set_area(area_id, scenario_id=scenario.id)
        self.active_scenario_id = scenario.id
        self.begin_arming(to_arm, scenario, force, to_bypass)
        return _ACCEPTED

    def arm_mode(self, event: ArmModeRequest) -> _Outcome:
        """The master panel arms the one scenario with this mode (decision 8)."""
        matches = [s for s in self.config.scenarios if s.ha_master_state == event.mode]
        if not matches:
            return _reject(Reason.NO_SCENARIO_FOR_MODE)
        if len(matches) > 1:
            return _reject(Reason.AMBIGUOUS_MODE)
        return self.arm_scenario(matches[0], force=event.force)

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
            reason = self.authorize(operation, area_ids=(event.area_id,))
            if reason is not None:
                return _reject(reason)
        outcome, to_bypass = self.check_arming((event.area_id,), event.force)
        if not outcome.accepted:
            return outcome
        self.begin_arming((event.area_id,), None, event.force, to_bypass)
        return _ACCEPTED

    # --- disarming --------------------------------------------------------------

    def disarm(self, area_ids: tuple[str, ...] | None) -> _Outcome:
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
        scenario = self.config.scenario(self.active_scenario_id)
        reason = self.authorize(
            Operation.DISARM, area_ids=tuple(targets), scenario=scenario
        )
        if reason is not None:
            return _reject(reason)
        if self.actor.duress:
            # The house disarms exactly as it always does, and nothing the
            # person at the keypad can see says otherwise (§8.1). What is
            # different is this occurrence, which a profile can answer.
            self.occur(
                Moment.DURESS,
                channel=self.channel,
                detail={"areas": ",".join(targets)},
            )
        for area_id in targets:
            self.disarm_area(area_id, self.channel)
        return _ACCEPTED

    def disarm_area(self, area_id: str, channel: str | None) -> None:
        """Disarm one area. Disarming an area the incident touched is also its
        acknowledgement (§7.2, part 2 decision 3). It never touches the
        technical channel (§5.5)."""
        rt = self.areas[area_id]
        self.occur(
            Moment.DISARMED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=rt.causes if rt.memory else (),
            channel=channel,
            detail={"from": rt.state.value},
        )
        incident = self.incident
        if (
            incident is not None
            and not incident.acknowledged
            and area_id in incident.area_ids
        ):
            self.acknowledge(channel, "disarm")
        # Disarming stops the sirens and abandons what a delay was still
        # holding for this area: the alarm is over (§5.2).
        self.stop_running(area_id, Moment.DISARMED)
        self.pending_runs = [r for r in self.pending_runs if r.area_id != area_id]
        self.clear_area(area_id)

    def clear_area(self, area_id: str) -> None:
        """Back to a plain disarmed area: no timer, no memory, no bypasses."""
        self.areas[area_id] = AreaRuntime()
        for zone in self.config.zones_in((area_id,)):
            # A manual exclusion with a duration outlives the disarm; one
            # without ends with this arming, as on a real panel (decision 10).
            if self.bypassed.get(zone.id) is BypassReason.MANUAL and (
                zone.id in self.bypass_until
            ):
                continue
            if self.bypassed.pop(zone.id, None) is not None:
                self.bypass_until.pop(zone.id, None)
        self.forget_activations(area_id)
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
        occurrences = tuple(self.occurrences)
        ctx = PlanContext(
            config=self.config,
            snapshot=replace(self.snapshot, entities=self.entities),
            now=self.now,
            areas=self.areas,
            incident=self.incident,
            active_zones=frozenset(self.active),
        )
        plan, self.run_seq = plan_occurrences(ctx, occurrences, self.run_seq)
        # Sequences a delay held back and whose time has come (decision 5).
        due = [r for r in self.pending_runs if r.due <= self.now]
        self.pending_runs = [r for r in self.pending_runs if r.due > self.now]
        for run in due:
            plan.extend(resume(ctx, run))
        self.pending_runs.extend(plan.pending)
        self.running.extend(plan.running)
        if self.incident is not None and plan.started:
            started = dict.fromkeys((*self.incident.actions_started, *plan.started))
            self.incident = replace(self.incident, actions_started=tuple(started))
        state = RuntimeState(
            areas=self.areas,
            active_scenario_id=self.active_scenario_id,
            bypassed=self.bypassed,
            active_zones=frozenset(self.active),
            seen_zones=frozenset(self.seen),
            seen_devices=frozenset(self.seen_devices),
            faults=self.faults,
            technical=self.technical,
            incident=self.incident,
            incident_seq=self.incident_seq,
            windows=self.windows,
            chime_enabled=self.chime_enabled,
            bypass_until=self.bypass_until,
            pending_runs=tuple(self.pending_runs),
            running=tuple(self.running),
            run_seq=self.run_seq,
            lockouts=self.lockouts,
        )
        return Decision(
            at=self.now,
            accepted=outcome.accepted,
            state=state,
            reason=outcome.reason,
            blocking_zones=outcome.blocking,
            bypassed_zones=tuple(self.new_bypasses),
            occurrences=occurrences,
            actions=(
                *self.extra,
                *plan.intents,
                *self.chime_intents(occurrences),
            ),
        )

    def chime_intents(
        self, occurrences: tuple[Occurrence, ...]
    ) -> tuple[ActionIntent, ...]:
        """The chime is a setting, not a profile (§6.6). The Decision carries
        everything the executor needs: it never reads the configuration."""
        chime = self.config.chime
        names = {z.id: z.name for z in self.config.zones}
        intents = []
        for occurrence in occurrences:
            if occurrence.moment is not Moment.CHIME or occurrence.zone_id is None:
                continue
            intents.append(
                ActionIntent(
                    action_id="chime",
                    kind="chime",
                    moment=Moment.CHIME,
                    placeholders={"zone": names.get(occurrence.zone_id, "")},
                    params={
                        "targets": tuple(
                            t
                            for t in occurrence.detail.get("targets", "").split(",")
                            if t
                        ),
                        "mode": chime.mode.value,
                        "sound": chime.sound,
                        "tts_entity": chime.tts_entity,
                        "volume": chime.volume,
                    },
                )
            )
        return tuple(intents)


def _window_detail(
    window: Verification, activations: tuple[Activation, ...]
) -> dict[str, str]:
    """What the trace shows: "Group X: 1 of 2 within 60 s" (§4.8)."""
    return {
        "verification": window.kind,
        "count": str(window.count(activations)),
        "n": str(window.n),
        "window": str(window.window),
    }
