"""A zone not answering right after a start is not news yet (decision 165).

Through Home Assistant: the integration has just started, a Zigbee2MQTT
contact is still unavailable and comes back half a minute later. It was a
fault meanwhile — the health sensor says so — and nobody was told.
"""

from __future__ import annotations

from custom_components.foyer.const import DOMAIN

from .conftest import ZONE
from .test_integration import _notifications
from .test_part2 import _advance, _set


def _fault_notices(hass) -> list[dict]:
    zone = hass.data[DOMAIN].config.zones[0].name
    return [n for n in _notifications(hass) if zone in str(n.get("message", ""))]


async def test_a_zone_back_within_the_grace_tells_nobody(hass, loaded, freezer):
    await _set(hass, ZONE, "unavailable")
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].state.faults  # still a fault meanwhile (INV-4)

    await _advance(hass, freezer, 30)
    await _set(hass, ZONE, "off")
    await _advance(hass, freezer, 120)

    assert not hass.data[DOMAIN].state.faults
    assert _fault_notices(hass) == []


async def test_a_zone_still_down_after_the_grace_is_announced(hass, loaded, freezer):
    await _set(hass, ZONE, "unavailable")
    await _advance(hass, freezer, 121)
    assert _fault_notices(hass) != []
