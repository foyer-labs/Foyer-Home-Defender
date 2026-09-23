"""Subscribes to the entities the engine is given, and feeds them to it.

Two streams: a state change (including an attribute-only one, which matters to
numeric attribute triggers and event entities) becomes a ZoneStateChanged; a
report without any change is a heartbeat for supervision (decision 11).

**Everything the snapshot carries is subscribed to, not only the zones**
(found in review). The engine is handed the world and never looks anything up
(INV-1), and the world it is handed includes each zone's battery entity, the
mains entity, every radio's coordinator and every entity an action's condition
reads. Subscribing to a narrower set than that is not a smaller subscription,
it is a power cut nobody notices until the next door opens.

The heartbeat stream stays on the zones alone: supervision is a property of a
zone (§4.2), and a battery reporting its level is not a door saying it is
still there.
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
    entity_ids = system.watched_entity_ids()
    zone_ids = system.zone_entity_ids()

    @callback
    def _changed(event: Event[EventStateChangedData]) -> None:
        # eager_start: decide() runs synchronously, here, in event order —
        # unless this change was written by Foyer's own _notify() while
        # another decision was still being made. It then waits for that one
        # to finish (FoyerSystem.async_handle).
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
        async_track_state_report_event(system.hass, zone_ids, _reported),
    ]

    @callback
    def unsubscribe() -> None:
        for unsub in unsubs:
            unsub()

    return unsubscribe
