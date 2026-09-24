"""Fix phase: an event or tag zone that has never fired is not in fault."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.foyer.core.models import EntityState, EventTrigger, Zone
from custom_components.foyer.core.triggers import fault_cause

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
PANIC = Zone(
    id="panic",
    name="Panic button",
    entity_id="event.panic_button",
    area_id="ground",
    trigger=EventTrigger("press"),
)


def _fault(state: str | None) -> str | None:
    return fault_cause(PANIC, EntityState(state=state), NOW, EntityState(state=None))


def test_a_button_nobody_has_pressed_yet_is_healthy():
    assert _fault("unknown") is None


def test_an_unavailable_button_is_still_a_fault():
    """INV-4 is untouched: a sensor that cannot be read is a fault."""
    assert _fault("unavailable") == "unavailable"
    assert _fault(None) == "unavailable"
