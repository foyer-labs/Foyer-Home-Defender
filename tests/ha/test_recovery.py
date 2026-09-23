"""An administrator recovering access, from the Configure step (§8.2).

Decisions 109 and 110: the step asks for the account, because Home Assistant
does not say who opened it; it enables that account's Foyer user, removes its
validity window and sets its code, or creates the user; and it is never
quiet — a row, a Home Assistant notification and a message to every contact.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.models import (
    Contact,
    ContactChannel,
    ContactChannelKind,
)

from .test_part2 import _ws
from .test_phase2 import CODE, OTHER, _make_user

NEW = "135792"


async def _recover(hass, entry, account: str, code: str):
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"account": account, "code": code}
    )
    await hass.async_block_till_done()
    return result


async def _rows(hass, event_type: str) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    rows = (await system.log.async_query(limit=1000))["rows"]
    return [r for r in rows if r["event_type"] == event_type]


async def test_an_administrator_with_no_code_gets_back_in_and_everybody_hears(
    hass, loaded, hass_ws_client, hass_admin_user
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    phone = async_mock_service(hass, "notify", "phone")
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        contacts=(
            Contact(
                "anna",
                "Anna",
                channels=(
                    ContactChannel("push", ContactChannelKind.PUSH, "notify.phone"),
                ),
            ),
        ),
    )
    rows = await _rows(hass, "access_recovered")
    assert rows == []

    result = await _recover(hass, loaded, hass_admin_user.id, NEW)
    assert result["type"] is FlowResultType.CREATE_ENTRY, result

    # Heard: a message to the contact, a Home Assistant notification.
    assert phone and hass_admin_user.name in phone[0].data["message"]
    notes = hass.data.get("persistent_notification", {})
    assert "foyer_access_recovered" in notes
    assert hass_admin_user.name in notes["foyer_access_recovered"]["message"]

    # And in: a person linked to the account, every permission, the new code.
    system = hass.data[DOMAIN]
    person = system.config.user_of_ha(hass_admin_user.id)
    assert person is not None and person.enabled
    assert "manage_users" in person.permissions
    (row,) = await _rows(hass, "access_recovered")
    assert row["category"] == "security"
    assert row["detail"]["account"] == hass_admin_user.name
    saved = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {"name": "Anna", "permissions": ["arm"]},
            "new_code": OTHER,
            "code": NEW,
        },
    )
    assert saved["success"], saved


async def test_a_disabled_user_of_the_administrator_is_enabled_again(
    hass, loaded, hass_ws_client, hass_admin_user
):
    client = await hass_ws_client(hass)
    now = dt_util.utcnow()
    await _make_user(hass, client, new_code=CODE)
    await _make_user(
        hass,
        client,
        name="Owner",
        new_code=OTHER,
        code=CODE,
        ha_user_id=hass_admin_user.id,
        enabled=False,
        valid_from=(now - timedelta(days=10)).isoformat(),
        valid_until=(now - timedelta(days=1)).isoformat(),
        permissions=["arm"],
    )
    result = await _recover(hass, loaded, hass_admin_user.id, NEW)
    assert result["type"] is FlowResultType.CREATE_ENTRY, result
    person = hass.data[DOMAIN].config.user_of_ha(hass_admin_user.id)
    assert person.name == "Owner" and person.enabled
    assert person.valid_from is None and person.valid_until is None
    # Their own permissions stay theirs: the recovery is a way in, not a
    # promotion — an administrator is never refused for want of one anyway.
    assert person.permissions == frozenset({"arm"})
    assert len(hass.data[DOMAIN].config.users) == 2


async def test_a_code_somebody_else_holds_is_refused_without_saying_whose(
    hass, loaded, hass_ws_client, hass_admin_user
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    result = await _recover(hass, loaded, hass_admin_user.id, CODE)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "code_in_use"}
    assert hass.data[DOMAIN].config.user_of_ha(hass_admin_user.id) is None
    assert await _rows(hass, "access_recovered") == []
