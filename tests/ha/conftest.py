"""Fixtures for the Home Assistant integration tests.

Run with the plugin enabled explicitly, so the pure suite never loads it:

    pytest -p pytest_homeassistant_custom_component tests/ha
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
