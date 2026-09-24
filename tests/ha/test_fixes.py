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


async def test_a_key_zone_keeps_its_person_through_a_panel_save(
    hass, loaded, hass_ws_client
):
    """§4.7: a key zone acts as a person. The panel now shows and sets it, and
    a zone saved from the panel keeps the person it had."""
    from .test_phase2 import CODE, _make_user

    client = await hass_ws_client(hass)
    luca = await _make_user(
        hass,
        client,
        new_code=CODE,
        permissions=["arm", "disarm", "edit_config", "manage_users"],
    )
    config = (await _ws(client, {"type": "foyer/config"}))["config"]
    scenario_id = config["scenarios"][0]["id"]
    area_id = config["areas"][0]["id"]
    hass.states.async_set("input_boolean.key_switch", "off")
    item = {
        "name": "Key switch",
        "entity_id": "input_boolean.key_switch",
        "area_id": area_id,
        "type": "key",
        "channel": "key",
        "arm_policy": "ignore",
        "trigger": {"kind": "state", "states": ["on"]},
        "key": {
            "on_activate": "toggle",
            "scenario_id": scenario_id,
            "on_deactivate": "none",
            "user_id": luca,
        },
    }
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": item,
            "trigger_confirmed": True,
            "code": CODE,
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()

    # The panel reads the zone and saves it back, as its editor does.
    config = (await _ws(client, {"type": "foyer/config"}))["config"]
    zone = next(z for z in config["zones"] if z["name"] == "Key switch")
    assert zone["key"]["user_id"] == luca
    again = await _ws(
        client,
        {"type": "foyer/config/save", "kind": "zone", "item": zone, "code": CODE},
    )
    assert again["success"], again
    await hass.async_block_till_done()
    zone = next(z for z in hass.data[DOMAIN].config.zones if z.name == "Key switch")
    assert zone.key.user_id == luca


async def test_a_walk_test_announces_itself_even_when_no_profile_does(
    hass, loaded, hass_ws_client
):
    """§11.3 calls the notification on start and on end mandatory. It came from
    the default profile alone, and unticking two moments removed it."""
    client = await hass_ws_client(hass)
    config = (await _ws(client, {"type": "foyer/config"}))["config"]
    profile = config["profiles"][0]
    for action in profile["actions"]:
        action["moments"] = [
            m
            for m in action["moments"]
            if m not in ("walk_test_started", "walk_test_ended")
        ]
    saved = await _ws(
        client, {"type": "foyer/config/save", "kind": "profile", "item": profile}
    )
    assert saved["success"], saved
    await hass.async_block_till_done()

    started = await hass.services.async_call(
        DOMAIN, "walk_test", {"enable": True}, blocking=True, return_response=True
    )
    assert started["success"] is True
    await hass.async_block_till_done()
    notes = hass.data["persistent_notification"]
    assert "foyer_walk_test" in notes

    await hass.services.async_call(
        DOMAIN, "walk_test", {"enable": False}, blocking=True, return_response=True
    )
    await hass.async_block_till_done()
    assert "over" in notes["foyer_walk_test"]["title"]
