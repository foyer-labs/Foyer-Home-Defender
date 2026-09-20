"""Action conditions, pure (SPEC §6.3).

Two kinds and no more — a daily time window and one entity's state — because
that boundary is what keeps this a response engine instead of a second
automation engine. Entity states come from the snapshot, never from Home
Assistant, so the simulator evaluates a condition exactly as the runtime does.

An action carries at most two conditions (``MAX_CONDITIONS``) combined with
``all`` or ``any`` (part 3 decision 4).
"""

from __future__ import annotations

from datetime import datetime, tzinfo

from .clock import in_daily_window
from .models import (
    FAULT_STATES,
    Condition,
    ConditionMode,
    ProfileAction,
    StateCondition,
    StateOperator,
    SystemSnapshot,
    TimeCondition,
)


def condition_entities(action: ProfileAction) -> tuple[str, ...]:
    """The entities this action's conditions read, for the snapshot to carry."""
    return tuple(
        c.entity_id for c in action.conditions if isinstance(c, StateCondition)
    )


def met(
    condition: Condition, snapshot: SystemSnapshot, now: datetime, tz: tzinfo
) -> bool:
    """Whether one condition holds. An entity that is missing holds nothing:
    a condition that cannot be read is not met, so an action never runs on a
    guess (the same reasoning as INV-4)."""
    if isinstance(condition, TimeCondition):
        return in_daily_window(now, tz, condition.after, condition.before)
    state = snapshot.entity(condition.entity_id).state
    if state is None or state in FAULT_STATES:
        # `unavailable` and `unknown` are not answers (INV-4, §6.3): read as
        # ordinary strings, "is not home" was satisfied by a tracker nobody
        # could read, and an action ran on a guess (found in review).
        return False
    if condition.operator is StateOperator.IS:
        return state == condition.state
    return state != condition.state


def evaluate(
    action: ProfileAction, snapshot: SystemSnapshot, now: datetime, tz: tzinfo
) -> bool:
    """Whether ``action`` may run now. No conditions means yes."""
    if not action.conditions:
        return True
    results = [met(c, snapshot, now, tz) for c in action.conditions]
    if action.condition_mode is ConditionMode.ANY:
        return any(results)
    return all(results)


def unmet(
    action: ProfileAction, snapshot: SystemSnapshot, now: datetime, tz: tzinfo
) -> tuple[Condition, ...]:
    """The conditions that failed, for the trace's "skipped AND WHY" (§11.2)."""
    return tuple(c for c in action.conditions if not met(c, snapshot, now, tz))
