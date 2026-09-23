"""Phase 2 part 1 inside Home Assistant: people, codes and what they may do.

The pure suite proves the rules (tests/core/test_identity.py, test_codes.py).
This proves the rules are reachable only through the backend: that a wrong
code is refused over the real API, that repeating it locks that channel, that
no hash ever comes back over the wire, and that the log finally answers the
question this project exists to answer — who disarmed, and through what.
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY
from .test_part2 import _advance, _state, _ws

CODE = "246813"
OTHER = "975310"
DURESS = "111222"


async def _make_user(hass, client, **fields) -> str:
    """Create a person, as page 7 does. Codes travel one way, never back.

    Saving reloads the integration, like every configuration change, so this
    waits for it: a command sent into the gap answers "not loaded".
    """
    result = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {
                "name": fields.pop("name", "Luca"),
                "permissions": fields.pop(
                    "permissions",
                    ["arm", "disarm", "bypass_zone", "change_scenario", "view_log"],
                ),
                "allowed_area_ids": fields.pop("allowed_area_ids", None),
                "allowed_scenario_ids": fields.pop("allowed_scenario_ids", None),
                "valid_from": fields.pop("valid_from", None),
                "valid_until": fields.pop("valid_until", None),
                "code_exempt_when_identified": fields.pop("exempt", False),
                "enabled": fields.pop("enabled", True),
                "ha_user_id": fields.pop("ha_user_id", None),
                **({"id": fields["id"]} if "id" in fields else {}),
            },
            **{k: v for k, v in fields.items() if k.startswith("new_")},
            # The code of whoever is saving, once codes are in force: an
            # administrator is asked for one like anybody else (decision 101).
            **({"code": fields["code"]} if "code" in fields else {}),
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    return result["id"]


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


async def _arm(hass, client, **extra) -> dict:
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    return await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id, **extra})


async def _armed(hass, client, freezer, **extra) -> None:
    result = await _arm(hass, client, **extra)
    assert result["success"], result
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


@pytest.fixture
async def with_user(hass, hass_ws_client, loaded):
    """A loaded installation where exactly one person holds a code."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, new_duress_code=DURESS)
    return client


# --- the policy comes into force with the first code ------------------------------


async def test_before_any_user_nothing_asks_for_a_code(hass, hass_ws_client, loaded):
    """Decision 78, from the outside: an installation upgrading into this
    version keeps working exactly as it did until somebody holds a code."""
    client = await hass_ws_client(hass)
    status = await _ws(client, {"type": "foyer/status"})

    assert status["security"]["enforced"] is False
    assert (await _arm(hass, client))["success"]
    assert (await _ws(client, {"type": "foyer/disarm"}))["success"]


