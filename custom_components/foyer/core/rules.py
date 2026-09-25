"""Automatic arming rules, pure (SPEC §9.4).

A closed rule model, not an automation engine: four triggers, three actions,
one active window, three guards. The boundary §6.3 draws for an action's
conditions is the same one drawn here, and for the same reason — anything
richer belongs in a Home Assistant automation driven by the events Foyer
emits.

Everything in this module is arithmetic over the configuration, the runtime
state and the entity states it is handed (INV-1). It executes nothing, and it
never asks what time it is: ``now`` and the installation's time zone arrive as
arguments, so the simulator of §11.2 evaluates a rule at a hypothetical
Tuesday 23:00 exactly as the runtime evaluates it at a real one.

Two distinctions carry most of the weight:

* **A level trigger and an edge trigger are different things.** ``absence``
  and ``entity`` describe a condition that stays true, so a rule a guard
  blocked acts as soon as the guard clears. ``time`` and ``presence`` happen
  once, so a blocked occurrence is spent (part 2 decision 4).
* **A rule that could leave the house less protected is gated.** That is any
  ``disarm``, and any ``switch`` that would drop an area the new scenario does
  not arm (part 2 decision 6) — and a perimeter area is never disarmed by a
  rule at all, which is enforced here rather than in the editor (§9.4).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta, tzinfo

from .clock import in_daily_window, parse_hhmm
from .models import (
    FAULT_STATES,
    Area,
    AreaState,
    AutoRule,
    Channel,
    FoyerConfig,
    RuleActionKind,
    RuleBlock,
    RuleRuntime,
    RuleTriggerKind,
    RuntimeState,
    Suspension,
    SuspensionKind,
)

# What a person entity says at the house. Home Assistant's own word, and the
# one `absence` and `presence` read: a zone's trigger spec exists precisely
# because entity states vary (INV-5), but the presence domain has one fixed
# point. Away is anything else that can be read — `not_home`, or the name of
# another zone ("Work", "School"): a person at work is not at home, and
# reading only `not_home` kept an empty house from ever arming (decision 166).
HOME = "home"
NOT_HOME = "not_home"


# --- the active window (§9.4) ----------------------------------------------------


def in_active_window(rule: AutoRule, now: datetime, tz: tzinfo) -> bool:
    """Whether the rule exists at all right now.

    Outside its window it does not: not blocked, not suspended, not logged.
    A rule that does not exist has nothing to explain.
    """
    window = rule.window
    local = now.astimezone(tz)
    if window.weekdays and local.weekday() not in window.weekdays:
        return False
    if window.after is None or window.before is None:
        return True
    return in_daily_window(now, tz, window.after, window.before)


# --- triggers (§9.4) --------------------------------------------------------------


def condition_holds(rule: AutoRule, states: dict[str, str | None]) -> bool:
    """Whether a level trigger's condition is true at this instant.

    An entity that cannot be read holds nothing — the same reasoning as INV-4
    and as an action's condition (§6.3). For ``absence`` that is the safe
    direction by construction: a person entity Home Assistant cannot read is
    not evidence that nobody is in.
    """
    trigger = rule.trigger
    if trigger.kind is RuleTriggerKind.ABSENCE:
        if not trigger.entity_ids:
            return False
        return all(_away(states.get(e)) for e in trigger.entity_ids)
    if trigger.kind is RuleTriggerKind.ENTITY:
        if not trigger.entity_ids or trigger.state is None:
            return False
        return states.get(trigger.entity_ids[0]) == trigger.state
    return False


def _away(state: str | None) -> bool:
    """Readable, and not at home: `not_home` or another zone's name."""
    return state is not None and state not in FAULT_STATES and state != HOME


