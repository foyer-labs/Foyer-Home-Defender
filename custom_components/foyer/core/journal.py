"""What the event log records, decided here and nowhere else (SPEC §10).

Pure, like everything in ``core``: it turns a Decision — the occurrences it
produced, and the request it may have refused — into log rows. The store
writes them; this module says what they are. Keeping it here means the
categories, the severities and the outcome of a refusal are testable with no
Home Assistant instance, and that the simulator (Phase 3) can show exactly the
rows a run would have written without writing any.

Two rules the rest of the code depends on:

- every ``Moment`` has a category and a severity, and a test asserts it: a
  moment added later without one would silently disappear from the log;
- a row is data. Nothing here formats a sentence for a human — the panel
  translates ``event_type`` like every other user-visible string.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import (
    AcknowledgeIncident,
    AcknowledgeTechnical,
    Actor,
    AreaState,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    Decision,
    DisarmRequest,
    Event,
    FoyerConfig,
    LogCategory,
    LogSeverity,
    Moment,
    Occurrence,
    Outcome,
    Reason,
    RuntimeState,
    SetChime,
    Startup,
    Tick,
    ZoneStateChanged,
)


def _frozen(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    from types import MappingProxyType

    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class LogRow:
    """One row of ``events`` (SPEC §10.1).

    ``user_name`` is denormalised on purpose: deleting a user must not erase
    the history of what that user did. There are no users before Phase 2, so
    both user columns are empty for now and the shape is already right.

    ``incident_id`` is not in the §10.1 table and is added here: §5.6 requires
    the incident id on every related row, and a JSON detail field cannot be
    filtered on.
    """

    ts: datetime
    category: LogCategory
    event_type: str
    severity: LogSeverity = LogSeverity.INFO
    area_id: str | None = None
    zone_id: str | None = None
    scenario_id: str | None = None
    incident_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    channel: str | None = None
    device_id: str | None = None
    outcome: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", _frozen(self.detail))


# Which category each moment belongs to (SPEC §10.2). The split that matters
# is not "how loud" but "what kind of question does this answer": arming
# answers "who armed", security answers "what was excluded or forced", alarm
# answers "what happened that night".
CATEGORY: dict[Moment, LogCategory] = {
    Moment.ARMED: LogCategory.ARMING,
    Moment.DISARMED: LogCategory.ARMING,
    Moment.ARM_FAILED: LogCategory.ARMING,
    # A forced arm and a bypass leave part of the house unprotected on
    # purpose: that is a security decision, not an arming detail.
    Moment.FORCED_ARM: LogCategory.SECURITY,
    Moment.ZONE_BYPASSED: LogCategory.SECURITY,
    Moment.ZONE_REJOINED: LogCategory.SECURITY,
    Moment.CODE_REJECTED: LogCategory.SECURITY,
    Moment.LOCKOUT: LogCategory.SECURITY,
    Moment.DURESS: LogCategory.SECURITY,
    Moment.ENTRY_STARTED: LogCategory.ALARM,
    Moment.TRIGGERED: LogCategory.ALARM,
    Moment.SIREN_CUTOFF: LogCategory.ALARM,
    Moment.INCIDENT_OPENED: LogCategory.ALARM,
    Moment.INCIDENT_JOINED: LogCategory.ALARM,
    Moment.INCIDENT_ACKNOWLEDGED: LogCategory.ALARM,
    Moment.INCIDENT_CLOSED: LogCategory.ALARM,
    Moment.TECHNICAL_RAISED: LogCategory.ALARM,
    Moment.TECHNICAL_ACKNOWLEDGED: LogCategory.ALARM,
    Moment.TECHNICAL_CLEARED: LogCategory.ALARM,
    Moment.VERIFICATION_PENDING: LogCategory.ALARM,
    Moment.VERIFICATION_SATISFIED: LogCategory.ALARM,
    Moment.VERIFICATION_EXPIRED: LogCategory.ALARM,
    Moment.ESCALATION_EXHAUSTED: LogCategory.ALARM,
    Moment.ZONE_FAULT: LogCategory.SYSTEM,
    Moment.LOW_BATTERY: LogCategory.SYSTEM,
    Moment.HA_RESTARTED: LogCategory.SYSTEM,
    Moment.WALK_TEST_STARTED: LogCategory.SYSTEM,
    Moment.WALK_TEST_ENDED: LogCategory.SYSTEM,
    Moment.CHIME_SWITCHED: LogCategory.SYSTEM,
    # A test is an action, filed with the actions — and marked (§11.4).
    Moment.ACTION_TESTED: LogCategory.ACTION,
    # A chime sounds exactly when a zone opens unmonitored (§6.6), which is
    # the volume class of zone activity while disarmed — and its category.
    Moment.CHIME: LogCategory.ZONE_DISARMED,
}

SEVERITY: dict[Moment, LogSeverity] = {
    Moment.ARMED: LogSeverity.INFO,
    Moment.DISARMED: LogSeverity.INFO,
    Moment.ARM_FAILED: LogSeverity.WARNING,
    Moment.FORCED_ARM: LogSeverity.WARNING,
    Moment.ZONE_BYPASSED: LogSeverity.WARNING,
    Moment.ZONE_REJOINED: LogSeverity.INFO,
    Moment.CODE_REJECTED: LogSeverity.WARNING,
    Moment.LOCKOUT: LogSeverity.WARNING,
    # A duress disarm is somebody being made to open their own house. It is
    # the loudest row in the log, and the only one the house itself hides.
    Moment.DURESS: LogSeverity.ALARM,
    Moment.ENTRY_STARTED: LogSeverity.WARNING,
    Moment.TRIGGERED: LogSeverity.ALARM,
    Moment.SIREN_CUTOFF: LogSeverity.WARNING,
    Moment.INCIDENT_OPENED: LogSeverity.ALARM,
    Moment.INCIDENT_JOINED: LogSeverity.ALARM,
    Moment.INCIDENT_ACKNOWLEDGED: LogSeverity.INFO,
    Moment.INCIDENT_CLOSED: LogSeverity.INFO,
    Moment.TECHNICAL_RAISED: LogSeverity.ALARM,
    Moment.TECHNICAL_ACKNOWLEDGED: LogSeverity.INFO,
    Moment.TECHNICAL_CLEARED: LogSeverity.INFO,
    Moment.VERIFICATION_PENDING: LogSeverity.WARNING,
    Moment.VERIFICATION_SATISFIED: LogSeverity.ALARM,
    Moment.VERIFICATION_EXPIRED: LogSeverity.INFO,
    Moment.ESCALATION_EXHAUSTED: LogSeverity.ALARM,
    Moment.ZONE_FAULT: LogSeverity.WARNING,
    Moment.LOW_BATTERY: LogSeverity.WARNING,
    # The restart gap is a hole in the coverage, however short (INV-3).
    Moment.HA_RESTARTED: LogSeverity.WARNING,
    Moment.WALK_TEST_STARTED: LogSeverity.WARNING,
    Moment.WALK_TEST_ENDED: LogSeverity.INFO,
    Moment.CHIME_SWITCHED: LogSeverity.INFO,
    Moment.CHIME: LogSeverity.INFO,
    Moment.ACTION_TESTED: LogSeverity.INFO,
}

# Moments whose row is named something else, because the spec names them: the
# restart gap is "system_unavailable from T1 to T2" (§10.1, INV-3).
EVENT_TYPE: dict[Moment, str] = {Moment.HA_RESTARTED: "system_unavailable"}

# A reload is not a restart. Saving a setting reloads the integration, and the
# gap that leaves is a fraction of a second in which nothing could have
# happened: recording it as "Foyer was not running" — in warning, next to the
# configuration change that caused it — teaches people to ignore the row that
# matters. Above this many seconds it is an outage again, whatever caused it,
# because the integration can also be disabled and re-enabled by hand.
RELOAD = "reloaded"
RELOAD_GAP_SECONDS = 60


def _restart_row(occurrence: Occurrence, at: datetime) -> tuple[str, LogSeverity]:
    """What to call a gap in coverage, and how loudly (INV-3)."""
    detail = occurrence.detail
    gap = detail.get("gap_seconds") or ""
    brief = gap.isdigit() and int(gap) <= RELOAD_GAP_SECONDS
    if detail.get("cause") == "reload" and brief:
        return RELOAD, LogSeverity.INFO
    return EVENT_TYPE[Moment.HA_RESTARTED], LogSeverity.WARNING


# A moment that is, in itself, a failed request.
OUTCOME: dict[Moment, Outcome] = {
    Moment.ARM_FAILED: Outcome.BLOCKED,
    Moment.CODE_REJECTED: Outcome.BAD_CODE,
    Moment.LOCKOUT: Outcome.BLOCKED,
}

# What a refused request is called and where it is filed. A refusal is worth
# a row of its own: "why did it not arm last night?" is a question users ask,
# and silence is the worst possible answer.
REJECTION: dict[type, tuple[str, LogCategory]] = {
    ArmRequest: ("arm_rejected", LogCategory.ARMING),
    ArmModeRequest: ("arm_rejected", LogCategory.ARMING),
    ArmAreaRequest: ("arm_rejected", LogCategory.ARMING),
    DisarmRequest: ("disarm_rejected", LogCategory.ARMING),
    BypassZone: ("bypass_rejected", LogCategory.SECURITY),
    AcknowledgeIncident: ("acknowledge_rejected", LogCategory.ALARM),
    AcknowledgeTechnical: ("acknowledge_rejected", LogCategory.ALARM),
    SetChime: ("chime_rejected", LogCategory.SYSTEM),
}

# Refusals that have already said who and why, under `security`.
_IDENTITY_MOMENTS = frozenset({Moment.CODE_REJECTED, Moment.LOCKOUT})

# States in which an area is watching its zones, for the zone_armed /
# zone_disarmed split (§10.2). ``arming`` counts: the exit delay is part of
# the arming, and a zone opening during it is worth the same row.
_MONITORING = frozenset(
    {AreaState.ARMING, AreaState.ARMED, AreaState.ENTRY, AreaState.TRIGGERED}
)


def category_of(moment: Moment) -> LogCategory:
    return CATEGORY[moment]


def severity_of(moment: Moment) -> LogSeverity:
    return SEVERITY[moment]


def event_type_of(moment: Moment) -> str:
    return EVENT_TYPE.get(moment, moment.value)


def row_for(occurrence: Occurrence, at: datetime) -> LogRow:
    """One occurrence, as the row that records it."""
    detail: dict[str, Any] = dict(occurrence.detail)
    if occurrence.zone_ids:
        detail["zone_ids"] = list(occurrence.zone_ids)
    if occurrence.group_id:
        detail["group_id"] = occurrence.group_id
    outcome = OUTCOME.get(occurrence.moment)
    event_type, severity = (
        event_type_of(occurrence.moment),
        severity_of(occurrence.moment),
    )
    if occurrence.moment is Moment.HA_RESTARTED:
        event_type, severity = _restart_row(occurrence, at)
    return LogRow(
        ts=at,
        category=category_of(occurrence.moment),
        event_type=event_type,
        severity=severity,
        area_id=occurrence.area_id,
        zone_id=occurrence.zone_id,
        scenario_id=occurrence.scenario_id,
        incident_id=occurrence.incident_id,
        user_id=occurrence.user_id,
        user_name=occurrence.user_name,
        channel=occurrence.channel,
        device_id=occurrence.device_id,
        outcome=(outcome or Outcome.OK).value,
        detail=detail,
    )


def rejection_row(
    event: Event, decision: Decision, config: FoyerConfig | None = None
) -> LogRow | None:
    """The row a refused request leaves behind, if the event can be refused.

    A refusal over identity — a wrong code, a locked channel, a permission
    somebody does not hold — has already written its own row under `security`
    (§8.4), which says more than "arm_rejected" ever could. Writing both would
    put the same event in the log twice, in two categories.
    """
    named = REJECTION.get(type(event))
    if named is None:
        return None
    if any(o.moment in _IDENTITY_MOMENTS for o in decision.occurrences):
        return None
    event_type, category = named
    actor = getattr(event, "actor", None) or Actor()
    user = config.user(actor.user_id) if config is not None else None
    detail: dict[str, Any] = {}
    if decision.reason is not None:
        detail["reason"] = decision.reason.value
    if decision.blocking_zones:
        detail["blocking_zones"] = list(decision.blocking_zones)
    return LogRow(
        ts=decision.at,
        category=category,
        event_type=event_type,
        severity=LogSeverity.WARNING,
        area_id=getattr(event, "area_id", None),
        zone_id=getattr(event, "zone_id", None),
        scenario_id=getattr(event, "scenario_id", None),
        user_id=actor.user_id,
        user_name=user.name if user else None,
        channel=actor.channel,
        device_id=actor.device_id,
        outcome=(
            Outcome.BAD_CODE
            if decision.reason in (Reason.BAD_CODE, Reason.CODE_REQUIRED)
            else Outcome.BLOCKED
        ).value,
        detail=detail,
    )


def zone_rows(
    event: ZoneStateChanged,
    state: RuntimeState,
    config: FoyerConfig,
    at: datetime,
    *,
    old: str | None = None,
    was_active: frozenset[str] = frozenset(),
) -> tuple[LogRow, ...]:
    """The movement of an entity, filed by whether its area was watching.

    One entity may back more than one zone, and each zone's own area decides
    its category: with "Windows only" armed, the same PIR is watched in one
    area and not in another.

    Home Assistant also reports a change when only the attributes moved — a
    battery level, a signal strength — and the watcher passes those on because
    a numeric attribute trigger depends on them. They are not zone activity,
    so a row is written only when the state itself moved, or when what Foyer
    makes of it did: a numeric trigger crossing its band changes nothing
    visible in the state and is exactly what the log should show.
    """
    rows = []
    for zone in config.zones:
        if zone.entity_id != event.entity_id:
            continue
        active = zone.id in state.active_zones
        if old == event.new.state and active == (zone.id in was_active):
            continue
        area_state = state.area(zone.area_id).state
        rows.append(
            LogRow(
                ts=at,
                category=(
                    LogCategory.ZONE_ARMED
                    if area_state in _MONITORING
                    else LogCategory.ZONE_DISARMED
                ),
                event_type="zone_state",
                severity=LogSeverity.INFO,
                area_id=zone.area_id,
                zone_id=zone.id,
                outcome=Outcome.OK.value,
                detail={
                    "from": old,
                    "to": event.new.state,
                    "area_state": area_state.value,
                    # What Foyer made of it: whether the zone now counts as
                    # triggered, which a state string alone does not say.
                    "active": active,
                },
            )
        )
    return tuple(rows)


def rows_for(
    event: Event,
    decision: Decision,
    config: FoyerConfig,
    *,
    old_state: str | None = None,
    was_active: frozenset[str] = frozenset(),
) -> tuple[LogRow, ...]:
    """Everything one decision puts in the log, in the order it happened.

    The occurrences first, because they are what happened; then the refusal,
    if the request was refused; then the raw zone movement, which is the noisy
    part and belongs at the end of the group.
    """
    rows = [row_for(occurrence, decision.at) for occurrence in decision.occurrences]
    if not decision.accepted and not isinstance(event, Tick | Startup):
        rejected = rejection_row(event, decision, config)
        if rejected is not None:
            rows.append(rejected)
    if isinstance(event, ZoneStateChanged):
        rows.extend(
            zone_rows(
                event,
                decision.state,
                config,
                decision.at,
                old=old_state,
                was_active=was_active,
            )
        )
    return tuple(rows)


def action_row(
    at: datetime,
    *,
    action_id: str,
    kind: str,
    moment: Moment | None,
    ok: bool,
    error: str | None = None,
    profile_id: str | None = None,
    area_id: str | None = None,
    zone_id: str | None = None,
    incident_id: str | None = None,
) -> LogRow:
    """What one action did (§10.2, category ``action``).

    A failure here is the one this project exists to prevent being discovered
    during the emergency, so it is a warning even when everything else went
    well: the siren that did not sound is not an "info".
    """
    detail: dict[str, Any] = {"kind": kind, "action_id": action_id}
    if profile_id:
        detail["profile_id"] = profile_id
    if error:
        detail["error"] = error
    return LogRow(
        ts=at,
        category=LogCategory.ACTION,
        event_type=f"action_{kind}",
        severity=LogSeverity.INFO if ok else LogSeverity.WARNING,
        area_id=area_id,
        zone_id=zone_id,
        incident_id=incident_id,
        outcome=(Outcome.OK if ok else Outcome.FAILED).value,
        detail={**detail, "moment": moment.value if moment else None},
    )


def test_action_row(
    at: datetime,
    *,
    action_id: str,
    kind: str,
    ok: bool,
    error: str | None = None,
    profile_id: str | None = None,
    user_id: str | None = None,
    user_name: str | None = None,
    channel: str | None = None,
) -> LogRow:
    """An action somebody tested on purpose (§11.4: "logged as a test").

    Filed with the actions, because it really ran, and named differently
    from every other one, because it did not happen: a test recorded as a
    real action is a log that claims the siren went off on the sixth of
    September, and the log exists to answer exactly that question.

    A failure is a warning for the same reason an ordinary action's is —
    louder, if anything, since somebody is watching and can fix it now.
    """
    detail: dict[str, Any] = {"kind": kind, "action_id": action_id, "test": True}
    if profile_id:
        detail["profile_id"] = profile_id
    if error:
        detail["error"] = error
    return LogRow(
        ts=at,
        category=LogCategory.ACTION,
        event_type="action_test",
        severity=LogSeverity.INFO if ok else LogSeverity.WARNING,
        user_id=user_id,
        user_name=user_name,
        channel=channel,
        outcome=(Outcome.OK if ok else Outcome.FAILED).value,
        detail=detail,
    )


def security_row(
    at: datetime,
    *,
    event_type: str,
    channel: str | None = None,
    device_id: str | None = None,
    user_id: str | None = None,
    user_name: str | None = None,
    outcome: str = Outcome.BLOCKED.value,
    detail: Mapping[str, Any] | None = None,
) -> LogRow:
    """A row under ``security`` for something the engine never sees (§10.2).

    A device that is not declared is refused before any event is built, so
    there is no Decision to take a row from — and a refusal that leaves no
    trace is the one thing the log may never do (§10.2: silence is the worst
    possible answer to "why did it not arm?").
    """
    return LogRow(
        ts=at,
        category=LogCategory.SECURITY,
        event_type=event_type,
        severity=LogSeverity.WARNING,
        user_id=user_id,
        user_name=user_name,
        channel=channel,
        device_id=device_id,
        outcome=outcome,
        detail=dict(detail or {}),
    )


def system_row(
    at: datetime,
    *,
    event_type: str,
    user_id: str | None = None,
    user_name: str | None = None,
    channel: str | None = None,
    severity: LogSeverity = LogSeverity.INFO,
    detail: Mapping[str, Any] | None = None,
) -> LogRow:
    """A row under ``system`` for something no Decision produced (§10.2).

    A simulation run is the first of these: nothing happened in the house, so
    there is no occurrence to take a row from — and §11.2 still requires the
    run and its inputs to be recorded, "so a configuration change can be
    justified after the fact".
    """
    return LogRow(
        ts=at,
        category=LogCategory.SYSTEM,
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        user_name=user_name,
        channel=channel,
        outcome=Outcome.OK.value,
        detail=dict(detail or {}),
    )


def config_row(
    at: datetime,
    *,
    operation: str,
    kind: str,
    item_id: str | None = None,
    user_id: str | None = None,
    user_name: str | None = None,
    channel: str | None = None,
    ok: bool = True,
    changes: Mapping[str, Any] | None = None,
) -> LogRow:
    """Who changed what (§10.2, category ``config``), with a diff summary."""
    detail: dict[str, Any] = {"kind": kind}
    if item_id:
        detail["item_id"] = item_id
    if changes:
        detail["changes"] = dict(changes)
    return LogRow(
        ts=at,
        category=LogCategory.CONFIG,
        event_type=f"config_{operation}",
        severity=LogSeverity.INFO if ok else LogSeverity.WARNING,
        user_id=user_id,
        user_name=user_name,
        channel=channel,
        outcome=(Outcome.OK if ok else Outcome.FAILED).value,
        detail=detail,
    )
