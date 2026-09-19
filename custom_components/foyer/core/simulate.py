"""The simulator: the same engine, a fabricated world, nothing executed (§11.2).

This is the feature the project exists for. Nobody can currently answer "what
would happen if the kitchen window opened right now, in this scenario, at this
hour?" without opening the window, and an alarm you cannot rehearse is an alarm
you find out about during a burglary.

**There is no second evaluation path here, and there must never be one.** This
module fabricates a snapshot and a clock, hands them to the very
``engine.decide()`` the runtime calls, steps the clock with the very
``engine.next_wakeup()`` the scheduler uses, and then simply never gives the
Decision to the executor. That is INV-1 doing the work it was written for: if
the trace and the house ever disagreed, the trace would be worse than nothing,
because it would be believed.

Everything below the stepping loop is **reporting**, not deciding:

- whether an action ran is read off the Decision, never recomputed;
- why one did *not* run is asked of ``response.skip_reason`` — the same
  function ``run_sequence`` itself calls, so the trace cannot explain a skip
  the engine did not make;
- which profile answered, and where it was inherited from, comes from
  ``response.resolve_profile``, which resolves both in one walk.

The clock and the time zone are given, like everywhere in ``core``. A
simulation at 23:30 must evaluate a 22:00-07:00 condition as the house would
at 23:30, and that only works if nothing here reads a real clock.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any

from .engine import decide, next_wakeup
from .models import (
    ActionIntent,
    AreaRuntime,
    AreaState,
    ArmAreaRequest,
    ArmRequest,
    Decision,
    EntityState,
    Event,
    FoyerConfig,
    Moment,
    Occurrence,
    PendingRun,
    RuntimeState,
    SystemSnapshot,
    Tick,
    ZoneStateChanged,
)
from .response import (
    FROM_NONE,
    SKIP_CONDITION,
    SKIP_HELD_BY_DELAY,
    Answer,
    PlanContext,
    answer_for,
    condition_summary,
    sequence,
    skip_reason,
)

# How far a run may reach, and how many decisions it may take to get there.
# Both are bounds on a loop the user drives, not policy: a siren cutoff is
# capped at 900 s (§5.3), so fifteen minutes is the longest chain of
# consequences a single trigger can still have, and a run that needed two
# hundred decisions to tell its story would not be a story anybody reads.
DEFAULT_HORIZON = 900
MAX_HORIZON = 3600
MAX_STEPS = 200

# What the step is, for the panel to lay out. ``setup`` is the one decision
# that is not part of the answer: it is the tick that reads the world once so
# every zone has a baseline, exactly as a real start does — without it the
# first reading of every sensor would look like a sensor changing.
STEP_SETUP = "setup"
STEP_REQUEST = "request"
STEP_ZONE = "zone"
STEP_TICK = "tick"


@dataclass(frozen=True, slots=True)
class ZoneOverride:
    """A zone forced into a state, at a chosen moment of the run.

    ``at`` is seconds from the start. It exists because the features §11.2
    demands of the trace — a verification group filling up, a second zone
    joining an incident — are about *sequence*: two zones forced at the same
    instant can never show a group reaching two of two thirty seconds apart.
    Zero is the default and is the ordinary case.
    """

    zone_id: str
    state: str
    at: int = 0


@dataclass(frozen=True, slots=True)
class SimulationRequest:
    """Everything a run is given. Nothing else is read (INV-1)."""

    start: datetime
    timezone: tzinfo = UTC
    # The hypothetical scenario (§11.2), or the areas to arm on their own.
    # Neither means a disarmed house, which is a real question too: a 24h or
    # technical zone answers whatever the arming state.
    scenario_id: str | None = None
    area_ids: tuple[str, ...] = ()
    zones: tuple[ZoneOverride, ...] = ()
    # States for the entities an action's condition reads (§6.3), so "only if
    # nobody is home" can be rehearsed both ways.
    entities: Mapping[str, str] = field(default_factory=dict)
    horizon: int = DEFAULT_HORIZON


@dataclass(frozen=True, slots=True)
class PlannedAction:
    """One action of one profile's sequence, and what became of it."""

    action_id: str
    kind: str
    name: str
    moment: str
    profile_id: str | None
    ran: bool
    # None when it ran. One of response.SKIP_*, which the panel translates.
    skipped: str | None = None
    # For SKIP_CONDITION: which conditions failed, in words (§11.2 asks the
    # trace to explain a skip "well enough to act on").
    conditions: tuple[str, ...] = ()
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlannedBatch:
    """The profile that answered a group of occurrences, and its sequence."""

    moment: str
    profile_id: str | None
    profile_name: str
    # Where the profile was inherited from: response.FROM_* (§6 requires the
    # UI to show this, "otherwise the behaviour looks arbitrary").
    source: str
    area_id: str | None
    zone_id: str | None
    group_id: str | None
    actions: tuple[PlannedAction, ...] = ()


