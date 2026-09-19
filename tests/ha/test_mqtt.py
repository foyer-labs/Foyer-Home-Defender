"""The MQTT contract in both directions (SPEC §9.2).

Four things are worth a test here and the rest is plumbing: that a keypad can
tell a wrong code from arming blocked by an open zone, that the topics are the
ones the installation configured, that an undeclared device can do nothing a
code would otherwise allow, and that the retained message says only what this
installation agreed to publish on somebody else's broker.
"""

from __future__ import annotations

import json

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY
from .test_part2 import _advance, _state, _ws
from .test_phase2 import CODE, _make_user
from .test_services import KEYPAD, SCENARIO, _save


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """The MQTT component keeps its own periodic timers running.

    They are Home Assistant's, not Foyer's, and moving a frozen clock inside a
    test wakes them; the alternative is not testing the contract with the
    clock moved, which is where the countdown lives.
    """
    return True


COMMAND = "house/alarm/cmd"
STATE = "house/alarm/state"


async def _enable_mqtt(hass, client, detail: str = "minimal", **overrides) -> None:
    """Switch the contract on, as page 8 does."""
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    settings["mqtt"] = {
        "enabled": True,
        "command_topic": COMMAND,
        "state_topic": STATE,
        "detail": detail,
        "retain": True,
        "qos": 1,
        **overrides,
    }
    result = await _ws(
        client, {"type": "foyer/config/settings", "settings": settings, "code": CODE}
    )
    assert result["success"], result
    await hass.async_block_till_done()


async def _send(hass, mqtt_mock, payload: dict) -> None:
    from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

    async_fire_mqtt_message(hass, COMMAND, json.dumps(payload))
    await hass.async_block_till_done()


def _published(mqtt_mock) -> list[dict]:
    """Every state message published so far, newest last."""
    return [
        json.loads(call.args[1])
        for call in mqtt_mock.async_publish.mock_calls
        if call.args and call.args[0] == STATE
    ]


@pytest.fixture
async def broker(hass, hass_ws_client, loaded, mqtt_mock):
    """A loaded Foyer with one person, one keypad, and MQTT switched on."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass,
        client,
        new_code=CODE,
        permissions=["arm", "disarm", "bypass_zone", "change_scenario", "edit_config"],
    )
    await _save(
        hass,
        client,
        "device",
        {"name": "Hall keypad", "kind": "keypad", "ref": KEYPAD},
        code=CODE,
    )
    await _enable_mqtt(hass, client)
    return mqtt_mock


# --- inbound ---------------------------------------------------------------------


async def test_a_keypad_arms_and_disarms_over_the_configured_topic(
    hass, broker, freezer
):
    await _send(
        hass,
        broker,
        {"action": "arm", "scenario": SCENARIO, "code": CODE, "device_id": KEYPAD},
    )
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    await _send(hass, broker, {"action": "disarm", "code": CODE, "device_id": KEYPAD})
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    assert _published(broker)[-1]["last_result"] == "ok"


async def test_a_wrong_code_is_answered_as_a_wrong_code(hass, broker, freezer):
    await _send(
        hass,
        broker,
        {"action": "arm", "scenario": SCENARIO, "code": CODE, "device_id": KEYPAD},
    )
    await _advance(hass, freezer, 31)

    await _send(
        hass, broker, {"action": "disarm", "code": "000000", "device_id": KEYPAD}
    )

    published = _published(broker)[-1]
    assert published["last_result"] == "bad_code"
    assert published["last_reason"] == "bad_code"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


async def test_an_open_zone_is_not_a_wrong_code(hass, broker):
    """The distinction the contract exists for (§9.2)."""
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()

    await _send(
        hass,
        broker,
        {"action": "arm", "scenario": SCENARIO, "code": CODE, "device_id": KEYPAD},
    )

    published = _published(broker)[-1]
    assert published["last_result"] == "blocked"
    assert published["last_reason"] == "zone_open"
    assert published["ready_to_arm"] is False
    assert published["blocking_zones"] == 1


async def test_an_undeclared_device_can_do_nothing_a_code_would_allow(hass, broker):
    await _send(
        hass,
        broker,
        {
            "action": "arm",
            "scenario": SCENARIO,
            "code": CODE,
            "device_id": "keypad_garden",
        },
    )

    published = _published(broker)[-1]
    # Four words in last_result, for ever (decision 87); the precise why is
    # beside it, for an adapter that wants to tell this from an open window.
    assert published["last_result"] == "blocked"
    assert published["last_reason"] == "device_not_registered"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_a_message_with_no_device_at_all_is_refused(hass, broker):
    """Anybody who can publish to the topic can publish a command."""
    await _send(hass, broker, {"action": "arm", "scenario": SCENARIO, "code": CODE})

    published = _published(broker)[-1]
    assert published["last_result"] == "blocked"
    assert published["last_reason"] == "device_not_registered"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_a_status_request_republishes_without_commanding(hass, broker):
    before = len(_published(broker))
    await _send(hass, broker, {"action": "status"})

    assert len(_published(broker)) == before + 1
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_an_unreadable_message_changes_nothing(hass, broker):
    from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

    async_fire_mqtt_message(hass, COMMAND, "not json at all")
    await hass.async_block_till_done()

    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


# --- outbound ---------------------------------------------------------------------


async def test_the_retained_message_names_nothing_by_default(hass, broker):
    """Part 2 decision 3: it is retained, on a broker that is often shared."""
    payload = _published(broker)[-1]

    assert set(payload) == {
        "master",
        "countdown",
        "ready_to_arm",
        "blocking_zones",
        "fault",
        "last_result",
        "last_reason",
    }
    assert "scenario" not in payload
    assert "open_zones" not in payload


async def test_the_full_level_is_paragraph_9_2_as_written(hass, hass_ws_client, broker):
    client = await hass_ws_client(hass)
    hass.states.async_set("binary_sensor.front_door", "on")
    await _enable_mqtt(hass, client, detail="full")

    await _send(hass, broker, {"action": "status"})
    payload = _published(broker)[-1]

    assert payload["scenario"] is None
    assert payload["areas"] == {"Casa": "disarmed"}
    assert payload["open_zones"] == ["Front door"]


async def test_the_standard_level_stops_short_of_the_open_windows(
    hass, hass_ws_client, broker
):
    client = await hass_ws_client(hass)
    hass.states.async_set("binary_sensor.front_door", "on")
    await _enable_mqtt(hass, client, detail="standard")

    await _send(hass, broker, {"action": "status"})
    payload = _published(broker)[-1]

    assert "areas" in payload
    assert "open_zones" not in payload


async def test_the_countdown_is_the_one_about_to_run_out(hass, broker, freezer):
    await _send(
        hass,
        broker,
        {"action": "arm", "scenario": SCENARIO, "code": CODE, "device_id": KEYPAD},
    )
    payload = _published(broker)[-1]

    assert payload["countdown"]["kind"] == "exit"
    assert 0 < payload["countdown"]["remaining"] <= 30

    await _advance(hass, freezer, 31)
    assert _published(broker)[-1]["countdown"] is None


async def test_nothing_is_published_while_the_contract_is_off(
    hass, hass_ws_client, loaded, mqtt_mock
):
    """An alarm that starts publishing on somebody else's broker the moment it
    is updated has made that choice for the household."""
    assert not _published(mqtt_mock)
    assert hass.data[DOMAIN].config.settings.mqtt.enabled is False
