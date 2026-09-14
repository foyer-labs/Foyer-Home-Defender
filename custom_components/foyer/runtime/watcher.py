"""Subscribes to zone entity state changes and feeds them to the engine."""

from __future__ import annotations

from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, callback
from homeassistant.helpers.event import async_track_state_change_event

from .system import FoyerSystem


@callback
def async_watch_zones(system: FoyerSystem) -> CALLBACK_TYPE:
    entity_ids = [zone.entity_id for zone in system.config.zones]

    @callback
    def _changed(event: Event[EventStateChangedData]) -> None:
        old = event.data["old_state"]
        new = event.data["new_state"]
        old_value = old.state if old else None
        new_value = new.state if new else None
        if old_value == new_value:
            return  # attribute-only change: nothing for the engine
        system.hass.async_create_task(
            system.async_zone_changed(event.data["entity_id"], old_value, new_value),
            eager_start=True,
        )

    return async_track_state_change_event(system.hass, entity_ids, _changed)
