"""Turning occurrences into actions: response profiles, pure (SPEC §6).

The engine says *what happened*; this module says *what should happen about
it*. It resolves the profile, evaluates the conditions, renders the templates
and produces the ActionIntents the executor runs — deciding everything, so the
executor decides nothing and the simulator's trace cannot disagree with the
runtime (INV-1).

Who answers for an occurrence (part 3 decision 1): **the area is the unit of
response**. Its chain is area → scenario → global default. A zone's own
profile is read only for its own alarm — the trigger, the entry it opens, the
group it satisfies — which is what makes graduated response work (§4.8): quiet
member profiles, a loud group profile. The technical channel has its own
default, because a smoke alarm must not respond differently depending on how
the house is armed (§5.5).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, tzinfo
from typing import Any

from .clock import in_daily_window
from .conditions import evaluate, unmet
from .models import (
    ActionIntent,
    ActionKind,
    AreaRuntime,
    ChimeSettings,
    FoyerConfig,
    Incident,
    Moment,
    Occurrence,
    PendingRun,
    ProfileAction,
    ResponseProfile,
    RunningAction,
    StateCondition,
    SystemSnapshot,
    TimeCondition,
    Zone,
)
from .templates import render

# The alarm of a zone: the only moments that read the zone's own profile
# (part 3 decision 1).
ZONE_MOMENTS: frozenset[Moment] = frozenset(
    {Moment.TRIGGERED, Moment.ENTRY_STARTED, Moment.VERIFICATION_SATISFIED}
)

# The technical channel's own moments (§5.5).
TECHNICAL_MOMENTS: frozenset[Moment] = frozenset(
    {
        Moment.TECHNICAL_RAISED,
        Moment.TECHNICAL_ACKNOWLEDGED,
        Moment.TECHNICAL_CLEARED,
    }
)

# Inside one incident these are unioned and deduplicated: a siren already
# sounding is not restarted (§5.6). Everything else — a disarm, a fault —
# happens in its own right even in an incident's area.
UNION_MOMENTS: frozenset[Moment] = frozenset(
    {
        Moment.TRIGGERED,
        Moment.ENTRY_STARTED,
        Moment.VERIFICATION_SATISFIED,
        Moment.INCIDENT_OPENED,
        Moment.INCIDENT_JOINED,
    }
)

# Kinds that leave something switched on and need switching off again.
REVERTIBLE: frozenset[str] = frozenset(
    {ActionKind.SIREN.value, ActionKind.SWITCH.value}
)

REVERT = "revert"


@dataclass(frozen=True, slots=True)
class PlanContext:
    """Everything the planner may read. Given, never looked up (INV-1)."""

    config: FoyerConfig
    snapshot: SystemSnapshot
    now: datetime
    areas: Mapping[str, AreaRuntime]
    incident: Incident | None = None
    active_zones: frozenset[str] = frozenset()

    @property
    def tz(self) -> tzinfo:
        return self.snapshot.timezone


@dataclass(slots=True)
class Plan:
    """What one batch of occurrences produces."""

    intents: list[ActionIntent] = field(default_factory=list)
    pending: list[PendingRun] = field(default_factory=list)
    running: list[RunningAction] = field(default_factory=list)
    started: list[str] = field(default_factory=list)

    def extend(self, other: Plan) -> None:
        self.intents.extend(other.intents)
        self.pending.extend(other.pending)
        self.running.extend(other.running)
        self.started.extend(other.started)


# --- profile resolution ------------------------------------------------------------


# Where an effective profile came from. §6 says the UI must always show it —
# "otherwise the behaviour looks arbitrary" — and the simulator's trace says
# it on every step (§11.2).
FROM_ZONE = "zone"
FROM_GROUP = "group"
FROM_AREA = "area"
FROM_SCENARIO = "scenario"
FROM_TECHNICAL = "technical"
FROM_DEFAULT = "default"
FROM_NONE = "none"


def _area_chain(
    config: FoyerConfig, area_id: str | None, scenario_id: str | None
) -> tuple[ResponseProfile | None, str]:
    area = config.area(area_id)
    scenario = config.scenario(scenario_id)
    for candidate, source in (
        (area.response_profile_id if area else None, FROM_AREA),
        (scenario.response_profile_id if scenario else None, FROM_SCENARIO),
        (config.settings.default_profile_id, FROM_DEFAULT),
    ):
        if (profile := config.profile(candidate)) is not None:
            return profile, source
    return None, FROM_NONE


def area_profile(
    config: FoyerConfig, area_id: str | None, scenario_id: str | None
) -> ResponseProfile | None:
    """area → scenario → global default (SPEC §6)."""
    return _area_chain(config, area_id, scenario_id)[0]


def resolve_profile(
    config: FoyerConfig,
    *,
    area_id: str | None = None,
    zone_id: str | None = None,
    group_id: str | None = None,
    scenario_id: str | None = None,
    moment: Moment | None = None,
) -> tuple[ResponseProfile | None, str]:
    """The profile that answers, **and where it was inherited from** (§6).

    The two are resolved together, in one function, because they are the same
    walk down the same chain: a separate "where did it come from" would be a
    second implementation of the inheritance rule, free to disagree with the
    first, and the trace would then explain a decision the engine did not
    make (part 3 decision 1, §11.2).
    """
    zone = config.zone(zone_id)
    if moment in TECHNICAL_MOMENTS:
        for candidate, source in (
            (zone.response_profile_id if zone else None, FROM_ZONE),
            (config.settings.technical_profile_id, FROM_TECHNICAL),
            (config.settings.default_profile_id, FROM_DEFAULT),
        ):
            if (profile := config.profile(candidate)) is not None:
                return profile, source
        return None, FROM_NONE
    if moment is Moment.VERIFICATION_SATISFIED and (
        (group := config.group(group_id)) is not None
    ):
        # Only the satisfied group answers with the group's profile: its
        # members keep their own when they alarm on their own (§4.8). That is
        # what makes the response graduated instead of uniform.
        if (profile := config.profile(group.response_profile_id)) is not None:
            return profile, FROM_GROUP
        return _area_chain(config, group.area_id, scenario_id)
    if (
        moment in ZONE_MOMENTS
        and zone is not None
        and (profile := config.profile(zone.response_profile_id)) is not None
    ):
        return profile, FROM_ZONE
    return _area_chain(config, area_id, scenario_id)


def effective_profile(
    config: FoyerConfig,
    *,
    area_id: str | None = None,
    zone_id: str | None = None,
    group_id: str | None = None,
    scenario_id: str | None = None,
    moment: Moment | None = None,
) -> ResponseProfile | None:
    """The profile that answers — the one rule of part 3 decision 1."""
    return resolve_profile(
        config,
        area_id=area_id,
        zone_id=zone_id,
        group_id=group_id,
        scenario_id=scenario_id,
        moment=moment,
    )[0]


# --- the actions of one moment -----------------------------------------------------


def sequence(profile: ResponseProfile, moment: Moment) -> tuple[ProfileAction, ...]:
    """The profile's actions for this moment, in the order the user put them.

    A ``delay`` participates like any other action: it holds back whatever
    comes after it *in this sequence*.
    """
    return tuple(a for a in profile.actions if a.enabled and moment in a.moments)


# Why an action in a profile's sequence did not run. The simulator shows
# these words (§11.2: "which were skipped AND WHY"), and it shows them
# because skip_reason below is the one place that decides — a second copy of
# the rule would let the trace explain a skip that never happened.
SKIP_SILENT = "silent"
SKIP_ALREADY_RUNNING = "already_running"
SKIP_CONDITION = "condition"
SKIP_HELD_BY_DELAY = "held_by_delay"


def skip_reason(
    action: ProfileAction,
    ctx: PlanContext,
    *,
    moment: Moment,
    suppressed: frozenset[str],
    already_started: frozenset[str],
) -> str | None:
    """Why this action does not run now, or None when it does.

    The order is the order of the reasons, not of the checks: a silent zone
    suppresses before anything is evaluated, a siren already sounding is not
    restarted before its conditions are asked again, and only what survives
    both is put to its conditions. Changing the order changes what the trace
    says happened, so there is one of it.
    """
    if action.kind.value in suppressed:
        return SKIP_SILENT
    if action.id in already_started and moment in UNION_MOMENTS:
        return SKIP_ALREADY_RUNNING
    if not evaluate(action, ctx.snapshot, ctx.now, ctx.tz):
        return SKIP_CONDITION
    return None


def _names(ids: Sequence[str | None], lookup: Mapping[str, str]) -> str:
    seen: list[str] = []
    for item in ids:
        if item and (name := lookup.get(item, item)) not in seen:
            seen.append(name)
    return ", ".join(seen)


def variables(ctx: PlanContext, group: Sequence[Occurrence]) -> dict[str, str]:
    """The fixed template variable set of §6.4, for one batch of occurrences."""
    config = ctx.config
    areas = {a.id: a.name for a in config.areas}
    zones = {z.id: z.name for z in config.zones}
    scenarios = {s.id: s.name for s in config.scenarios}
    local = ctx.now.astimezone(ctx.tz)
    detail: dict[str, str] = {}
    for occurrence in group:
        detail.update(occurrence.detail)
    zone_ids = [o.zone_id for o in group] + [z for o in group for z in o.zone_ids]
    states = [
        ctx.areas[o.area_id].state.value
        for o in group
        if o.area_id is not None and o.area_id in ctx.areas
    ]
    incident_zones = ctx.incident.zone_ids if ctx.incident is not None else ()
    return {
        "zone": _names([o.zone_id for o in group], zones) or _names(zone_ids, zones),
        "area": _names([o.area_id for o in group], areas),
        "scenario": _names([o.scenario_id for o in group], scenarios),
        "user": "",  # identities arrive in Phase 2
        "channel": _names([o.channel for o in group], {}),
        "time": local.strftime("%H:%M"),
        "date": local.strftime("%Y-%m-%d"),
        "state": _names(states, {}),
        "open_zones": _names(
            [z.id for z in config.zones if z.id in ctx.active_zones], zones
        ),
        "reason": detail.get("reason") or detail.get("cause", ""),
        "incident_zones": _names(list(incident_zones), zones),
        # Not a §6.4 variable: the built-in notification's own placeholder for
        # every zone of the batch, kept from Phase 0 so its text is unchanged.
        "zones": _names(zone_ids, zones),
    }


def _params(
    action: ProfileAction,
    values: Mapping[str, str],
    ctx: PlanContext,
    area_id: str | None,
) -> dict[str, Any]:
    """The action's parameters, with every template already rendered."""
    params = {
        key: render(value, values) if isinstance(value, str) else value
        for key, value in action.params.items()
    }
    if action.kind is ActionKind.CALL_SERVICE and isinstance(
        params.get("data"), Mapping
    ):
        params["data"] = {
            key: render(value, values) if isinstance(value, str) else value
            for key, value in params["data"].items()
        }
    if action.kind is ActionKind.SIREN:
        # Never beyond the siren cutoff: a sounder that outlives the alarm is
        # what the cutoff exists to prevent (§5.3).
        area = ctx.areas.get(area_id or "")
        scenario = ctx.config.scenario(area.scenario_id if area else None)
        cutoff = ctx.config.siren_duration(scenario)
        duration = params.get("duration")
        params["duration"] = cutoff if not duration else min(int(duration), cutoff)
    if action.kind is ActionKind.CAMERA:
        params.setdefault("directory", ctx.config.settings.camera_dir)
    if action.kind is ActionKind.NOTIFY and params.get("camera_entity_id"):
        # A notification that has to write the picture to a file writes it
        # where every other camera file goes, and the choice is made here so
        # the executor is left with nothing to decide (INV-1).
        params.setdefault("directory", ctx.config.settings.camera_dir)
    return params


