"""Config flow: names, zone entity, and an explicitly confirmed trigger (INV-5)."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.foyer.const import DOMAIN

from .conftest import ZONE

STEP_USER = {
    "area_name": " Casa ",
    "scenario_name": "Fuori casa",
    "zone_entity": ZONE,
}


async def _to_trigger_step(hass):
    hass.states.async_set(ZONE, "off")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], STEP_USER
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "trigger"
    return result


async def test_full_flow_creates_the_entry(hass):
    result = await _to_trigger_step(hass)

    with (
        patch("custom_components.foyer.async_setup_entry", return_value=True),
        patch("custom_components.foyer.async_unload_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"trigger_states": ["on"], "confirm_trigger": True},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Casa"
    assert result["data"] == {
        "area_name": "Casa",
        "scenario_name": "Fuori casa",
        "zone_entity": ZONE,
        "trigger_states": ["on"],
    }


async def test_trigger_must_be_confirmed(hass):
    result = await _to_trigger_step(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"trigger_states": ["on"], "confirm_trigger": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"confirm_trigger": "trigger_not_confirmed"}


async def test_fault_state_cannot_be_a_trigger(hass):
    result = await _to_trigger_step(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"trigger_states": ["on", "unavailable"], "confirm_trigger": True},
    )

    assert result["errors"] == {"trigger_states": "fault_state_as_trigger"}


async def test_only_one_instance(hass, loaded):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