def occurrence_due(
    rule: AutoRule, now: datetime, tz: tzinfo, last: datetime | None
) -> datetime | None:
    """``time``: the instant this rule was due, if it is due and unhandled.

    Returns the local occurrence as an aware datetime, so the state can record
    which one has been dealt with. A scheduler that wakes twice in the same
    minute, or a restart inside it, must not arm the house twice.
    """
    trigger = rule.trigger
    if trigger.kind is not RuleTriggerKind.TIME or trigger.at is None:
        return None
    at = parse_hhmm(trigger.at)
    if at is None:
        return None
    local = now.astimezone(tz)
    if trigger.weekdays and local.weekday() not in trigger.weekdays:
        return None
    due = local.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    if due > local:
        return None
    if last is not None and last >= due:
        return None
    return due


def occurrence_in(
    rule: AutoRule,
    since: datetime,
    now: datetime,
    tz: tzinfo,
    last: datetime | None,
) -> datetime | None:
    """The occurrence of a ``time`` rule that fell between ``since`` and now.

    For the restart gap: the instant is behind us, so nothing else will ever
    mention it. At most one is reported — the most recent — because a house
    that was off for a week does not need seven rows saying the same thing.
    """
    trigger = rule.trigger
    if trigger.kind is not RuleTriggerKind.TIME or trigger.at is None:
        return None
    at = parse_hhmm(trigger.at)
    if at is None:
        return None
    days = trigger.weekdays or tuple(range(7))
    local = now.astimezone(tz)
    for back in range(8):
        day = local - timedelta(days=back)
        candidate = day.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
        if candidate > local or candidate < since:
            continue
        if day.weekday() not in days:
            continue
        if last is not None and last >= candidate:
            return None
        return candidate
    return None


def next_occurrence(rule: AutoRule, now: datetime, tz: tzinfo) -> datetime | None:
    """When a ``time`` rule is next due, for the sensor and the scheduler."""
    trigger = rule.trigger
    if trigger.kind is not RuleTriggerKind.TIME or trigger.at is None:
        return None
    at = parse_hhmm(trigger.at)
    if at is None:
        return None
    local = now.astimezone(tz)
    days = trigger.weekdays or tuple(range(7))
    for ahead in range(8):
        day = local + timedelta(days=ahead)
        candidate = day.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
        if candidate > now.astimezone(tz) and day.weekday() in days:
            return candidate
    return None


def next_window_open(rule: AutoRule, now: datetime, tz: tzinfo) -> datetime | None:
    """When this rule's active window next opens, if it is shut now.

    The scheduler needs it: a rule whose condition has been true since this
    morning and whose window opens at 22:00 has nothing else to wake the
    engine at 22:00, and a house that arms itself "some time after ten" is
    not what anybody configured.
    """
    window = rule.window
    if in_active_window(rule, now, tz):
        return None
    # A window of weekdays with no hours opens at midnight on the next of
    # them, and nothing else would wake the engine there.
    at = parse_hhmm(window.after) if window.after else time(0, 0)
    if at is None:
        return None
    local = now.astimezone(tz)
    days = window.weekdays or tuple(range(7))
    for ahead in range(8):
        day = local + timedelta(days=ahead)
        candidate = day.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
        if candidate > local and day.weekday() in days:
            return candidate
    return None


def matures_at(rule: AutoRule, runtime: RuleRuntime) -> datetime | None:
    """When a level trigger's "for N minutes" runs out, if it is running."""
    if not rule.trigger.level or runtime.since is None:
        return None
    return runtime.since + timedelta(minutes=rule.trigger.minutes)


# --- suspensions (§9.4) -----------------------------------------------------------


def covering(state: RuntimeState, rule: AutoRule, now: datetime) -> Suspension | None:
    """The suspension holding this rule back, if one is.

    A named expected-visitor window wins over a bare suspension when both
    apply: the log row it will write is the one worth keeping, because in six
    months "Boiler engineer" answers the question and "rule suspended" does
    not.
    """
    active = [s for s in state.suspensions if s.active(now) and s.covers(rule.id)]
    if not active:
        return None
    named = [s for s in active if s.kind is SuspensionKind.VISITOR]
    return (named or active)[0]


