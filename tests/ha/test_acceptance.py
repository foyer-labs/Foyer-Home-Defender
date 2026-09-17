"""Phase 1 acceptance: "a real house can be protected with it".

One file that walks every bullet of the Phase 1 "Done when", in a real Home
Assistant, against the real configuration API — not against the engine's
internals. The pure suite proves the decisions; this proves the house.

  1. multiple areas arm independently on a scenario
  2. a delayed zone grants entry delay while an instant one does not
  3. an open zone blocks, bypasses, waits or is ignored per its policy
  4. a verification group produces graduated response
  5. two zones in one break-in produce one incident
  6. a smoke detector fires while disarmed and survives a disarm
  7. every state change is in the log, with where and through which channel
  8. Home Assistant restarts mid-armed without losing the alarm
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.const import DOMAIN

from .conftest import MASTER, PANEL_ENTITY, ZONE
from .test_part2 import _advance, _set, _state, _ws

# The house this test builds on top of the one the config flow made.
HALL = "binary_sensor.hall_pir"
LANDING = "binary_sensor.landing_pir"
PATIO = "binary_sensor.patio_door"
WINDOW = "binary_sensor.bath_window"
SMOKE = "binary_sensor.kitchen_smoke"
SIREN = "siren.outdoor"

UPSTAIRS_PANEL = "alarm_control_panel.foyer_upstairs"


async def _zone(hass, client, item: dict) -> str:
    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": item,
            "trigger_confirmed": True,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    return result["id"]


async def _save(hass, client, kind: str, item: dict) -> str:
    result = await _ws(
        client, {"type": "foyer/config/save", "kind": kind, "item": item}
    )
    assert result["success"], result
    await hass.async_block_till_done()
    return result["id"]


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


@pytest.fixture
async def house(hass, hass_ws_client, loaded):
    """Two areas, five zones, one scenario, a group and a loud profile.

    Built entirely through the WebSocket API, so what is asserted afterwards
    is what a person could have configured from the panel.
    """
    client = await hass_ws_client(hass)
    for entity, name in (
        (HALL, "Hall motion"),
        (LANDING, "Landing motion"),
        (PATIO, "Patio door"),
        (WINDOW, "Bath window"),
        (SMOKE, "Kitchen smoke"),
    ):
        await _set(hass, entity, "off", friendly_name=name)
    hass.states.async_set(SIREN, "off", {"friendly_name": "Outdoor siren"})

    ground = (await _config(client))["areas"][0]
    ground_id = ground["id"]
    upstairs_id = await _save(
        hass,
        client,
        "area",
        {
            "name": "Upstairs",
            "ha_state_when_armed": "armed_night",
            "default_entry_delay": 30,
            "default_exit_delay": 30,
            "response_profile_id": None,
        },
    )

    # The front door from the config flow becomes the delayed way in.
    door = (await _config(client))["zones"][0]
    await _zone(hass, client, {**door, "type": "delayed", "entry_mode": "delayed"})

    hall_id = await _zone(
        hass,
        client,
        {
            "name": "Hall motion",
            "entity_id": HALL,
            "area_id": ground_id,
            "type": "follower",
            "trigger": {"kind": "state", "states": ["on"]},
        },
    )
    landing_id = await _zone(
        hass,
        client,
        {
            "name": "Landing motion",
            "entity_id": LANDING,
            "area_id": upstairs_id,
            "type": "instant",
            "trigger": {"kind": "state", "states": ["on"]},
        },
    )
    await _zone(
        hass,
        client,
        {
            "name": "Patio door",
            "entity_id": PATIO,
            "area_id": ground_id,
            "type": "instant",
            "arm_policy": "auto_bypass",
            "trigger": {"kind": "state", "states": ["on"]},
        },
    )
    await _zone(
        hass,
        client,
        {
            "name": "Kitchen smoke",
            "entity_id": SMOKE,
            "area_id": ground_id,
            "type": "technical",
            "trigger": {"kind": "state", "states": ["on"]},
        },
    )

    scenario = (await _config(client))["scenarios"][0]
    await _save(
        hass,
        client,
        "scenario",
        {**scenario, "name": "Away", "areas": [ground_id, upstairs_id]},
    )
    return {
        "client": client,
        "ground": ground_id,
        "upstairs": upstairs_id,
        "hall": hall_id,
        "landing": landing_id,
    }


async def _arm_scenario(hass, house, freezer) -> None:
    client = house["client"]
    scenario = (await _config(client))["scenarios"][0]
    result = await _ws(client, {"type": "foyer/arm", "scenario_id": scenario["id"]})
    assert result["success"], result
    await _advance(hass, freezer, 31)


async def _rows(client, **filters) -> list[dict]:
    return (await _ws(client, {"type": "foyer/log/query", **filters}))["rows"]


# --- 1. areas arm independently on a scenario ------------------------------------


async def test_a_scenario_arms_both_areas_and_each_keeps_its_own_state(
    hass, house, freezer
):
    await _arm_scenario(hass, house, freezer)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, UPSTAIRS_PANEL) == AlarmControlPanelState.ARMED_NIGHT
    # Disarming one area leaves the other armed: independent state (§4.1).
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    assert _state(hass, UPSTAIRS_PANEL) == AlarmControlPanelState.ARMED_NIGHT
    # A partially armed house is not a disarmed house (§13).
    assert _state(hass, MASTER) != AlarmControlPanelState.DISARMED


# --- 2. delayed grants the entry delay, instant does not -------------------------


async def test_the_front_door_grants_time_to_disarm_and_the_landing_does_not(
    hass, house, freezer
):
    await _arm_scenario(hass, house, freezer)

    await _set(hass, ZONE, "on")
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.PENDING
    # The hallway follows the door: it inherits the window, not a new one.
    await _set(hass, HALL, "on")
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.PENDING
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED

    # Upstairs is still armed, and its instant zone does not wait for anyone.
    await _set(hass, LANDING, "on")
    assert _state(hass, UPSTAIRS_PANEL) == AlarmControlPanelState.TRIGGERED


# --- 3. the four arm policies ----------------------------------------------------


async def test_an_open_zone_blocks_and_says_which_one(hass, house):
    await _set(hass, ZONE, "on")
    with pytest.raises(ServiceValidationError, match="Front door"):
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            {"entity_id": PANEL_ENTITY},
            blocking=True,
        )


async def test_an_auto_bypass_zone_arms_the_house_and_rejoins_when_it_closes(
    hass, house, freezer
):
    client = house["client"]
    await _set(hass, PATIO, "on")
    await _arm_scenario(hass, house, freezer)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    status = await _ws(client, {"type": "foyer/status"})
    patio = next(z for z in status["zones"] if z["entity_id"] == PATIO)
    assert patio["bypassed"] == "auto_bypass"

    await _set(hass, PATIO, "off")
    status = await _ws(client, {"type": "foyer/status"})
    patio = next(z for z in status["zones"] if z["entity_id"] == PATIO)
    assert patio["bypassed"] is None
    # And it protects again at once.
    await _set(hass, PATIO, "on")
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.TRIGGERED


async def test_a_zone_set_to_arm_after_closing_waits_for_the_door(hass, house, freezer):
    client = house["client"]
    config = await _config(client)
    patio = next(z for z in config["zones"] if z["entity_id"] == PATIO)
    await _zone(hass, client, {**patio, "arm_policy": "arm_after_closing"})

    await _set(hass, PATIO, "on")
    scenario = (await _config(client))["scenarios"][0]
    assert (await _ws(client, {"type": "foyer/arm", "scenario_id": scenario["id"]}))[
        "success"
    ]
    await _advance(hass, freezer, 31)
    # The exit delay is over and the door is still open: still arming, not armed.
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMING

    await _set(hass, PATIO, "off")
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


# --- 4. a verification group produces graduated response -------------------------


async def test_one_sensor_notifies_and_two_within_the_window_sound_the_siren(
    hass, house, freezer
):
    """The point of groups (§4.8): the member's profile below the threshold,
    the group's profile at it. One PIR notifies; two sound the siren."""
    client = house["client"]
    calls = async_mock_service(hass, "siren", "turn_on")

    loud = await _save(
        hass,
        client,
        "profile",
        {
            "name": "Full",
            "severity": 5,
            "actions": [
                {
                    "kind": "siren",
                    "moments": ["verification_satisfied"],
                    "name": "Outdoor siren",
                    "params": {"entity_ids": [SIREN], "duration": 60},
                    "conditions": [],
                    "condition_mode": "all",
                    "enabled": True,
                }
            ],
        },
    )
    await _save(
        hass,
        client,
        "group",
        {
            "name": "Open plan",
            "area_id": house["ground"],
            "members": [house["hall"], house["landing"]],
            "n": 2,
            "window_seconds": 60,
            "suppress_members": False,
            "response_profile_id": loud,
        },
    )

    await _arm_scenario(hass, house, freezer)
    await _set(hass, HALL, "on")
    assert not calls, "one member alone must not sound the siren"

    await _advance(hass, freezer, 10)
    await _set(hass, LANDING, "on")
    assert calls, "two members within the window must sound it"
    assert calls[0].data["entity_id"] == SIREN


