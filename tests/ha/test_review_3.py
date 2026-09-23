"""What the third full review found on the Home Assistant side of store/ and
api/, pinned down. The pure findings live in tests/core/test_review_3.py."""

from __future__ import annotations

from custom_components.foyer.api.backup import backup_document, restore
from custom_components.foyer.const import DOMAIN
from custom_components.foyer.store.log_store import export_csv


def test_a_name_that_looks_like_a_formula_is_exported_as_text():
    """§10.3: a zone named `=HYPERLINK(...)` is a name, and a spreadsheet
    opening the export must not run it."""
    text = export_csv(
        [{"ts": "2026-09-23T10:00:00", "user_name": '=HYPERLINK("x")', "detail": {}}]
    )
    assert "'=HYPERLINK" in text
    assert ",=HYPERLINK" not in text


async def test_a_backup_with_the_watchdog_on_restores_where_no_url_is_set(hass, loaded):
    """The URL never travels in a backup; on a fresh install the restore was
    refused for a URL nobody could enter before restoring."""
    system = hass.data[DOMAIN]
    assert not system.config.health.watchdog.url
    document = backup_document(system.config)
    document["config"]["health"]["watchdog"]["enabled"] = True
    result = restore(system, document)
    assert result.config is not None, result.problems
    assert result.config.health.watchdog.enabled is False


async def test_a_backup_whose_config_is_not_a_map_is_refused_not_a_traceback(
    hass, loaded
):
    system = hass.data[DOMAIN]
    document = backup_document(system.config)
    document["config"] = "not a configuration"
    result = restore(system, document)
    assert result.config is None
    assert result.problems[0].code == "invalid"
    document = backup_document(system.config)
    document["config"]["zones"] = "not a list"
    result = restore(system, document)
    assert result.config is None
    assert result.problems[0].code == "invalid"