@dataclass(frozen=True, slots=True)
class AreaChange:
    area_id: str
    was: str
    now: str
    timer_kind: str | None = None
    timer_due: datetime | None = None


@dataclass(frozen=True, slots=True)
class Scheduled:
    """Something the run knows will happen later, if nothing intervenes."""

    at: datetime
    kind: str
    profile_id: str | None = None
    moment: str | None = None
    area_id: str | None = None


@dataclass(frozen=True, slots=True)
class SimStep:
    """One decide() call, reported."""

    at: datetime
    kind: str
    # What was sent: a zone id, a scenario id, or nothing for a tick.
    zone_id: str | None = None
    zone_state: str | None = None
    scenario_id: str | None = None
    accepted: bool = True
    reason: str | None = None
    blocking_zones: tuple[str, ...] = ()
    low_battery_zones: tuple[str, ...] = ()
    areas: tuple[AreaChange, ...] = ()
    occurrences: tuple[Occurrence, ...] = ()
    batches: tuple[PlannedBatch, ...] = ()
    # Chime and revert intents: they belong to no profile, and leaving them
    # out would make a trace that says nothing about a siren being switched
    # off at the cutoff.
    loose_actions: tuple[PlannedAction, ...] = ()
    scheduled: tuple[Scheduled, ...] = ()


@dataclass(frozen=True, slots=True)
class Simulation:
    request: SimulationRequest
    steps: tuple[SimStep, ...] = ()
    # The final state, so a caller can assert on it without replaying.
    final: RuntimeState | None = None
    # True when the run stopped because it ran out of room rather than
    # because nothing more was going to happen. Said plainly: a trace that
    # simply stops reads as "and then it was over", which is a lie.
    truncated: bool = False


# --- the run -----------------------------------------------------------------------


def _initial(
    config: FoyerConfig,
    request: SimulationRequest,
    live: Mapping[str, EntityState],
) -> dict[str, EntityState]:
    """The world the run starts in: the real one, with the overrides not yet
    applied — they are applied as changes, because a change is what a zone
    does and what the engine reads."""
    entities = dict(live)
    for entity_id, state in request.entities.items():
        entities[entity_id] = EntityState(
            state, last_reported=request.start, last_changed=request.start
        )
    return entities


def _queue(
    config: FoyerConfig, request: SimulationRequest
) -> list[tuple[datetime, Event]]:
    """The events the operator asked for, in the order they happen.

    The arming request goes first at the start instant, then each override at
    its own offset. Everything between them is a Tick the scheduler would
    have sent, and that is worked out step by step rather than listed here.
    """
    events: list[tuple[datetime, Event]] = []
    if request.scenario_id:
        events.append((request.start, ArmRequest(request.scenario_id)))
    else:
        for area_id in request.area_ids:
            events.append((request.start, ArmAreaRequest(area_id)))
    zones = {z.id: z for z in config.zones}
    for override in request.zones:
        zone = zones.get(override.zone_id)
        if zone is None:
            continue
        at = request.start + timedelta(seconds=max(0, override.at))
        events.append(
            (
                at,
                ZoneStateChanged(
                    zone.entity_id,
                    EntityState(override.state, last_reported=at, last_changed=at),
                ),
            )
        )
    events.sort(key=lambda item: item[0])
    return events


