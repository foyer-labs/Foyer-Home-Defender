"""End to end inside Home Assistant: entities, engine, stores, WebSocket, panel."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.foyer.const import DOMAIN, PANEL_ICON, PANEL_URL_PATH
from custom_components.foyer.store.config_store import STORAGE_KEY
from custom_components.foyer.store.migrations import migrate
from custom_components.foyer.store.schema import STORAGE_MINOR_VERSION, STORAGE_VERSION
from custom_components.foyer.store.state_store import STATE_KEY

from .conftest import MASTER, PANEL_ENTITY, SELECT, ZONE

PHASE_0_DOCUMENT = {
    "version": 1,
    "minor_version": 1,
    "key": STORAGE_KEY,
    "data": {
        "areas": [{"id": "a", "name": "Garage", "ha_state_when_armed": "armed_away"}],
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
            {"id": "s", "name": "Out", "areas": ["a"], "ha_master_state": "armed_away"}
        ],
        "actions": [
            {
                "id": "n",
                "kind": "notification",
                "moments": ["armed", "disarmed", "zone_fault"],
            }
        ],
        "code_policy": {"arm": False, "disarm": False},
    },
}


async def _call(hass, service: str, entity_id: str = PANEL_ENTITY, **data) -> None:
    await hass.services.async_call(
        "alarm_control_panel",
        service,
        {"entity_id": entity_id, **data},
        blocking=True,
    )


async def _advance(hass, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def _state(hass, entity_id: str = PANEL_ENTITY) -> str:
    return hass.states.get(entity_id).state


def _notifications(hass) -> list[dict]:
    return list(hass.data.get("persistent_notification", {}).values())


# --- arming ----------------------------------------------------------------------


async def test_entities_start_disarmed(hass, loaded):
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert _state(hass, MASTER) == AlarmControlPanelState.DISARMED
    assert _state(hass, SELECT) == "unknown"
    assert _state(hass, "binary_sensor.foyer_ready_to_arm") == "on"


async def test_area_arms_through_its_exit_delay(hass, loaded, freezer):
    await _call(hass, "alarm_arm_away")
    assert _state(hass) == AlarmControlPanelState.ARMING
    assert int(_state(hass, "sensor.foyer_countdown_casa")) == 30

    await _advance(hass, freezer, 30)

    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, "sensor.foyer_countdown_casa") == "0"
    # Armed on its own panel: outside any scenario, so the master is custom.
    assert _state(hass, MASTER) == AlarmControlPanelState.ARMED_CUSTOM_BYPASS


async def test_scenario_select_arms_and_the_master_reports_its_mode(
    hass, loaded, freezer
):
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Fuori casa"},
        blocking=True,
    )
    await _advance(hass, freezer, 30)

    assert _state(hass, SELECT) == "Fuori casa"
    assert _state(hass, MASTER) == AlarmControlPanelState.ARMED_AWAY


async def test_master_arm_and_disarm(hass, loaded, freezer):
    await _call(hass, "alarm_arm_away", MASTER)
    await _advance(hass, freezer, 30)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY

    await _call(hass, "alarm_disarm", MASTER)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_arm_is_refused_while_the_zone_is_open(hass, loaded):
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await _call(hass, "alarm_arm_away")

    assert err.value.translation_key == "rejected_zone_open"
    assert err.value.translation_placeholders == {"zones": "Front door"}
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert _state(hass, "binary_sensor.foyer_ready_to_arm") == "off"


async def test_arm_is_refused_while_the_zone_is_unavailable(hass, loaded):
    """INV-4: unavailable is a fault, never calm."""
    hass.states.async_set(ZONE, "unavailable")
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await _call(hass, "alarm_arm_away")

    assert err.value.translation_key == "rejected_zone_fault"
    assert _state(hass, "binary_sensor.foyer_fault") == "on"


async def test_zone_trigger_while_armed_triggers_and_cuts_off(hass, loaded, freezer):
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()

    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    assert _state(hass, "binary_sensor.foyer_zone_front_door") == "on"

    await _advance(hass, freezer, 180)
    state = hass.states.get(PANEL_ENTITY)
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    assert state.attributes["alarm_memory"] is True


async def test_the_action_runs_through_the_executor(hass, loaded, freezer):
    hass.config.language = "it"
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)

    notes = _notifications(hass)
    assert len(notes) == 1
    assert notes[0]["title"] == "Foyer: inserito"
    assert "Casa" in notes[0]["message"]


# --- persistence (INV-3) ------------------------------------------------------------


async def test_state_survives_a_reload(hass, loaded, freezer):
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)

    assert await hass.config_entries.async_reload(loaded.entry_id)
    await hass.async_block_till_done()

    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_state_is_restored_from_storage_on_start(
    hass, entry, hass_storage, freezer
):
    """A restart mid-armed does not lose the alarm, and a timer that ran out
    while Home Assistant was down fires on start."""
    hass.states.async_set(ZONE, "off", {"friendly_name": "Front door"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _call(hass, "alarm_arm_away")
    await _advance(hass, freezer, 30)
    hass.states.async_set(ZONE, "on", {"friendly_name": "Front door"})
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    assert await hass.config_entries.async_unload(entry.entry_id)
    saved = hass_storage[STATE_KEY]["data"]
    area_id = next(iter(saved["state"]["areas"]))
    assert saved["state"]["areas"][area_id]["state"] == "triggered"
    assert saved["alive_at"]

    freezer.tick(timedelta(minutes=10))  # down for ten minutes, siren long over
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(PANEL_ENTITY)
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    assert state.attributes["alarm_memory"] is True


async def test_state_is_saved_immediately(hass, loaded, hass_storage):
    await _call(hass, "alarm_arm_away")
    await hass.async_block_till_done()
    area = next(iter(hass_storage[STATE_KEY]["data"]["state"]["areas"].values()))
    assert area["state"] == "arming"


# --- stored configuration -------------------------------------------------------------


async def test_configuration_is_persisted_with_a_schema_version(
    hass, loaded, hass_storage
):
    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert stored["minor_version"] == STORAGE_MINOR_VERSION
    assert stored["data"]["areas"][0]["name"] == "Casa"
    assert stored["data"]["zones"][0]["trigger"] == {"kind": "state", "states": ["on"]}


async def test_a_phase_0_installation_is_migrated_not_reset(hass, entry, hass_storage):
    """Real installations have a 1.1 document: it migrates, and behaves as before."""
    hass_storage[STORAGE_KEY] = PHASE_0_DOCUMENT
    hass.states.async_set(ZONE, "off")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    garage = "alarm_control_panel.foyer_garage"
    await _call(hass, "alarm_arm_away", garage)
    assert _state(hass, garage) == AlarmControlPanelState.ARMED_AWAY  # no exit delay

    system = hass.data[DOMAIN]
    assert system.config.zones[0].name == "Shutter"
    assert hass_storage[STORAGE_KEY]["version"] == STORAGE_VERSION


async def test_panel_is_registered_with_the_foyer_icon(hass, loaded):
    panels = hass.data["frontend_panels"]
    assert panels[PANEL_URL_PATH].sidebar_icon == PANEL_ICON


async def test_unload_removes_the_panel(hass, loaded):
    assert await hass.config_entries.async_unload(loaded.entry_id)
    assert PANEL_URL_PATH not in hass.data["frontend_panels"]
    assert DOMAIN not in hass.data


# --- WebSocket ------------------------------------------------------------------------


async def test_ws_status(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/status"})
    status = (await client.receive_json())["result"]

    assert status["areas"][0]["state"] == "disarmed"
    assert status["areas"][0]["entity_id"] == PANEL_ENTITY
    assert status["areas"][0]["ready"] is True
    assert status["master"] == {"state": "disarmed", "mode": None}
    zone = status["zones"][0]
    assert (zone["name"], zone["state"], zone["fault"], zone["open"]) == (
        "Front door",
        "off",
        None,
        False,
    )


async def test_ws_subscribe_pushes_live_changes(hass, loaded, hass_ws_client):
    """The panel reflects arming without reloading."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/subscribe"})
    assert (await client.receive_json())["success"]
    first = await client.receive_json()
    assert first["event"]["areas"][0]["state"] == "disarmed"

    await _call(hass, "alarm_arm_away")
    update = await client.receive_json()
    assert update["event"]["areas"][0]["state"] == "arming"
    assert update["event"]["areas"][0]["timer"]["kind"] == "exit"