# --- 5. one break-in, one incident -----------------------------------------------


async def test_two_zones_in_one_break_in_produce_one_incident(hass, house, freezer):
    client = house["client"]
    await _arm_scenario(hass, house, freezer)

    await _set(hass, PATIO, "on")
    first = hass.data[DOMAIN].state.incident
    assert first is not None
    await _advance(hass, freezer, 5)
    await _set(hass, LANDING, "on")

    incident = hass.data[DOMAIN].state.incident
    assert incident.id == first.id
    assert len(incident.zone_ids) == 2
    # And the log reads as one night, not as scattered rows.
    rows = await _rows(client, incident_id=incident.id)
    assert {r["event_type"] for r in rows} >= {"incident_opened", "incident_joined"}


# --- 6. the technical channel ----------------------------------------------------


async def test_a_smoke_detector_fires_while_disarmed_and_survives_a_disarm(hass, house):
    """§5.5: always live, never on alarm_control_panel, disarm does not clear it."""
    client = house["client"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED

    await _set(hass, SMOKE, "on")
    assert _state(hass, "binary_sensor.foyer_technical_alarm") == "on"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    assert _state(hass, MASTER) == AlarmControlPanelState.DISARMED

    # Arming and disarming the intrusion side has no authority here (§5.5).
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert _state(hass, "binary_sensor.foyer_technical_alarm") == "on"

    # It clears only on acknowledgement AND the detector returning to normal.
    await _ws(client, {"type": "foyer/acknowledge", "target": "technical"})
    assert _state(hass, "binary_sensor.foyer_technical_alarm") == "on"
    await _set(hass, SMOKE, "off")
    assert _state(hass, "binary_sensor.foyer_technical_alarm") == "off"


# --- 7. the log says what happened, where, and through what ----------------------


async def test_the_night_is_in_the_log_with_where_and_through_what(
    hass, house, freezer
):
    client = house["client"]
    await _arm_scenario(hass, house, freezer)
    await _set(hass, ZONE, "on")
    await _advance(hass, freezer, 31)  # entry delay runs out
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    rows = await _rows(client, limit=200)
    types = [r["event_type"] for r in rows]
    for expected in (
        "armed",
        "entry_started",
        "triggered",
        "incident_opened",
        "disarmed",
    ):
        assert expected in types, types
    # Every row of the night can be placed: through what it came, where it
    # happened, or which incident it belongs to. A row that is none of those
    # is a row nobody can read tomorrow morning.
    for row in rows:
        if row["category"] in {"arming", "alarm"}:
            assert row["channel"] or row["area_id"] or row["incident_id"], row
    armed = next(r for r in rows if r["event_type"] == "armed")
    assert armed["channel"] == "ha_ui"
    assert armed["area_id"] in {house["ground"], house["upstairs"]}
    # Users arrive in Phase 2; the column exists and is honestly empty.
    assert armed["user_name"] is None


# --- 8. a restart in the middle of an armed night --------------------------------


async def test_the_house_is_still_armed_after_a_restart_and_the_gap_is_logged(
    hass, house, entry, freezer
):
    client = house["client"]
    await _arm_scenario(hass, house, freezer)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, UPSTAIRS_PANEL) == AlarmControlPanelState.ARMED_NIGHT
    # And the log does not pretend the house was covered throughout.
    rows = await _rows(client, categories=["system"])
    assert [r for r in rows if r["event_type"] == "system_unavailable"]

    # It still protects: an instant zone fires straight away.
    await _set(hass, LANDING, "on")
    assert _state(hass, UPSTAIRS_PANEL) == AlarmControlPanelState.TRIGGERED