def run(
    config: FoyerConfig,
    request: SimulationRequest,
    live: Mapping[str, EntityState] | None = None,
) -> Simulation:
    """Rehearse the configuration. Executes nothing, ever (§11.2, INV-1).

    ``live`` is what the zones are really reading right now, handed in by the
    runtime because reading Home Assistant is the runtime's job. The house
    starts **disarmed** whatever it is really doing: the question is
    hypothetical, and inheriting a real alarm in progress would answer a
    different one.
    """
    entities = _initial(config, request, live or {})
    state = RuntimeState(areas={a.id: AreaRuntime() for a in config.areas})
    now = request.start
    deadline = request.start + timedelta(
        seconds=max(0, min(request.horizon, MAX_HORIZON))
    )
    steps: list[SimStep] = []
    pending = _queue(config, request)
    truncated = False

    def send(event: Event, at: datetime, kind: str) -> Decision:
        nonlocal state, entities
        before = {a: rt.state for a, rt in state.areas.items()}
        snapshot = SystemSnapshot(state, entities, False, request.timezone)
        decision = decide(snapshot, event, config, at)
        state = decision.state
        if isinstance(event, ZoneStateChanged):
            entities = {**entities, event.entity_id: event.new}
        steps.append(
            _report(
                config,
                decision,
                event,
                kind,
                before=before,
                entities=entities,
                request=request,
            )
        )
        return decision

    # One tick before anything else, so every zone has been read once: a
    # zone's first readable value is its baseline and not an activation
    # (§4.7), and a real system has always had that tick.
    send(Tick(), now, STEP_SETUP)

    for _ in range(MAX_STEPS):
        wake = next_wakeup(
            SystemSnapshot(state, entities, False, request.timezone), config, now
        )
        due = pending[0][0] if pending else None
        # A timer exactly at ``now`` has just been processed by the decision
        # that brought us here, so a wake-up must strictly advance or the run
        # would tread water at one instant. A queued event may fire at it:
        # two overrides can share a second.
        candidates = [t for t in (wake,) if t is not None and t > now]
        candidates += [t for t in (due,) if t is not None and t >= now]
        if not candidates:
            break
        at = min(candidates)
        if at > deadline:
            # Something is still scheduled beyond the horizon: the trace says
            # so rather than ending as if the house had gone quiet.
            truncated = True
            break
        if due is not None and at == due:
            _, event = pending.pop(0)
            kind = STEP_ZONE if isinstance(event, ZoneStateChanged) else STEP_REQUEST
            send(event, at, kind)
        else:
            send(Tick(), at, STEP_TICK)
        now = at
    else:
        truncated = (
            bool(pending)
            or next_wakeup(
                SystemSnapshot(state, entities, False, request.timezone), config, now
            )
            is not None
        )

    return Simulation(
        request=request, steps=tuple(steps), final=state, truncated=truncated
    )


# --- reporting: reads the Decision, never re-decides -------------------------------


def _area_changes(
    before: Mapping[str, AreaState], state: RuntimeState
) -> tuple[AreaChange, ...]:
    out = []
    for area_id, was in before.items():
        rt = state.area(area_id)
        if rt.state is was:
            continue
        out.append(
            AreaChange(
                area_id=area_id,
                was=was.value,
                now=rt.state.value,
                timer_kind=rt.timer.kind.value if rt.timer else None,
                timer_due=rt.timer.due if rt.timer else None,
            )
        )
    return tuple(out)


def _held_from(
    runs: Sequence[PendingRun], profile_id: str, moment: Moment
) -> int | None:
    """The index a delay stopped this sequence at, if one did."""
    for run_ in runs:
        if run_.profile_id == profile_id and run_.moment is moment:
            return run_.index
    return None


def _action_name(action) -> str:
    return action.name or action.kind.value


