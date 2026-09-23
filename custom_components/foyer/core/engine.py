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

from collections.abc import Container
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from . import (
    authz,
    escalation as escalation_engine,
    health as health_engine,
    rules as rules_engine,
)
from .models import (
    CUSTOM_BYPASS,
    ESCALATION_RESTART_GRACE,
    FAULT_STATES,
    MAX_WALK_TEST_TIMEOUT,
    MAX_WALK_TEST_TOTAL,
    MIN_WALK_TEST_TIMEOUT,
    AcknowledgeIncident,
    Acknowledgement,
    AcknowledgeTechnical,
    ActionIntent,
    ActionKind,
    Activation,
    Actor,
    AreaRuntime,
    AreaState,
    ArmAreaRequest,
    ArmingDevice,
    ArmModeRequest,
    ArmPolicy,
    ArmRequest,
    AutoRule,
    BypassReason,
    BypassZone,
    CancelAutoAction,
    Channel,
    ChannelFault,
    ChannelHealth,
    CodeAttempt,
    CodeResult,
    Contributor,
    Decision,
    Detection,
    DeviceContact,
    DeviceTransport,
    DisarmRequest,
    EntityState,
    EntryMode,
    Escalation,
    EscalationKind,
    Event,
    FoyerConfig,
    HealthReport,
    Incident,
    KeyCommand,
    KeyRelease,
    Lockout,
    Moment,
    Occurrence,
    Operation,
    PendingRuleAction,
    Radio,
    RadioHealth,
    Reason,
    RuleActionKind,
    RuleBlock,
    RuleRuntime,
    RuleTriggerKind,
    RuntimeState,
    Scenario,
    ScheduledStep,
    SetAutoArming,
    SetChime,
    SetSuspension,
    Startup,
    Suspension,
    SuspensionKind,
    SystemHealth,
    SystemSnapshot,
    TechnicalAlarm,
    Tick,
    Timer,
    TimerKind,
    WalkTest,
    WalkTestRequest,
    Zone,
    ZoneStateChanged,
)
from .response import (
    TECHNICAL_MOMENTS,
    PlanContext,
    audible_targets,
    chime_suppressed,
    effective_profile,
    escalation_intent,
    plan_occurrences,
    recipients_for,
    resume,
    revert_intent,
    variables,
    without,
)
from .triggers import (
    NEVER_FIRED,
    battery_low,
    fault_cause,
    fires_momentarily,
    has_baseline,
    is_active,
    is_unavailable,
    scanned,
    supervision_due,
)
from .verification import Verification, all_windows, counter_of, groups

KEY_ZONE_CHANNEL = "key_zone"
# The channel an automatic rule acts on (§9.4). The engine's own word: §9.1
# lets a request claim only `api` or `automation`, so nothing outside can
# arrive wearing this one (decision 84).
AUTO_RULE_CHANNEL = "auto_rule"

# Why a step did not go out, when it was the restart that swallowed it. The
# other reasons are response.SKIP_*, which the panel already translates.
RESTART = "restart"

# What a row says when the name on it was asserted by the request and not
# established by a code or a token (§9.1, decision 88).
_CLAIMED = {"attributed": "claimed"}

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
    run.note_transport()
    run.expire_windows()
    run.expire_bypasses()
    run.expire_running()
    run.process_due_timers()
    # Before the zones are read, so a walk test whose time is up does not
    # swallow the detection that arrives in the same call: the house is
    # answering again from the instant the auto-exit falls due (§5.3).
    run.expire_walk_test()

    changed: str | None = None
    if isinstance(event, ZoneStateChanged):
        changed = event.entity_id
        run.entities[event.entity_id] = event.new
    run.process_zone_changes(snapshot, changed)
    run.process_device_scans(snapshot, changed)

    outcome = _ACCEPTED
    if isinstance(event, ArmRequest):
        outcome = run.arm_scenario(
            config.scenario(event.scenario_id),
            force=event.force,
            skip_exit_delay=event.skip_exit_delay,
        )
    elif isinstance(event, ArmModeRequest):
        outcome = run.arm_mode(event)
    elif isinstance(event, ArmAreaRequest):
        outcome = run.arm_area(event)
    elif isinstance(event, DisarmRequest):
        outcome = run.disarm(event.area_ids)
    elif isinstance(event, AcknowledgeIncident):
        outcome = run.acknowledge_incident(event)
    elif isinstance(event, AcknowledgeTechnical):
        outcome = run.acknowledge_technical(event)
    elif isinstance(event, BypassZone):
        outcome = run.bypass_zone(event)
    elif isinstance(event, SetChime):
        run.set_chime(event.enabled)
    elif isinstance(event, WalkTestRequest):
        outcome = run.walk_test_request(event)
    elif isinstance(event, CodeAttempt):
        outcome = run.code_attempt(event)
    elif isinstance(event, CancelAutoAction):
        outcome = run.cancel_auto_action(event)
    elif isinstance(event, SetAutoArming):
        outcome = run.set_auto_arming(event.enabled)
    elif isinstance(event, SetSuspension):
        outcome = run.set_suspension(event)
    elif isinstance(event, HealthReport):
        run.apply_health_report(event)
    elif isinstance(event, Startup):
        # How long the gap was, measured rather than described: the log grades
        # a configuration reload and an hour with the integration disabled
        # differently, and only the number can tell them apart.
        gap = (
            int((now - event.down_since).total_seconds()) if event.down_since else None
        )
        run.restarted = True
        run.gap_since = event.down_since
        run.occur(
            Moment.HA_RESTARTED,
            detail={
                "down_since": event.down_since.isoformat() if event.down_since else "",
                "up_at": now.isoformat(),
                "cause": event.cause,
                "gap_seconds": str(max(0, gap)) if gap is not None else "",
            },
        )
    elif isinstance(event, DeviceContact):
        # Nothing to decide: `note_transport` above has already recorded
        # whether this keypad reached the endpoint encrypted (§9.2.1).
        pass
    elif not isinstance(event, ZoneStateChanged | Tick):
        raise TypeError(f"unsupported event: {event!r}")

    # After the event, so a Cancel arriving in the same instant as a
    # countdown's deadline stops it (§9.4), and never while Home Assistant is
    # still starting: half the entities are missing, and "every person is
    # not_home" would be true of a house full of people.
    if not snapshot.settling:
        run.run_rules()
    run.rejoin_closed_bypasses()
    if not snapshot.settling or isinstance(event, Startup):
        run.reconcile_faults()
        run.reconcile_batteries()
        # Last of the reconciliations, because it reads what the first one
        # wrote: a zone fault is one of the causes system health reports
        # (§13), and reading a set the same call is still filling would make
        # the health sensor lag the fault by one event.
        run.reconcile_health()
    run.close_incident_if_settled()
    return run.decision(outcome)


# --- read models, pure as well -----------------------------------------------------


