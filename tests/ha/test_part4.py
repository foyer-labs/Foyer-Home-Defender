"""Phase 1 part 4 inside Home Assistant: the event log, backup and restore.

The pure suite proves what a row *is* (tests/core/test_journal.py); this
proves that rows reach a real SQLite database, that the filters and the export
read them back, that retention removes what it should, that the restart gap
lands, and that a restore refuses a document it cannot honestly accept.
"""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.foyer.const import DOMAIN
from custom_components.foyer.store.log_store import EVENT_FOYER

from .conftest import PANEL_ENTITY, ZONE
from .test_part2 import _advance, _set, _state, _ws


async def _rows(client, **filters) -> list[dict]:
    result = await _ws(client, {"type": "foyer/log/query", **filters})
    return result["rows"]


async def _types(client, **filters) -> list[str]:
    return [row["event_type"] for row in await _rows(client, **filters)]


async def _arm(hass, freezer: FrozenDateTimeFactory) -> None:
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


# --- writing and reading ---------------------------------------------------------


async def test_arming_and_disarming_are_in_the_log_with_their_channel(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    rows = await _rows(client, categories=["arming"])
    assert [r["event_type"] for r in rows] == ["disarmed", "armed"]
    assert all(r["channel"] for r in rows)
    assert all(r["outcome"] == "ok" for r in rows)
    assert rows[0]["area_id"] == hass.data[DOMAIN].config.areas[0].id


async def test_zone_activity_while_disarmed_is_off_by_default(
    hass, hass_ws_client, loaded
):
    """§10.2: the trap row. Thousands a day, and they bury what matters."""
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on")
    await _set(hass, ZONE, "off")

    assert await _rows(client, categories=["zone_disarmed"]) == []


async def test_zone_activity_can_be_switched_on_for_diagnosis(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    settings = dict(config["config"]["settings"])
    settings["log"] = dict(
        settings["log"],
        enabled={**settings["log"]["enabled"], "zone_disarmed": True},
    )
    assert (await _ws(client, {"type": "foyer/config/settings", "settings": settings}))[
        "success"
    ]
    await hass.async_block_till_done()

    await _set(hass, ZONE, "on")
    rows = await _rows(client, categories=["zone_disarmed"])
    assert [r["event_type"] for r in rows] == ["zone_state"]
    assert rows[0]["detail"]["to"] == "on"


async def test_zone_activity_while_armed_is_logged_without_being_asked(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)
    await _set(hass, ZONE, "on")

    rows = await _rows(client, categories=["zone_armed"])
    assert [r["event_type"] for r in rows] == ["zone_state"]
    assert rows[0]["detail"]["area_state"] == "triggered"


async def test_an_alarm_carries_its_incident_id_on_every_related_row(
    hass, hass_ws_client, loaded, freezer
):
    """§5.6: the log reads as "what happened that night", not as scattered rows."""
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)
    await _set(hass, ZONE, "on")

    incident = hass.data[DOMAIN].state.incident
    assert incident is not None
    rows = await _rows(client, incident_id=incident.id)
    assert {r["event_type"] for r in rows} >= {"triggered", "incident_opened"}
    assert all(r["incident_id"] == incident.id for r in rows)
    # And the actions the alarm ran are on the same incident.
    assert any(r["category"] == "action" for r in rows)


async def test_a_failed_action_is_recorded_as_failed(
    hass, hass_ws_client, loaded, freezer
):
    """The emergency channel discovered broken during the emergency (§11.4)."""
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    profile = config["config"]["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["armed"],
            "name": "Push",
            # A service that does not exist: exactly the misconfiguration
            # this category exists to surface.
            "params": {"service": "notify.nobody", "message": "armed"},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
        }
    )
    assert (
        await _ws(
            client, {"type": "foyer/config/save", "kind": "profile", "item": profile}
        )
    )["success"]
    await hass.async_block_till_done()

    await _arm(hass, freezer)
    rows = await _rows(client, categories=["action"], outcome="failed")
    assert rows and rows[0]["event_type"] == "action_notify"
    assert rows[0]["severity"] == "warning"
    assert rows[0]["detail"]["error"]


async def test_a_refused_arming_is_a_row_that_names_the_zone(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on")
    # The panel tells the caller which zone blocked it; the log says the same
    # thing tomorrow morning, which is when the question is actually asked.
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            {"entity_id": PANEL_ENTITY},
            blocking=True,
        )
    await hass.async_block_till_done()

    rows = await _rows(client, categories=["arming"], outcome="blocked")
    assert rows and rows[0]["event_type"] == "arm_rejected"
    assert rows[0]["detail"]["reason"] == "zone_open"
    assert rows[0]["detail"]["blocking_zones"]


