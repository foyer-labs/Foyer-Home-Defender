"""How a zone's entity is read: fault, active, momentary fire (SPEC §4.4, INV-4/5).

Pure functions over EntityState. Nothing here knows about areas or arming.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import math

from .models import (
    FAULT_STATES,
    ArmingDevice,
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


def battery_level(entity: EntityState) -> float | None:
    """The battery percentage an entity reports, or None when it is not one.

    A numeric `sensor` carries the percentage in its state. A `binary_sensor`
    carries no number at all — it says low or not low — so it has no level to
    show and the diagnostics table shows the flag instead.
    """
    raw = entity.state
    if raw is None or raw in FAULT_STATES:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def battery_low(zone: Zone, entity: EntityState, threshold: int) -> bool:
    """Whether this zone's battery counts as low (§4.2, part 1 decision 1).

    Home Assistant's own convention for a battery `binary_sensor` is that
    ``on`` means low, so that is read as it stands. A numeric sensor is low
    below the installation's threshold. An entity that cannot be read is
    neither: it is a fault, reported as one, and calling it low as well would
    put the same problem in two places under two names.
    """
    if zone.battery_entity_id is None or is_unavailable(entity):
        return False
    level = battery_level(entity)
    if level is None:
        return entity.state == "on"
    return level < threshold


def battery_fault(zone: Zone, entity: EntityState) -> str | None:
    """A declared battery entity that cannot be read is a fault (INV-4).

    Chosen deliberately, and it is the half of the battery question that is
    not a warning: a battery sensor that has gone silent is a radio that has
    gone silent, and the contact beside it is the thing that stops reporting
    next. A level of 15 % says the sensor is working and will need a cell; no
    level at all says nothing about the door, which is what INV-4 is for.
    """
    if zone.battery_entity_id is None:
        return None
    return "battery_unavailable" if is_unavailable(entity) else None


def fault_cause(
    zone: Zone, entity: EntityState, now: datetime, battery: EntityState
) -> str | None:
    """Why this zone is in fault right now, or None when it is healthy.

    ``battery`` is the state of ``zone.battery_entity_id``, and it has no
    default on purpose: a caller that forgot it would silently stop seeing
    one of the two faults this function reports. It is passed in rather than
    looked up, like everything else the engine reads (INV-1).
    """
    if is_unavailable(entity):
        return "unavailable"
    trigger = zone.trigger
    if isinstance(trigger, NumericTrigger) and numeric_value(trigger, entity) is None:
        return "not_numeric"
    if supervision_lapsed(zone, entity, now):
        return "supervision"
    return battery_fault(zone, battery)


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


# What an event or tag entity that has never fired says. Not a fault of the
# restore kind: the entity is there and has simply had nothing to report.
NEVER_FIRED = "unknown"
# What an entity is while Home Assistant starts, before it restores the last
# event: a change out of this is the restore, not an event.
RESTORED_FROM = "unavailable"


def is_new_event(old: EntityState, new: EntityState) -> bool:
    """Whether an event/tag entity's change is a new event (§4.4).

    Only a change out of ``unavailable`` is Home Assistant restoring the last
    timestamp at startup. A change out of ``unknown`` is the first event an
    entity has ever had — the first press of a new panic button — and must
    not be swallowed (found in review).
    """
    if is_unavailable(new) or old.state == new.state:
        return False
    return old.state is not None and old.state != RESTORED_FROM


def has_baseline(zone: Zone, entity: EntityState) -> bool:
    """Whether this reading can be a zone's first, baseline reading (§4.7).

    For an event or tag entity, ``unknown`` is a reading: the entity has
    never fired, and its first event must be able to count."""
    if isinstance(zone.trigger, EventTrigger) and entity.state == NEVER_FIRED:
        return True
    return not is_unavailable(entity)


def fires_momentarily(zone: Zone, old: EntityState, new: EntityState) -> bool:
    """Whether an event/tag zone fires on this change.

    Event and tag entities hold the timestamp of their last event, so a new
    event is a change of state. A change *out of* unavailable is Home
    Assistant restoring the last timestamp at startup, not a new event.
    """
    trigger = zone.trigger
    if not isinstance(trigger, EventTrigger):
        return False
    if not is_new_event(old, new):
        return False
    if trigger.event_type is None:
        return True
    return new.attributes.get("event_type") == trigger.event_type


def scanned(device: ArmingDevice, old: EntityState, new: EntityState) -> bool:
    """Whether this change is a tag being presented (SPEC §9.3).

    The same reading as an event zone's, and deliberately the same three
    rules: a `tag.*` or `event.*` entity holds the timestamp of its last
    event, so a new one is a change of state; a change out of unavailable is
    Home Assistant restoring that timestamp at startup, not somebody at the
    door; and a device that names an ``event_type`` fires only on that button.
    """
    if not is_new_event(old, new):
        return False
    if device.event_type is None:
        return True
    return new.attributes.get("event_type") == device.event_type