def arm_blockers(
    snapshot: SystemSnapshot,
    config: FoyerConfig,
    area_ids: tuple[str, ...] | frozenset[str],
    now: datetime,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(faulted, open) zones that would block arming these areas right now.

    The world is read first, exactly as a decision reads it: the stored set
    of active zones is what the last decision saw, and this question is about
    now. Page 9's "blocks arming" column and the refusal a real arm request
    would give must never be able to disagree (§11.1).
    """
    run = _Run(snapshot, config, now)
    run.refresh_active()
    faulted, open_ = run.blockers(area_ids)
    return tuple(z.id for z in faulted), tuple(z.id for z in open_)


def walk_test_zones(
    config: FoyerConfig, bypassed: Container[str] = ()
) -> tuple[str, ...]:
    """The zones a walk should reach, so that silence can be a finding (§11.3).

    Intrusion zones that are enabled and not excluded. An `always_on` zone is
    left out: it is live rather than under test, and nobody sets off the
    smoke detector to prove it works.

    A read model, here rather than in the runtime, because the engine answers
    the same question when it says which zones never reacted — and a table
    listing a zone the engine had not expected would be a finding nobody
    could act on.
    """
    return tuple(
        z.id
        for z in config.zones
        if z.enabled
        and z.channel is Channel.INTRUSION
        and not z.always_on
        and z.id not in bypassed
    )


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
    if state.walk_test is not None:
        # The auto-exit is a timer like any other (§5.3), which is why it is
        # in the state and not in memory: a restart must not leave a house
        # inhibited with nothing due to end it (INV-3).
        dues.append(state.walk_test.deadline())
    dues.extend(run.due for run in state.pending_runs)
    # An escalation step is a timer like any other, and the reason it is in
    # the state rather than in memory is the same: a restart must not leave
    # an alarm nobody answered with nothing due to chase it (INV-3).
    dues.extend(escalation_engine.wakeups(state.escalations, config, now))
    dues.extend(r.until for r in state.running if r.until is not None)
    # Automatic rules (§9.4): the countdown that is running, the moment a
    # level trigger's "for N minutes" matures, the next occurrence of a time
    # rule, the hour an active window opens, and the end of a suspension —
    # every one of them a moment at which the house may act on its own, and
    # none of them announced by anything else.
    # Not while Home Assistant is still starting: `decide` does not run the
    # rules then, so a due already past would be a wake-up that wakes,
    # consumes nothing, reschedules itself for the same moment and does it
    # again — a decision and a state save per turn, through the whole of a
    # cold boot (found in review). The Startup event that ends the settling
    # period runs the rules itself.
    if not snapshot.settling:
        dues.extend(p.due for p in state.pending_rules)
    for suspension in state.suspensions:
        dues.extend(
            at
            for at in (suspension.start, suspension.until)
            if at is not None and at > now
        )
    quiet_since = rules_engine.last_interior_motion(
        config,
        state.active_zones,
        {
            zone.id: snapshot.entity(zone.entity_id).last_changed
            for zone in config.zones
        },
        now,
    )
    for rule in config.rules:
        if not rule.enabled:
            continue
        runtime = state.rule(rule.id)
        for at in (
            rules_engine.matures_at(rule, runtime),
            rules_engine.next_occurrence(rule, now, snapshot.timezone),
            rules_engine.next_window_open(rule, now, snapshot.timezone),
            # The house going quiet is the one guard nothing else announces:
            # a hall that stops moving raises no event at all.
            rules_engine.quiet_at(config, rule, quiet_since),
        ):
            if at is not None and at > now:
                dues.append(at)
    # The RF confirmation window (§12.5, part 1 decision 8). Nothing else
    # wakes the engine for it: the zones went quiet a minute ago and will not
    # report again — being quiet is the whole point — so without this the
    # suspicion would sit unconfirmed until the next door opened.
    for radio in config.health.radios:
        current = state.health.radio(radio.id)
        if radio.enabled and current.suspected_since and not current.confirmed:
            due = current.suspected_since + timedelta(seconds=config.health.rf_confirm)
            # Only a deadline that is still ahead, as every other branch of
            # this function does. A deadline already past is one the next
            # decision settles anyway, and scheduling it would be a wake-up
            # at ``now`` — which, while Home Assistant is still starting and
            # reconcile_health is deliberately skipped, nothing can consume:
            # the Tick would decide nothing, reschedule the same past time
            # and fire again, spinning through the whole of startup.
            if due > now:
                dues.append(due)
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


@dataclass(frozen=True, slots=True)
class _RuleDecision:
    """What an automatic rule would do now, or what is stopping it (§9.4).

    ``area_ids`` is what the action will actually touch, with any perimeter
    area already taken out, and ``refused`` is what was taken out — for a
    ``disarm`` the areas it may not have, and for a ``switch`` the areas that
    will stay armed instead of being dropped (part 2 decision 6).
    """

    action: RuleActionKind
    scenario_id: str | None = None
    area_ids: tuple[str, ...] = ()
    refused: tuple[str, ...] = ()
    suspension: Suspension | None = None
    substituted: bool = False
    block: RuleBlock | None = None

    @property
    def disarms(self) -> bool:
        """Whether running this would leave part of the house unprotected.

        Read off ``area_ids`` — what the action would actually disarm — and
        not off the word on the rule. An ``arm`` action is the same call as a
        ``switch`` (``arm_scenario``), so with a scenario already running it
        drops the areas the new one does not name just the same (§4.6.1).
        """
        return bool(self.area_ids)


def _spend(
    rule: AutoRule,
    runtime: RuleRuntime,
    occurrence: datetime | None,
    acted: bool = False,
) -> RuleRuntime:
    """Record that this turn of the rule has been dealt with (part 2 decision 4).

    A ``time`` occurrence is spent whatever came of it: 23:00 happens once. A
    ``presence`` arrival is spent by the arrival itself. A level trigger
    latches only when it actually acts, so a guard that clears two minutes
    later still finds a rule willing to arm the house.
    """
    if rule.trigger.kind is RuleTriggerKind.TIME:
        return replace(runtime, last_occurrence=occurrence or runtime.last_occurrence)
    if rule.trigger.kind is RuleTriggerKind.PRESENCE:
        return runtime
    return replace(runtime, latched=True) if acted else runtime


def _rule_detail(rt: AreaRuntime) -> dict[str, str]:
    """Which automatic rule armed this area, for the row written later (§9.4)."""
    if rt.rule_id is None:
        return {}
    return {"rule": rt.rule_name or "", "rule_id": rt.rule_id}


def _suspension_detail(suspension: Suspension) -> dict[str, str]:
    """What a suspension puts on the row that mentions it (§9.4).

    The name travels into the log because the log is what lasts: the object
    expires, and "Boiler engineer" six months later is the whole reason the
    expected-visitor window is a first-class thing rather than a checkbox.
    """
    return {
        "suspension": suspension.id,
        "suspension_kind": suspension.kind.value,
        "name": suspension.name or "",
        "rules": ",".join(suspension.rule_ids),
        "until": suspension.until.isoformat() if suspension.until else "",
        "reduced": suspension.reduced_scenario_id or "",
    }


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
        # The keypads whose last request crossed the network in the clear
        # (§9.2.1): what keeps page 8's warning up until one arrives
        # encrypted, across a restart.
        self.in_clear = set(
            state.in_clear
            & {d.id for d in config.devices if d.transport is DeviceTransport.HTTP}
        )
        self.faults = frozenset(state.faults & zone_ids)
        self.low_batteries = frozenset(state.low_batteries & zone_ids)
        self.entities: dict[str, EntityState] = dict(snapshot.entities)
        self.timezone = snapshot.timezone
        self.occurrences: list[Occurrence] = []
        self.new_bypasses: list[str] = []
        # Filled by check_arming, and empty for every event that is not an
        # arming attempt: the warning belongs to the attempt (part 1 decision 2).
        self.low_battery_zones: tuple[str, ...] = ()
        # Which setting asked for the code, when a request was refused for
        # want of one (§8.2): for the UI to name it.
        self.code_required_by: tuple[str, str | None] | None = None
        # Who is asking. decide() fills it from the event; a timer or a zone
        # opening has no actor, and the default one identifies nobody.
        self.actor = Actor()
        # Failed code attempts, per channel and device (§8.4). Persisted with
        # everything else, because a lockout a restart clears is an invitation
        # to restart Home Assistant.
        self.lockouts: dict[str, Lockout] = dict(state.lockouts)
        # The walk test (§11.3). ``inhibiting`` is separate from it on
        # purpose: a decision that *begins* inside a walk test holds its
        # response back all the way through, so ending one does not let the
        # disarm it performs announce itself while the arming it performed
        # never did.
        self.walk_test: WalkTest | None = state.walk_test
        self.inhibiting = state.walk_test is not None
        # The technical channel: never read or written by the area machine.
        self.technical: dict[str, TechnicalAlarm] = {
            z: a for z, a in state.technical.items() if z in zone_ids
        }
        # Escalations in progress (§7.2), and whether this call is a restart.
        # ``restarted`` is what tells the escalation that an overdue step is
        # overdue because nobody was running, rather than because its time
        # has simply come (part 1 decision 5). It is a flag and not the gap
        # itself, because a Startup that cannot say how long the gap was is
        # still a restart: "unknown" is read as an outage, not as none.
        self.escalations: list[Escalation] = [
            e
            for e in state.escalations
            # A technical escalation outlives nothing: the channel is empty
            # when the zone that raised it has been deleted, and an
            # escalation nobody can acknowledge — acknowledge_technical
            # refuses when nothing is pending — would run to its end
            # calling people about an alarm that no longer exists.
            if e.kind is not EscalationKind.TECHNICAL or self.technical
        ]
        self.restarted = False
        self.gap_since: datetime | None = None
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
        # Automatic arming rules (§9.4). A countdown or a memory belonging to
        # a rule that has been deleted is dropped: it names nothing, and
        # firing it would arm the house on an instruction nobody can read.
        rule_ids = {r.id for r in config.rules}
        self.auto_arming = state.auto_arming
        # Kept even when the rule has gone: run_rules cancels it with a row
        # rather than letting it disappear between two restarts.
        self.pending_rules = list(state.pending_rules)
        self.suspensions = [
            s
            for s in state.suspensions
            if not s.rule_ids or any(r in rule_ids for r in s.rule_ids)
        ]
        self.rules_runtime: dict[str, RuleRuntime] = {
            r: rt for r, rt in state.rules.items() if r in rule_ids
        }
        self.pending_seq = state.pending_seq
        # What every row a rule causes carries, so the log can say which rule
        # armed the house without each call site remembering to add it (§9.4).
        self.rule_detail: dict[str, str] = {}
        # System health (§12): state of the system itself, beside the areas
        # and never in them. A channel or a radio that configuration has
        # removed is dropped here rather than carried for ever, the same rule
        # every other map in this constructor follows.
        health = state.health
        known_channels = set(health_engine.configured_channels(config))
        radio_ids = {r.id for r in config.health.radios}
        self.mains_lost_since = health.mains_lost_since
        self.channels = {
            key: value
            for key, value in health.channels.items()
            if key in known_channels
        }
        self.watchdog = health.watchdog
        self.radios = {
            key: value for key, value in health.radios.items() if key in radio_ids
        }
        self.quiet_since = {
            zone_id: at
            for zone_id, at in health.quiet_since.items()
            if zone_id in zone_ids
        }
        self.unknown_zones = set(health.unknown_zones & zone_ids)
        # Carried, never decided here: the engine has no opinion about a
        # card in Home Assistant's Settings, and dropping the set on the
        # next decision would undo every acknowledgement.
        self.acknowledged_issues = health.acknowledged_issues
        # Radios the configuration no longer has, kept for one more call so
        # reconcile_radios can end what they were reporting with a row. A
        # suspicion that simply disappeared from the log would be the one row
        # somebody looks for afterwards, and deleting a radio must not be a
        # quieter way of doing what disabling one announces.
        self.gone_radios = {
            key: value for key, value in health.radios.items() if key not in radio_ids
        }

    # --- world ----------------------------------------------------------------

    def entity(self, zone: Zone) -> EntityState:
        return self.entity_state(zone.entity_id)

    def entity_state(self, entity_id: str) -> EntityState:
        return self.entities.get(entity_id) or EntityState(state=None)

    def battery(self, zone: Zone) -> EntityState:
        return self.entity_state(zone.battery_entity_id or "")

    def fault(self, zone: Zone) -> str | None:
        return fault_cause(zone, self.entity(zone), self.now, self.battery(zone))

    def low_battery(self, zone: Zone) -> bool:
        return battery_low(
            zone, self.battery(zone), self.config.settings.low_battery_threshold
        )

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
        # Whether this occurrence replays somebody else's request — an
        # arming whose exit delay ran out, a walk test timing out — rather
        # than being caused by the one in hand. Such a row names its own
        # device and person, and the current request's transport notes do
        # not belong on it (found in review).
        replayed = "user_id" in kwargs or "device_id" in kwargs
        if kwargs.get("user_id") and "user_name" not in kwargs:
            named = self.config.user(kwargs["user_id"])
            kwargs["user_name"] = named.name if named else None
        if self.rule_detail and kwargs.get("channel") == AUTO_RULE_CHANNEL:
            # Which rule did this, on every row it causes (§9.4). Added here
            # rather than at each call site, because the rows a rule produces
            # are written by the ordinary arming and disarming paths, which
            # know nothing about rules and should not have to.
            kwargs["detail"] = {**self.rule_detail, **kwargs.get("detail", {})}
        if kwargs.get("channel") == actor.channel and "user_id" not in kwargs:
            if actor.user_id is not None:
                kwargs["user_id"] = actor.user_id
                user = self.config.user(actor.user_id)
                kwargs["user_name"] = user.name if user else None
                if actor.claimed:
                    kwargs["detail"] = {**kwargs.get("detail", {}), **_CLAIMED}
            if actor.device_id is not None:
                kwargs["device_id"] = actor.device_id
        # Every row a request to the device endpoint causes says whether
        # it arrived in the clear (§9.2.1). For the keypad's own rows that is
        # read from the keypad — so the `armed` row its exit delay writes
        # thirty seconds later says it too — and for a request with no
        # device behind it, from the request, with where it came from:
        # without that, a token-guessing loop in the log is a list of
        # refusals from nowhere.
        extra: dict[str, str] = {}
        if kwargs.get("device_id") in self.in_clear:
            extra["encrypted"] = "false"
        if (
            not replayed
            and kwargs.get("channel") == actor.channel
            and actor.device_id is None
            and actor.address
        ):
            extra["address"] = actor.address
            if actor.encrypted is False:
                extra["encrypted"] = "false"
        if extra:
            kwargs["detail"] = {**kwargs.get("detail", {}), **extra}
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
            if group.suppress and not self.can_satisfy(group):
                # Too few members left able to count — excluded by hand,
                # bypassed at arming, or in fault — for the group ever to be
                # satisfied. Held back now, this activation would be held
                # for ever: an intruder seen by the one working PIR and
                # silence. It acts on its own, as it would with no group
                # watching it (found in review).
                return True, group.group_id
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

    def can_satisfy(self, group: Verification) -> bool:
        """Whether enough members are left able to count towards the group."""
        able = [
            m
            for m in group.members
            if m not in self.bypassed
            and (zone := self.config.zone(m)) is not None
            # Unable only when its own entity cannot report: a supervision
            # or battery fault leaves a detector that still counts.
            and not is_unavailable(self.entity(zone))
        ]
        return len(able) >= group.n

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
        # After the stop, so that what it switches is not switched back.
        self.occur(
            Moment.ALARM_ENDED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            zone_ids=rt.causes,
            detail={"cause": "siren_cutoff"},
        )
        # And what a delay was still holding for this alarm. §6.2 says a
        # siren never sounds beyond the cutoff and that the cutoff stops what
        # it started — a sequence whose `delay` outlasted the cutoff started
        # the bell afterwards, on an armed house, for its whole duration
        # (found in review). The technical channel keeps its own, as it keeps
        # everything else (§5.5).
        incident = self.incident
        self.pending_runs = [
            r
            for r in self.pending_runs
            if r.moment in TECHNICAL_MOMENTS
            or not (
                r.area_id == area_id
                or (incident is not None and r.incident_id == incident.id)
            )
        ]
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

    def refresh_active(self) -> set[str]:
        """Read every zone's trigger from the world, and return what it was.

        Side-effect free on purpose: it is the first thing a decision does,
        and it is also what the read models of §11.1 need — a table that
        said "does not block" from a stale set while an arming refused would
        be worse than no table at all.
        """
        previous = set(self.active)
        self.active = {
            z.id
            for z in self.config.zones
            if z.enabled and is_active(z, self.entity(z), z.id in previous)
        }
        return previous

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
        previous = self.refresh_active()
        for zone in self.config.zones:
            if not zone.enabled:
                # A key zone is forgotten while it is off, so that switching
                # it back on is a baseline like saving it new (§4.7): one
                # re-enabled with its switch on must not disarm the house.
                # Only a key: a smoke detector or a tamper switch re-enabled
                # while it is detecting is an alarm, and a baseline would
                # have swallowed it (second review).
                if zone.channel is Channel.KEY:
                    self.seen.discard(zone.id)
                continue
            if zone.id not in self.seen:
                if has_baseline(zone, self.entity(zone)):
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
        if self.walk_test is not None and not zone.always_on:
            # It saw somebody, and that is the whole of what a walk test
            # asks of it (§11.3, part 2 decision 3). Recorded whatever the
            # area is doing: a zone in an area that failed to arm still
            # reacted, and "it detected me but nothing was watching" is a
            # more useful answer than a missing row.
            #
            # The chime is still *decided* here, and then held back with
            # every other action: §6.6 expects an armed area and no chime,
            # but an area that could not arm would chime through the whole
            # walk, and the trace should say it was held rather than that it
            # was never considered.
            if effect is None:
                self.chime(zone, rt)
            self.walk_test_detection(zone)
            return
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

    # --- walk test (§11.3) ---------------------------------------------------------

    def note_transport(self) -> None:
        """Remember whether this keypad's request arrived encrypted (§9.2.1).

        Whatever the request goes on to be — accepted, refused, a status —
        it crossed the network, and whether its token and code could be read
        on the way is a fact about the keypad, not about the request.
        """
        actor = self.actor
        if actor.device_id is None or actor.encrypted is None:
            return
        if actor.encrypted:
            self.in_clear.discard(actor.device_id)
        else:
            self.in_clear.add(actor.device_id)

    def code_attempt(self, event: CodeAttempt) -> _Outcome:
        """A code offered to a command that decides for itself (§8.4).

        Only the lockout half: whether this channel is shut, whether the code
        was wrong, and the counter either way. What the caller may *do* with
        a right code is its own question — a log read asks for `view_log`,
        not for the permission this operation maps to — so it stays with the
        caller, and this stays the one place a wrong code is counted.
        """
        if (reason := self.check_code(event.operation)) is not None:
            return _reject(reason)
        self.code_cleared()
        return _ACCEPTED

    def walk_test_request(self, event: WalkTestRequest) -> _Outcome:
        """Enter or leave the walk test. One operation, §8.2 like any other."""
        if event.enable == (self.walk_test is not None):
            return _reject(Reason.INVALID_STATE)
        if (reason := self.authorize(Operation.WALK_TEST)) is not None:
            return _reject(reason)
        if event.enable:
            return self.start_walk_test(event.duration)
        self.end_walk_test("manual")
        return _ACCEPTED

    def walk_test_window(self, duration: int | None) -> int:
        """How long the test runs without a detection (§5.3, part 2 decision 5).

        The installation's setting is the ceiling and ``duration`` may only
        ask for less: §5.3 calls the auto-exit mandatory and non-disableable,
        so there is no number a caller can send that lengthens it.
        """
        configured = min(
            max(self.config.settings.walk_test_timeout, MIN_WALK_TEST_TIMEOUT),
            MAX_WALK_TEST_TIMEOUT,
        )
        if duration is None:
            return configured
        return max(MIN_WALK_TEST_TIMEOUT, min(int(duration), configured))

    def start_walk_test(self, duration: int | None) -> _Outcome:
        """Arm every area, then hold the response back (part 2 decisions 2, 7).

        Every area, because a walk test is walked through the whole house and
        §9.1's signature has no scenario in it. An area that cannot arm — an
        open window, a zone in fault — simply does not, and the §9.1 answer
        names the zones: a window left open must not stop somebody finding
        out that the garage PIR is dead.

        There is no exit delay. The person is inside the house and about to
        walk it; a test that spent its first thirty seconds not watching
        anything would report those zones as never having reacted.
        """
        window = self.walk_test_window(duration)
        blocking: list[str] = []
        armed: list[str] = []
        low: list[str] = []
        for area_id in self.areas:
            if self.areas[area_id].state is not AreaState.DISARMED:
                continue
            outcome, _ = self.check_arming((area_id,), False)
            # check_arming answers one area at a time and records that area's
            # dying batteries; the answer is about the whole request, so they
            # are collected rather than overwritten (part 1 decision 2).
            low.extend(self.low_battery_zones)
            if not outcome.accepted:
                blocking.extend(outcome.blocking)
                continue
            armed.append(area_id)
        self.low_battery_zones = tuple(dict.fromkeys(low))
        user = self.config.user(self.actor.user_id)
        self.walk_test = WalkTest(
            started_at=self.now,
            until=self.now + timedelta(seconds=window),
            hard_until=self.now + timedelta(seconds=MAX_WALK_TEST_TOTAL),
            window=window,
            armed_areas=tuple(armed),
            user_id=self.actor.user_id,
            user_name=user.name if user else None,
            channel=self.actor.channel,
            device_id=self.actor.device_id,
        )
        self.inhibiting = True
        # Armed after the walk test exists, so the arming this performs is
        # already inhibited: §11.3 inhibits every action, and "the house has
        # armed" is an action like the rest.
        self.begin_arming(tuple(armed), None, False, [], skip_exit_delay=True)
        self.occur(
            Moment.WALK_TEST_STARTED,
            channel=self.actor.channel,
            detail={
                "window": str(window),
                "until": self.walk_test.until.isoformat(),
                "hard_until": self.walk_test.hard_until.isoformat(),
                "armed_areas": ",".join(armed),
                "blocked_zones": ",".join(dict.fromkeys(blocking)),
            },
        )
        # Not a refusal: the test is running. The zones that kept an area out
        # travel on the answer so the caller can say which (§9.1).
        return _Outcome(accepted=True, blocking=tuple(dict.fromkeys(blocking)))

    def end_walk_test(self, cause: str) -> None:
        """Leave the walk test: the house answers again, and says what it saw.

        Only the areas this walk test armed are disarmed. One that was
        already armed when it started is left exactly as it was
        (part 2 decision 2): the walk test borrowed nothing from it.

        **And never an area in alarm.** A disarm stops the sirens and
        acknowledges the incident (§7.2), so disarming here would let the
        walk test silence the one alarm it was built to keep live: an
        `always_on` zone fires, stays fully live as §11.3 demands, and then
        the auto-exit falls due fifteen minutes later and switches it off
        with nobody having seen it. It is the same rule §4.6.1 already makes
        for a scenario switch — an alarm ends with a disarm, by a person.
        """
        walk = self.walk_test
        if walk is None:
            return
        expected = walk_test_zones(self.config, self.bypassed)
        missed = tuple(z for z in expected if z not in walk.detections)
        self.walk_test = None
        in_alarm: list[str] = []
        for area_id in walk.armed_areas:
            rt = self.areas.get(area_id)
            if rt is None or rt.state is AreaState.DISARMED:
                continue
            if rt.state in (AreaState.ENTRY, AreaState.TRIGGERED) or rt.memory:
                in_alarm.append(area_id)
                continue
            self.disarm_area(area_id, walk.channel)
        self.occur(
            Moment.WALK_TEST_ENDED,
            channel=walk.channel,
            user_id=walk.user_id,
            zone_ids=missed,
            detail={
                "cause": cause,
                "started_at": walk.started_at.isoformat(),
                "seconds": str(int((self.now - walk.started_at).total_seconds())),
                "detected": str(len(walk.detections)),
                "expected": str(len(expected)),
                # The finding, not the tally: a zone that never reacted is
                # what §11.3 exists to surface, and it belongs on the row.
                "never_detected": ",".join(missed),
                # Left armed because they are in alarm, or hold its memory.
                # Written down: "why is the hall still armed?" has an answer.
                "left_in_alarm": ",".join(in_alarm),
            },
        )

    def expire_walk_test(self) -> None:
        """The auto-exit of §5.3: not disableable, and measured two ways.

        ``until`` moves with every detection so a forty-zone house can be
        walked in one pass; ``hard_until`` never moves, so a walk test
        somebody forgot about — with a cat in front of a PIR keeping it
        alive — still ends (part 2 decision 4).
        """
        walk = self.walk_test
        if walk is None:
            return
        if self.now >= walk.hard_until:
            self.end_walk_test("hard_timeout")
        elif self.now >= walk.until:
            self.end_walk_test("timeout")

    def walk_test_detection(self, zone: Zone) -> None:
        """A zone saw somebody during the walk test. That is all it does.

        It does not go to ``triggered``, it opens no incident and it leaves
        no alarm memory (part 2 decision 3): forty zones walked would
        otherwise leave forty alarms in the log, and
        ``alarm_control_panel.foyer_master`` would be telling HomeKit,
        Google and Alexa that somebody had broken in for the whole walk.

        Every detection pushes the auto-exit back, under the cap that never
        moves.
        """
        walk = self.walk_test
        assert walk is not None
        previous = walk.detections.get(zone.id)
        detection = (
            Detection(first=self.now, last=self.now)
            if previous is None
            else replace(previous, last=self.now, count=previous.count + 1)
        )
        self.walk_test = replace(
            walk,
            detections={**walk.detections, zone.id: detection},
            until=min(
                self.now + timedelta(seconds=walk.window),
                walk.hard_until,
            ),
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
        self.start_technical_escalation(zone)

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

    def acknowledge_technical(self, event: AcknowledgeTechnical) -> _Outcome:
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
        self.stop_escalation(EscalationKind.TECHNICAL)
        self.occur(
            Moment.TECHNICAL_ACKNOWLEDGED,
            zone_ids=tuple(pending),
            channel=self.channel,
            detail={"via": event.via, "contact_id": event.contact_id or ""},
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
                # As for a zone: switched back on, it starts from a baseline.
                self.seen_devices.discard(device.id)
                continue
            entity = self.entity_state(device.entity_id)
            if device.id not in self.seen_devices:
                # `unknown` is a tag never scanned: a reading, so its first
                # scan can count (§4.4, found in review).
                if not is_unavailable(entity) or entity.state == NEVER_FIRED:
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
            self.token_act(device.command, device.scenario_id, device.channel)
        finally:
            self.actor = previous

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
            self.token_act(
                command,
                zone.key.scenario_id,
                KEY_ZONE_CHANNEL,
                area_id=zone.area_id,
                zone_id=zone.id,
            )
        finally:
            self.actor = previous

    def token_act(
        self,
        command: KeyCommand,
        scenario_id: str | None,
        channel: str,
        *,
        area_id: str | None = None,
        zone_id: str | None = None,
    ) -> None:
        """What a tag or a key does: the credential is the thing itself.

        ``area_id`` and ``zone_id`` are the key zone's, for the row; a tag
        has neither.
        """
        if command is KeyCommand.TOGGLE:
            armed = any(
                rt.state is not AreaState.DISARMED for rt in self.areas.values()
            )
            command = KeyCommand.DISARM if armed else KeyCommand.ARM
        if command is KeyCommand.DISARM:
            outcome = self.disarm(None)
            if outcome.reason is Reason.INVALID_STATE:
                return  # nothing was armed: presented twice is not a failure
        else:
            outcome = self.arm_scenario(self.config.scenario(scenario_id), force=False)
        if not outcome.accepted:
            # Never silent: a tag or a key that did nothing must say why, or
            # the person walks away believing the house is armed (§4.7).
            self.occur(
                Moment.ARM_FAILED,
                area_id=area_id,
                zone_id=zone_id,
                scenario_id=scenario_id,
                zone_ids=outcome.blocking,
                channel=channel,
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
        """Stop this area's sounders, and the incident's if it shares one.

        Never the technical channel's (§5.5, found in review). A technical
        response carries the area of the zone that raised it, so without the
        flag a disarm of that area — or the intrusion siren cutoff — switched
        off a smoke sounder while the kitchen was still on fire. Disarming is
        an intrusion command and has no authority here.
        """
        incident = self.incident
        in_incident = incident is not None and area_id in incident.area_ids
        stopped = [
            r
            for r in self.running
            if not r.technical
            and (
                r.area_id == area_id
                or (
                    in_incident
                    and incident is not None
                    and r.incident_id == incident.id
                )
            )
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

    def reconcile_batteries(self) -> None:
        """Announce each battery once on the way down (§4.2, §6.1).

        The same shape as a fault and deliberately not the same thing: this
        one does not enter ``faults``, does not block arming and does not stop
        the zone being watched. A cell that has been replaced simply leaves
        the set, with no occurrence: "the battery is fine again" is not news,
        and a profile written against low_battery would fire on it.
        """
        current = {z.id for z in self.config.zones if z.enabled and self.low_battery(z)}
        for zone_id in sorted(current - self.low_batteries):
            zone = self.config.zone(zone_id)
            assert zone is not None
            self.occur(
                Moment.LOW_BATTERY,
                area_id=zone.area_id,
                zone_id=zone_id,
                detail={
                    "entity_id": zone.battery_entity_id or "",
                    "state": self.battery(zone).state or "",
                    "threshold": str(self.config.settings.low_battery_threshold),
                },
            )
        self.low_batteries = frozenset(current)

    # --- system health (§12) ----------------------------------------------------

    def apply_health_report(self, event: HealthReport) -> None:
        """Record what the runtime went and looked at. Decides nothing here.

        The counting and the thresholds are in ``core.health``; what follows
        from them — the moments, the incident, the state — is decided in
        ``reconcile_health`` at the end of the call, with everything else.
        """
        if event.watchdog is not None:
            current = self.watchdog
            if event.watchdog:
                # ``announced`` and ``down_since`` are deliberately kept:
                # reconcile_watchdog is the one place that decides an outage
                # is over, and clearing them here would mean the recovery
                # was never announced.
                self.watchdog = replace(
                    current,
                    failures=0,
                    last_ok=self.now,
                    last_attempt=self.now,
                    last_error="",
                    ever_ok=True,
                )
            else:
                self.watchdog = replace(
                    current,
                    failures=current.failures + 1,
                    last_attempt=self.now,
                    last_error=event.watchdog_error,
                )
        threshold = self.config.health.channel_failures
        known = health_engine.configured_channels(self.config)
        for key in known:
            present = (event.channels_present or {}).get(key)
            sent = (event.channel_sends or {}).get(key)
            if present is None and sent is None:
                continue
            self.channels[key] = health_engine.channel_after(
                self.channels.get(key) or ChannelHealth(),
                self.now,
                present=present,
                sent_ok=sent,
                threshold=threshold,
            )

    def world(self) -> SystemSnapshot:
        """The snapshot as it is *now*, with this call's change applied.

        ``self.snapshot`` is the world as the call began; the event's entity
        change lives in ``self.entities``. Everything in core.health reads a
        snapshot, so it is handed this one — reading the original would make
        a power cut visible only at the next unrelated event.
        """
        return replace(self.snapshot, entities=self.entities)

    def reconcile_health(self) -> None:
        """Announce what changed about the system itself, once each (§12).

        Everything here is state without an acknowledgement: each raised
        moment has the matching one that says it is over, and nothing waits
        for a person. That is the deliberate difference from the technical
        channel this sits beside (§5.5) — that one is about the house and
        needs somebody to say they have seen it; this one is about Foyer,
        where the only useful question is whether it is still true.
        """
        self.reconcile_mains()
        self.reconcile_channels()
        self.reconcile_watchdog()
        self.reconcile_radios()

    def reconcile_mains(self) -> None:
        """A mains failure notifies at once and is never a quiet night (§12.1)."""
        if not self.config.health.mains_entity_id:
            # The picker was cleared. Nothing about the house changed, so
            # nothing is announced: a "power restored" row for an entity
            # somebody unconfigured is the log saying something that did not
            # happen.
            self.mains_lost_since = None
            return
        lost = health_engine.mains_state(self.config, self.world())
        if lost is True and self.mains_lost_since is None:
            self.mains_lost_since = self.now
            self.occur(
                Moment.SYSTEM_POWER_LOST,
                detail={"entity_id": self.config.health.mains_entity_id or ""},
            )
        elif lost is False and self.mains_lost_since is not None:
            since = self.mains_lost_since
            self.mains_lost_since = None
            self.occur(
                Moment.SYSTEM_POWER_RESTORED,
                detail={
                    "since": since.isoformat(),
                    "seconds": str(int((self.now - since).total_seconds())),
                },
            )

    def reconcile_channels(self) -> None:
        """A broken channel is announced over one that still works (§12.2)."""
        for key, service in health_engine.configured_channels(self.config).items():
            current = self.channels.get(key)
            if current is None:
                continue
            was = self.previous_channel_fault(key)
            if current.fault is not None and was is None:
                over = health_engine.announce_over(self.config, self.channels, key)
                contact_id, _, channel_id = key.partition(":")
                self.occur(
                    Moment.NOTIFICATION_CHANNEL_DOWN,
                    detail={
                        "contact_id": contact_id,
                        "channel_id": channel_id,
                        "service": service,
                        "cause": current.fault.value,
                        # Which channel this may be said over, so the
                        # response profile answering this moment does not
                        # have to work it out and cannot get it wrong.
                        "over_contact_id": over[0] if over else "",
                        "over_channel_id": over[1] if over else "",
                    },
                )
            elif current.fault is None and was is not None:
                contact_id, _, channel_id = key.partition(":")
                self.occur(
                    Moment.NOTIFICATION_CHANNEL_RESTORED,
                    detail={
                        "contact_id": contact_id,
                        "channel_id": channel_id,
                        "service": service,
                    },
                )

    def previous_channel_fault(self, key: str) -> ChannelFault | None:
        """What this channel's fault was when the call started.

        Read from the snapshot rather than remembered in a second field:
        the state the call began with is already here, and a copy of it is a
        copy that can disagree.
        """
        return self.snapshot.state.health.channel(key).fault

    def reconcile_watchdog(self) -> None:
        """Foyer watches the watchdog (§12.3).

        Repeated failures to reach the endpoint mean no internet-based
        notification would go out either, so the panel has to say so — the
        ping is not only for whoever is at the other end of it.
        """
        settings = self.config.health.watchdog
        if not settings.enabled:
            if self.watchdog.down_since is not None or self.watchdog.announced:
                self.watchdog = replace(
                    self.watchdog, down_since=None, announced=False, failures=0
                )
            return
        current = self.watchdog
        if current.failures >= max(1, settings.failures) and not current.announced:
            self.watchdog = replace(
                current, down_since=current.down_since or self.now, announced=True
            )
            self.occur(
                Moment.WATCHDOG_UNREACHABLE,
                detail={
                    "failures": str(current.failures),
                    "error": current.last_error,
                    # "it has never worked" is almost always a mistyped URL,
                    # and it is a different sentence from "it stopped".
                    "ever_ok": "1" if current.ever_ok else "",
                },
            )
        elif current.failures == 0 and current.announced:
            self.watchdog = replace(current, down_since=None, announced=False)
            self.occur(Moment.WATCHDOG_RECOVERED)

    def reconcile_radios(self) -> None:
        """Correlated silence on one radio, gated on the coordinator (§12.5).

        The order matters. A coordinator that is itself unreachable is a
        coordinator or network failure, reported as such, and the radio is
        not examined for interference at all: a PoE coordinator dying with
        its switch is a different fault with a different fix, and conflating
        them teaches the household to ignore both.
        """
        self.track_quiet_zones()
        settings = self.config.health
        for radio_id, gone in self.gone_radios.items():
            self.end_radio(Radio(radio_id, radio_id), gone, "radio_removed")
        self.gone_radios = {}
        for radio in settings.radios:
            if not radio.enabled:
                self.end_radio(radio, self.radios.pop(radio.id, None), "radio_disabled")
                continue
            current = self.radios.get(radio.id) or RadioHealth()
            answering = health_engine.coordinator_answering(radio, self.world())
            if answering is False:
                current = self.coordinator_lost(radio, current)
                self.radios[radio.id] = current
                continue
            if current.coordinator_down_since is not None:
                if current.coordinator_announced:
                    self.occur(
                        Moment.RADIO_COORDINATOR_UP,
                        detail={"radio": radio.name, "radio_id": radio.id},
                    )
                current = replace(
                    current, coordinator_down_since=None, coordinator_announced=False
                )
            if answering is None:
                # No coordinator named: the gate cannot be applied, so
                # nothing is raised. Page 14 says so beside the radio.
                if current.confirmed:
                    self.occur(
                        Moment.RF_INTERFERENCE_CLEARED,
                        detail={
                            "radio": radio.name,
                            "radio_id": radio.id,
                            "cause": "coordinator_unset",
                        },
                    )
                self.radios[radio.id] = replace(
                    current, suspected_since=None, confirmed=False, zone_ids=()
                )
                continue
            self.radios[radio.id] = self.evaluate_radio(radio, current)

    def end_radio(self, radio: Radio, current: RadioHealth | None, cause: str) -> None:
        """A radio stops being watched: say what it was reporting is over.

        Switching one off and deleting one are the same fact to whoever
        reads the log afterwards, so they write the same rows. Every moment
        system health raises has the one that says it is over, and a
        suspicion that simply disappeared would be the row somebody looks
        for the next morning.
        """
        if current is None:
            return
        if current.confirmed:
            self.occur(
                Moment.RF_INTERFERENCE_CLEARED,
                detail={"radio": radio.name, "radio_id": radio.id, "cause": cause},
            )
        if current.coordinator_announced:
            self.occur(
                Moment.RADIO_COORDINATOR_UP,
                detail={"radio": radio.name, "radio_id": radio.id, "cause": cause},
            )

    def coordinator_lost(self, radio: Radio, current: RadioHealth) -> RadioHealth:
        if current.confirmed:
            # The suspicion is withdrawn: what looked like interference was
            # the coordinator going with it. Saying so is the point.
            self.occur(
                Moment.RF_INTERFERENCE_CLEARED,
                detail={
                    "radio": radio.name,
                    "radio_id": radio.id,
                    "cause": "coordinator_down",
                },
            )
        if current.coordinator_down_since is None:
            self.occur(
                Moment.RADIO_COORDINATOR_DOWN,
                detail={
                    "radio": radio.name,
                    "radio_id": radio.id,
                    "entity_id": radio.coordinator_entity_id or "",
                    # Not "zones": response.variables() owns that name for
                    # the zone *names* of the batch, and this occurrence
                    # carries none — so the message rendered "its  zones".
                    "radio_zones": str(
                        len(health_engine.zones_on(self.config, self.world(), radio))
                    ),
                },
            )
        # While the coordinator was gone, a zone's silence said nothing
        # about that zone: nobody was there to hear it. So the clock is not
        # merely reset — the zones become uncounted until they are readable
        # again, exactly as they are at a restart. Without this, a
        # coordinator on a failing switch produces one confirmed
        # interference, one incident and one siren per flap, which is the
        # fault class §12.5 insists must not be reported as interference.
        for zone_id in health_engine.zones_on(self.config, self.world(), radio):
            if self.quiet_since.pop(zone_id, None) is not None:
                self.unknown_zones.add(zone_id)
        return RadioHealth(
            coordinator_down_since=current.coordinator_down_since or self.now,
            coordinator_announced=True,
        )

    def evaluate_radio(self, radio: Radio, current: RadioHealth) -> RadioHealth:
        """One radio, with its coordinator answering. The whole heuristic."""
        on_radio = health_engine.zones_on(self.config, self.world(), radio)
        window = self.config.health.rf_window_of(radio)
        quiet = health_engine.burst(self.quiet_since, on_radio, window)
        threshold = self.config.health.rf_threshold(radio, len(on_radio))
        if len(quiet) < threshold:
            if current.confirmed:
                self.occur(
                    Moment.RF_INTERFERENCE_CLEARED,
                    detail={
                        "radio": radio.name,
                        "radio_id": radio.id,
                        "cause": "zones_back",
                    },
                )
            return RadioHealth()
        if current.suspected_since is None:
            # The confirmation window starts here and nothing is announced
            # yet: a coordinator reboot and a firmware update both walk into
            # this minute instead of into the siren.
            return RadioHealth(suspected_since=self.now, zone_ids=quiet)
        confirm = timedelta(seconds=self.config.health.rf_confirm)
        if current.confirmed or self.now < current.suspected_since + confirm:
            return replace(current, zone_ids=quiet)
        self.raise_interference(radio, quiet, on_radio)
        return replace(current, confirmed=True, zone_ids=quiet)

    def raise_interference(
        self, radio: Radio, quiet: tuple[str, ...], on_radio: tuple[str, ...]
    ) -> None:
        """The moment, and — armed only — the incident (§12.5, part 1 dec. 8).

        The first line reports how many zones, on which radio, and that the
        coordinator is still answering, because that is what lets somebody
        tell jamming from the four other things that look exactly like it.
        """
        armed = tuple(
            area.id
            for area in self.config.areas
            if self.areas[area.id].state
            in (AreaState.ARMED, AreaState.ARMING, AreaState.ENTRY, AreaState.TRIGGERED)
            and any(
                zone.area_id == area.id
                for zone_id in on_radio
                if (zone := self.config.zone(zone_id)) is not None
            )
        )
        if self.inhibiting:
            # A walk test arms every area itself (§11.3), so "the house is
            # armed" here is not the household's arming — and §11.3 says all
            # actions are inhibited and means it. The moment is still
            # raised, for the log and for the live page; the incident is
            # not, because response.inhibits exempts anything belonging to
            # an open incident, on the stated assumption that during a walk
            # test only an always_on zone can have opened one.
            armed = ()
        detail = {
            "radio": radio.name,
            "radio_id": radio.id,
            "count": str(len(quiet)),
            "of": str(len(on_radio)),
            "coordinator": "answering",
            "armed": "1" if armed else "",
        }
        self.occur(Moment.RF_INTERFERENCE_SUSPECTED, zone_ids=quiet, detail=detail)
        for area_id in armed:
            # Jamming is a tamper condition in professional panels, so an
            # armed house treats it as one: the incident opens with no zone
            # of its own, because no zone did this — the radio did.
            self.trigger(area_id, None, detail=dict(detail))

    def track_quiet_zones(self) -> None:
        """When each zone's entity stopped being readable (§12.5).

        Recorded for every zone rather than only those on a radio: a radio
        can be configured after its zones have already gone quiet, and a
        count that started only at that moment would miss the burst that
        prompted somebody to configure it.

        A zone that is *already* unreadable when Foyer starts watching it
        gets no timestamp at all, and is not counted until it has been
        readable again. That is the rule this whole heuristic stands on. At
        a restart, battery-powered end devices are unavailable until they
        are interviewed while the mains-powered coordinator answers at
        once — which is the §12.5 burst signature exactly, produced by
        nothing but a reboot. §12.1 guards the mains against the identical
        hazard, and §4.7 already says a zone's first reading is a baseline
        rather than an event. What Foyer did not see happen, it does not
        claim to have seen.

        The cost is a jamming attempt that begins while Foyer is down and
        never lets its zones back: those zones stay uncounted. Every one of
        them is in fault the whole time (INV-4), which blocks arming and
        raises ``zone_fault`` on each, so nothing about it is silent.
        """
        for zone in self.config.zones:
            readable = zone.enabled and not health_engine.is_unreadable(
                self.entity(zone)
            )
            if readable or not zone.enabled:
                self.quiet_since.pop(zone.id, None)
                self.unknown_zones.discard(zone.id)
                continue
            if zone.id in self.quiet_since or zone.id in self.unknown_zones:
                continue
            if self.restarted or zone.id not in self.seen:
                self.unknown_zones.add(zone.id)
            else:
                self.quiet_since[zone.id] = self.now

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
                # The moment this contributor is joining *for*. A zone that
                # satisfied a group joins with the group's profile, which is
                # the loud one §4.8 exists to give it — resolved as
                # TRIGGERED, the group id was computed and then ignored, so
                # the incident adopted the quiet member profile's escalation,
                # or none at all when the member profile had no steps (found
                # in review).
                moment=(
                    Moment.VERIFICATION_SATISFIED if of_group else Moment.TRIGGERED
                ),
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
        # Every join recomputes which policy the incident escalates with
        # (§5.6): a louder zone joining is exactly when the household needs
        # the louder list of people.
        self.adopt_escalation()
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

    def acknowledge(
        self, channel: str | None, via: str, contact_id: str | None = None
    ) -> None:
        incident = self.incident
        assert incident is not None
        named = self.config.user(self.actor.user_id)
        self.incident = replace(
            incident,
            acknowledged=True,
            acknowledgements=(
                *incident.acknowledgements,
                Acknowledgement(
                    at=self.now,
                    channel=channel,
                    via=via,
                    user_id=self.actor.user_id,
                    user_name=named.name if named else None,
                    contact_id=contact_id,
                ),
            ),
        )
        # The policy stops immediately (§7.2). This is the one path: a
        # disarm of an area the incident touched arrives here too, which is
        # what makes disarming an acknowledgement (decision 57).
        self.stop_escalation(EscalationKind.INCIDENT)
        self.occur(
            Moment.INCIDENT_ACKNOWLEDGED,
            zone_ids=incident.zone_ids,
            channel=channel,
            detail={"via": via, "contact_id": contact_id or ""},
        )

    def acknowledge_incident(self, event: AcknowledgeIncident) -> _Outcome:
        """One acknowledgement acknowledges the whole incident (§5.6).

        Four paths arrive here and none of them invents an authorisation of
        its own: the button, the push, the keypress and the disarm all go
        through the same ``authorize`` as everything else (§8.2).
        """
        if self.incident is None or self.incident.acknowledged:
            return _reject(Reason.NOTHING_TO_ACKNOWLEDGE)
        if (reason := self.authorize(Operation.ACKNOWLEDGE)) is not None:
            return _reject(reason)
        self.acknowledge(self.channel, event.via, event.contact_id)
        return _ACCEPTED

    # --- escalation (§7.2) ------------------------------------------------------

    def escalation_of(self, kind: EscalationKind) -> Escalation | None:
        return next((e for e in self.escalations if e.kind is kind), None)

    def set_escalation(self, new: Escalation) -> None:
        self.escalations = [e for e in self.escalations if e.kind is not new.kind]
        self.escalations.append(new)

    def stop_escalation(self, kind: EscalationKind) -> None:
        """An acknowledgement stops the policy immediately (§7.2). Nothing is
        recorded here: the acknowledgement itself is the row."""
        self.escalations = [e for e in self.escalations if e.kind is not kind]

    def adopt_escalation(self) -> None:
        """The incident escalates with the highest-severity contributor's
        policy (§5.6), recomputed every time a zone joins.

        A policy adopted while the incident is already running keeps the
        incident's own clock: the escalation started when the house was
        broken into, not when the louder zone went, so its early steps are
        already overdue and go out at once rather than starting again.
        """
        incident = self.incident
        if incident is None or incident.acknowledged:
            return
        if incident.escalation_exhausted:
            # Everybody on the list has been tried for this incident. A
            # louder zone joining now updates the notification text, as every
            # join does, and does not start the climb again (found in
            # review).
            return
        profile = escalation_engine.policy_for(self.config, incident)
        if profile is None:
            return
        current = self.escalation_of(EscalationKind.INCIDENT)
        if current is not None and current.profile_id == profile.id:
            return
        started = escalation_engine.start(
            EscalationKind.INCIDENT, profile, self.now, reference=incident.id
        )
        if current is not None:
            started = replace(started, started_at=current.started_at)
        self.set_escalation(started)

    def start_technical_escalation(self, zone: Zone) -> None:
        """The technical channel's own escalation (§5.5), independent of any
        intrusion incident and stopped only by its own acknowledgement.

        One escalation for the channel, not one per detector: one
        acknowledgement already acts on every technical alarm pending at that
        moment (decision 49), so a second escalation would be a second set of
        calls nothing separate can stop.
        """
        if self.escalation_of(EscalationKind.TECHNICAL) is not None:
            return
        profile = effective_profile(
            self.config, zone_id=zone.id, moment=Moment.TECHNICAL_RAISED
        )
        if not escalation_engine.has_steps(profile, Moment.TECHNICAL_RAISED):
            return
        assert profile is not None
        self.set_escalation(
            escalation_engine.start(
                EscalationKind.TECHNICAL, profile, self.now, reference=zone.id
            )
        )

    def run_escalations(self, ctx: PlanContext) -> list[ActionIntent]:
        """Send the steps whose time has come, and say what was not sent.

        Called from decision(), before the occurrences are frozen, so that
        ``escalation_exhausted`` is answered by a profile in the same call
        that raises it — it is a moment like any other (§7.2).
        """
        intents: list[ActionIntent] = []
        surviving: list[Escalation] = []
        for current in self.escalations:
            profile = self.config.profile(current.profile_id)
            if profile is None:
                # The policy was deleted while it was running. There is
                # nothing left to reach anybody with, and pretending
                # otherwise would leave an escalation open for ever.
                self.occur(
                    Moment.ESCALATION_EXHAUSTED,
                    detail={"kind": current.kind.value, "cause": "profile_gone"},
                    incident_id=current.reference
                    if current.kind is EscalationKind.INCIDENT
                    else None,
                )
                continue
            done = list(current.done)
            # Steps that did not go out, and why. There are two ways for a
            # step to reach nobody and both are recorded: a notification that
            # never went is exactly the silence this feature exists to end,
            # and "the escalation ran and nothing happened" is the worst
            # possible answer to "why did nobody call me?".
            missed: list[tuple[str, str]] = []
            for action in escalation_engine.due(current, profile, self.now):
                at = escalation_engine.due_at(current, action)
                index = escalation_engine.index_of(current, profile, action.id)
                late = (self.now - at).total_seconds()
                if self.restarted and late > ESCALATION_RESTART_GRACE:
                    # It fell due while Home Assistant was down. A
                    # notification this late is worse than none (part 1
                    # decision 5), so it is recorded and not sent, and the
                    # steps still ahead carry on at their own times.
                    missed.append((str(index), RESTART))
                    done.append(action.id)
                    continue
                intent, why = escalation_intent(
                    ctx,
                    profile,
                    action,
                    self.escalation_values(ctx, current),
                    moment=current.moment,
                    index=index,
                    kind=current.kind.value,
                    area_id=self.escalation_area(current),
                    incident_id=current.reference
                    if current.kind is EscalationKind.INCIDENT
                    else None,
                )
                done.append(action.id)
                if intent is not None:
                    intents.append(intent)
                else:
                    # Every contact it names is inside their quiet hours, or
                    # disabled, or a condition on it is not met. The step is
                    # spent either way — its moment has passed — but it is
                    # said, with the reason skip_reason gave.
                    missed.append((str(index), why or ""))
            if missed:
                self.occur(
                    Moment.ESCALATION_SKIPPED,
                    area_id=self.escalation_area(current),
                    detail={
                        "kind": current.kind.value,
                        "steps": ",".join(index for index, _ in missed),
                        "reasons": ",".join(why for _, why in missed),
                        "since": self.gap_since.isoformat() if self.gap_since else "",
                    },
                    incident_id=current.reference
                    if current.kind is EscalationKind.INCIDENT
                    else None,
                )
            advanced = replace(current, done=tuple(done))
            if escalation_engine.exhausted(advanced, profile):
                if not missed:
                    # Every step has gone out and nobody has answered (§7.2).
                    # A moment a profile can act on, and the last entry the
                    # panel's "nothing raises this yet" list had.
                    #
                    # Only when the list was really tried: an escalation
                    # whose last steps were swallowed by a restart, or which
                    # reached nobody, has not been exhausted — it has been
                    # missed, and the row above says so. A profile answering
                    # "the whole list failed" must not fire for a list that
                    # was never attempted.
                    self.occur(
                        Moment.ESCALATION_EXHAUSTED,
                        area_id=self.escalation_area(advanced),
                        detail={
                            "kind": advanced.kind.value,
                            "steps": str(
                                len(escalation_engine.steps(profile, advanced.moment))
                            ),
                        },
                        incident_id=advanced.reference
                        if advanced.kind is EscalationKind.INCIDENT
                        else None,
                    )
                    if (
                        advanced.kind is EscalationKind.INCIDENT
                        and self.incident is not None
                        and self.incident.id == advanced.reference
                    ):
                        # Remembered on the incident, because the escalation
                        # itself is about to be dropped: otherwise the next
                        # zone to join finds none running and starts the whole
                        # list over (found in review).
                        self.incident = replace(
                            self.incident, escalation_exhausted=True
                        )
                continue
            surviving.append(advanced)
        self.escalations = surviving
        return intents

    def escalation_area(self, current: Escalation) -> str | None:
        if current.kind is EscalationKind.INCIDENT and self.incident is not None:
            return next(iter(self.incident.area_ids), None)
        zone = self.config.zone(current.reference)
        return zone.area_id if zone else None

    def escalation_values(
        self, ctx: PlanContext, current: Escalation
    ) -> dict[str, str]:
        """The §6.4 variables for a step's message, built from the same
        function every other message uses, so "{{ incident_zones }}" means
        the same thing in a step as it does in the alarm that started it."""
        if current.kind is EscalationKind.INCIDENT:
            incident = self.incident
            occurrence = Occurrence(
                moment=current.moment,
                area_id=self.escalation_area(current),
                zone_ids=incident.zone_ids if incident else (),
                incident_id=current.reference,
            )
        else:
            occurrence = Occurrence(
                moment=current.moment,
                area_id=self.escalation_area(current),
                zone_id=current.reference,
            )
        return variables(ctx, (occurrence,))

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
            # Belt and braces: an incident only closes once acknowledged, and
            # the acknowledgement already stopped the policy. An escalation
            # outliving its incident would call the neighbour about an alarm
            # that is over.
            self.stop_escalation(EscalationKind.INCIDENT)

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
        if (reason := self.check_code(operation)) is not None:
            return reason
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
            self.code_required_by = authz.code_required_by(
                self.config, operation, areas=areas, scenario=scenario
            )
            return Reason.CODE_REQUIRED
        self.code_cleared()
        return None

    def check_code(self, operation: Operation | None) -> Reason | None:
        """The lockout half of §8.4, the same on every path.

        A channel already shut is answered without another attempt counting
        against it; a wrong code is an attempt and counts; a missing code is
        not an attempt at all, and is left to the caller.
        """
        actor = self.actor
        if (until := authz.locked_until(self.lockouts, actor, self.now)) is not None:
            self.occur(
                Moment.CODE_REJECTED,
                channel=actor.channel,
                detail={
                    "operation": operation.value if operation else "",
                    "reason": Reason.LOCKED_OUT.value,
                    "until": until.isoformat(),
                },
            )
            return Reason.LOCKED_OUT
        if actor.code is CodeResult.INVALID:
            self.code_failed(operation)
            return Reason.BAD_CODE
        return None

    def code_cleared(self) -> None:
        """A correct code ends the run of failures on this channel. It does
        not end a lockout already in force: that is what waiting is for."""
        if not self.actor.code_verified:
            return
        key = authz.lockout_key(self.actor)
        cleared = authz.clear_failures(self.lockouts.get(key))
        if cleared is None:
            self.lockouts.pop(key, None)
        else:
            self.lockouts[key] = cleared

    def code_failed(self, operation: Operation | None) -> None:
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
        # A credential with no device behind it is a token that did not
        # match, at the device endpoint (§9.2.1): the same counter, the same
        # row, the same moment, and the word that says which it was.
        token = actor.device_id is None and bool(actor.address)
        self.occur(
            Moment.CODE_REJECTED,
            channel=actor.channel,
            detail={
                "operation": operation.value if operation else "",
                "reason": (Reason.BAD_TOKEN if token else Reason.BAD_CODE).value,
            },
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
        """Preconditions (§5.4). Returns the zones a forced arm will bypass.

        A low battery is not a precondition and never appears in the blocking
        list — it does not stop this arming and must not read as if it did.
        It is recorded here because this is the one place both arming paths
        pass through, so the answer carries it whether the arming went ahead
        or was refused for something else (part 1 decision 2).
        """
        self.low_battery_zones = tuple(
            z.id
            for z in self.config.zones_in(area_ids)
            if z.id not in self.bypassed and self.low_battery(z)
        )
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
        skip_exit_delay: bool = False,
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
            delay = 0 if skip_exit_delay else self.config.exit_delay(area, scenario)
            self.set_area(
                area_id,
                state=AreaState.ARMING,
                scenario_id=scenario.id if scenario else None,
                timer=Timer(TimerKind.EXIT, self.now + timedelta(seconds=delay)),
                forced=force,
                channel=channel,
                user_id=self.actor.user_id,
                device_id=self.actor.device_id,
                claimed=self.actor.claimed,
                skipped_exit=skip_exit_delay,
                causes=(),
                rule_id=self.rule_detail.get("rule_id"),
                rule_name=self.rule_detail.get("rule"),
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
        # Which zones went under guard on a battery that is running out. The
        # row is written at the moment the area actually arms, not when the
        # button was pressed, because that is when it became true of the
        # house — and it is the row "why did the garage never fire?" is read
        # against six weeks later (part 1 decision 2).
        low = tuple(
            z.id
            for z in self.config.zones_in((area_id,))
            if z.id not in self.bypassed and self.low_battery(z)
        )
        self.occur(
            Moment.ARMED,
            area_id=area_id,
            scenario_id=rt.scenario_id,
            channel=rt.channel,
            user_id=rt.user_id,
            device_id=rt.device_id,
            zone_ids=low,
            detail={
                **({"skip_exit_delay": "1"} if rt.skipped_exit else {}),
                **({"low_battery": ",".join(low)} if low else {}),
                **(_CLAIMED if rt.claimed else {}),
                **_rule_detail(rt),
            },
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
            detail={
                "reason": reason.value,
                **(_CLAIMED if rt.claimed else {}),
                **_rule_detail(rt),
            },
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
        self,
        scenario: Scenario | None,
        *,
        force: bool,
        skip_exit_delay: bool = False,
        keep_armed: frozenset[str] = frozenset(),
    ) -> _Outcome:
        """Arm a scenario, or switch to it while armed (decisions 7 and 9).

        Areas of the new scenario not yet armed go through their exit delay;
        areas already armed stay armed and now belong to it; areas armed by the
        previous scenario and absent from this one are disarmed. Areas armed on
        their own, outside any scenario, are left exactly as they are.

        ``keep_armed`` names areas this switch may not disarm — the perimeter,
        when an automatic rule is doing the switching (§9.4 point 3, part 2
        decision 6). They stay armed and become areas armed on their own, so
        the master reports ``armed_custom_bypass`` and the house is left more
        protected than the scenario asked for, never less.
        """
        if scenario is None:
            return _reject(Reason.UNKNOWN_SCENARIO)
        if self.walk_test is not None:
            return _reject(Reason.WALK_TEST_ACTIVE)
        current = self.active_scenario_id
        target = [a for a in scenario.areas if a in self.areas]
        dropping = [
            a
            for a, rt in self.areas.items()
            if current is not None
            and rt.scenario_id == current
            and rt.state is not AreaState.DISARMED
            and a not in target
        ]
        leaving = [a for a in dropping if a not in keep_armed]
        staying = [a for a in dropping if a in keep_armed]
        in_alarm = [
            a
            for a in (*target, *dropping)
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
        for area_id in staying:
            # Armed, and now belonging to nothing: §4.6.1's "areas armed on
            # their own are left exactly as they are", reached from the other
            # side. The row says which rule left it armed and why.
            self.set_area(area_id, scenario_id=None)
            self.occur(
                Moment.AUTO_BLOCKED,
                area_id=area_id,
                channel=self.channel,
                detail={"reason": RuleBlock.PERIMETER.value},
            )
        for area_id in target:
            if area_id not in to_arm:
                self.set_area(area_id, scenario_id=scenario.id)
        self.active_scenario_id = scenario.id
        self.begin_arming(to_arm, scenario, force, to_bypass, skip_exit_delay)
        return _ACCEPTED

    def arm_mode(self, event: ArmModeRequest) -> _Outcome:
        """The master panel arms the one scenario with this mode (decision 8)."""
        matches = [s for s in self.config.scenarios if s.ha_master_state == event.mode]
        if not matches:
            return _reject(Reason.NO_SCENARIO_FOR_MODE)
        if len(matches) > 1:
            return _reject(Reason.AMBIGUOUS_MODE)
        return self.arm_scenario(
            matches[0], force=event.force, skip_exit_delay=event.skip_exit_delay
        )

    def arm_area(self, event: ArmAreaRequest) -> _Outcome:
        """One area on its own, outside any scenario (decision 5)."""
        if self.config.area(event.area_id) is None:
            return _reject(Reason.UNKNOWN_AREA)
        if self.walk_test is not None:
            # Every area is already armed by the walk test, and its end
            # disarms them all: an arming accepted now would be a house its
            # owner believes armed that is not (found in review).
            return _reject(Reason.WALK_TEST_ACTIVE)
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
        self.begin_arming(
            (event.area_id,), None, event.force, to_bypass, event.skip_exit_delay
        )
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
        self.pending_runs = [
            r
            for r in self.pending_runs
            # What a delay is still holding for this area, unless it belongs
            # to the technical channel: disarming is an intrusion command
            # (§5.5) and the rest of a smoke alarm's sequence is not its to
            # abandon (found in review).
            if r.area_id != area_id or r.moment in TECHNICAL_MOMENTS
        ]
        if rt.memory and rt.state is AreaState.TRIGGERED:
            # The alarm ends here rather than at a cutoff that will not run
            # now. An area in memory but no longer triggered has had its
            # cutoff, and its alarm_ended with it (decision 105).
            self.occur(
                Moment.ALARM_ENDED,
                area_id=area_id,
                scenario_id=rt.scenario_id,
                zone_ids=rt.causes,
                channel=channel,
                detail={"cause": "disarmed"},
            )
        if rt.memory:
            self.occur(
                Moment.ALARM_CLEARED,
                area_id=area_id,
                scenario_id=rt.scenario_id,
                zone_ids=rt.causes,
                channel=channel,
            )
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

    # --- automatic arming rules (§9.4) --------------------------------------------

    def run_rules(self) -> None:
        """Everything §9.4 does on one wake-up, in the one order that works.

        Suspensions expire first, so a window that ended at one o'clock does
        not hold back the rule evaluated at one o'clock and a second. Then the
        countdowns whose time is up — after the event has been handled, so a
        Cancel arriving in the same instant as the deadline cancels. Then the
        rules themselves.
        """
        self.expire_suspensions()
        self.record_missed_occurrences()
        self.drop_orphan_countdowns()
        self.fire_pending_rules()
        self.evaluate_rules()

    def record_missed_occurrences(self) -> None:
        """A `time` rule whose hour passed while Home Assistant was down.

        The occurrence is gone — ``occurrence_due`` only looks at today's
        instant and it is behind us — so the rule will say nothing on its
        own. That is the one failure §9.4 is written against: "why did it not
        arm last night?" needs an answer even when the answer is "nothing was
        running". A countdown that fell due in the same gap fires late
        (part 2 decision 12); an occurrence that never started one cannot be
        fired late without announcing an arming nobody was told about, so it
        is recorded and missed.
        """
        if not self.restarted or self.gap_since is None:
            return
        for rule in self.config.rules:
            if not rule.enabled or rule.trigger.kind is not RuleTriggerKind.TIME:
                continue
            runtime = self.rules_runtime.get(rule.id, RuleRuntime())
            missed = rules_engine.occurrence_in(
                rule, self.gap_since, self.now, self.timezone, runtime.last_occurrence
            )
            if missed is None:
                continue
            self.rules_runtime[rule.id] = replace(
                runtime, last_occurrence=missed, blocked=RuleBlock.MISSED
            )
            self.occur(
                Moment.AUTO_BLOCKED,
                channel=AUTO_RULE_CHANNEL,
                detail={
                    "rule": rule.name,
                    "rule_id": rule.id,
                    "reason": RuleBlock.MISSED.value,
                    "due": missed.isoformat(),
                },
            )

    def drop_orphan_countdowns(self) -> None:
        """A countdown whose rule was deleted or switched off is cancelled.

        With a row: the card is showing "arming in two minutes" and it is
        about to stop doing so, and a countdown that vanishes with nothing in
        the log is the kind of silence this section exists against.
        """
        for pending in list(self.pending_rules):
            rule = self.config.rule(pending.rule_id)
            if rule is not None and rule.enabled:
                continue
            self.pending_rules.remove(pending)
            self.occur(
                Moment.AUTO_CANCELLED,
                channel=AUTO_RULE_CHANNEL,
                scenario_id=pending.scenario_id,
                detail={
                    "rule": pending.rule_name,
                    "rule_id": pending.rule_id,
                    "pending_id": pending.id,
                    "action": pending.action.value,
                    "via": "rule_removed",
                },
            )

    def expire_suspensions(self) -> None:
        """A suspension ends on its own, and says so: the row is what a user
        reads in six months, and "Boiler engineer, 09:00-13:00" is the only
        form of it that answers anything (part 2 decision 7)."""
        expired = [s for s in self.suspensions if s.expired(self.now)]
        for suspension in expired:
            self.suspensions.remove(suspension)
            self.occur(
                Moment.AUTO_SUSPENSION_CLEARED,
                detail=_suspension_detail(suspension) | {"cause": "expired"},
            )

    def fire_pending_rules(self) -> None:
        """Countdowns whose time is up (§9.4).

        The guards are evaluated again here, not only when the countdown
        started: two minutes is long enough for somebody to come home, and a
        rule that announced itself and then acted on a world that had changed
        would be exactly the annoyance the grace period exists to prevent.

        A countdown whose deadline passed while Home Assistant was down fires
        all the same (part 2 decision 12), and the row says so.
        """
        due = [p for p in self.pending_rules if p.due <= self.now]
        self.pending_rules = [p for p in self.pending_rules if p.due > self.now]
        for pending in due:
            rule = self.config.rule(pending.rule_id)
            if rule is None or not rule.enabled:
                continue
            decided = self.rule_decision(rule, scenario_id=pending.scenario_id)
            if decided.block is not None:
                spent = self.rule_blocked(rule, decided.block, decided.suspension)
                if not spent:
                    # A guard, a walk test or the switch: the condition still
                    # holds, so the rule asks again when that clears. A skip
                    # somebody pressed during the countdown is the exception —
                    # unlatching there would spend the skip and then arm the
                    # house two minutes later, which is the opposite of what
                    # the button says.
                    self.spend(rule)
                continue
            self.rule_act(rule, decided, late=self.restarted)

    def evaluate_rules(self) -> None:
        for rule in self.config.rules:
            if not rule.enabled:
                # Forgotten, so that switching it on again starts from a
                # baseline: a `presence` rule re-enabled while somebody is
                # home has not seen them arrive, and a level rule's "for N
                # minutes" starts again (found in review).
                self.rules_runtime.pop(rule.id, None)
                continue
            self.unblock_when_ready(rule)
            runtime, wants, occurrence = self.rule_wants(rule)
            if wants and not rules_engine.in_active_window(
                rule, self.now, self.timezone
            ):
                # Outside its window the rule does not exist (§9.4): not
                # blocked, not suspended, not logged. An edge that happened
                # there is spent, a condition that still holds is not.
                runtime = _spend(rule, runtime, occurrence)
                wants = False
            if wants and self.pending_rule_for(rule.id) is not None:
                wants = False  # already counting down
            if not wants:
                self.rules_runtime[rule.id] = runtime
                continue
            decided = self.rule_decision(rule)
            if decided.block is not None:
                self.rules_runtime[rule.id] = _spend(rule, runtime, occurrence)
                self.rule_blocked(rule, decided.block, decided.suspension)
                continue
            self.rules_runtime[rule.id] = replace(
                _spend(rule, runtime, occurrence, acted=True), blocked=None
            )
            if rule.grace_seconds > 0:
                self.start_countdown(rule, decided)
            else:
                self.rule_act(rule, decided)

    def pending_rule_for(self, rule_id: str) -> PendingRuleAction | None:
        return next((p for p in self.pending_rules if p.rule_id == rule_id), None)

    def rule_wants(self, rule: AutoRule) -> tuple[RuleRuntime, bool, datetime | None]:
        """Whether this rule's trigger asks for something now (§9.4).

        The bookkeeping travels with the answer: a level trigger's ``since``
        is when its condition became true, and an edge trigger's baseline is
        recorded on the first evaluation so that a rule created while
        somebody is already at home has not seen them arrive.
        """
        runtime = self.rules_runtime.get(rule.id, RuleRuntime())
        trigger = rule.trigger
        states = {e: self.entity_state(e).state for e in trigger.entity_ids}
        if trigger.level:
            if not rules_engine.condition_holds(rule, states):
                # The condition went false: the rule is free to act again the
                # next time it becomes true, and whatever blocked it is over.
                return (
                    replace(
                        runtime, since=None, latched=False, blocked=None, seen=True
                    ),
                    False,
                    None,
                )
            runtime = replace(runtime, since=runtime.since or self.now, seen=True)
            if runtime.latched:
                return runtime, False, None
            mature = rules_engine.matures_at(rule, runtime)
            return runtime, mature is not None and mature <= self.now, None
        if trigger.kind is RuleTriggerKind.PRESENCE:
            home = any(state == rules_engine.HOME for state in states.values())
            if not runtime.seen:
                return replace(runtime, seen=True, latched=home), False, None
            if home and not runtime.latched:
                return replace(runtime, latched=True), True, None
            if home:
                return runtime, False, None
            if any(state in (None, *FAULT_STATES) for state in states.values()):
                # A tracker that restarted, a phone off the network: not a
                # departure, so the latch stays as it is. Clearing it here
                # would make the next readable `home` an arrival — and that
                # arrival can disarm a house (INV-4 applied to people).
                return runtime, False, None
            return replace(runtime, latched=False), False, None
        schedule = f"{trigger.at}|{','.join(map(str, sorted(trigger.weekdays)))}"
        if not runtime.seen or runtime.schedule != schedule:
            # The baseline (§4.7's rule, applied to a rule): an hour already
            # past today when the rule was saved, re-enabled or re-timed is
            # not an occurrence it has missed, and must not arm — or disarm —
            # the house the moment somebody presses Save.
            passed = rules_engine.occurrence_due(rule, self.now, self.timezone, None)
            return (
                replace(
                    runtime,
                    seen=True,
                    schedule=schedule,
                    last_occurrence=passed or runtime.last_occurrence,
                ),
                False,
                None,
            )
        occurrence = rules_engine.occurrence_due(
            rule, self.now, self.timezone, runtime.last_occurrence
        )
        return replace(runtime, seen=True), occurrence is not None, occurrence

    # What a zone can put right by closing, and what it cannot.
    _ZONE_REFUSALS = frozenset(
        {Reason.ZONE_OPEN, Reason.ZONE_FAULT, Reason.ARM_HOLD_EXPIRED}
    )

    def refused(self, rule: AutoRule, reason: Reason | None) -> None:
        """Record that the action this rule asked for did not happen."""
        runtime = self.rules_runtime.get(rule.id, RuleRuntime())
        self.rules_runtime[rule.id] = replace(
            runtime,
            latched=runtime.latched or rule.trigger.level,
            blocked=(
                RuleBlock.NOT_READY_REFUSED
                if reason in self._ZONE_REFUSALS
                else RuleBlock.REFUSED
            ),
        )

    def unblock_when_ready(self, rule: AutoRule) -> None:
        """Let a rule an open window refused ask again, once it is shut.

        The only thing that releases it is the thing that refused it, which
        is why this reads the same blockers the arming itself reads rather
        than a timer: "shut the window and the house arms" is the behaviour,
        and "ask again every two minutes" is the one it must not have.
        """
        runtime = self.rules_runtime.get(rule.id, RuleRuntime())
        if runtime.blocked is not RuleBlock.NOT_READY_REFUSED:
            return
        scenario = self.config.scenario(rule.scenario_id)
        faulted, open_ = self.blockers(tuple(scenario.areas) if scenario else ())
        if not faulted and not open_:
            self.rules_runtime[rule.id] = replace(runtime, latched=False, blocked=None)

    def spend(self, rule: AutoRule) -> None:
        """After a countdown was stopped at the last moment by a guard.

        A condition that still holds may try again — somebody shut the window
        and the house is still empty — so a level trigger is unlatched. An
        edge occurrence was already spent when the countdown started, and one
        occurrence is all it ever had (part 2 decision 4).
        """
        runtime = self.rules_runtime.get(rule.id, RuleRuntime())
        if rule.trigger.level:
            self.rules_runtime[rule.id] = replace(runtime, latched=False)

    def rule_decision(
        self, rule: AutoRule, scenario_id: str | None = None
    ) -> _RuleDecision:
        """What this rule would do now, or what is stopping it (§9.4).

        One place, called both when a countdown starts and when it ends, so
        the second evaluation cannot disagree with the first about what the
        rules are.
        """
        suspension = rules_engine.covering(
            replace(self.snapshot.state, suspensions=tuple(self.suspensions)),
            rule,
            self.now,
        )
        substitute = rules_engine.substitute_scenario(suspension)
        scenario_id = scenario_id or substitute or rule.scenario_id
        decided = _RuleDecision(
            action=rule.action,
            scenario_id=scenario_id,
            suspension=suspension,
            substituted=substitute is not None and rule.action is RuleActionKind.ARM,
        )
        if not self.auto_arming:
            return replace(decided, block=RuleBlock.SWITCH_OFF)
        if self.walk_test is not None:
            # The house is armed for a test and somebody is walking through
            # it (part 2 decision 11). Fifteen minutes is a cheap thing to
            # lose; a prova interrupted half-way is not.
            return replace(decided, block=RuleBlock.WALK_TEST)
        if suspension is not None and not decided.substituted:
            return replace(decided, block=RuleBlock.SUSPENDED)

        target_areas: tuple[str, ...] = ()
        if rule.action is RuleActionKind.DISARM:
            allowed, refused = rules_engine.disarm_targets(self.config, rule)
            if not rule.area_ids or any(
                self.config.area(a) is None for a in rule.area_ids
            ):
                return replace(decided, block=RuleBlock.UNKNOWN_AREA)
            decided = replace(decided, area_ids=allowed, refused=refused)
            if not allowed:
                # Every area it named is the perimeter, so there is nothing
                # left for it to do (§9.4 point 3).
                return replace(decided, block=RuleBlock.PERIMETER)
        else:
            scenario = self.config.scenario(scenario_id)
            target_areas = tuple(scenario.areas) if scenario else ()
            # An `arm` action and a `switch` action are the same call
            # (`arm_scenario`), and with a scenario already running they do
            # the same thing: the areas only the old scenario armed are
            # disarmed (§4.6.1). So both are read the same way here. Reading
            # only the word on the rule would leave "arm Night" as a way of
            # disarming the perimeter without ever asking (part 2 decision 6).
            dropped, perimeter = rules_engine.switch_drops(
                self.config,
                # The world as it is *now*, both halves of it. The areas were
                # already live here and the active scenario was not, so
                # anything that switched scenario earlier in this same
                # decision left this reading a scenario that had already gone
                # — and with it the list of areas the rule was about to drop.
                # Empty list, nothing refused, and `arm_scenario` then
                # disarmed the perimeter itself, past the one constraint
                # §9.4 says is enforced in the engine (found in review).
                replace(
                    self.snapshot.state,
                    areas=self.areas,
                    active_scenario_id=self.active_scenario_id,
                ),
                scenario_id,
            )
            # What it would actually disarm, with the perimeter taken out: a
            # switch whose only dropped area is the perimeter disarms
            # nothing, and must not be refused for a consequence it has not.
            decided = replace(
                decided,
                area_ids=tuple(a for a in dropped if a not in perimeter),
                refused=perimeter,
            )
        live = (
            set(self.incident.area_ids)
            if self.incident is not None and not self.incident.acknowledged
            else set()
        )
        if decided.disarms and any(
            self.areas[area_id].state in (AreaState.ENTRY, AreaState.TRIGGERED)
            or area_id in live
            for area_id in decided.area_ids
            if area_id in self.areas
        ):
            # The incident is part of the question, not only the area's
            # state: after the siren cutoff an area is back to `armed` with
            # its memory set and the escalation still climbing, and a disarm
            # there acknowledges it just the same (found in review).
            # §4.6.1 already refuses a scenario switch while an area it would
            # touch is in entry or triggered: changing scenario must never
            # silence an alarm without a disarm. A rule is the same case and
            # more so — disarming an area the incident touched acknowledges
            # the incident and stops the escalation (§7.2), so a phone
            # walking through the door would stop the call on its way to the
            # neighbour. A person may do that; an inference from a phone may
            # not.
            return replace(decided, block=RuleBlock.ALARM_IN_PROGRESS)
        if decided.disarms and not self.config.settings.allow_auto_disarm:
            # §9.4 point 2, enforced rather than documented: a rule that
            # would leave the house less protected does nothing until
            # somebody has turned automatic disarming on, having read what it
            # costs.
            return replace(decided, block=RuleBlock.AUTO_DISARM_DISABLED)
        faulted, open_ = self.blockers(target_areas)
        block = rules_engine.guard_block(
            rule,
            disarmed=all(rt.state is AreaState.DISARMED for rt in self.areas.values()),
            ready=not faulted and not open_,
            quiet=self.interior_quiet(rule.guards.quiet_minutes),
        )
        return replace(decided, block=block)

    def interior_quiet(self, minutes: int | None) -> bool:
        """Whether the inside of the house has been still for long enough.

        Read from the zones themselves rather than from a memory of its own:
        a zone that is active now, or whose entity changed inside the window,
        is somebody moving. Perimeter areas are left out — a front door
        contact is not evidence that anybody is in.
        """
        if minutes is None:
            return True
        last = rules_engine.last_interior_motion(
            self.config,
            frozenset(self.active),
            {zone.id: self.entity(zone).last_changed for zone in self.config.zones},
            self.now,
        )
        return last is None or last <= self.now - timedelta(minutes=minutes)

    def rule_blocked(
        self, rule: AutoRule, block: RuleBlock, suspension: Suspension | None
    ) -> bool:
        """Say why a rule did not act — once, at the start of the block.

        §9.4 asks for this row by name, under ``system``: "why did it not arm
        last night?" is a question users ask.

        For a **level** trigger the row is written once, when the block
        begins: the rule is re-evaluated at every wake-up and a row a minute
        would bury the log it belongs to (part 2 decision 4). For an **edge**
        trigger every occurrence is its own event, so every blocked 23:00
        gets its own row — otherwise a rule blocked on Monday would spend the
        rest of the week not arming in silence, which is the failure this
        row exists to prevent.
        """
        runtime = self.rules_runtime.get(rule.id, RuleRuntime())
        if runtime.blocked is not block or not rule.trigger.level:
            detail = {"rule": rule.name, "rule_id": rule.id, "reason": block.value}
            if suspension is not None:
                detail |= _suspension_detail(suspension)
            self.occur(Moment.AUTO_BLOCKED, channel=AUTO_RULE_CHANNEL, detail=detail)
        skipped = (
            block is RuleBlock.SUSPENDED
            and suspension is not None
            and suspension.kind is SuspensionKind.NEXT
        )
        self.rules_runtime[rule.id] = replace(
            runtime,
            blocked=block,
            # For a level trigger an "occurrence" is the whole time its
            # condition holds: latching it is what makes the skip last until
            # somebody comes home, rather than until the next wake-up sixty
            # seconds later.
            latched=runtime.latched or (skipped and rule.trigger.level),
        )
        if skipped and suspension is not None:
            self.consume_suspension(suspension)
        return skipped

    def consume_suspension(self, suspension: Suspension) -> None:
        """ "Skip the next occurrence" is spent by use, never by the clock."""
        if suspension in self.suspensions:
            self.suspensions.remove(suspension)
            self.occur(
                Moment.AUTO_SUSPENSION_CLEARED,
                detail=_suspension_detail(suspension) | {"cause": "used"},
            )

    def start_countdown(self, rule: AutoRule, decided: _RuleDecision) -> None:
        """Announce what is about to happen, with a Cancel button (§9.4)."""
        self.pending_seq += 1
        pending = PendingRuleAction(
            id=f"{rule.id}:{self.pending_seq}",
            rule_id=rule.id,
            rule_name=rule.name,
            action=decided.action,
            due=self.now + timedelta(seconds=rule.grace_seconds),
            started_at=self.now,
            scenario_id=decided.scenario_id,
            area_ids=decided.area_ids,
            suspension_name=(decided.suspension.name if decided.substituted else None),
        )
        self.pending_rules.append(pending)
        if (
            decided.substituted
            and decided.suspension is not None
            and decided.suspension.kind is SuspensionKind.NEXT
        ):
            # Only "skip the next occurrence" is spent by use. A visitor
            # window runs until its end: the engineer is there all morning,
            # and a window that ended at the first substitution would arm the
            # house around them at the second rule of the day.
            self.consume_suspension(decided.suspension)
        self.occur(
            Moment.AUTO_PENDING,
            channel=AUTO_RULE_CHANNEL,
            scenario_id=decided.scenario_id,
            detail={
                "rule": rule.name,
                "rule_id": rule.id,
                "pending_id": pending.id,
                "action": decided.action.value,
                "seconds": str(rule.grace_seconds),
                "due": pending.due.isoformat(),
                "areas": ",".join(decided.area_ids),
                "contacts": ",".join(rule.notify_contact_ids),
            },
        )

    def cancel_auto_action(self, event: CancelAutoAction) -> _Outcome:
        """Somebody pressed Cancel (§9.4).

        Its own operation in the code policy, without a code by default
        (part 2 decision 3): the button travels in a push notification, and
        no push carries a code. An installation that raises it gets a button
        that refuses visibly rather than one that lies.
        """
        targets = [
            p
            for p in self.pending_rules
            if event.pending_id is None or p.id == event.pending_id
        ]
        if not targets:
            return _reject(Reason.NOTHING_TO_CANCEL)
        if (reason := self.authorize(Operation.CANCEL_AUTO_ACTION)) is not None:
            return _reject(reason)
        for pending in targets:
            self.pending_rules.remove(pending)
            self.occur(
                Moment.AUTO_CANCELLED,
                channel=self.channel or AUTO_RULE_CHANNEL,
                scenario_id=pending.scenario_id,
                detail={
                    "rule": pending.rule_name,
                    "rule_id": pending.rule_id,
                    "pending_id": pending.id,
                    "action": pending.action.value,
                    "via": event.via,
                    "contact": event.contact_id or "",
                },
            )
        return _ACCEPTED

    def set_auto_arming(self, enabled: bool) -> _Outcome:
        """switch.foyer_auto_arming (§9.4): the whole mechanism, off or on.

        Countdowns already running are cancelled with it. A switch that left
        the announced arming to happen anyway would be a switch that does not
        do what it says at the one moment somebody reaches for it.

        It goes through the same policy entry as Cancel, and for the same
        reason: both stop the house arming itself, one for two minutes and
        one for as long as it stays off. No code by default (part 2
        decision 3), and an installation that raises that entry raises both.
        """
        if (reason := self.authorize(Operation.CANCEL_AUTO_ACTION)) is not None:
            return _reject(reason)
        self.auto_arming = enabled
        self.occur(
            Moment.AUTO_ARMING_SWITCHED,
            channel=self.channel,
            detail={"enabled": "1" if enabled else "0"},
        )
        if enabled:
            return _ACCEPTED
        for pending in list(self.pending_rules):
            self.pending_rules.remove(pending)
            self.occur(
                Moment.AUTO_CANCELLED,
                channel=self.channel,
                detail={
                    "rule": pending.rule_name,
                    "rule_id": pending.rule_id,
                    "pending_id": pending.id,
                    "action": pending.action.value,
                    "via": "switch",
                },
            )
        return _ACCEPTED

    def set_suspension(self, event: SetSuspension) -> _Outcome:
        """Suspend automatic arming, or lift a suspension (§9.4).

        Runtime state, not configuration (part 2 decision 7): three clicks
        from the card, and no ``edit_config`` between somebody and the
        morning the boiler engineer is expected. It is still an operation,
        though — suspending every rule is the kill switch with a date on it —
        so it asks the same policy entry Cancel asks.
        """
        if (reason := self.authorize(Operation.CANCEL_AUTO_ACTION)) is not None:
            return _reject(reason)
        if event.suspension is None:
            found = next(
                (s for s in self.suspensions if s.id == event.suspension_id), None
            )
            if found is None:
                return _reject(Reason.UNKNOWN_SUSPENSION)
            self.suspensions.remove(found)
            self.occur(
                Moment.AUTO_SUSPENSION_CLEARED,
                channel=self.channel,
                user_id=self.actor.user_id,
                detail=_suspension_detail(found) | {"cause": "lifted"},
            )
            return _ACCEPTED
        suspension = event.suspension
        if suspension.kind is not SuspensionKind.NEXT and suspension.until is None:
            # §9.4 offers three forms and every one of them ends: until a
            # date, for one occurrence, or a named window. One with no end
            # would be the kill switch wearing a name nobody would think to
            # look for — and `expired()` would never remove it.
            return _reject(Reason.INVALID_STATE)
        if any(
            rule_id not in {r.id for r in self.config.rules}
            for rule_id in suspension.rule_ids
        ):
            return _reject(Reason.UNKNOWN_RULE)
        if (
            suspension.reduced_scenario_id is not None
            and self.config.scenario(suspension.reduced_scenario_id) is None
        ):
            return _reject(Reason.UNKNOWN_SCENARIO)
        self.suspensions = [s for s in self.suspensions if s.id != suspension.id]
        self.suspensions.append(suspension)
        self.occur(
            Moment.AUTO_SUSPENSION_SET,
            channel=self.channel,
            user_id=self.actor.user_id,
            detail=_suspension_detail(suspension),
        )
        return _ACCEPTED

    def rule_act(
        self, rule: AutoRule, decided: _RuleDecision, *, late: bool = False
    ) -> None:
        """The rule acts, as a user would (§9.4).

        The channel is ``auto_rule`` and the actor holds no code: nobody is
        there to be asked for one, and the authorisation happened earlier,
        when somebody with ``edit_config`` saved the rule (part 2 decision
        9). What it does not buy is the perimeter: ``decided.area_ids`` has
        already had those areas taken out of it.
        """
        previous, self.actor = (
            self.actor,
            Actor(channel=AUTO_RULE_CHANNEL, token=True),
        )
        self.rule_detail = {"rule": rule.name, "rule_id": rule.id}
        if decided.substituted and decided.suspension is not None:
            self.rule_detail["suspension"] = decided.suspension.name or ""
        if late:
            # It fell due while nothing was running and it is happening now,
            # which is a thing the log has to say out loud (part 2 decision 12).
            self.rule_detail["late"] = "1"
        try:
            outcome = self.rule_perform(decided)
        finally:
            self.actor = previous
            self.rule_detail = {}
        if outcome.accepted:
            return
        if decided.action is RuleActionKind.DISARM:
            self.occur(
                Moment.AUTO_BLOCKED,
                channel=AUTO_RULE_CHANNEL,
                detail={
                    "rule": rule.name,
                    "rule_id": rule.id,
                    "reason": outcome.reason.value if outcome.reason else "",
                },
            )
            return
        # It did not happen. A level trigger waits rather than asking again
        # at once: `evaluate_rules` runs in this same call, so unlatching
        # here would start another countdown immediately and every two
        # minutes after that — an actionable push saying "the house will arm
        # in two minutes", all night, about an arming that cannot happen.
        # What it waits for depends on what refused it: an open window is
        # something a zone can put right, and the rule tries again the moment
        # the areas it wants are ready (`unblock_when_ready`). Anything else
        # waits for the condition to go false and true again, like a rule
        # that has had its turn.
        self.refused(rule, outcome.reason)
        if outcome.reason is Reason.INVALID_STATE:
            # Already armed, or already this scenario: not a failure, and not
            # worth a warning row every evening.
            return
        self.occur(
            Moment.ARM_FAILED,
            scenario_id=decided.scenario_id,
            zone_ids=outcome.blocking,
            channel=AUTO_RULE_CHANNEL,
            detail={
                "rule": rule.name,
                "rule_id": rule.id,
                "reason": outcome.reason.value if outcome.reason else "",
            },
        )

    def rule_perform(self, decided: _RuleDecision) -> _Outcome:
        if decided.action is RuleActionKind.DISARM:
            return self.disarm(decided.area_ids)
        return self.arm_scenario(
            self.config.scenario(decided.scenario_id),
            force=False,
            # A switch never disarms a perimeter area: those stay armed,
            # outside any scenario, and the master then reports
            # armed_custom_bypass (§13, part 2 decision 6).
            keep_armed=frozenset(decided.refused),
        )

    # --- result -----------------------------------------------------------------

    def decision(self, outcome: _Outcome) -> Decision:
        ctx = PlanContext(
            config=self.config,
            snapshot=self.world(),
            now=self.now,
            areas=self.areas,
            incident=self.incident,
            active_zones=frozenset(self.active),
            walk_test=self.inhibiting,
            # §12.5's rule that defeats the feature if missed: an action
            # whose target sits on a radio currently suspected of being
            # jammed is not run, because announcing a Zigbee blackout
            # through a Zigbee siren is not a notification.
            impaired=SystemHealth(radios=self.radios).impaired_radios,
            broken_channels=frozenset(
                key for key, health in self.channels.items() if health.fault is not None
            ),
            technical=dict(self.technical),
        )
        # Escalation steps first, because reaching the end of one raises a
        # moment a profile answers in this same call (§7.2).
        steps = self.run_escalations(ctx)
        occurrences = tuple(self.occurrences)
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
        # The device endpoint counts by source address (§9.2.1), and a house
        # reachable from outside meets many. A counter with nothing left to
        # count is dropped rather than kept for ever.
        self.lockouts = {
            key: lock
            for key, lock in self.lockouts.items()
            if not (key.startswith("http:") and authz.stale(lock, self.now))
        }
        state = RuntimeState(
            areas=self.areas,
            active_scenario_id=self.active_scenario_id,
            bypassed=self.bypassed,
            active_zones=frozenset(self.active),
            seen_zones=frozenset(self.seen),
            seen_devices=frozenset(self.seen_devices),
            in_clear=frozenset(self.in_clear),
            faults=self.faults,
            low_batteries=self.low_batteries,
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
            walk_test=self.walk_test,
            escalations=tuple(self.escalations),
            auto_arming=self.auto_arming,
            pending_rules=tuple(self.pending_rules),
            suspensions=tuple(self.suspensions),
            rules=self.rules_runtime,
            pending_seq=self.pending_seq,
            health=SystemHealth(
                mains_lost_since=self.mains_lost_since,
                channels=self.channels,
                watchdog=self.watchdog,
                radios=self.radios,
                quiet_since=self.quiet_since,
                unknown_zones=frozenset(self.unknown_zones),
                acknowledged_issues=self.acknowledged_issues,
            ),
        )
        chime, chime_inhibited = self.chime_intents(occurrences)
        countdown = self.countdown_intents(occurrences)
        return Decision(
            at=self.now,
            accepted=outcome.accepted,
            state=state,
            reason=outcome.reason,
            blocking_zones=outcome.blocking,
            bypassed_zones=tuple(self.new_bypasses),
            low_battery_zones=self.low_battery_zones,
            code_required_by=(
                self.code_required_by
                if outcome.reason is Reason.CODE_REQUIRED
                else None
            ),
            occurrences=occurrences,
            actions=(*self.extra, *steps, *plan.intents, *chime, *countdown),
            inhibited=(*plan.inhibited, *chime_inhibited),
            # What is still to come, read off the state this decision
            # produced: never a second prediction of it (§11.2, INV-1).
            escalation=self.scheduled_steps(),
        )

    def scheduled_steps(self) -> tuple[ScheduledStep, ...]:
        out: list[ScheduledStep] = []
        for current in self.escalations:
            profile = self.config.profile(current.profile_id)
            if profile is not None:
                out.extend(escalation_engine.scheduled(current, profile, self.now))
        return tuple(sorted(out, key=lambda step: (step.due, step.index)))

    def countdown_intents(
        self, occurrences: tuple[Occurrence, ...]
    ) -> tuple[ActionIntent, ...]:
        """ "The house will arm in two minutes", with a Cancel button (§9.4).

        The rule names its own contacts (part 2 decision 2), so this is built
        here rather than by a response profile, and it is built the way the
        chime is: the Decision carries everything the executor needs and the
        executor looks nothing up (INV-1).

        A contact inside their quiet hours is held back exactly as they are
        for anything else at this severity (§7.1). The countdown still runs —
        what a quiet window buys is silence, not a different decision — and
        the row records who was not told.
        """
        intents: list[ActionIntent] = []
        for occurrence in occurrences:
            if occurrence.moment is not Moment.AUTO_PENDING:
                continue
            pending_id = occurrence.detail.get("pending_id", "")
            contact_ids = [
                c for c in occurrence.detail.get("contacts", "").split(",") if c
            ]
            if not contact_ids:
                continue
            recipients, quiet = recipients_for(
                self.config,
                [{"contact_id": c, "channel_id": None} for c in contact_ids],
                self.now,
                self.timezone,
                Moment.AUTO_PENDING,
                cancel=pending_id,
            )
            if not recipients:
                continue
            scenario = self.config.scenario(occurrence.scenario_id)
            intents.append(
                ActionIntent(
                    action_id=f"auto_rule:{pending_id}",
                    kind=ActionKind.NOTIFY.value,
                    moment=Moment.AUTO_PENDING,
                    placeholders={
                        "rule": occurrence.detail.get("rule", ""),
                        "scenario": scenario.name if scenario else "",
                        "seconds": occurrence.detail.get("seconds", ""),
                    },
                    variant=occurrence.detail.get("action"),
                    params={
                        "recipients": recipients,
                        "quiet": ",".join(quiet),
                        "pending_id": pending_id,
                    },
                )
            )
        return tuple(intents)

    def chime_intents(
        self, occurrences: tuple[Occurrence, ...]
    ) -> tuple[tuple[ActionIntent, ...], tuple[ActionIntent, ...]]:
        """The chime is a setting, not a profile (§6.6). The Decision carries
        everything the executor needs: it never reads the configuration.

        Returns what sounds and what a walk test held back. §6.6 says the
        chime needs no special case for a walk test, because the area is
        armed and its zones are monitored — but an area that failed to arm
        would chime through the whole walk, and "all actions are inhibited"
        (§11.3) is the rule that covers it.
        """
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
        if self.inhibiting:
            return (), tuple(intents)
        return tuple(intents), ()


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