def _batch(
    config: FoyerConfig,
    answer: Answer,
    group: Sequence[Occurrence],
    decision: Decision,
    ctx: PlanContext,
) -> PlannedBatch:
    """One run of one profile, and what became of every action in it.

    The group is the batch the engine itself made (``response.answer_for``),
    so a trace line stands for exactly one thing the house does: three areas
    arming together send one notification naming all three, and the trace
    says so once.
    """
    profile, moment = answer.profile, answer.moment
    suppressed = (
        frozenset(config.settings.silent_suppresses) if answer.silent else frozenset()
    )
    started = frozenset(ctx.incident.actions_started if ctx.incident else ())
    # Whether an action ran is read off the Decision, never recomputed: the
    # Decision is what the executor would have been handed.
    ran = {
        i.action_id
        for i in decision.actions
        if i.profile_id == profile.id and i.moment is moment
    }
    held_at = _held_from(decision.state.pending_runs, profile.id, moment)
    actions = []
    for index, action in enumerate(sequence(profile, moment)):
        did_run = action.id in ran
        why: str | None = None
        conditions: tuple[str, ...] = ()
        if not did_run:
            if held_at is not None and index >= held_at:
                why = SKIP_HELD_BY_DELAY
            else:
                why = skip_reason(
                    action,
                    ctx,
                    moment=moment,
                    suppressed=suppressed,
                    already_started=started,
                )
                if why == SKIP_CONDITION:
                    conditions = condition_summary(action, ctx)
        actions.append(
            PlannedAction(
                action_id=action.id,
                kind=action.kind.value,
                name=_action_name(action),
                moment=moment.value,
                profile_id=profile.id,
                ran=did_run,
                skipped=why,
                conditions=conditions,
                params=dict(action.params),
            )
        )
    return PlannedBatch(
        moment=moment.value,
        profile_id=profile.id,
        profile_name=profile.name,
        source=answer.source,
        area_id=next((o.area_id for o in group if o.area_id), None),
        zone_id=next((o.zone_id for o in group if o.zone_id), None),
        group_id=next((o.group_id for o in group if o.group_id), None),
        actions=tuple(actions),
    )


def _unanswered(occurrence: Occurrence) -> PlannedBatch:
    """An occurrence no profile answers: worth a line of its own, because
    "nothing happened and here is why" is the question §11.2 is for."""
    return PlannedBatch(
        moment=occurrence.moment.value,
        profile_id=None,
        profile_name="",
        source=FROM_NONE,
        area_id=occurrence.area_id,
        zone_id=occurrence.zone_id,
        group_id=occurrence.group_id,
    )


def _loose(intent: ActionIntent) -> PlannedAction:
    """A chime or a revert: real, and belonging to no profile (§6.6, §6.2)."""
    return PlannedAction(
        action_id=intent.action_id,
        kind=intent.kind,
        name=intent.kind,
        moment=intent.moment.value,
        profile_id=None,
        ran=True,
        params=dict(intent.params),
    )


def _scheduled(decision: Decision) -> tuple[Scheduled, ...]:
    """What the decision leaves running: timers and held sequences.

    These are the "⏱" lines of §11.2's example. They are read off the state
    the engine produced rather than predicted, so a line that says the siren
    stops at 19:35 is the siren's own timer.
    """
    out = [
        Scheduled(at=rt.timer.due, kind=rt.timer.kind.value, area_id=area_id)
        for area_id, rt in decision.state.areas.items()
        if rt.timer is not None
    ]
    out.extend(
        Scheduled(
            at=run_.due,
            kind="delay",
            profile_id=run_.profile_id,
            moment=run_.moment.value,
            area_id=run_.area_id,
        )
        for run_ in decision.state.pending_runs
    )
    out.extend(
        Scheduled(at=running.until, kind="revert", area_id=running.area_id)
        for running in decision.state.running
        if running.until is not None
    )
    out.extend(
        Scheduled(at=when, kind="bypass_ends")
        for when in decision.state.bypass_until.values()
    )
    return tuple(sorted(out, key=lambda s: s.at))


def _report(
    config: FoyerConfig,
    decision: Decision,
    event: Event,
    kind: str,
    *,
    before: Mapping[str, AreaState],
    entities: Mapping[str, EntityState],
    request: SimulationRequest,
) -> SimStep:
    ctx = PlanContext(
        config=config,
        snapshot=SystemSnapshot(decision.state, entities, False, request.timezone),
        now=decision.at,
        areas=decision.state.areas,
        incident=decision.state.incident,
        active_zones=decision.state.active_zones,
    )
    # Grouped exactly as the engine grouped them, by response.answer_for.
    grouped: dict[tuple[Any, ...], tuple[Answer, list[Occurrence]]] = {}
    batches: list[PlannedBatch] = []
    for occurrence in decision.occurrences:
        answer = answer_for(ctx, occurrence)
        if answer is None:
            batches.append(_unanswered(occurrence))
            continue
        grouped.setdefault(answer.key, (answer, []))[1].append(occurrence)
    batches.extend(
        _batch(config, answer, group, decision, ctx)
        for answer, group in grouped.values()
    )
    known = {i.action_id for b in batches for i in b.actions}
    loose = tuple(
        _loose(intent)
        for intent in decision.actions
        if intent.profile_id is None or intent.action_id not in known
    )
    return SimStep(
        at=decision.at,
        kind=kind,
        zone_id=_zone_of(config, event),
        zone_state=event.new.state if isinstance(event, ZoneStateChanged) else None,
        scenario_id=getattr(event, "scenario_id", None),
        accepted=decision.accepted,
        reason=decision.reason.value if decision.reason else None,
        blocking_zones=decision.blocking_zones,
        low_battery_zones=decision.low_battery_zones,
        areas=_area_changes(before, decision.state),
        occurrences=decision.occurrences,
        batches=tuple(batches),
        loose_actions=loose,
        scheduled=_scheduled(decision),
    )


