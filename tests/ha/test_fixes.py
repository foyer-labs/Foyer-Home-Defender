"""The fix phase before 1.0: defects found while the documentation was written.

Each test names the defect it pins down, so that it cannot come back
quietly.
"""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.const import DOMAIN

from .test_part2 import _advance, _ws
from .test_part3 import _profile, _siren_action


async def test_a_tested_siren_on_a_switch_is_switched_off_again(
    hass, loaded, hass_ws_client, freezer
):
    """§11.4: the siren sounds for three seconds. A switch-driven siren, or one
    that takes no duration, used to stay on until somebody went to it."""
    on = async_mock_service(hass, "switch", "turn_on")
    off = async_mock_service(hass, "switch", "turn_off")
    hass.states.async_set("switch.siren_relay", "off")
    client = await hass_ws_client(hass)
    await _profile(client, [_siren_action(entity_ids=["switch.siren_relay"])])
    await hass.async_block_till_done()
    profile = hass.data[DOMAIN].config.profiles[-1]

    result = await _ws(
        client,
        {
            "type": "foyer/test_action",
            "profile_id": profile.id,
            "action_id": profile.actions[0].id,
        },
    )
    assert result["success"] is True
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in on] == ["switch.siren_relay"]
    assert off == []

    await _advance(hass, freezer, 3)
    assert [c.data["entity_id"] for c in off] == ["switch.siren_relay"]
