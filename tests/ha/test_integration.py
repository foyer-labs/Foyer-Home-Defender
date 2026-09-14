"""End to end inside Home Assistant: entity, engine, store, WebSocket, panel."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import ServiceValidationError
import pytest

from custom_components.foyer.const import DOMAIN, PANEL_ICON, PANEL_URL_PATH
from custom_components.foyer.store.config_store import STORAGE_KEY
from custom_components.foyer.store.schema import STORAGE_MINOR_VERSION, STORAGE_VERSION

from .conftest import PANEL_ENTITY, ZONE


async def _call(hass, service: str) -> None:
    await hass.services.async_call(
        "alarm_control_panel",
        service,
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )


def _notifications(hass) -> list[dict]:
    return list(hass.data.get("persistent_notification", {}).values())


async def test_entity_starts_disarmed(hass, loaded):
    state = hass.states.get(PANEL_ENTITY)
    assert state is not None
    assert state.state == AlarmControlPanelState.DISARMED


async def test_arm_and_disarm_go_through_the_engine(hass, loaded):
    await _call(hass, "alarm_arm_away")
    await hass.async_block_till_done()

    state = hass.states.get(PANEL_ENTITY)
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    assert state.attributes["scenario_id"] is not None

    await _call(hass, "alarm_disarm")
    await hass.async_block_till_done()

    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.DISARMED


async def test_arm_is_refused_while_the_zone_is_open(hass, loaded):
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await _call(hass, "alarm_arm_away")

    assert err.value.translation_key == "rejected_zone_open"
    assert err.value.translation_placeholders == {"zones": "Front door"}
    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.DISARMED


async def test_arm_is_refused_while_the_zone_is_unavailable(hass, loaded):
    """INV-4: unavailable is a fault, never calm."""
    hass.states.async_set(ZONE, "unavailable")
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await _call(hass, "alarm_arm_away")

    assert err.value.translation_key == "rejected_zone_fault"


async def test_zone_trigger_while_armed_triggers_the_area(hass, loaded):
    await _call(hass, "alarm_arm_away")
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()

    assert hass.states.get(PANEL_ENTITY).state == AlarmControlPanelState.TRIGGERED


async def test_the_action_runs_through_the_executor(hass, loaded):
    hass.config.language = "it"
    await _call(hass, "alarm_arm_away")
    await hass.async_block_till_done()

    notes = _notifications(hass)
    assert len(notes) == 1
    assert notes[0]["title"] == "Foyer: inserito"
    assert "Fuori casa" in notes[0]["message"]


async def test_configuration_is_persisted_with_a_schema_version(
    hass, loaded, hass_storage
):
    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert stored["minor_version"] == STORAGE_MINOR_VERSION
    assert stored["data"]["areas"][0]["name"] == "Casa"
    assert stored["data"]["zones"][0]["trigger"] == {"kind": "state", "states": ["on"]}
    assert stored["data"]["code_policy"] == {"arm": False, "disarm": False}


async def test_stored_configuration_wins_over_the_entry_seed(hass, entry, hass_storage):
    """After the first run, .storage/foyer.config is the source of truth."""
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": STORAGE_MINOR_VERSION,
        "key": STORAGE_KEY,
        "data": {
            "areas": [
                {"id": "a", "name": "Garage", "ha_state_when_armed": "armed_away"}
            ],
            "zones": [
                {
                    "id": "z",
                    "name": "Shutter",
                    "entity_id": ZONE,
                    "area_id": "a",
                    "trigger": {"kind": "state", "states": ["on"]},
                }
            ],
            "scenarios": [
                {
                    "id": "s",
                    "name": "Out",
                    "areas": ["a"],
                    "ha_master_state": "armed_away",
                }
            ],
            "actions": [],
            "code_policy": {"arm": False, "disarm": False},
        },
    }
    hass.states.async_set(ZONE, "off")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("alarm_control_panel.foyer_garage") is not None


async def test_panel_is_registered_with_the_foyer_icon(hass, loaded):
    panels = hass.data["frontend_panels"]
    assert panels[PANEL_URL_PATH].sidebar_icon == PANEL_ICON


async def test_unload_removes_the_panel(hass, loaded):
    assert await hass.config_entries.async_unload(loaded.entry_id)
    assert PANEL_URL_PATH not in hass.data["frontend_panels"]
    assert DOMAIN not in hass.data


# --- WebSocket -------------------------------------------------------------------


async def test_ws_status(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/status"})
    msg = await client.receive_json()

    assert msg["success"]
    status = msg["result"]
    assert status["areas"][0]["state"] == "disarmed"
    assert status["areas"][0]["entity_id"] == PANEL_ENTITY
    assert status["zones"][0] == {
        "id": status["zones"][0]["id"],
        "name": "Front door",
        "area_id": status["areas"][0]["id"],
        "entity_id": ZONE,
        "state": "off",
        "fault": False,
        "open": False,
    }


async def test_ws_subscribe_pushes_live_changes(hass, loaded, hass_ws_client):
    """The panel reflects arming without reloading."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/subscribe"})
    assert (await client.receive_json())["success"]
    first = await client.receive_json()
    assert first["event"]["areas"][0]["state"] == "disarmed"

    await _call(hass, "alarm_arm_away")
    update = await client.receive_json()

    assert update["event"]["areas"][0]["state"] == "armed"
    assert update["event"]["active_scenario_id"] is not None


async def test_ws_translations_follow_the_language(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/translations", "language": "it"})
    msg = await client.receive_json()

    assert msg["result"]["language"] == "it"
    assert msg["result"]["strings"]["help"]["overview"]["title"]

    await client.send_json({"id": 2, "type": "foyer/translations", "language": "de"})
    msg = await client.receive_json()
    assert msg["result"]["language"] == "en"
