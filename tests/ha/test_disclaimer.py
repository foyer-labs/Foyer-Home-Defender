"""SPEC §20.4: the disclaimer, accepted before setup or from a repair card."""

from __future__ import annotations

from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.foyer import repairs
from custom_components.foyer.const import CONF_DISCLAIMER, DISCLAIMER_VERSION, DOMAIN

from .conftest import ZONE


async def _rows(hass, event_type: str) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    rows = (await system.log.async_query(limit=1000))["rows"]
    return [r for r in rows if r["event_type"] == event_type]


def _issue(hass):
    return ir.async_get(hass).async_get_issue(DOMAIN, repairs.DISCLAIMER)


async def test_an_accepted_installation_raises_no_card(hass, loaded):
    assert _issue(hass) is None


async def test_the_first_start_logs_the_acceptance(hass, loaded):
    (row,) = await _rows(hass, "config_disclaimer_accepted")
    assert row["category"] == "config"


async def test_an_older_installation_gets_a_card_and_keeps_working(hass, entry):
    """Decision 152: a card in Repairs, never an alarm that stops."""
    data = dict(entry.data)
    data.pop(CONF_DISCLAIMER)
    old = MockConfigEntry(domain=DOMAIN, title=entry.title, data=data)
    hass.states.async_set(ZONE, "off", {"friendly_name": "Front door"})
    old.add_to_hass(hass)
    assert await hass.config_entries.async_setup(old.entry_id)
    await hass.async_block_till_done()

    assert _issue(hass) is not None
    assert hass.states.get("alarm_control_panel.foyer_master") is not None
    assert await _rows(hass, "config_disclaimer_accepted") == []

    flow = await repairs.async_create_fix_flow(hass, repairs.DISCLAIMER, None)
    assert isinstance(flow, repairs.DisclaimerRepairFlow)
    refused = await flow.async_step_confirm({"accept_disclaimer": False})
    assert refused["errors"] == {"accept_disclaimer": "disclaimer_not_accepted"}
    assert _issue(hass) is not None

    await repairs.async_accept_disclaimer(hass)
    await hass.async_block_till_done()

    assert _issue(hass) is None
    accepted = old.data[CONF_DISCLAIMER]
    assert accepted["version"] == DISCLAIMER_VERSION
    (row,) = await _rows(hass, "config_disclaimer_accepted")
    assert row["channel"] == "ha_config"


def test_only_the_current_version_counts():
    assert repairs.disclaimer_accepted(
        {CONF_DISCLAIMER: {"version": DISCLAIMER_VERSION, "accepted_at": "x"}}
    )
    assert not repairs.disclaimer_accepted(
        {CONF_DISCLAIMER: {"version": DISCLAIMER_VERSION - 1, "accepted_at": "x"}}
    )
    assert not repairs.disclaimer_accepted({})