def _entity_ids(params: Mapping[str, Any]) -> tuple[str, ...]:
    value = params.get("entity_ids") or params.get("entity_id") or ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def run_sequence(
    ctx: PlanContext,
    profile: ResponseProfile,
    moment: Moment,
    values: Mapping[str, str],
    *,
    start: int = 0,
    area_id: str | None = None,
    zone_id: str | None = None,
    incident_id: str | None = None,
    silent: bool = False,
    already_started: frozenset[str] = frozenset(),
    run_id: str = "",
) -> Plan:
    """Walk a profile's actions for one moment, from ``start``.

    Stops at a ``delay``, leaving a PendingRun that resumes at the same index
    in the same sequence. Skips actions whose conditions are not met, actions a
    silent zone suppresses, and actions this incident has already started.
    """
    plan = Plan()
    actions = sequence(profile, moment)
    suppressed = (
        frozenset(ctx.config.settings.silent_suppresses) if silent else frozenset()
    )
    for index in range(start, len(actions)):
        action = actions[index]
        if action.kind is ActionKind.DELAY:
            seconds = max(0, int(action.params.get("seconds", 0)))
            if seconds and index + 1 < len(actions):
                plan.pending.append(
                    PendingRun(
                        id=run_id,
                        profile_id=profile.id,
                        moment=moment,
                        index=index + 1,
                        due=ctx.now + timedelta(seconds=seconds),
                        area_id=area_id,
                        zone_id=zone_id,
                        incident_id=incident_id,
                        silent=silent,
                        placeholders=dict(values),
                    )
                )
                return plan
            continue
        if (
            skip_reason(
                action,
                ctx,
                moment=moment,
                suppressed=suppressed,
                already_started=already_started,
            )
            is not None
        ):
            continue
        params = _params(action, values, ctx, area_id)
        plan.intents.append(
            ActionIntent(
                action_id=action.id,
                kind=action.kind.value,
                moment=moment,
                profile_id=profile.id,
                placeholders=dict(values),
                variant="area"
                if moment is Moment.ARMED and not values.get("scenario")
                else None,
                params=params,
            )
        )
        if incident_id is not None and moment in UNION_MOMENTS:
            plan.started.append(action.id)
        if action.kind.value in REVERTIBLE:
            running = _running(action, params, area_id, incident_id, ctx.now)
            if running is not None:
                plan.running.append(running)
    return plan