async def test_a_configuration_change_records_who_and_what_moved(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    area = dict(config["config"]["areas"][0], default_exit_delay=45)
    assert (
        await _ws(client, {"type": "foyer/config/save", "kind": "area", "item": area})
    )["success"]
    await hass.async_block_till_done()

    rows = await _rows(client, categories=["config"])
    assert rows and rows[0]["event_type"] == "config_save"
    assert rows[0]["user_name"]
    # The value before and the value after: a field name alone does not
    # answer "who changed what".
    assert rows[0]["detail"]["changes"]["areas"]["changed"] == {
        area["name"]: {"default_exit_delay": [30, 45]}
    }


async def test_every_row_also_reaches_the_bus(hass, hass_ws_client, loaded, freezer):
    """§10.3: one trigger for an external collector, and no database."""
    events = async_capture_events(hass, EVENT_FOYER)
    await _arm(hass, freezer)

    assert [e.data["event_type"] for e in events if e.data["category"] == "arming"] == [
        "armed"
    ]
    assert events[0].data["severity"] in {"info", "warning", "alarm"}


async def test_the_last_event_sensor_ignores_zone_noise(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    settings = dict(config["config"]["settings"])
    settings["log"] = dict(
        settings["log"],
        enabled={**settings["log"]["enabled"], "zone_disarmed": True},
    )
    await _ws(client, {"type": "foyer/config/settings", "settings": settings})
    await hass.async_block_till_done()

    await _arm(hass, freezer)
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await _set(hass, ZONE, "on")

    sensor = hass.states.get("sensor.foyer_last_event")
    assert sensor.state == "disarmed"
    assert sensor.attributes["category"] == "arming"


# --- the restart gap (INV-3) -----------------------------------------------------


async def test_the_restart_gap_is_logged_as_system_unavailable(
    hass, hass_ws_client, loaded
):
    """INV-3 is only complete once this row lands."""
    client = await hass_ws_client(hass)
    rows = await _rows(client, categories=["system"])
    gap = [r for r in rows if r["event_type"] == "system_unavailable"]
    assert gap, rows
    assert gap[0]["severity"] == "warning"
    assert gap[0]["detail"]["cause"] in {"ha_start", "reload"}
    assert gap[0]["detail"]["up_at"]


async def test_saving_a_setting_is_a_reload_not_an_outage(
    hass, hass_ws_client, entry, loaded
):
    """Every configuration change reloads the integration. A row saying "Foyer
    was not running", in warning, beside each of them is how a real gap gets
    ignored."""
    client = await hass_ws_client(hass)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    rows = await _rows(client, categories=["system"])
    reloads = [r for r in rows if r["event_type"] == "reloaded"]
    assert reloads, [r["event_type"] for r in rows]
    assert reloads[0]["severity"] == "info"
    assert int(reloads[0]["detail"]["gap_seconds"]) <= 60


# --- retention and export --------------------------------------------------------


async def test_retention_removes_what_is_older_than_its_category_keeps(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)
    assert await _rows(client, categories=["arming"])

    log = hass.data[DOMAIN].log
    settings = hass.data[DOMAIN].config.settings.log
    # Thirty days on, to the hour after the default retention.
    from homeassistant.util import dt as dt_util

    removed = await log.async_purge(settings, dt_util.utcnow() + timedelta(days=31))
    assert removed >= 1
    assert await _rows(client, categories=["arming"]) == []


async def test_retention_is_applied_at_every_start_not_only_once_a_day(
    hass, hass_ws_client, entry, loaded, freezer
):
    """A daily timer never fires on a house that restarts more often than
    that — and every configuration change reloads the entry."""
    from homeassistant.util import dt as dt_util

    client = await hass_ws_client(hass)
    await _arm(hass, freezer)
    assert await _rows(client, categories=["arming"])

    # A month later, with no purge having run in between: the next start has
    # to clear what is past its retention.
    freezer.move_to(dt_util.utcnow() + timedelta(days=40))
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert await _rows(client, categories=["arming"]) == []


async def test_export_honours_the_filters_it_was_given(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)

    result = await _ws(
        client, {"type": "foyer/log/export", "format": "csv", "categories": ["arming"]}
    )
    assert result["filename"].endswith(".csv")
    assert not result["truncated"]
    lines = result["content"].strip().splitlines()
    assert lines[0].startswith("ts,category,event_type")
    assert len(lines) == 1 + result["rows"]
    assert all(",arming," in line for line in lines[1:])

    as_json = await _ws(
        client, {"type": "foyer/log/export", "format": "json", "categories": ["alarm"]}
    )
    assert as_json["rows"] == 0


async def test_clearing_the_log_is_itself_logged(hass, hass_ws_client, loaded, freezer):
    """§10.3: audit-useful, not tamper-proof — and it says so."""
    client = await hass_ws_client(hass)
    await _arm(hass, freezer)

    result = await _ws(client, {"type": "foyer/log/clear"})
    assert result["removed"] >= 1
    await hass.async_block_till_done()

    rows = await _rows(client)
    assert [r["event_type"] for r in rows] == ["config_log_cleared"]


# --- backup and restore (§15.1) --------------------------------------------------


async def test_a_backup_round_trips_through_export_and_import(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    backup = await _ws(client, {"type": "foyer/config/export"})
    assert backup["filename"].endswith(".json")
    document = backup["document"]
    assert document["foyer"] == "foyer.config"

    # Change something, then restore the backup over it.
    config = await _ws(client, {"type": "foyer/config"})
    area = dict(config["config"]["areas"][0], name="Renamed")
    await _ws(client, {"type": "foyer/config/save", "kind": "area", "item": area})
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.areas[0].name == "Renamed"

    result = await _ws(client, {"type": "foyer/config/import", "document": document})
    assert result["success"], result
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.areas[0].name == "Casa"


async def test_a_restore_refuses_a_document_from_a_newer_major_version(
    hass, hass_ws_client, loaded
):
    """Dropping fields it does not understand could drop an alarm setting."""
    client = await hass_ws_client(hass)
    backup = await _ws(client, {"type": "foyer/config/export"})
    document = dict(backup["document"], version=[99, 1])

    result = await _ws(client, {"type": "foyer/config/import", "document": document})
    assert not result["success"]
    assert result["problems"][0]["code"] == "backup_version_unsupported"


async def test_a_restore_refuses_a_file_that_is_not_a_foyer_backup(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    result = await _ws(
        client, {"type": "foyer/config/import", "document": {"hello": "world"}}
    )
    assert not result["success"]
    assert result["problems"][0]["code"] == "not_a_foyer_backup"


async def test_a_restore_that_would_touch_an_armed_area_is_refused(
    hass, hass_ws_client, loaded, freezer
):
    """A restore goes through the same guard as any other edit, never around."""
    client = await hass_ws_client(hass)
    backup = await _ws(client, {"type": "foyer/config/export"})
    document = backup["document"]
    document["config"]["areas"][0]["default_entry_delay"] = 90

    await _arm(hass, freezer)
    result = await _ws(client, {"type": "foyer/config/import", "document": document})
    assert not result["success"]
    assert result["problems"]
    assert hass.data[DOMAIN].config.areas[0].default_entry_delay != 90


async def test_the_language_setting_changes_what_foyer_sends_not_the_panel(
    hass, hass_ws_client, loaded, freezer
):
    """§15.1: the panel follows each Home Assistant user; this is the language
    of the messages Foyer sends out."""
    from .test_integration import _notifications

    hass.config.language = "en"
    client = await hass_ws_client(hass)
    config = await _ws(client, {"type": "foyer/config"})
    settings = dict(config["config"]["settings"], language="it")
    assert (await _ws(client, {"type": "foyer/config/settings", "settings": settings}))[
        "success"
    ]
    await hass.async_block_till_done()

    await _arm(hass, freezer)
    notes = _notifications(hass)
    assert notes and notes[-1]["title"] == "Foyer: inserito"


async def test_with_no_language_set_foyer_speaks_what_home_assistant_speaks(
    hass, loaded, freezer
):
    hass.config.language = "it"
    await _arm(hass, freezer)

    from .test_integration import _notifications

    notes = _notifications(hass)
    assert notes and notes[-1]["title"] == "Foyer: inserito"


# --- the card's module actually reaches the browser --------------------------------


async def test_the_card_module_is_served_and_registered(hass, hass_client, loaded):
    """A missing card element has two possible causes, and this rules out ours:
    the file is served, and its URL is on the list Home Assistant puts into the
    page it renders. What is left is a page rendered before Foyer existed."""
    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL

    urls = list(hass.data[DATA_EXTRA_MODULE_URL].urls)
    card = next((u for u in urls if "foyer-card.js" in u), None)
    assert card, urls
    assert card.startswith("/foyer_static/foyer-card.js?v=")

    client = await hass_client()
    response = await client.get(card)
    assert response.status == 200
    body = await response.text()
    # The element the dashboard looks for, and the entry in the card picker.
    assert "foyer-card" in body
    assert "customCards" in body


async def test_the_icons_module_is_served_too(hass, hass_client, loaded):
    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL

    urls = list(hass.data[DATA_EXTRA_MODULE_URL].urls)
    icons = next((u for u in urls if "foyer-icons.js" in u), None)
    assert icons, urls
    client = await hass_client()
    assert (await client.get(icons)).status == 200


async def test_a_forced_arm_is_recorded_as_forced(hass, hass_ws_client, loaded):
    """§5.4: forced arming is never implicit, and never silent. The card offers
    it on a refusal, so the row it leaves is what says it was taken."""
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on")
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id

    refused = await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id})
    assert not refused["success"]
    assert refused["reason"] == "zone_open"

    forced = await _ws(
        client, {"type": "foyer/arm", "scenario_id": scenario_id, "force": True}
    )
    assert forced["success"], forced
    assert forced["state"]["zones"][0]["bypassed"] == "forced"
    await hass.async_block_till_done()

    rows = await _rows(client, categories=["security"])
    assert "forced_arm" in [r["event_type"] for r in rows]
