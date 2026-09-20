"""Phase 5 part 1 inside Home Assistant: system health (SPEC §12).

The pure suite proves the arithmetic — how many zones went quiet inside one
window, how many sends failed in a row, how many pings were missed. This
proves the half only a real Home Assistant can: that the two entities of §13
exist and are not deleted again as stale at the next start, that the
watchdog's ping actually leaves with nothing in it, that the sweep notices a
`notify` service somebody removed in an update, that the persistent problems
become repair issues in Settings, and that the download button answers with a
document carrying no names.
"""

from __future__ import annotations

from homeassistant.helpers import issue_registry as ir
import pytest

from custom_components.foyer import repairs
from custom_components.foyer.const import DOMAIN
from custom_components.foyer.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import ZONE
from .test_part2 import _set, _ws

HEALTH_SENSOR = "binary_sensor.foyer_system_health"
PING = "https://hc-ping.example/token"


def _system(hass):
    return hass.data[DOMAIN]


async def _save_health(hass, client, **overrides) -> dict:
    """The health block as page 14 saves it."""
    health = {
        "mains_entity_id": None,
        "mains_lost_states": ["on"],
        "watchdog": {
            "enabled": False,
            "url": "",
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": False,
        },
        "radios": [],
        "rf_zones": 4,
        "rf_window": 60,
        "rf_confirm": 60,
        "channel_sweep": 900,
        "channel_failures": 2,
        "repair_after": 172800,
        **overrides,
    }
    result = await _ws(client, {"type": "foyer/config/health", "health": health})
    assert result["success"], result
    await hass.async_block_till_done()
    return result


# --- the entities of §13 ----------------------------------------------------------


async def test_the_system_health_sensor_exists_and_says_what_is_wrong(
    hass, loaded, hass_ws_client
):
    state = hass.states.get(HEALTH_SENSOR)
    assert state is not None
    assert state.state == "off"

    await _set(hass, ZONE, "unavailable")
    await hass.async_block_till_done()
    state = hass.states.get(HEALTH_SENSOR)
    assert state.state == "on"
    assert "zone_fault" in state.attributes["causes"]


async def test_the_health_entities_survive_a_restart_rather_than_being_stale(
    hass, loaded, hass_ws_client
):
    """An entity missing from expected_unique_ids is created at every start
    and deleted again as stale, which is a sensor that never appears."""
    from custom_components.foyer.entity.common import expected_unique_ids

    client = await hass_ws_client(hass)
    await _save_health(
        hass,
        client,
        radios=[
            {
                "id": "zigbee",
                "name": "Zigbee",
                "entry_id": "entry_zha",
                "coordinator_entity_id": "sensor.zha_coordinator",
                "n_zones": None,
                "window": None,
                "enabled": True,
            }
        ],
    )
    system = _system(hass)
    expected = expected_unique_ids("entry", system.config)
    assert "entry_system_health" in expected
    assert "entry_rf_interference_zigbee" in expected
    assert hass.states.get("binary_sensor.foyer_rf_interference_zigbee") is not None


# --- the external watchdog (§12.3) ------------------------------------------------


async def test_the_heartbeat_leaves_with_nothing_in_it(
    hass, loaded, hass_ws_client, aioclient_mock
):
    """P-1 and §19: the ping carries no data unless somebody turned it on."""
    client = await hass_ws_client(hass)
    aioclient_mock.get(PING, text="OK")
    await _save_health(
        hass,
        client,
        watchdog={
            "enabled": True,
            "url": PING,
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": False,
        },
    )
    await _system(hass)._async_watchdog()
    await hass.async_block_till_done()

    assert aioclient_mock.call_count == 1
    method, _url, data, _headers = aioclient_mock.mock_calls[0]
    assert method == "GET"
    assert not data
    assert _system(hass).state.health.watchdog.ever_ok


async def test_a_payload_that_was_asked_for_says_the_least_that_works(
    hass, loaded, hass_ws_client, aioclient_mock
):
    client = await hass_ws_client(hass)
    aioclient_mock.post(PING, text="OK")
    await _save_health(
        hass,
        client,
        watchdog={
            "enabled": True,
            "url": PING,
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": True,
        },
    )
    await _system(hass)._async_watchdog()
    await hass.async_block_till_done()

    _method, _url, data, _headers = aioclient_mock.mock_calls[0]
    assert set(data) == {"armed_areas", "areas", "healthy"}


