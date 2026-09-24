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


async def test_an_administrator_calling_the_services_is_never_locked_out(
    hass, loaded, hass_ws_client, hass_admin_user
):
    """§8.4: the admin path is never locked out. A foyer.* service called by an
    administrator's account was counted like any other, and locked."""
    from homeassistant.core import Context

    from .test_phase2 import CODE, _make_user

    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    armed = await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id})
    assert armed["success"], armed
    reasons = []
    for _ in range(7):
        result = await hass.services.async_call(
            DOMAIN,
            "disarm",
            {"code": "999999"},
            blocking=True,
            return_response=True,
            context=Context(user_id=hass_admin_user.id),
        )
        reasons.append(result["reason"])
    assert "locked_out" not in reasons
    assert set(reasons) == {"bad_code"}


async def test_an_undeclared_device_is_heard_of_on_every_service(hass, loaded):
    """Decision 81: an undeclared device is refused, recorded and notified. On
    the action test and the export and import services it was only refused,
    which made them the quiet place to try names."""
    result = await hass.services.async_call(
        DOMAIN,
        "export_log",
        {"device_id": "made_up_keypad"},
        blocking=True,
        return_response=True,
    )
    assert result["reason"] == "device_not_registered"
    await hass.async_block_till_done()
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    rows = (await system.log.async_query(limit=100))["rows"]
    assert any(
        r["event_type"] == "device_rejected" and r["device_id"] == "made_up_keypad"
        for r in rows
    )


async def test_a_person_cannot_be_linked_to_an_account_home_assistant_runs(
    hass, loaded, hass_ws_client
):
    """Only the Users page kept Home Assistant Cloud's account out of the list;
    a command sent around it could link a person, exemption and all."""
    cloud = await hass.auth.async_create_system_user("Home Assistant Cloud")
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {
                "name": "Voice",
                "permissions": ["arm"],
                "allowed_area_ids": None,
                "allowed_scenario_ids": None,
                "valid_from": None,
                "valid_until": None,
                "code_exempt_when_identified": True,
                "enabled": True,
                "ha_user_id": cloud.id,
            },
        },
    )
    assert result["success"] is False
    assert [p["code"] for p in result["problems"]] == ["unknown_ha_user"]


async def test_the_first_zone_takes_the_type_proposed_for_its_sensor(hass, entry):
    """The config flow's zone was always instant, so a front door had no entry
    delay until somebody changed it. It now takes the type the zone editor
    proposes: delayed for a door."""
    from .conftest import ZONE

    hass.states.async_set(
        ZONE, "off", {"friendly_name": "Front door", "device_class": "door"}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    (zone,) = hass.data[DOMAIN].config.zones
    assert zone.type.value == "delayed"
    assert zone.entry_mode.value == "delayed"
