"""An armed house keeps the answer and the codes it was armed with (§15.1).

Decisions 138 and 139 from the outside: the panel's commands, a restore and
the Configure step's recovery, with an area armed. The rule itself — which
setting is kept, which profile and contact are in use — is pinned in
tests/core/test_armed_edits.py.
"""

from __future__ import annotations

from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.foyer.api.backup import backup_document, restore
from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.models import AreaState

from .test_part2 import _ws
from .test_phase2 import CODE, _make_user
from .test_recovery import NEW, _recover

EVERYTHING = ["arm", "disarm", "edit_config", "manage_users", "view_log"]


def _armed_areas(hass) -> list[str]:
    state = hass.data[DOMAIN].state
    return [a for a, rt in state.areas.items() if rt.state is not AreaState.DISARMED]


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


@pytest.fixture
async def armed(hass, hass_ws_client, loaded):
    """One person holding a code, and the house armed: its exit delay is
    running, and an area counting down is not disarmed."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, permissions=EVERYTHING)
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    result = await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id})
    assert result["success"], result
    assert _armed_areas(hass)
    return client


async def test_the_code_policy_cannot_change_while_an_area_is_armed(hass, armed):
    client = armed
    security = (await _config(client))["settings"]["security"]
    answer = await _ws(
        client,
        {
            "type": "foyer/config/security",
            "code_policy": {"disarm": False},
            "security": security,
            "code": CODE,
        },
    )
    assert answer["success"] is False
    assert answer["problems"] == [
        {
            "code": "armed_setting",
            "kind": "settings",
            "ref": None,
            "field": "code_policy",
        }
    ]
    assert hass.data[DOMAIN].config.code_policy.disarm is True


async def test_a_settings_save_keeps_the_siren_and_lets_the_language_go(hass, armed):
    client = armed
    settings = (await _config(client))["settings"]
    refused = await _ws(
        client,
        {
            "type": "foyer/config/settings",
            "settings": {**settings, "siren_duration": 60},
            "code": CODE,
        },
    )
    assert refused["success"] is False
    assert [(p["code"], p["field"]) for p in refused["problems"]] == [
        ("armed_setting", "siren_duration")
    ]
    accepted = await _ws(
        client,
        {
            "type": "foyer/config/settings",
            "settings": {**settings, "language": "it"},
            "code": CODE,
        },
    )
    assert accepted["success"], accepted
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.settings.language == "it"
    assert _armed_areas(hass)


async def test_the_webhook_can_be_switched_on_and_off_while_armed(hass, armed):
    """It round-trips the whole settings block: the round trip must not read
    as a change to anything the armed house keeps."""
    client = armed
    on = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True, "code": CODE})
    assert on["success"], on
    await hass.async_block_till_done()
    off = await _ws(
        client, {"type": "foyer/ack_webhook", "enabled": False, "code": CODE}
    )
    assert off["success"], off
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.settings.ack_webhook_id is None


async def test_the_last_usable_code_cannot_be_removed_while_armed(hass, armed):
    client = armed
    person = {
        "id": hass.data[DOMAIN].config.users[0].id,
        "name": "Luca",
        "permissions": EVERYTHING,
    }
    answer = await _ws(
        client,
        {"type": "foyer/user/save", "user": person, "new_code": None, "code": CODE},
    )
    assert answer["success"] is False
    assert [p["code"] for p in answer["problems"]] == ["last_usable_code"]
    assert hass.data[DOMAIN].config.users[0].code_hash


async def test_a_restore_is_refused_exactly_where_the_same_edit_would_be(hass, armed):
    system = hass.data[DOMAIN]
    document = backup_document(system.config)
    document["config"]["settings"]["language"] = "it"
    free = restore(system, document)
    assert free.config is not None, free.problems
    document["config"]["settings"]["siren_duration"] = 60
    kept = restore(system, document)
    assert kept.config is None
    assert [(p.code, p.field) for p in kept.problems] == [
        ("armed_setting", "siren_duration")
    ]


async def test_the_recovery_works_while_the_house_is_armed(
    hass, armed, loaded, hass_admin_user
):
    """The administrator locked out while the house is armed is the one who
    needs it most, and the recovery writes a person, which stays free."""
    armed_before = _armed_areas(hass)
    result = await _recover(hass, loaded, hass_admin_user.id, NEW)
    assert result["type"] is FlowResultType.CREATE_ENTRY, result
    person = hass.data[DOMAIN].config.user_of_ha(hass_admin_user.id)
    assert person is not None and person.enabled and person.code_hash
    # And nothing was disarmed on the way.
    assert _armed_areas(hass) == armed_before
