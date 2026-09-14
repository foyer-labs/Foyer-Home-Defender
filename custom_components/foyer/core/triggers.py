"""How a zone's entity is read: fault, active, momentary fire (SPEC §4.4, INV-4/5).

Pure functions over EntityState. Nothing here knows about areas or arming.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import math

from .models import (
    FAULT_STATES,
    EntityState,
    EventTrigger,
    NumericOperator,
    NumericTrigger,
    StateTrigger,
    Zone,
)


def is_unavailable(entity: EntityState) -> bool:
    """A missing, unavailable or unknown entity is a fault (INV-4)."""
    return entity.state is None or entity.state in FAULT_STATES


def numeric_value(trigger: NumericTrigger, entity: EntityState) -> float | None:
    raw = (
        entity.state
        if trigger.attribute is None
        else entity.attributes.get(trigger.attribute)
    )
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def supervision_lapsed(zone: Zone, entity: EntityState, now: datetime) -> bool:
    """No report at all within the supervision window is a fault (INV-4).

    Any report counts, changed or not: a door that stays closed for a week but
    keeps checking in is alive (decision 11, 2026-09-14).
    """
    if zone.supervision_timeout is None or entity.last_reported is None:
        return False
    return now - entity.last_reported > timedelta(seconds=zone.supervision_timeout)


def supervision_due(zone: Zone, entity: EntityState) -> datetime | None:
    """When supervision will lapse if nothing is reported before then."""
    if zone.supervision_timeout is None or entity.last_reported is None:
        return None
    return entity.last_reported + timedelta(seconds=zone.supervision_timeout)


def fault_cause(zone: Zone, entity: EntityState, now: datetime) -> str | None:
    """Why this zone is in fault right now, or None when it is healthy."""
    if is_unavailable(entity):
        return "unavailable"
    trigger = zone.trigger
    if isinstance(trigger, NumericTrigger) and numeric_value(trigger, entity) is None:
        return "not_numeric"
    if supervision_lapsed(zone, entity, now):
        return "supervision"
    return None


def is_active(zone: Zone, entity: EntityState, was_active: bool) -> bool:
    """Whether a level trigger counts as triggered (INV-5).

    An entity that cannot be read keeps whatever it was: going unavailable does
    not close a zone, and coming back in the state it left does not re-trigger
    it. The fault itself is reported separately. Event triggers are momentary
    and are never "active".
    """
    trigger = zone.trigger
    if isinstance(trigger, EventTrigger):
        return False
    if is_unavailable(entity):
        return was_active
    if isinstance(trigger, StateTrigger):
        return entity.state in trigger.states
    value = numeric_value(trigger, entity)
    if value is None:
        return was_active
    if trigger.operator is NumericOperator.EQ:
        return value == trigger.value
    if trigger.operator is NumericOperator.GT:
        if value > trigger.value:
            return True
        return was_active and value > trigger.value - trigger.hysteresis
    if value < trigger.value:
        return True
    return was_active and value < trigger.value + trigger.hysteresis


def fires_momentarily(zone: Zone, old: EntityState, new: EntityState) -> bool:
    """Whether an event/tag zone fires on this change.

    Event and tag entities hold the timestamp of their last event, so a new
    event is a change of state. A change *out of* unavailable is Home
    Assistant restoring the last timestamp at startup, not a new event.
    """
    trigger = zone.trigger
    if not isinstance(trigger, EventTrigger):
        return False
    if is_unavailable(old) or is_unavailable(new) or old.state == new.state:
        return False
    if trigger.event_type is None:
        return True
    return new.attributes.get("event_type") == trigger.event_type