async def test_the_first_code_puts_the_policy_in_force(hass, with_user, freezer):
    client = with_user
    status = await _ws(client, {"type": "foyer/status"})
    assert status["security"]["enforced"] is True
    assert status["security"]["require_code"]["disarm"] is True
    assert status["security"]["require_code"]["arm"] is False

    await _armed(hass, client, freezer)
    refused = await _ws(client, {"type": "foyer/disarm"})
    assert not refused["success"]
    assert refused["reason"] == "code_required"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    accepted = await _ws(client, {"type": "foyer/disarm", "code": CODE})
    assert accepted["success"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_a_wrong_code_is_refused_and_says_nothing_else(hass, with_user, freezer):
    client = with_user
    await _armed(hass, client, freezer)
    refused = await _ws(client, {"type": "foyer/disarm", "code": OTHER})

    assert not refused["success"]
    assert refused["reason"] == "bad_code"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    # Nothing in the answer says whose code it nearly was, or how close.
    assert "Luca" not in str(refused)


# --- lockout (§8.4) ---------------------------------------------------------------


async def test_repeating_a_wrong_code_locks_that_channel(
    hass, with_user, freezer, hass_ws_client, hass_read_only_access_token
):
    """Five failures within the window shut the channel, and then even the
    right code has to wait — which is the whole point of a lockout.

    From a non-administrator's connection, because the administrator path is
    never locked (§8.4): nobody may shut themselves out of their own house.
    """
    await _armed(hass, with_user, freezer)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for _ in range(5):
        assert (await _ws(client, {"type": "foyer/disarm", "code": OTHER}))[
            "reason"
        ] in ("bad_code", "locked_out")

    locked = await _ws(client, {"type": "foyer/disarm", "code": CODE})
    assert locked["reason"] == "locked_out"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    # The administrator's own connection is untouched by any of it.
    assert (await _ws(with_user, {"type": "foyer/disarm", "code": CODE}))["success"]


async def test_the_administrator_path_is_never_locked_out(hass, with_user, freezer):
    """§8.4, and the reason it is worth a test of its own: an administrator
    who could not get back in would simply disable the integration."""
    await _armed(hass, with_user, freezer)
    for _ in range(8):
        assert (await _ws(with_user, {"type": "foyer/disarm", "code": OTHER}))[
            "reason"
        ] == "bad_code"
    assert (await _ws(with_user, {"type": "foyer/disarm", "code": CODE}))["success"]


async def test_the_lockout_survives_a_restart(
    hass, with_user, freezer, hass_ws_client, hass_read_only_access_token
):
    """INV-3: a lockout a restart clears is an invitation to restart."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await _armed(hass, with_user, freezer)
    for _ in range(5):
        await _ws(client, {"type": "foyer/disarm", "code": OTHER})

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    after = await _ws(client, {"type": "foyer/disarm", "code": CODE})
    assert after["reason"] == "locked_out"


async def _me(client) -> str:
    """The Home Assistant account this connection is signed in as."""
    return (await _ws(client, {"type": "auth/current_user"}))["id"]


def _area(hass) -> str:
    return hass.data[DOMAIN].config.areas[0].id


# --- permissions and scope (§8.3) -------------------------------------------------


async def test_a_permission_the_panel_hides_is_refused_when_sent_by_hand(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, permissions=["arm"], new_code=CODE)
    await _armed(hass, client, freezer)

    refused = await _ws(client, {"type": "foyer/disarm", "code": CODE})
    assert refused["reason"] == "not_permitted"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


async def test_an_expired_guest_code_is_refused(hass, hass_ws_client, loaded, freezer):
    client = await hass_ws_client(hass)
    await _make_user(
        hass,
        client,
        name="Guest",
        new_code=CODE,
        valid_until="2020-01-01T00:00:00+00:00",
    )
    # Nobody holds a *usable* code, so the policy is not in force at all: the
    # expired guest neither opens the house nor locks everybody out of it.
    status = await _ws(client, {"type": "foyer/status"})
    assert status["security"]["enforced"] is False

    await _make_user(hass, client, name="Luca", new_code=OTHER)
    await _armed(hass, client, freezer)
    refused = await _ws(client, {"type": "foyer/disarm", "code": CODE})
    assert refused["reason"] == "user_not_valid"


async def test_an_area_outside_the_scope_is_refused(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, allowed_area_ids=[])

    refused = await _ws(
        client, {"type": "foyer/arm", "area_id": _area(hass), "code": CODE}
    )
    assert refused["reason"] == "area_not_allowed"


# --- codes never come back (§8.1, INV-2) ------------------------------------------


async def test_no_hash_is_ever_returned_by_the_api(hass, with_user):
    client = with_user
    config = await _config(client)
    backup = await _ws(client, {"type": "foyer/config/export"})
    status = await _ws(client, {"type": "foyer/status"})
    rows = await _ws(client, {"type": "foyer/log/query"})

    for payload in (config, backup, status, rows):
        text = str(payload)
        assert "$2b$" not in text and "code_hash" not in text
        assert CODE not in text and DURESS not in text
    # What the panel is told instead is that a code exists.
    assert config["users"][0]["has_code"] is True
    assert config["users"][0]["has_duress_code"] is True


async def test_a_restored_backup_cannot_set_a_code(hass, with_user):
    """A file can add people; it can never hand somebody a code of its own
    choosing, and the people it brings back keep the codes already here."""
    client = with_user
    backup = await _ws(client, {"type": "foyer/config/export", "code": CODE})
    document = backup["document"]
    document["config"]["users"][0]["code_hash"] = "$2b$10$" + "x" * 53

    result = await _ws(
        client, {"type": "foyer/config/import", "document": document, "code": CODE}
    )
    assert result["success"], result
    await hass.async_block_till_done()
    users = hass.data[DOMAIN].config.users
    # Still the code created above, not the one the file tried to plant.
    assert users[0].code_hash.startswith("$2b$")
    assert users[0].code_hash != "$2b$10$" + "x" * 53


async def test_a_code_that_belongs_to_somebody_else_is_refused(hass, with_user):
    client = with_user
    result = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {"name": "Anna", "permissions": ["arm", "disarm"]},
            "new_code": CODE,
            "code": CODE,
        },
    )
    assert not result["success"]
    assert result["problems"][0]["code"] == "code_in_use"
    # And it does not say whose code it was.
    assert "Luca" not in str(result)


async def test_a_duress_code_may_not_be_the_persons_own_ordinary_code(hass, with_user):
    """The uniqueness check skips the user being edited, so that they can keep
    their own code — which means it cannot catch this one.

    A duress code equal to its owner's ordinary code would never be reached:
    the ordinary hash matches first, and the silent alarm could never fire.
    """
    client = with_user
    user_id = hass.data[DOMAIN].config.users[0].id

    same = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {"id": user_id, "name": "Luca", "permissions": ["arm", "disarm"]},
            "new_duress_code": CODE,
            "code": CODE,
        },
    )
    assert not same["success"]
    assert same["problems"][0]["code"] == "code_in_use"

    # And the other way round: taking the duress code as the ordinary one
    # would quietly retire the silent alarm.
    reversed_ = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {"id": user_id, "name": "Luca", "permissions": ["arm", "disarm"]},
            "new_code": DURESS,
            "code": CODE,
        },
    )
    assert not reversed_["success"]
    assert reversed_["problems"][0]["code"] == "code_in_use"

    # The duress code still works, which is the whole point of refusing.
    await hass.async_block_till_done()
    assert (await _ws(client, {"type": "foyer/disarm", "code": DURESS}))[
        "reason"
    ] != "bad_code"


async def test_clearing_the_code_field_does_not_remove_the_code(hass, with_user):
    """The editor sends the field as soon as somebody types in it. Typing and
    then clearing must leave the code alone; only an explicit null removes."""
    client = with_user
    user_id = hass.data[DOMAIN].config.users[0].id
    person = {"id": user_id, "name": "Luca", "permissions": ["arm", "disarm"]}

    kept = await _ws(
        client,
        {"type": "foyer/user/save", "user": person, "new_code": "", "code": CODE},
    )
    assert kept["success"], kept
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.users[0].code_hash

    removed = await _ws(
        client,
        {"type": "foyer/user/save", "user": person, "new_code": None, "code": CODE},
    )
    assert removed["success"], removed
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.users[0].code_hash is None


# --- the log answers "who" (§10.1) ------------------------------------------------


async def test_the_log_says_who_disarmed_and_through_which_channel(
    hass, with_user, freezer
):
    client = with_user
    await _armed(hass, client, freezer)
    assert (await _ws(client, {"type": "foyer/disarm", "code": CODE}))["success"]

    rows = (await _ws(client, {"type": "foyer/log/query"}))["rows"]
    disarmed = next(r for r in rows if r["event_type"] == "disarmed")
    assert disarmed["user_name"] == "Luca"
    assert disarmed["channel"] == "ha_ui"

    # And a refusal is a row of its own, under security, naming nobody.
    await _armed(hass, client, freezer)
    await _ws(client, {"type": "foyer/disarm", "code": OTHER})
    rows = (await _ws(client, {"type": "foyer/log/query"}))["rows"]
    rejected = next(r for r in rows if r["event_type"] == "code_rejected")
    assert rejected["category"] == "security"
    assert rejected["outcome"] == "bad_code"
    assert rejected["user_name"] is None


async def test_a_duress_code_disarms_and_leaves_only_a_silent_trace(
    hass, with_user, freezer
):
    client = with_user
    await _armed(hass, client, freezer)
    result = await _ws(client, {"type": "foyer/disarm", "code": DURESS})

    assert result["success"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    rows = (await _ws(client, {"type": "foyer/log/query"}))["rows"]
    duress = next(r for r in rows if r["event_type"] == "duress")
    assert duress["severity"] == "alarm"
    assert duress["user_name"] == "Luca"
    # Nothing in what the person at the keypad is told differs from a normal
    # disarm: the answer carries no sign of it.
    assert "duress" not in str(result).lower()


# --- editing the configuration (§8.2) ---------------------------------------------


def _area_item(hass) -> dict:
    return {
        "id": _area(hass),
        "name": "Casa",
        "ha_state_when_armed": "armed_away",
        "default_entry_delay": 30,
        "default_exit_delay": 45,
        "response_profile_id": None,
        "require_code_to_arm": None,
        "require_code_to_disarm": None,
    }


async def test_editing_the_configuration_asks_for_a_code(hass, hass_ws_client, loaded):
    """§8.2: editing the configuration needs a code, once somebody holds one."""
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, ha_user_id=await _me(client))
    item = _area_item(hass)

    refused = await _ws(
        client, {"type": "foyer/config/save", "kind": "area", "item": item}
    )
    assert refused["reason"] == "code_required"

    accepted = await _ws(
        client,
        {"type": "foyer/config/save", "kind": "area", "item": item, "code": CODE},
    )
    assert accepted["success"], accepted
    # An accepted save schedules a reload. Waited for here, or the test ends
    # with a new entry setting itself up behind it — which on a fast runner is
    # a lingering task reported against whatever ran next.
    await hass.async_block_till_done()


async def test_a_non_administrator_needs_the_permission_to_configure(
    hass, hass_ws_client, hass_read_only_access_token, loaded
):
    """The permission is real for everybody the invariant does not already
    hand the house to: an administrator can rewrite .storage anyway (INV-6),
    and refusing them here would only lock an owner out of their own
    configuration."""
    admin = await hass_ws_client(hass)
    await _make_user(hass, admin, new_code=CODE)
    client = await hass_ws_client(hass, hass_read_only_access_token)

    refused = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "area",
            "item": _area_item(hass),
            "code": CODE,
        },
    )
    assert refused["reason"] == "not_permitted"


async def test_an_identified_user_can_be_exempt_from_the_code(
    hass, hass_ws_client, loaded, freezer
):
    """Decision 79: the exemption belongs to the person and needs the channel
    to identify them by itself."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass, client, new_code=CODE, ha_user_id=await _me(client), exempt=True
    )

    await _armed(hass, client, freezer)
    assert (await _ws(client, {"type": "foyer/disarm"}))["success"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


# --- the acknowledge button (§13, decision 77) ------------------------------------


async def test_the_acknowledge_button_exists_and_acknowledges(hass, loaded):
    assert hass.states.get("button.foyer_acknowledge") is not None
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.foyer_acknowledge"},
        blocking=True,
    )


