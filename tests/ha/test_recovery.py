"""An administrator recovering access, from the Configure step (§8.2).

Decisions 109 and 110: the step asks for the account, because Home Assistant
does not say who opened it; it enables that account's Foyer user, removes its
validity window and sets its code, or creates the user; and it is never
quiet — a row, a Home Assistant notification and a message to every contact.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.util import dt as dt_util
import pytest
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
    (note,) = [n for k, n in notes.items() if k.startswith("foyer_access_recovered")]
    assert hass_admin_user.name in note["message"]

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
    # The save reloads the entry; a reload still running at teardown races
    # the log fixture that unlinks the database (seen on CI).
    await hass.async_block_till_done()


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


async def test_only_an_administrator_account_can_be_recovered(
    hass, loaded, hass_ws_client, hass_read_only_user
):
    """Decision 110: the recovery is an administrator's own access."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    # Not even offered: the form refuses it before Foyer sees it.
    with pytest.raises(InvalidData):
        await _recover(hass, loaded, hass_read_only_user.id, NEW)
    assert hass.data[DOMAIN].config.user_of_ha(hass_read_only_user.id) is None


async def test_a_recovery_that_could_not_be_written_is_not_announced_as_done(
    hass, loaded, hass_ws_client, hass_admin_user, monkeypatch
):
    """Found in review: announced first, a recovery that another save beat
    to the write told everybody about a code that did not exist."""
    from custom_components.foyer.api import recovery

    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)

    async def beaten(*_args, **_kwargs):
        # What async_write answers when another save got there first.
        return {"success": False, "problems": [{"code": "config_reloading"}]}

    monkeypatch.setattr(recovery, "async_write", beaten)
    result = await _recover(hass, loaded, hass_admin_user.id, NEW)
    assert result.get("errors") == {"base": "reloading"}, result
    (row,) = await _rows(hass, "access_recovered")
    assert row["outcome"] == "failed"
    notes = hass.data.get("persistent_notification", {})
    assert not any(key.startswith("foyer_access_recovered") for key in notes)


async def test_two_recoveries_leave_two_notices(
    hass, loaded, hass_ws_client, hass_admin_user, freezer
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    await _recover(hass, loaded, hass_admin_user.id, NEW)
    freezer.tick(timedelta(seconds=5))
    await _recover(hass, loaded, hass_admin_user.id, "246800")
    notes = hass.data.get("persistent_notification", {})
    assert sum(key.startswith("foyer_access_recovered") for key in notes) == 2