def substitute_scenario(suspension: Suspension | None) -> str | None:
    """What a visitor window arms instead, if it names anything (§9.4).

    Nothing happens at the window's edges: the reduced scenario replaces the
    suspended rule's own action at the moment that rule would have acted
    (part 2 decision 8). Arming at the window's opening would, with the house
    already armed, have to disarm something — which is the one thing §9.4
    restricts.
    """
    if suspension is None or suspension.kind is not SuspensionKind.VISITOR:
        return None
    return suspension.reduced_scenario_id


# --- what happens next (§9.4, §13) ------------------------------------------------


@dataclass(frozen=True, slots=True)
class NextAction:
    """What the house will do on its own next, and when (§9.4).

    A read model, pure, so that ``sensor.foyer_next_auto_action``, page 12 and
    the simulator's trace all say the same thing. It is deliberately what is
    **scheduled**, not what will certainly happen: the guards are evaluated at
    the moment the rule acts, and a second code path that tried to predict
    them here would be a prediction the Decision could contradict (INV-1).
    """

    rule_id: str
    rule_name: str
    action: RuleActionKind
    at: datetime | None
    scenario_id: str | None = None
    area_ids: tuple[str, ...] = ()
    pending_id: str | None = None  # set when it is already counting down
    suspension: Suspension | None = None


def next_action(
    config: FoyerConfig, state: RuntimeState, now: datetime, tz: tzinfo
) -> NextAction | None:
    """The nearest scheduled automatic action, countdowns first.

    A ``presence`` rule has no next time — nobody knows when somebody will
    come home — so it appears here only while it is counting down. That is
    honest rather than tidy: a sensor that invented a time for it would be
    inventing the one thing it exists to report.
    """
    candidates: list[NextAction] = []
    for pending in state.pending_rules:
        rule = config.rule(pending.rule_id)
        candidates.append(
            NextAction(
                rule_id=pending.rule_id,
                rule_name=pending.rule_name or (rule.name if rule else ""),
                action=pending.action,
                at=pending.due,
                scenario_id=pending.scenario_id,
                area_ids=pending.area_ids,
                pending_id=pending.id,
            )
        )
    counting = {p.rule_id for p in state.pending_rules}
    if not state.auto_arming:
        # The whole mechanism is off (§9.4). What is already counting down is
        # cancelled by the switch, so nothing is scheduled at all.
        return min(candidates, key=_when) if candidates else None
    for rule in config.rules:
        runtime = state.rule(rule.id)
        if not rule.enabled or rule.id in counting:
            continue
        if runtime.latched:
            # It has had its turn and cannot act again until its condition
            # goes false — somebody has to come home before "the house is
            # empty" is news. Announcing it as due now, for ever, would be
            # the read model contradicting the scheduler, which is the one
            # thing this function exists to prevent.
            continue
        at = matures_at(rule, runtime) or next_occurrence(rule, now, tz)
        if at is None:
            continue
        candidates.append(
            NextAction(
                rule_id=rule.id,
                rule_name=rule.name,
                action=rule.action,
                at=max(at, now),
                scenario_id=rule.scenario_id,
                area_ids=named_areas(config, rule),
                suspension=covering(state, rule, at),
            )
        )
    return min(candidates, key=_when) if candidates else None


def _when(candidate: NextAction) -> datetime:
    assert candidate.at is not None
    return candidate.at


# --- guards (§9.4) ----------------------------------------------------------------


def last_interior_motion(
    config: FoyerConfig,
    active_zones: frozenset[str],
    changed: Mapping[str, datetime | None],
    now: datetime,
) -> datetime | None:
    """When the inside of the house last moved, as the quiet guard reads it.

    ``now`` for a zone that is active at this instant — it is moving, and the
    window starts when it stops. Otherwise the most recent state change among
    the interior zones. None when nothing is known, which is the quiet answer.
    """
    latest: datetime | None = None
    for zone_id in interior_zone_ids(config):
        at = now if zone_id in active_zones else changed.get(zone_id)
        if at is not None and (latest is None or at > latest):
            latest = at
    return latest