async def test_three_missed_pings_are_reported_locally(
    hass, loaded, hass_ws_client, aioclient_mock
):
    client = await hass_ws_client(hass)
    aioclient_mock.get(PING, status=500)
    await _save_health(
        hass,
        client,
        watchdog={
            "enabled": True,
            "url": PING,
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": False,
        },
    )
    for _ in range(3):
        await _system(hass)._async_watchdog()
    await hass.async_block_till_done()

    health = _system(hass).state.health.watchdog
    assert health.failures == 3
    assert health.down_since is not None
    assert "500" in health.last_error
    assert "watchdog_unreachable" in hass.states.get(HEALTH_SENSOR).attributes["causes"]


async def test_nothing_is_pinged_while_home_assistant_is_still_starting(
    hass, loaded, hass_ws_client, aioclient_mock
):
    """A ping that fails because the network stack is not up yet is a failure
    about Home Assistant's boot order, not about the watchdog."""
    client = await hass_ws_client(hass)
    aioclient_mock.get(PING, text="OK")
    await _save_health(
        hass,
        client,
        watchdog={
            "enabled": True,
            "url": PING,
            "interval": 900,
            "timeout": 30,
            "failures": 3,
            "payload": False,
        },
    )
    system = _system(hass)
    system.settling = True
    await system._async_watchdog()
    assert aioclient_mock.call_count == 0


# --- notification channel health (§12.2) ------------------------------------------


async def _contact(hass, client, service: str = "notify.mobile_app_luca") -> str:
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "name": "Luca",
                "channels": [
                    {"id": "push", "kind": "push", "service": service},
                    {"id": "sms", "kind": "sms", "service": "notify.gsm"},
                ],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    return _system(hass).config.contacts[0].id


async def test_a_service_removed_in_an_update_is_found_by_the_sweep(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)

    async def noop(call):
        return None

    hass.services.async_register("notify", "gsm", noop)
    await _contact(hass, client)
    # notify.mobile_app_luca is not registered: the integration was removed.
    await _system(hass)._async_channel_sweep()
    await hass.async_block_till_done()

    status = _system(hass).health_status()
    broken = [c for c in status["channels"] if c["fault"]]
    assert [c["service"] for c in broken] == ["notify.mobile_app_luca"]
    assert broken[0]["fault"] == "missing_service"
    assert "channel_down" in hass.states.get(HEALTH_SENSOR).attributes["causes"]


async def test_the_page_says_which_working_channel_the_warning_went_over(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)

    async def noop(call):
        return None

    hass.services.async_register("notify", "gsm", noop)
    contact_id = await _contact(hass, client)
    await _system(hass)._async_channel_sweep()
    await hass.async_block_till_done()

    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["system"]})
    down = [r for r in rows["rows"] if r["event_type"] == "notification_channel_down"]
    assert down, rows["rows"]
    assert down[0]["detail"]["over_contact_id"] == contact_id
    assert down[0]["detail"]["over_channel_id"] == "sms"


# --- page 14 ----------------------------------------------------------------------


async def test_the_page_is_open_to_whoever_may_read_the_log(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)
    status = await _ws(client, {"type": "foyer/health"})
    assert set(status) >= {"causes", "mains", "watchdog", "channels", "radios"}