def _running(
    action: ProfileAction,
    params: Mapping[str, Any],
    area_id: str | None,
    incident_id: str | None,
    now: datetime,
) -> RunningAction | None:
    entity_ids = _entity_ids(params)
    if not entity_ids:
        return None
    if action.kind is ActionKind.SIREN:
        duration = int(params.get("duration") or 0)
        return RunningAction(
            action_id=action.id,
            kind=action.kind.value,
            entity_ids=entity_ids,
            until=now + timedelta(seconds=duration) if duration else None,
            restore="off",
            area_id=area_id,
            incident_id=incident_id,
        )
    revert_after = params.get("revert_after")
    if not revert_after:
        return None
    return RunningAction(
        action_id=action.id,
        kind=action.kind.value,
        entity_ids=entity_ids,
        until=now + timedelta(seconds=int(revert_after)),
        restore="off" if params.get("state", "on") == "on" else "on",
        area_id=area_id,
        incident_id=incident_id,
    )


def revert_intent(running: RunningAction, moment: Moment) -> ActionIntent:
    """Switch off what an action switched on: the siren cutoff, a disarm, or
    the auto-revert running out (§6.2)."""
    return ActionIntent(
        action_id=running.action_id,
        kind=REVERT,
        moment=moment,
        placeholders={},
        params={
            "target_kind": running.kind,
            "entity_ids": running.entity_ids,
            "state": running.restore or "off",
        },
    )


