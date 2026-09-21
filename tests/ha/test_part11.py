"""Phase 5 part 3 inside Home Assistant: the way in (SPEC §20.2).

The pure suite proves what the Alarmo importer makes of a file
(tests/core/test_alarmo.py). This proves what only a running Home Assistant
can: that the file is read from this installation's own ``.storage``, that a
preview writes nothing, that an apply stores exactly what the preview showed
and is logged as a configuration change, that it is refused when anything
changed in between, and that a zone it brought across cannot be switched on
until somebody has confirmed its trigger.

The Alarmo document is the hand-written fixture of the pure suite, not one
captured from a real installation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.foyer.const import DOMAIN
from custom_components.foyer.store.schema import zone_to_dict

from ..core.test_alarmo import alarmo_file
from .test_part2 import _ws
from .test_part10 import _rows

LABELS = {
    "modes": {"armed_away": "Away", "armed_home": "Home", "armed_night": "Night"},
    "split": "{area} ({modes})",
    "profile": "{area} (from Alarmo)",
}


def _path(hass) -> Path:
    return Path(hass.config.path(".storage", "alarmo.storage"))


async def _write(hass, document) -> None:
    def write() -> None:
        _path(hass).parent.mkdir(parents=True, exist_ok=True)
        _path(hass).write_text(json.dumps(document), encoding="utf-8")

    await hass.async_add_executor_job(write)


@pytest.fixture
async def alarmo(hass, loaded):
    """This house's Alarmo, on disk where Alarmo keeps it, and its sensors."""
    for entity, name in (
        ("binary_sensor.kitchen_window", "Kitchen window"),
        ("binary_sensor.hall_pir", "Hall PIR"),
        ("binary_sensor.kitchen_smoke", "Kitchen smoke"),
        ("binary_sensor.panel_tamper", "Panel tamper"),
    ):
        hass.states.async_set(entity, "off", {"friendly_name": name})
    await _write(hass, alarmo_file())
    yield
    # The test configuration directory is shared between tests.
    await hass.async_add_executor_job(lambda: _path(hass).unlink(missing_ok=True))


async def test_a_preview_reads_the_file_and_writes_nothing(
    hass, hass_ws_client, alarmo
):
    client = await hass_ws_client(hass)
    before = hass.data[DOMAIN].config
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    assert preview["success"], preview
    assert preview["lines"][0]["code"] == "codes"
    assert preview["counts"]["zones"] == 4
    assert "House (Away)" in preview["created"]["areas"]
    assert preview["created"]["people"] == ["Anna"]
    assert preview["fingerprint"]
    assert hass.data[DOMAIN].config is before


async def test_an_apply_stores_what_the_preview_showed_and_logs_it(
    hass, hass_ws_client, alarmo
):
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    result = await _ws(
        client,
        {
            "type": "foyer/alarmo/apply",
            "fingerprint": preview["fingerprint"],
            "labels": LABELS,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    config = hass.data[DOMAIN].config
    imported = [z for z in config.zones if z.entity_id != "binary_sensor.front_door"]
    assert len(imported) == 4
    assert all(not z.enabled and not z.trigger_confirmed for z in imported)
    anna = next(u for u in config.users if u.name == "Anna")
    assert anna.code_hash is None
    rows = await _rows(hass, categories=["config"])
    assert any(row["event_type"] == "config_import" for row in rows)


async def test_an_apply_is_refused_when_the_file_changed_after_the_preview(
    hass, hass_ws_client, alarmo
):
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    changed = alarmo_file()
    changed["data"]["sensors"].pop()
    await _write(hass, changed)
    result = await _ws(
        client,
        {
            "type": "foyer/alarmo/apply",
            "fingerprint": preview["fingerprint"],
            "labels": LABELS,
        },
    )
    assert not result["success"]
    assert result["refused"]["code"] == "changed"
    assert len(hass.data[DOMAIN].config.zones) == 1


async def test_no_file_is_a_sentence_not_an_error(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await hass.async_add_executor_job(lambda: _path(hass).unlink(missing_ok=True))
    preview = await _ws(client, {"type": "foyer/alarmo/preview"})
    assert preview == {"success": False, "refused": {"code": "not_found", "params": {}}}


async def test_a_version_it_has_not_read_is_refused_by_name(
    hass, hass_ws_client, alarmo
):
    await _write(hass, {**alarmo_file(), "version": 7, "minor_version": 1})
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview"})
    assert preview["refused"] == {
        "code": "version_unsupported",
        "params": {"version": "7.1"},
    }


async def test_an_imported_zone_cannot_be_switched_on_unconfirmed(
    hass, hass_ws_client, alarmo
):
    """INV-5 through the real command the zone editor sends."""
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    await _ws(
        client,
        {
            "type": "foyer/alarmo/apply",
            "fingerprint": preview["fingerprint"],
            "labels": LABELS,
        },
    )
    await hass.async_block_till_done()
    zone = next(
        z
        for z in hass.data[DOMAIN].config.zones
        if z.entity_id == "binary_sensor.kitchen_window"
    )
    item = {**zone_to_dict(zone), "enabled": True, "trigger_confirmed": True}
    refused = await _ws(
        client, {"type": "foyer/config/save", "kind": "zone", "item": item}
    )
    assert not refused["success"]
    assert [p["code"] for p in refused["problems"]] == ["trigger_not_confirmed"]
    accepted = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "zone",
            "item": item,
            "trigger_confirmed": True,
        },
    )
    assert accepted["success"], accepted


async def test_the_outgoing_languages_are_read_from_the_files(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": "foyer/languages"})
    assert {"code": "it", "name": "Italiano"} in result["languages"]
    assert {"code": "en", "name": "English"} in result["languages"]


async def test_a_sensor_moving_between_preview_and_apply_refuses_nothing(
    hass, hass_ws_client, alarmo
):
    """A PIR detecting somebody while they read the report is a house being
    lived in, not a change to what the import would do."""
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    hass.states.async_set("binary_sensor.hall_pir", "on", {"friendly_name": "Hall PIR"})
    await hass.async_block_till_done()
    result = await _ws(
        client,
        {
            "type": "foyer/alarmo/apply",
            "fingerprint": preview["fingerprint"],
            "labels": LABELS,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()


async def test_a_restored_backup_cannot_confirm_a_zone_nobody_checked(
    hass, hass_ws_client, alarmo
):
    """Editing a backup to say `true` is not somebody testing the sensor
    (found in review): the zone comes back as unconfirmed as it went out."""
    client = await hass_ws_client(hass)
    preview = await _ws(client, {"type": "foyer/alarmo/preview", "labels": LABELS})
    await _ws(
        client,
        {
            "type": "foyer/alarmo/apply",
            "fingerprint": preview["fingerprint"],
            "labels": LABELS,
        },
    )
    await hass.async_block_till_done()
    backup = (await _ws(client, {"type": "foyer/config/export"}))["document"]
    for zone in backup["config"]["zones"]:
        if zone["entity_id"] == "binary_sensor.kitchen_window":
            zone["trigger_confirmed"] = True
            zone["enabled"] = True
    result = await _ws(client, {"type": "foyer/config/import", "document": backup})
    assert not result["success"]
    assert "trigger_not_confirmed" in [p["code"] for p in result["problems"]]
