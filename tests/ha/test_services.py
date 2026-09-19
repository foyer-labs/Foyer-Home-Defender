"""The foyer.* service contract (SPEC §9.1, §14.1), inside Home Assistant.

What matters here is not that arming works — the WebSocket tests prove that.
It is that a second way in gives the **same** answers as the first: the same
structured result, the same code check, the same refusal for a device nobody
declared. Two paths that disagree is how one of them ends up being the one
without the check.
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY
from .test_part2 import _advance, _state, _ws
from .test_phase2 import CODE, _make_user

KEYPAD = "keypad_hall"
SCENARIO = "Fuori casa"


async def _call(hass, service: str, **data) -> dict:
    return await hass.services.async_call(
        DOMAIN, service, data, blocking=True, return_response=True
    )


async def _save(hass, client, kind: str, item: dict, **extra) -> dict:
    result = await _ws(
        client, {"type": "foyer/config/save", "kind": kind, "item": item, **extra}
    )
    assert result["success"], result
    await hass.async_block_till_done()
    return result


@pytest.fixture
async def with_keypad(hass, hass_ws_client, loaded):
    """One person with a code, and one keypad declared on page 8."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass,
        client,
        new_code=CODE,
        permissions=[
            "arm",
            "disarm",
            "bypass_zone",
            "change_scenario",
            "view_log",
            "edit_config",
        ],
    )
    await _save(
        hass,
        client,
        "device",
        {"name": "Hall keypad", "kind": "keypad", "ref": KEYPAD},
        code=CODE,
    )
    return client


# --- the contract ------------------------------------------------------------------


async def test_a_service_answers_the_same_shape_as_the_websocket(
    hass, hass_ws_client, loaded
):
    """§9.1: one result, whichever way in the caller used."""
    client = await hass_ws_client(hass)
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id

    over_ws = await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id})
    await _ws(client, {"type": "foyer/disarm"})
    over_service = await _call(hass, "arm", scenario_id=scenario_id)

    assert over_ws.keys() == over_service.keys()
    assert over_service["success"] is True
    assert over_service["reason"] is None
    assert over_service["blocking_zones"] == []
    assert over_service["state"]["master"]["state"] == "arming"


async def test_a_blocked_arming_names_the_zone_that_blocked_it(hass, loaded):
    """The distinction the whole contract exists for: this is not a bad code."""
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()

    result = await _call(hass, "arm", scenario_name="Fuori casa")

    assert result["success"] is False
    assert result["reason"] == "zone_open"
    assert [z["name"] for z in result["blocking_zones"]] == ["Front door"]


async def test_a_bad_code_over_a_service_is_answered_as_a_bad_code(
    hass, with_keypad, freezer
):
    assert (
        await _call(hass, "arm", scenario_name=SCENARIO, code=CODE, device_id=KEYPAD)
    )["success"]
    await _advance(hass, freezer, 31)

    result = await _call(hass, "disarm", code="000000", device_id=KEYPAD)

    assert result["success"] is False
    assert result["reason"] == "bad_code"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


async def test_arming_by_scenario_name_and_by_area(hass, loaded, freezer):
    system = hass.data[DOMAIN]
    assert (await _call(hass, "arm", scenario_name="Fuori casa"))["success"]
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    assert (await _call(hass, "disarm"))["success"]
    area_id = system.config.areas[0].id
    assert (await _call(hass, "arm", area_id=area_id))["success"]


async def test_an_unknown_scenario_name_is_refused_by_name(hass, loaded):
    result = await _call(hass, "arm", scenario_name="Nowhere")
    assert result["success"] is False
    assert result["reason"] == "unknown_scenario"