def interior_zone_ids(config: FoyerConfig) -> tuple[str, ...]:
    """The zones the quiet guard watches.

    Enabled intrusion zones that are not ``always_on``, in areas not marked
    ``is_perimeter``: a front door contact is not evidence that somebody is
    in the house, and a tamper switch is not motion. With no area marked as
    the perimeter every intrusion zone counts, which is the cautious
    direction — more reasons not to arm, never fewer.
    """
    perimeter = {a.id for a in config.areas if a.is_perimeter}
    return tuple(
        z.id
        for z in config.zones
        if z.enabled
        and z.channel is Channel.INTRUSION
        and not z.always_on
        and z.area_id not in perimeter
    )


def quiet_at(
    config: FoyerConfig,
    rule: AutoRule,
    last_motion: datetime | None,
) -> datetime | None:
    """When the quiet guard will be satisfied, if motion is what blocks it.

    The scheduler needs this one as much as it needs a timer: nothing else
    happens when a hall stops moving. Without it a rule blocked by motion
    would wait for some unrelated entity to change, and "the rule acts as
    soon as the guard clears" would be true of every guard but this one.
    """
    minutes = rule.guards.quiet_minutes
    if minutes is None or last_motion is None:
        return None
    return last_motion + timedelta(minutes=minutes)


def guard_block(
    rule: AutoRule,
    *,
    disarmed: bool,
    ready: bool,
    quiet: bool,
) -> RuleBlock | None:
    """Which guard, if any, is holding this rule back (§9.4).

    The three are evaluated in the order the page lists them, so the reason
    the log gives is the first one a person would have noticed themselves.
    """
    guards = rule.guards
    if guards.only_when_disarmed and not disarmed:
        return RuleBlock.NOT_DISARMED
    if guards.only_when_ready and not ready:
        return RuleBlock.NOT_READY
    if guards.quiet_minutes is not None and not quiet:
        return RuleBlock.MOTION
    return None


# --- what an action would actually do (§9.4 point 3) -------------------------------


def disarm_targets(
    config: FoyerConfig, rule: AutoRule
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(areas this rule may disarm, areas it may not because they are perimeter).

    The hard constraint of §9.4 point 3 lives here, on the way to the
    Decision, and it covers both shapes: a ``disarm`` naming areas, and a
    ``switch`` that would drop the areas only the old scenario armed
    (part 2 decision 6). Whoever walks in on a stolen phone still finds every
    external door and window protected.
    """
    named = named_areas(config, rule) if rule.action is RuleActionKind.DISARM else ()
    areas: tuple[Area, ...] = tuple(
        a for a in (config.area(a_id) for a_id in named) if a is not None
    )
    allowed = tuple(a.id for a in areas if not a.is_perimeter)
    refused = tuple(a.id for a in areas if a.is_perimeter)
    return allowed, refused


def named_areas(config: FoyerConfig, rule: AutoRule) -> tuple[str, ...]:
    """The areas a ``disarm`` rule names: its list, or every area the house
    has right now when it names them all (decision 163)."""
    if rule.all_areas:
        return tuple(a.id for a in config.areas)
    return rule.area_ids


def switch_drops(
    config: FoyerConfig, state: RuntimeState, scenario_id: str | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(areas a switch to ``scenario_id`` would disarm, of which the perimeter ones).

    §4.6.1: switching scenario disarms the areas the old scenario armed and
    the new one does not name. Areas armed on their own, outside any
    scenario, are left exactly as they are, so they are not counted here.
    """
    target = config.scenario(scenario_id)
    if target is None:
        return (), ()
    dropped = tuple(
        area_id
        for area_id, rt in state.areas.items()
        if rt.state is not AreaState.DISARMED
        and rt.scenario_id is not None
        and rt.scenario_id == state.active_scenario_id
        and area_id not in target.areas
    )
    perimeter = tuple(
        a_id
        for a_id in dropped
        if (a := config.area(a_id)) is not None and a.is_perimeter
    )
    return dropped, perimeter
