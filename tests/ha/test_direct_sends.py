"""A notification sent straight to a service counts for the contact channels
on that same service (decision 164).

The notifications arrived and page 14 still said the phone's channel had
never been used, because they named the service rather than the contact.
A send that works is evidence about that transport; one that fails is not
counted against the channel, whose own data may differ from the action's.
"""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from .test_part2 import _advance, _ws
from .test_part12 import _config
from .test_services import SCENARIO, _call, _save


async def _house(hass, client) -> None:
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "name": "Luke",
                "channels": [{"id": "push", "kind": "push", "service": "notify.phone"}],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    profile = (await _config(client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["armed"],
            "name": "",
            "params": {"service": "notify.phone", "message": "{{ event }}"},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, client, "profile", profile)


async def _channel(client) -> dict:
    status = await _ws(client, {"type": "foyer/health"})
    return next(c for c in status["channels"] if c["service"] == "notify.phone")


async def test_a_direct_send_that_works_proves_the_contact_channel(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    async_mock_service(hass, "notify", "phone")
    await _house(hass, client)
    assert (await _channel(client))["checked"] is False

    await _call(hass, "arm", scenario_name=SCENARIO, channel="automation")
    await _advance(hass, freezer, 31)
    await hass.async_block_till_done()

    channel = await _channel(client)
    assert channel["checked"] is True
    assert channel["fault"] is None


async def test_a_direct_send_that_fails_is_not_held_against_it(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)

    async def refuse(call):
        raise HomeAssistantError("the phone refused it")

    hass.services.async_register("notify", "phone", refuse)
    await _house(hass, client)

    await _call(hass, "arm", scenario_name=SCENARIO, channel="automation")
    await _advance(hass, freezer, 31)
    await hass.async_block_till_done()

    channel = await _channel(client)
    assert channel["checked"] is False
    assert channel["failures"] == 0
    assert channel["fault"] is None