async def test_ws_arm_reports_the_blocking_zone(hass, loaded, hass_ws_client):
    hass.states.async_set(ZONE, "on", {"friendly_name": "Front door"})
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id

    await client.send_json({"id": 1, "type": "foyer/arm", "scenario_id": scenario_id})
    result = (await client.receive_json())["result"]
    assert result["success"] is False
    assert result["reason"] == "zone_open"
    assert result["blocking_zones"][0]["name"] == "Front door"

    await client.send_json(
        {"id": 2, "type": "foyer/arm", "scenario_id": scenario_id, "force": True}
    )
    result = (await client.receive_json())["result"]
    assert result["success"] is True
    assert result["state"]["zones"][0]["bypassed"] == "forced"


async def test_ws_translations_follow_the_language(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/translations", "language": "it"})
    msg = await client.receive_json()
    assert msg["result"]["language"] == "it"
    assert msg["result"]["strings"]["help"]["overview"]["title"]

    await client.send_json({"id": 2, "type": "foyer/translations", "language": "de"})
    assert (await client.receive_json())["result"]["language"] == "en"


async def test_ws_config_edit_creates_an_area_and_its_entity(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "foyer/config/save",
            "kind": "area",
            "item": {"name": "Upstairs", "ha_state_when_armed": "armed_night"},
        }
    )
    result = (await client.receive_json())["result"]
    assert result["success"], result
    await hass.async_block_till_done()

    assert hass.states.get("alarm_control_panel.foyer_upstairs") is not None
    assert hass.states.get("sensor.foyer_countdown_upstairs") is not None