async def test_skip_exit_delay_arms_at_once_and_says_so(hass, loaded):
    """Part 2 decision 5: no permission of its own, but never silent."""
    result = await _call(hass, "arm", scenario_name="Fuori casa", skip_exit_delay=True)

    assert result["success"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    rows = await _rows(hass, category="arming")
    armed = [r for r in rows if r["event_type"] == "armed"]
    assert armed and armed[0]["detail"]["skip_exit_delay"] == "1"


async def _rows(hass, **filters) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    categories = [filters.pop("category")] if "category" in filters else None
    result = await system.log.async_query(
        limit=200, **({"categories": categories} if categories else {}), **filters
    )
    return result["rows"]


# --- the device white list (part 2 decision 1) -------------------------------------


async def test_an_undeclared_device_is_refused_whatever_code_it_brings(
    hass, with_keypad
):
    result = await _call(
        hass, "arm", scenario_name=SCENARIO, code=CODE, device_id="keypad_garden"
    )

    assert result["success"] is False
    assert result["reason"] == "device_not_registered"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_an_undeclared_device_is_recorded_and_shown(hass, with_keypad):
    from homeassistant.components.persistent_notification import (
        DOMAIN as NOTIFICATIONS,
    )

    await _call(
        hass, "arm", scenario_name=SCENARIO, code=CODE, device_id="keypad_garden"
    )

    rows = await _rows(hass, category="security")
    rejected = [r for r in rows if r["event_type"] == "device_rejected"]
    assert rejected and rejected[0]["device_id"] == "keypad_garden"

    shown = hass.data[NOTIFICATIONS]
    assert any("keypad_garden" in n["message"] for n in shown.values())


async def test_a_declared_keypad_arms_and_is_named_in_the_log(
    hass, with_keypad, freezer
):
    """The acceptance of this phase, through a service: a person, a channel."""
    device_id = hass.data[DOMAIN].config.devices[0].id

    assert (
        await _call(hass, "arm", scenario_name=SCENARIO, code=CODE, device_id=KEYPAD)
    )["success"]
    await _advance(hass, freezer, 31)
    assert (await _call(hass, "disarm", code=CODE, device_id=KEYPAD))["success"]

    rows = await _rows(hass, category="arming")
    disarmed = [r for r in rows if r["event_type"] == "disarmed"]
    assert disarmed
    assert disarmed[0]["user_name"] == "Luca"
    assert disarmed[0]["channel"] == "keypad"
    assert disarmed[0]["device_id"] == device_id


async def test_a_name_a_service_call_asserts_is_marked_in_the_log(
    hass, with_keypad, freezer
):
    """§9.1 lets a caller name somebody; nothing verified it (decision 88).

    The row keeps the name — attribution is useful — and stops asserting more
    than it knows, because a wrong answer to "who disarmed at 03:14" is worse
    than no answer.
    """
    user_id = hass.data[DOMAIN].config.users[0].id
    assert (await _call(hass, "arm", scenario_name=SCENARIO, user_id=user_id))[
        "success"
    ]
    # The `armed` row is written when the exit delay ends, which is exactly
    # why the area has to remember how it came by the name.
    await _advance(hass, freezer, 31)

    rows = await _rows(hass, category="arming")
    armed = [r for r in rows if r["event_type"] == "armed"]
    assert armed
    assert armed[0]["user_name"] == "Luca"
    assert armed[0]["detail"]["attributed"] == "claimed"


async def test_a_name_a_code_established_is_not_marked(hass, with_keypad, freezer):
    assert (
        await _call(hass, "arm", scenario_name=SCENARIO, code=CODE, device_id=KEYPAD)
    )["success"]
    await _advance(hass, freezer, 31)

    rows = await _rows(hass, category="arming")
    armed = [r for r in rows if r["event_type"] == "armed"]
    assert armed and "attributed" not in armed[0]["detail"]


async def test_a_channel_that_identifies_cannot_be_claimed_by_a_caller(
    hass, with_keypad
):
    """Otherwise an automation buys the per-user exemption of §8.2 by typing."""
    result = await _call(hass, "arm", scenario_name=SCENARIO, channel="nfc")
    assert result["success"] is False
    assert result["reason"] == "device_not_registered"


async def test_a_disabled_keypad_stops_commanding(hass, with_keypad):
    client = with_keypad
    device = hass.data[DOMAIN].config.devices[0]
    await _save(
        hass,
        client,
        "device",
        {
            "id": device.id,
            "name": device.name,
            "kind": "keypad",
            "ref": KEYPAD,
            "enabled": False,
        },
        code=CODE,
    )

    result = await _call(
        hass, "arm", scenario_name=SCENARIO, code=CODE, device_id=KEYPAD
    )
    assert result["reason"] == "device_not_registered"


# --- the services that read and write the configuration ----------------------------


async def test_exporting_the_configuration_carries_no_hash(hass, with_keypad):
    result = await _call(hass, "export_config", code=CODE)
    assert result["success"], result
    users = result["document"]["config"]["users"]
    assert users and users[0]["has_code"] is True
    assert "code_hash" not in users[0]


async def test_a_configuration_service_refuses_without_the_code(hass, with_keypad):
    """§8.2: editing the configuration asks for a code, on every channel."""
    result = await _call(hass, "export_config")
    assert result["success"] is False
    assert result["reason"] in ("code_required", "not_permitted")


async def test_exporting_the_log_returns_the_rows_it_matched(hass, with_keypad):
    result = await _call(
        hass, "export_log", code=CODE, format="json", categories=["config"]
    )
    assert result["success"], result
    assert result["rows"] >= 1
    assert "config_save" in result["content"]


async def test_restoring_a_configuration_that_is_not_ours_is_refused(hass, with_keypad):
    result = await _call(hass, "import_config", code=CODE, document={"hello": "world"})
    assert result["success"] is False
    assert [p["code"] for p in result["problems"]] == ["not_a_foyer_backup"]


async def test_walk_test_and_action_test_are_not_registered_yet(hass, loaded):
    """Phase 3 builds them (§11.3, §11.4). A service that exists and does
    nothing answers its caller with silence, which is the answer that gets
    mistaken for success."""
    assert not hass.services.has_service(DOMAIN, "walk_test")
    assert not hass.services.has_service(DOMAIN, "test_action")