def _zone_of(config: FoyerConfig, event: Event) -> str | None:
    if not isinstance(event, ZoneStateChanged):
        return None
    zone = next((z for z in config.zones if z.entity_id == event.entity_id), None)
    return zone.id if zone else None


# --- the wire ----------------------------------------------------------------------


def as_dict(simulation: Simulation, config: FoyerConfig) -> dict[str, Any]:
    """The trace as the panel receives it: identifiers and numbers, never
    sentences. Every word a person reads is translated in the panel (§15.2)."""

    def when(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    return {
        "at": simulation.request.start.isoformat(),
        "scenario_id": simulation.request.scenario_id,
        "area_ids": list(simulation.request.area_ids),
        "truncated": simulation.truncated,
        "steps": [
            {
                "at": step.at.isoformat(),
                "kind": step.kind,
                "zone_id": step.zone_id,
                "zone_state": step.zone_state,
                "scenario_id": step.scenario_id,
                "accepted": step.accepted,
                "reason": step.reason,
                "blocking_zones": list(step.blocking_zones),
                "low_battery_zones": list(step.low_battery_zones),
                "areas": [
                    {
                        "area_id": a.area_id,
                        "was": a.was,
                        "now": a.now,
                        "timer_kind": a.timer_kind,
                        "timer_due": when(a.timer_due),
                    }
                    for a in step.areas
                ],
                "occurrences": [
                    {
                        "moment": o.moment.value,
                        "area_id": o.area_id,
                        "zone_id": o.zone_id,
                        "zone_ids": list(o.zone_ids),
                        "group_id": o.group_id,
                        "incident_id": o.incident_id,
                        "scenario_id": o.scenario_id,
                        "detail": dict(o.detail),
                    }
                    for o in step.occurrences
                ],
                "batches": [
                    {
                        "moment": b.moment,
                        "profile_id": b.profile_id,
                        "profile_name": b.profile_name,
                        "source": b.source,
                        "area_id": b.area_id,
                        "zone_id": b.zone_id,
                        "group_id": b.group_id,
                        "actions": [_action_dict(a) for a in b.actions],
                    }
                    for b in step.batches
                ],
                "loose_actions": [_action_dict(a) for a in step.loose_actions],
                "scheduled": [
                    {
                        "at": s.at.isoformat(),
                        "kind": s.kind,
                        "profile_id": s.profile_id,
                        "moment": s.moment,
                        "area_id": s.area_id,
                    }
                    for s in step.scheduled
                ],
            }
            for step in simulation.steps
        ],
    }


def _action_dict(action: PlannedAction) -> dict[str, Any]:
    return {
        "action_id": action.action_id,
        "kind": action.kind,
        "name": action.name,
        "moment": action.moment,
        "profile_id": action.profile_id,
        "ran": action.ran,
        "skipped": action.skipped,
        "conditions": list(action.conditions),
    }


def inputs(request: SimulationRequest) -> dict[str, Any]:
    """What the run was given, for the log row §11.2 asks for.

    "Every simulation run is logged with its inputs, so a configuration
    change can be justified after the fact" — which only works if the row
    carries enough to run it again.
    """
    return {
        "start": request.start.isoformat(),
        "scenario_id": request.scenario_id,
        "area_ids": list(request.area_ids),
        "zones": [
            {"zone_id": z.zone_id, "state": z.state, "at": z.at} for z in request.zones
        ],
        "entities": dict(request.entities),
        "horizon": request.horizon,
    }
