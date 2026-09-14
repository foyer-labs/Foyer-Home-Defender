"""Subscribes to zone entities and feeds them to the engine.

Two streams: a state change (including an attribute-only one, which matters to
numeric attribute triggers and event entities) becomes a ZoneStateChanged; a
report without any change is a heartbeat for supervision (decision 11).
"""

from __future__ import annotations

from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    EventStateReportedData,
    callback,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
)

from .system import FoyerSystem


@callback
def async_watch_zones(system: FoyerSystem) -> CALLBACK_TYPE:
    entity_ids = system.zone_entity_ids()

    @callback
    def _changed(event: Event[EventStateChangedData]) -> None:
        # eager_start: decide() runs synchronously, here, in event order.
        system.hass.async_create_task(
            system.async_zone_changed(
                event.data["entity_id"],
                event.data["old_state"],
                event.data["new_state"],
            ),
            eager_start=True,
        )

    @callback
    def _reported(event: Event[EventStateReportedData]) -> None:
        system.async_heartbeat(event.data["entity_id"])

    unsubs = [
        async_track_state_change_event(system.hass, entity_ids, _changed),
        async_track_state_report_event(system.hass, entity_ids, _reported),
    ]

    @callback
    def unsubscribe() -> None:
        for unsub in unsubs:
            unsub()

    return unsubscribe
