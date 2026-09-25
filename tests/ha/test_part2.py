"""Phase 1 part 2 inside Home Assistant: technical channel, incidents, chime."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.foyer.const import DOMAIN

from .conftest import MASTER, PANEL_ENTITY, ZONE

SMOKE = "binary_sensor.kitchen_smoke"
TECHNICAL = "binary_sensor.foyer_technical_alarm"
CAUSE = "sensor.foyer_technical_cause"
INCIDENT = "sensor.foyer_incident"
CHIME = "switch.foyer_chime"


def _state(hass, entity_id: str) -> str:
    return hass.states.get(entity_id).state


async def _advance(hass, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


_IDS = iter(range(100, 10_000))  # WebSocket message ids, unique per connection


async def _ws(client, message: dict) -> dict:
    await client.send_json({"id": next(_IDS), **message})
    msg = await client.receive_json()
    assert msg["success"], msg
    return msg["result"]


async def _set(hass, entity_id: str, state: str, **attributes) -> None:
    hass.states.async_set(entity_id, state, attributes)
    await hass.async_block_till_done()


async def _add_smoke_detector(hass, client) -> None:
    await _set(hass, SMOKE, "off", friendly_name="Kitchen smoke")
    area_id = hass.data[DOMAIN].config.areas[0].id
    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": {
                "name": "Kitchen smoke",
                "entity_id": SMOKE,
                "area_id": area_id,
                "type": "technical",
                "trigger": {"kind": "state", "states": ["on"]},
            },
            "trigger_confirmed": True,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()


async def test_an_alpha_3_configuration_is_migrated_to_the_new_major(
    hass, entry, hass_storage
):
    """Schema 3.1 (decision 58): a 2.2 file is upgraded, never reset."""
    from custom_components.foyer.store.config_store import STORAGE_KEY
    from custom_components.foyer.store.migrations import migrate
    from custom_components.foyer.store.schema import (
        STORAGE_MINOR_VERSION,
        STORAGE_VERSION,
    )

    from .test_integration import PHASE_0_DOCUMENT

    alpha_3 = migrate((1, 1), (2, 2), PHASE_0_DOCUMENT["data"])
    hass_storage[STORAGE_KEY] = {
        "version": 2,
        "minor_version": 2,
        "key": STORAGE_KEY,
        "data": alpha_3,
    }
    hass.states.async_set(ZONE, "off")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (STORAGE_VERSION, STORAGE_MINOR_VERSION) == (8, 5)
    system = hass.data[DOMAIN]
    assert system.config.zones[0].name == "Shutter"
    assert system.config.groups == ()
    assert _state(hass, TECHNICAL) == "off"


async def test_the_new_entities_exist_and_start_quiet(hass, loaded):
    assert _state(hass, TECHNICAL) == "off"
    assert _state(hass, CAUSE) == "none"
    assert _state(hass, INCIDENT) == "none"
    assert _state(hass, CHIME) == "on"


async def test_a_smoke_detector_alarms_on_its_own_channel(hass, loaded, hass_ws_client):
    """§5.5 end to end: never an alarm panel, disarm has no authority."""
    client = await hass_ws_client(hass)
    await _add_smoke_detector(hass, client)

    await _set(hass, SMOKE, "on", friendly_name="Kitchen smoke")
    assert _state(hass, TECHNICAL) == "on"
    assert _state(hass, CAUSE) == "Kitchen smoke"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    assert _state(hass, MASTER) == AlarmControlPanelState.DISARMED
    titles = [n["title"] for n in hass.data["persistent_notification"].values()]
    assert "Foyer: TECHNICAL ALARM" in titles

    refused = await _ws(client, {"type": "foyer/disarm"})
    assert refused["success"] is False  # nothing armed; and it clears nothing
    assert _state(hass, TECHNICAL) == "on"

    acked = await _ws(client, {"type": "foyer/acknowledge", "target": "technical"})
    assert acked["success"] is True
    assert acked["state"]["technical"][0]["acknowledged"] is True
    assert _state(hass, TECHNICAL) == "on"  # still detecting

    await _set(hass, SMOKE, "off", friendly_name="Kitchen smoke")
    assert _state(hass, TECHNICAL) == "off"
    assert _state(hass, CAUSE) == "none"


async def test_an_incident_is_exposed_and_closed_by_disarming(
    hass, loaded, hass_ws_client, freezer
):
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await _advance(hass, freezer, 30)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    state = hass.states.get(INCIDENT)
    assert state.state != "none"
    assert state.attributes["zones"] == ["Front door"]
    assert state.attributes["acknowledged"] is False

    client = await hass_ws_client(hass)
    status = await _ws(client, {"type": "foyer/status"})
    assert status["incident"]["id"] == state.state

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": MASTER},
        blocking=True,
    )
    assert _state(hass, INCIDENT) == "none"


async def test_nothing_to_acknowledge_is_a_structured_refusal(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": "foyer/acknowledge", "target": "incident"})
    assert (result["success"], result["reason"]) == (False, "nothing_to_acknowledge")


async def test_the_chime_plays_through_the_executor(hass, loaded, hass_ws_client):
    calls = async_mock_service(hass, "media_player", "play_media")
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    zone = dict(config["config"]["zones"][0], chime=True)
    assert (
        await _ws(client, {"type": "foyer/config/save", "kind": "zone", "item": zone})
    )["success"]
    await hass.async_block_till_done()
    chime = {
        "targets": [{"entity_id": "media_player.kitchen"}],
        "mode": "sound",
        "sound": "media-source://media_source/local/chime.mp3",
        "tts_entity": None,
        "volume": None,
        "quiet_start": None,
        "quiet_end": None,
        "during_exit": False,
    }
    assert (await _ws(client, {"type": "foyer/config/chime", "chime": chime}))[
        "success"
    ]
    await hass.async_block_till_done()

    await _set(hass, ZONE, "on", friendly_name="Front door")  # disarmed: chime
    assert len(calls) == 1
    assert calls[0].data["media_content_id"].endswith("chime.mp3")

    await _set(hass, ZONE, "off", friendly_name="Front door")
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": CHIME}, blocking=True
    )
    await _set(hass, ZONE, "on", friendly_name="Front door")
    assert len(calls) == 1  # silenced


async def test_the_chime_switch_survives_a_reload(hass, loaded):
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": CHIME}, blocking=True
    )
    assert await hass.config_entries.async_reload(loaded.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, CHIME) == "off"


async def test_a_group_is_saved_over_websocket(hass, loaded, hass_ws_client):
    await _set(hass, "binary_sensor.hall", "off", friendly_name="Hall")
    client = await hass_ws_client(hass)
    area_id = hass.data[DOMAIN].config.areas[0].id
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": {
                "name": "Hall",
                "entity_id": "binary_sensor.hall",
                "area_id": area_id,
                "type": "instant",
                "trigger": {"kind": "state", "states": ["on"]},
            },
            "trigger_confirmed": True,
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    door = hass.data[DOMAIN].config.zones[0].id

    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "group",
            "item": {
                "name": "Entrance",
                "area_id": area_id,
                "members": [door, saved["id"]],
                "n": 2,
                "window_seconds": 60,
            },
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    assert [g.name for g in hass.data[DOMAIN].config.groups] == ["Entrance"]
