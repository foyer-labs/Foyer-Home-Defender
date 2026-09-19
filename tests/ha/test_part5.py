"""Phase 3 part 1 inside Home Assistant: page 9's two reads (§11.1, §11.2).

The pure suite proves what the table says and what the trace contains
(tests/core/test_diagnostics.py, tests/core/test_simulate.py). This proves the
part only a real Home Assistant can: that the live states reach them, that the
gate in front of them is the one that was chosen deliberately — a read, not an
edit — and that a simulation run leaves a row behind and changes nothing in
the house.
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY, ZONE
from .test_part2 import _set, _state, _ws

BATTERY = "sensor.front_door_battery"


async def _diagnostics(client) -> dict:
    return await _ws(client, {"type": "foyer/diagnostics"})


async def _zone_row(client, zone_id: str) -> dict:
    result = await _diagnostics(client)
    return next(z for z in result["zones"] if z["zone_id"] == zone_id)


def _the_zone(hass) -> str:
    return hass.data[DOMAIN].config.zones[0].id


# --- diagnostics (§11.1) -----------------------------------------------------------


async def test_the_table_carries_the_live_state_of_every_mapped_zone(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    result = await _diagnostics(client)
    assert [z["entity_id"] for z in result["zones"]] == [ZONE]
    row = result["zones"][0]
    assert row["state"] == "off"
    assert row["triggered"] is False
    assert row["available"] is True
    assert row["last_changed"] is not None


async def test_the_trigger_evaluation_follows_the_entity(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on")
    row = await _zone_row(client, _the_zone(hass))
    assert (row["state"], row["triggered"]) == ("on", True)


async def test_an_unavailable_zone_is_a_fault_and_blocks_arming(
    hass, hass_ws_client, loaded
):
    """INV-4 seen from the page a household actually opens."""
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "unavailable")
    row = await _zone_row(client, _the_zone(hass))
    assert row["fault"] == "unavailable"
    assert row["blocks_arming"] is True
    assert row["blocks_because"] == "fault"


async def test_a_renamed_entity_is_named_once_rather_than_left_to_guess(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    hass.states.async_remove(ZONE)
    await hass.async_block_till_done()
    result = await _diagnostics(client)
    assert result["missing_entities"] == [ZONE]


async def test_a_battery_reaches_the_table_from_the_entity_that_reports_it(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    await _set(hass, BATTERY, "11")
    zone = hass.data[DOMAIN].config.zones[0]
    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": {
                **_zone_document(zone),
                "battery_entity_id": BATTERY,
            },
            "trigger_confirmed": True,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()

    row = await _zone_row(client, zone.id)
    assert row["battery_entity_id"] == BATTERY
    assert row["battery_level"] == 11.0
    assert row["battery_low"] is True
    # And it warns without blocking: the arming goes ahead (part 1 decision 2).
    assert row["blocks_arming"] is False


def _zone_document(zone) -> dict:
    from custom_components.foyer.store.schema import zone_to_dict

    return zone_to_dict(zone)


async def test_signal_quality_is_shown_when_the_entity_exposes_it(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "off", linkquality=128)
    row = await _zone_row(client, _the_zone(hass))
    assert row["signal"] == {"value": 128.0, "unit": "lqi"}


# --- the simulator (§11.2) ---------------------------------------------------------


async def test_a_run_answers_with_a_trace_and_changes_nothing_in_the_house(
    hass, hass_ws_client, loaded
):
    """The whole promise: the house is disarmed before and after."""
    client = await hass_ws_client(hass)
    scenario = hass.data[DOMAIN].config.scenarios[0]
    before = _state(hass, PANEL_ENTITY)

    result = await _ws(
        client,
        {
            "type": "foyer/simulate",
            "scenario_id": scenario.id,
            "zones": [{"zone_id": _the_zone(hass), "state": "on", "at": 60}],
        },
    )
    await hass.async_block_till_done()

    moments = [
        o["moment"] for step in result["steps"] for o in step["occurrences"]
    ]
    assert "armed" in moments
    assert "triggered" in moments
    assert _state(hass, PANEL_ENTITY) == before == AlarmControlPanelState.DISARMED
    assert hass.data[DOMAIN].state.active_scenario_id is None


async def test_a_run_executes_nothing(hass, hass_ws_client, loaded):
    """Not "no action was configured": no service call left the process."""
    calls = []

    async def record(call):
        calls.append(call)

    hass.services.async_register("persistent_notification", "create", record)
    client = await hass_ws_client(hass)
    scenario = hass.data[DOMAIN].config.scenarios[0]
    await _ws(
        client,
        {
            "type": "foyer/simulate",
            "scenario_id": scenario.id,
            "zones": [{"zone_id": _the_zone(hass), "state": "on", "at": 60}],
        },
    )
    await hass.async_block_till_done()
    assert calls == []


async def test_the_trace_shows_which_profile_answered_and_where_it_came_from(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    scenario = hass.data[DOMAIN].config.scenarios[0]
    result = await _ws(
        client,
        {
            "type": "foyer/simulate",
            "scenario_id": scenario.id,
            "zones": [{"zone_id": _the_zone(hass), "state": "on", "at": 60}],
        },
    )
    triggered = next(
        step
        for step in result["steps"]
        if any(o["moment"] == "triggered" for o in step["occurrences"])
    )
    [batch] = [b for b in triggered["batches"] if b["moment"] == "triggered"]
    assert batch["source"] == "default"
    assert batch["actions"]
    assert all(a["ran"] for a in batch["actions"])


async def test_a_run_is_logged_under_system_with_its_inputs(
    hass, hass_ws_client, loaded
):
    """§11.2: so a configuration change can be justified after the fact."""
    client = await hass_ws_client(hass)
    scenario = hass.data[DOMAIN].config.scenarios[0]
    await _ws(
        client,
        {
            "type": "foyer/simulate",
            "scenario_id": scenario.id,
            "zones": [{"zone_id": _the_zone(hass), "state": "on", "at": 60}],
        },
    )
    await hass.async_block_till_done()

    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["system"]})
    run = next(r for r in rows["rows"] if r["event_type"] == "simulation_run")
    assert run["detail"]["scenario_id"] == scenario.id
    assert run["detail"]["zones"] == [
        {"zone_id": _the_zone(hass), "state": "on", "at": 60}
    ]


async def test_a_run_on_a_house_that_would_refuse_to_arm_says_so(
    hass, hass_ws_client, loaded
):
    """The most useful answer of all, and it costs nothing to ask for."""
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on")
    scenario = hass.data[DOMAIN].config.scenarios[0]
    result = await _ws(
        client, {"type": "foyer/simulate", "scenario_id": scenario.id}
    )
    refused = next(s for s in result["steps"] if not s["accepted"])
    assert refused["reason"] == "zone_open"
    assert refused["blocking_zones"] == [_the_zone(hass)]


async def test_the_hypothetical_clock_is_honoured(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    scenario = hass.data[DOMAIN].config.scenarios[0]
    result = await _ws(
        client,
        {
            "type": "foyer/simulate",
            "scenario_id": scenario.id,
            "start": "2026-01-01T03:00:00+00:00",
        },
    )
    assert result["steps"][0]["at"].startswith("2026-01-01T03:00")


# --- the gate, chosen deliberately -------------------------------------------------


@pytest.mark.parametrize("command", ["foyer/diagnostics", "foyer/simulate"])
async def test_both_are_reads_and_neither_asks_for_a_code(
    hass, hass_ws_client, loaded, command
):
    """§8.2 asks for a code to *edit* the configuration. Demanding one to open
    a page teaches a household to keep the code on a sticky note."""
    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": command})
    assert result is not None


@pytest.mark.parametrize("command", ["foyer/diagnostics", "foyer/simulate"])
async def test_neither_is_offered_to_somebody_who_may_not_read_the_log(
    hass, hass_ws_client, hass_read_only_access_token, loaded, command
):
    """view_log, not edit_config: what these reveal is what the log reveals."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json({"id": 7, "type": command})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_permitted"
