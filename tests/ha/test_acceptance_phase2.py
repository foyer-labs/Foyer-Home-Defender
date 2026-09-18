"""The acceptance of Phase 2, walked end to end (SPEC §16).

    "Arming and disarming from a physical keypad works with correct feedback
     on the keypad itself, and the log attributes every action to a person
     and a channel."

One test, in the order a household would live it: somebody gets a code, a
keypad is declared, the keypad arms the house and is told so, a wrong code is
refused and says which kind of refusal it was, the keypad disarms — and then
the log is read, which is the half of the sentence that is easy to forget.

A second test does the same through a tag, because §9.3's channel carries no
code at all and has to be attributable anyway.

Keep this passing.
"""

from __future__ import annotations

import json

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY
from .test_mqtt import COMMAND, STATE, _enable_mqtt, _published, _send
from .test_part2 import _advance, _state
from .test_phase2 import CODE, _make_user
from .test_services import KEYPAD, SCENARIO, _save

TAG_ENTITY = "tag.luca_keyring"


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Home Assistant's own MQTT timers; see tests/ha/test_mqtt.py."""
    return True


async def _rows(hass, category: str) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    result = await system.log.async_query(limit=200, categories=[category])
    return result["rows"]


async def test_a_keypad_on_a_broker_arms_disarms_and_is_answered(
    hass, hass_ws_client, loaded, mqtt_mock, freezer
):
    client = await hass_ws_client(hass)

    # 1. A person, with a code. Until now the policy was inert (decision 78).
    user_id = await _make_user(
        hass,
        client,
        new_code=CODE,
        permissions=["arm", "disarm", "change_scenario", "edit_config"],
    )

    # 2. The keypad is declared. Until it is, it can do nothing at all.
    await _save(
        hass,
        client,
        "device",
        {"name": "Hall keypad", "kind": "keypad", "ref": KEYPAD},
        code=CODE,
    )
    await _enable_mqtt(hass, client)
    device_id = hass.data[DOMAIN].config.devices[0].id

    # 3. It arms. The keypad is told the exit delay is running, and how long.
    await _send(
        hass,
        mqtt_mock,
        {"action": "arm", "scenario": SCENARIO, "code": CODE, "device_id": KEYPAD},
    )
    feedback = _published(mqtt_mock)[-1]
    assert feedback["last_result"] == "ok"
    assert feedback["countdown"]["kind"] == "exit"
    assert 0 < feedback["countdown"]["remaining"] <= 30

    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    assert _published(mqtt_mock)[-1]["master"] == "armed_away"

    # 4. A wrong code is refused, and says which refusal it was.
    await _send(
        hass, mqtt_mock, {"action": "disarm", "code": "000000", "device_id": KEYPAD}
    )
    assert _published(mqtt_mock)[-1]["last_result"] == "bad_code"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    # 5. A device nobody declared gets a different answer, not the same one.
    await _send(
        hass,
        mqtt_mock,
        {"action": "disarm", "code": CODE, "device_id": "keypad_garden"},
    )
    assert _published(mqtt_mock)[-1]["last_result"] == "unknown_device"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    # 6. The right code disarms.
    await _send(
        hass, mqtt_mock, {"action": "disarm", "code": CODE, "device_id": KEYPAD}
    )
    assert _published(mqtt_mock)[-1]["last_result"] == "ok"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED

    # 7. And the log says who, through what, on which device. Every row.
    arming = await _rows(hass, "arming")
    acted = [r for r in arming if r["event_type"] in ("armed", "disarmed")]
    assert len(acted) >= 2
    for row in acted:
        assert row["user_id"] == user_id
        assert row["user_name"] == "Luca"
        assert row["channel"] == "keypad"
        assert row["device_id"] == device_id

    # The refusals are on record too, in their own category, and neither of
    # them names the code or whose it nearly was.
    security = await _rows(hass, "security")
    kinds = {r["event_type"] for r in security}
    assert {"code_rejected", "device_rejected"} <= kinds
    assert CODE not in json.dumps(security)


async def test_a_tag_arms_the_house_and_the_log_still_names_a_person(
    hass, hass_ws_client, loaded, freezer
):
    """§9.3: possession is the credential, and it is still attributable."""
    client = await hass_ws_client(hass)
    user_id = await _make_user(
        hass, client, new_code=CODE, permissions=["arm", "disarm", "edit_config"]
    )
    hass.states.async_set(TAG_ENTITY, "2026-09-18T08:00:00+00:00")
    await hass.async_block_till_done()

    await _save(
        hass,
        client,
        "device",
        {
            "name": "Luca's keyring",
            "kind": "tag",
            "entity_id": TAG_ENTITY,
            "user_id": user_id,
            "command": "toggle",
            "scenario_id": hass.data[DOMAIN].config.scenarios[0].id,
        },
        code=CODE,
    )
    device_id = hass.data[DOMAIN].config.devices[0].id

    # The tag is scanned. No code travels, and none is asked for.
    hass.states.async_set(TAG_ENTITY, "2026-09-18T19:40:00+00:00")
    await hass.async_block_till_done()
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    hass.states.async_set(TAG_ENTITY, "2026-09-18T19:50:00+00:00")
    await hass.async_block_till_done()
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED

    rows = await _rows(hass, "arming")
    acted = [r for r in rows if r["event_type"] in ("armed", "disarmed")]
    assert acted
    for row in acted:
        assert row["user_name"] == "Luca"
        assert row["channel"] == "nfc"
        assert row["device_id"] == device_id


async def test_the_topics_are_the_ones_this_installation_chose(
    hass, hass_ws_client, loaded, mqtt_mock
):
    """§9.2: people run more than one site against one broker."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, permissions=["arm", "edit_config"])
    await _enable_mqtt(hass, client)

    published = [
        call.args[0] for call in mqtt_mock.async_publish.mock_calls if call.args
    ]
    assert STATE in published
    assert not any(topic.startswith("foyer/") for topic in published)
    assert mqtt_mock.async_subscribe.call_args is not None
    assert COMMAND in str(mqtt_mock.async_subscribe.mock_calls)