async def test_an_administrator_is_asked_for_the_code_like_anybody_else(
    hass, with_user
):
    """Decision 101: being an administrator identifies nobody — the wall
    tablet is signed in as one. What they keep is never being locked out."""
    client = with_user
    save = {
        "type": "foyer/user/save",
        "user": {"name": "Anna", "permissions": ["arm", "disarm"]},
        "new_code": OTHER,
    }
    refused = await _ws(client, save)
    assert refused["success"] is False
    assert refused["reason"] == "code_required"

    saved = await _ws(client, {**save, "code": CODE})
    assert saved["success"], saved
    # The save reloads the entry; a reload still running at teardown races
    # the log fixture that unlinks the database (seen on CI).
    await hass.async_block_till_done()


async def test_a_restore_that_changes_people_needs_manage_users(
    hass, with_user, hass_ws_client, hass_read_only_user, hass_read_only_access_token
):
    """Decision 111: edit_config alone was a way to hand oneself every
    permission through a backup file."""
    admin = with_user
    await _make_user(
        hass,
        admin,
        name="Editor",
        new_code=OTHER,
        code=CODE,
        permissions=["edit_config"],
        ha_user_id=hass_read_only_user.id,
    )
    editor = await hass_ws_client(hass, hass_read_only_access_token)
    backup = await _ws(editor, {"type": "foyer/config/export", "code": OTHER})
    assert backup["document"], backup

    # The same file, unchanged: no person moves, edit_config is enough.
    same = await _ws(
        editor,
        {"type": "foyer/config/import", "document": backup["document"], "code": OTHER},
    )
    assert same["success"], same
    await hass.async_block_till_done()

    document = backup["document"]
    for person in document["config"]["users"]:
        if person["name"] == "Editor":
            person["permissions"] = [*person["permissions"], "manage_users"]
    refused = await _ws(
        editor, {"type": "foyer/config/import", "document": document, "code": OTHER}
    )
    assert refused["success"] is False
    assert refused["reason"] == "not_permitted"
    editor_now = next(u for u in hass.data[DOMAIN].config.users if u.name == "Editor")
    assert "manage_users" not in editor_now.permissions