# --- the batch ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """Who answers one occurrence, and under what run it is grouped.

    ``key`` is what decides that three areas arming together send one
    notification naming all three (see plan_occurrences). The simulator
    groups its trace by the same key, from this same function, so the trace
    shows one line where the house sends one message (§11.2).
    """

    profile: ResponseProfile
    source: str
    silent: bool
    incident_id: str | None
    moment: Moment

    @property
    def key(self) -> tuple[str, Moment, bool, str | None]:
        return (self.profile.id, self.moment, self.silent, self.incident_id)


def answer_for(ctx: PlanContext, occurrence: Occurrence) -> Answer | None:
    """The profile that answers this occurrence, or None when none does."""
    zone = ctx.config.zone(occurrence.zone_id)
    area = ctx.areas.get(occurrence.area_id or "")
    scenario_id = occurrence.scenario_id or (area.scenario_id if area else None)
    profile, source = resolve_profile(
        ctx.config,
        area_id=occurrence.area_id,
        zone_id=occurrence.zone_id,
        group_id=occurrence.group_id,
        scenario_id=scenario_id,
        moment=occurrence.moment,
    )
    if profile is None:
        return None
    return Answer(
        profile=profile,
        source=source,
        silent=bool(zone and zone.silent and occurrence.moment in ZONE_MOMENTS),
        incident_id=occurrence.incident_id,
        moment=occurrence.moment,
    )


def plan_occurrences(
    ctx: PlanContext, occurrences: Sequence[Occurrence], run_seq: int
) -> tuple[Plan, int]:
    """One run per (profile, moment, silent), so three areas arming together
    send one notification naming all three, not three notifications."""
    plan = Plan()
    started = set(ctx.incident.actions_started if ctx.incident else ())
    batches: dict[tuple[str, Moment, bool, str | None], list[Occurrence]] = {}
    for occurrence in occurrences:
        if (answer := answer_for(ctx, occurrence)) is not None:
            batches.setdefault(answer.key, []).append(occurrence)
    for (profile_id, moment, silent, incident_id), group in batches.items():
        profile = ctx.config.profile(profile_id)
        assert profile is not None
        run_seq += 1
        batch = run_sequence(
            ctx,
            profile,
            moment,
            variables(ctx, group),
            area_id=next((o.area_id for o in group if o.area_id), None),
            zone_id=next((o.zone_id for o in group if o.zone_id), None),
            incident_id=incident_id,
            silent=silent,
            already_started=frozenset(started),
            run_id=f"run-{run_seq}",
        )
        started.update(batch.started)
        plan.extend(batch)
    return plan, run_seq


def resume(ctx: PlanContext, run: PendingRun) -> Plan:
    """Carry on a sequence a ``delay`` held back (part 3 decision 5)."""
    profile = ctx.config.profile(run.profile_id)
    if profile is None:
        return Plan()
    return run_sequence(
        ctx,
        profile,
        run.moment,
        run.placeholders,
        start=run.index,
        area_id=run.area_id,
        zone_id=run.zone_id,
        incident_id=run.incident_id,
        silent=run.silent,
        already_started=frozenset(ctx.incident.actions_started if ctx.incident else ()),
        run_id=run.id,
    )


# --- chime (§6.6) ------------------------------------------------------------------


def audible_targets(chime: ChimeSettings, now: datetime, tz: tzinfo) -> tuple[str, ...]:
    """The targets not inside quiet hours right now.

    A target's own window replaces the global one (part 3 decision 8): the
    speakers all day, the phone only between nine and ten.
    """
    out: list[str] = []
    for target in chime.targets:
        start = target.quiet_start or chime.quiet_start
        end = target.quiet_end or chime.quiet_end
        if start and end and in_daily_window(now, tz, start, end):
            continue
        out.append(target.entity_id)
    return tuple(out)


def chime_suppressed(config: FoyerConfig, zone: Zone) -> bool:
    """A silent zone makes no noise in the house, the chime included."""
    return zone.silent and "chime" in config.settings.silent_suppresses


def condition_summary(
    action: ProfileAction, ctx: PlanContext
) -> tuple[Mapping[str, str], ...]:
    """Which of an action's conditions failed, so the trace can say why (§11.2).

    Data, never a sentence. "time 22:00-07:00" and "binary_sensor.x is on"
    read like English because they are English, and a backend that writes the
    words a person reads is a backend an Italian installation cannot
    translate. The panel builds the sentence from these fields, as it does for
    every other word on the page.
    """
    out: list[Mapping[str, str]] = []
    for condition in unmet(action, ctx.snapshot, ctx.now, ctx.tz):
        if isinstance(condition, TimeCondition):
            out.append(
                {"kind": "time", "after": condition.after, "before": condition.before}
            )
        elif isinstance(condition, StateCondition):
            out.append(
                {
                    "kind": "state",
                    "entity_id": condition.entity_id,
                    "operator": condition.operator.value,
                    "state": condition.state,
                }
            )
    return tuple(out)


def without(
    running: Sequence[RunningAction], stopped: Sequence[RunningAction]
) -> tuple[RunningAction, ...]:
    ids = {(r.action_id, r.entity_ids) for r in stopped}
    return tuple(r for r in running if (r.action_id, r.entity_ids) not in ids)


def renumber(run: PendingRun, run_seq: int) -> tuple[PendingRun, int]:
    run_seq += 1
    return replace(run, id=f"run-{run_seq}"), run_seq
