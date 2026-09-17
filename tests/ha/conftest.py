"""Fixtures for the Home Assistant integration tests.

Run with the plugin enabled explicitly, so the pure suite never loads it:

    pytest -p pytest_homeassistant_custom_component tests/ha
"""

from __future__ import annotations

from collections.abc import Generator
import pathlib

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    get_test_config_dir,
)

from custom_components.foyer.const import (
    CONF_AREA_NAME,
    CONF_SCENARIO_NAME,
    CONF_TRIGGER_STATES,
    CONF_ZONE_ENTITY,
    DOMAIN,
)

ZONE = "binary_sensor.front_door"
PANEL_ENTITY = "alarm_control_panel.foyer_casa"
MASTER = "alarm_control_panel.foyer_master"
SELECT = "select.foyer_scenario"


@pytest.fixture(autouse=True)
def isolated_log(monkeypatch, request) -> Generator[None]:
    """One event log database per test.

    The test configuration directory is shared between tests, and the log is
    deliberately a file in it (that is where a real installation keeps it), so
    without this a test would read the rows of the one before it.
    """
    from custom_components.foyer.store import log_store

    name = f"foyer-log-{abs(hash(request.node.nodeid))}.db"
    monkeypatch.setattr(log_store, "DB_FILENAME", name)
    yield
    for suffix in ("", "-wal", "-shm"):
        path = pathlib.Path(get_test_config_dir(name + suffix))
        path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    yield


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Casa",
        data={
            CONF_AREA_NAME: "Casa",
            CONF_SCENARIO_NAME: "Fuori casa",
            CONF_ZONE_ENTITY: ZONE,
            CONF_TRIGGER_STATES: ["on"],
        },
    )


@pytest.fixture
async def loaded(hass, entry):
    """A loaded Foyer with its zone closed, after Home Assistant has started."""
    hass.states.async_set(ZONE, "off", {"friendly_name": "Front door"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