async def test_an_editor_cannot_put_people_on_a_scenario_or_a_key(
    hass, with_user, hass_ws_client, hass_read_only_user, hass_read_only_access_token
):
    """Decision 112: edit_config alone does not decide who may do what."""
    admin = with_user
    await _make_user(
        hass,
        admin,
        name="Editor",
        new_code=OTHER,
        code=CODE,
        permissions=["edit_config"],
        ha_user_id=hass_read_only_user.id,
    )
    editor = await hass_ws_client(hass, hass_read_only_access_token)
    config = await _config(editor)
    editor_id = next(u["id"] for u in config["users"] if u["name"] == "Editor")

    scenario = config["scenarios"][0]
    renamed = await _ws(
        editor,
        {
            "type": "foyer/config/save",
            "kind": "scenario",
            "item": {**scenario, "name": "Out"},
            "code": OTHER,
        },
    )
    assert renamed["success"], renamed
    await hass.async_block_till_done()

    scenario = (await _config(editor))["scenarios"][0]
    listed = await _ws(
        editor,
        {
            "type": "foyer/config/save",
            "kind": "scenario",
            "item": {**scenario, "allowed_user_ids": [editor_id]},
            "code": OTHER,
        },
    )
    assert listed["success"] is False
    assert listed["reason"] == "not_permitted"