async def test_ws_zone_save_requires_confirmed_trigger(hass, loaded, hass_ws_client):
    """INV-5 is enforced in the backend: the client cannot skip confirmation."""
    client = await hass_ws_client(hass)
    area_id = hass.data[DOMAIN].config.areas[0].id
    item = {
        "name": "Kitchen window",
        "entity_id": "binary_sensor.kitchen_window",
        "area_id": area_id,
        "type": "instant",
        "trigger": {"kind": "state", "states": ["on"]},
    }
    await client.send_json(
        {"id": 1, "type": "foyer/config/save", "kind": "zone", "item": item}
    )
    result = (await client.receive_json())["result"]
    assert result["success"] is False
    assert result["problems"][0]["code"] == "trigger_not_confirmed"

    await client.send_json(
        {
            "id": 2,
            "type": "foyer/config/save",
            "kind": "zone",
            "item": item,
            "trigger_confirmed": True,
        }
    )
    assert (await client.receive_json())["result"]["success"]
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.foyer_zone_kitchen_window") is not None


async def test_ws_config_edit_is_refused_while_armed(hass, loaded, hass_ws_client):
    await _call(hass, "alarm_arm_away")
    client = await hass_ws_client(hass)
    area = dict(next(a for a in (await _config(client))["config"]["areas"]))
    area["default_entry_delay"] = 10
    await client.send_json(
        {"id": 9, "type": "foyer/config/save", "kind": "area", "item": area}
    )
    result = (await client.receive_json())["result"]
    assert result["success"] is False
    assert result["problems"][0]["code"] == "area_not_disarmed"


async def _config(client) -> dict:
    await client.send_json({"id": 8, "type": "foyer/config"})
    return (await client.receive_json())["result"]


async def test_ws_config_is_admin_only(
    hass, loaded, hass_ws_client, hass_read_only_access_token
):
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json({"id": 1, "type": "foyer/config"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"


async def test_ws_propose_zone(hass, loaded, hass_ws_client):
    hass.states.async_set("binary_sensor.back_door", "off", {"device_class": "door"})
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "foyer/zone/propose", "entity_id": "binary_sensor.back_door"}
    )
    result = (await client.receive_json())["result"]
    assert result["zone_type"] == "delayed"
    assert result["proposed"] == ["on"]


async def test_ws_prefs_follow_the_user(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "foyer/prefs/set", "prefs": {"help": {"zones": False}}}
    )
    assert (await client.receive_json())["result"] == {"help": {"zones": False}}
    await client.send_json({"id": 2, "type": "foyer/prefs"})
    assert (await client.receive_json())["result"]["help"] == {"zones": False}


async def test_supervision_heartbeat(hass, entry, hass_storage, freezer):
    """A zone that keeps reporting the same state is alive (decision 11)."""
    document = migrate(
        (1, 1), (STORAGE_VERSION, STORAGE_MINOR_VERSION), PHASE_0_DOCUMENT["data"]
    )
    document["zones"][0]["supervision_timeout"] = 600
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": STORAGE_MINOR_VERSION,
        "key": STORAGE_KEY,
        "data": document,
    }
    hass.states.async_set(ZONE, "off")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for _ in range(3):
        await _advance(hass, freezer, 500)
        hass.states.async_set(ZONE, "off")  # same state: a report, not a change
        await hass.async_block_till_done()
    assert _state(hass, "binary_sensor.foyer_fault") == "off"

    await _advance(hass, freezer, 601)
    assert _state(hass, "binary_sensor.foyer_fault") == "on"

    hass.states.async_set(ZONE, "off")  # it speaks again: the fault clears
    await hass.async_block_till_done()
    assert _state(hass, "binary_sensor.foyer_fault") == "off"


async def test_ws_subscription_survives_a_configuration_reload(
    hass, loaded, hass_ws_client
):
    """The panel that saved a change keeps receiving live state afterwards."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "foyer/subscribe"})
    assert (await client.receive_json())["success"]
    await client.receive_json()  # the initial status

    await client.send_json(
        {
            "id": 2,
            "type": "foyer/config/save",
            "kind": "area",
            "item": {"name": "Attic"},
        }
    )
    names: set[str] = set()
    for _ in range(20):
        msg = await client.receive_json()
        if msg.get("id") == 1 and "event" in msg:
            names = {a["name"] for a in msg["event"]["areas"]}
            if "Attic" in names:
                break
    assert "Attic" in names