async def test_the_radio_picker_offers_only_entries_that_back_a_zone(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": "foyer/health/radios"})
    # The test zone is a bare state with no entity registry entry behind it,
    # so the honest answer is an empty list rather than a menu of
    # integrations that are not radios.
    assert result["radios"] == []


async def test_a_radio_with_no_coordinator_is_refused(hass, loaded, hass_ws_client):
    """The gate is what makes the heuristic worth having (§12.5)."""
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {
            "type": "foyer/config/health",
            "health": {
                "mains_entity_id": None,
                "mains_lost_states": ["on"],
                "watchdog": {
                    "enabled": False,
                    "url": "",
                    "interval": 900,
                    "timeout": 30,
                    "failures": 3,
                    "payload": False,
                },
                "radios": [
                    {
                        "id": "zigbee",
                        "name": "Zigbee",
                        "entry_id": "entry_zha",
                        "coordinator_entity_id": None,
                        "n_zones": None,
                        "window": None,
                        "enabled": True,
                    }
                ],
                "rf_zones": 4,
                "rf_window": 60,
                "rf_confirm": 60,
                "channel_sweep": 900,
                "channel_failures": 2,
                "repair_after": 172800,
            },
        },
    )
    assert not result["success"]
    assert any(p["code"] == "coordinator_required" for p in result["problems"])


async def test_a_watchdog_without_a_url_is_refused(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {
            "type": "foyer/config/health",
            "health": {
                "mains_entity_id": None,
                "mains_lost_states": ["on"],
                "watchdog": {
                    "enabled": True,
                    "url": "",
                    "interval": 900,
                    "timeout": 30,
                    "failures": 3,
                    "payload": False,
                },
                "radios": [],
                "rf_zones": 4,
                "rf_window": 60,
                "rf_confirm": 60,
                "channel_sweep": 900,
                "channel_failures": 2,
                "repair_after": 172800,
            },
        },
    )
    assert not result["success"]
    assert any(p["code"] == "watchdog_url_required" for p in result["problems"])


# --- repairs and diagnostics (§12.4) ----------------------------------------------


async def test_a_broken_channel_becomes_a_repair_issue_and_goes_away_again(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)

    async def noop(call):
        return None

    hass.services.async_register("notify", "gsm", noop)
    await _contact(hass, client)
    await _system(hass)._async_channel_sweep()
    await hass.async_block_till_done()
    _system(hass).async_reconcile_issues()

    registry = ir.async_get(hass)
    issues = [i for (d, i) in registry.issues if d == DOMAIN]
    assert any(i.startswith(repairs.CHANNEL_BROKEN) for i in issues)

    hass.services.async_register("notify", "mobile_app_luca", noop)
    await _system(hass)._async_channel_sweep()
    await hass.async_block_till_done()
    _system(hass).async_reconcile_issues()

    issues = [i for (d, i) in registry.issues if d == DOMAIN]
    assert not any(i.startswith(repairs.CHANNEL_BROKEN) for i in issues)


async def test_every_repair_issue_can_be_marked_as_seen(hass, loaded):
    """Part 1 decision 10: all of them are fixable, and fixing one is saying
    you have seen it."""
    flow = await repairs.async_create_fix_flow(hass, "channel_broken_x", None)
    assert flow is not None


async def test_the_diagnostics_download_carries_no_names(
    hass, loaded, hass_ws_client, entry
):
    client = await hass_ws_client(hass)
    await _contact(hass, client)
    document = await async_get_config_entry_diagnostics(hass, entry)
    text = str(document)
    assert "Luca" not in text
    assert "notify.mobile_app_luca" not in text
    assert ZONE not in text
    assert document["config"]["zones"][0]["entity"].startswith("binary_sensor.zone_")
    assert document["integration"]["config_schema"] == "7.2"


@pytest.mark.parametrize("language", ["en", "it"])
def test_every_repair_issue_has_its_strings(language: str):
    """Repair issues need their own `issues` section, which hassfest
    validates against a closed schema (decision 35's problem, in a new
    place)."""
    import json
    import pathlib

    path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "custom_components/foyer/translations"
        / f"{language}.json"
    )
    issues = json.loads(path.read_text(encoding="utf-8"))["issues"]
    for key in (
        repairs.ZONE_UNREACHABLE,
        repairs.CHANNEL_BROKEN,
        repairs.WATCHDOG_NEVER_WORKED,
        repairs.WATCHDOG_UNREACHABLE,
        repairs.RF_INTERFERENCE,
        repairs.COORDINATOR_DOWN,
        repairs.MAINS_LOST,
    ):
        assert key in issues, key
        assert "title" in issues[key]
        assert "confirm" in issues[key]["fix_flow"]["step"]
