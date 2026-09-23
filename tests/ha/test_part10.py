"""Phase 5 part 2 inside Home Assistant: the log is about people, and leaving.

The pure suite proves which rows are a person's and what is left of one
(tests/core/test_privacy.py). This proves the half only a real Home Assistant
can: that a file with somebody's rows in it comes back over the API, that
erasing them empties the columns in the database and leaves the events where
they are, that the daily sweep replaces a name with an identifier and does it
once, and that removing the integration takes its entities, its retained MQTT
message and — only if somebody said so — its log database with it.
"""

from __future__ import annotations

import json

from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
import pytest

from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.journal import system_row
from custom_components.foyer.store import log_store

from .conftest import ZONE
from .test_part2 import _set, _ws
from .test_phase2 import CODE, _make_user

CLEANER = "Ana Cleaner"
# Whoever runs the panel. Somebody else's code than the cleaner's, so that
# the rows the erasure writes are not the cleaner's own (decision 101: an
# administrator is asked for a code like anybody else).
OWNER_CODE = "864200"


async def _exists(hass, path: str) -> bool:
    """Off the event loop, like every other blocking call in this codebase."""
    import pathlib

    return await hass.async_add_executor_job(pathlib.Path(path).exists)


async def _rows(hass, **filters) -> list[dict]:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    result = await system.log.async_query(limit=1000, **filters)
    return result["rows"]


async def _disarm_as(hass, client, user_id: str) -> None:
    """A disarm attributed to somebody, so the log has a row about them."""
    await _ws(client, {"type": "foyer/disarm", "code": CODE})
    await hass.async_block_till_done()


@pytest.fixture
async def with_cleaner(hass, hass_ws_client, loaded):
    """One person with a code, and some rows in the log about them."""
    client = await hass_ws_client(hass)
    user_id = await _make_user(
        hass,
        client,
        name=CLEANER,
        new_code=CODE,
        permissions=["arm", "disarm", "view_log"],
    )
    await _make_user(
        hass,
        client,
        name="Owner",
        new_code=OWNER_CODE,
        code=CODE,
        permissions=["arm", "disarm", "view_log", "manage_users", "edit_config"],
    )
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    await _ws(client, {"type": "foyer/arm", "scenario_id": scenario_id, "code": CODE})
    await hass.async_block_till_done()
    await _ws(client, {"type": "foyer/disarm", "code": CODE})
    await hass.async_block_till_done()
    return client, user_id


# --- one person's rows, in a file (§10.4) ------------------------------------------


async def test_a_person_can_be_handed_every_row_that_names_them(hass, with_cleaner):
    """The acceptance: somebody asks for their data and gets a file with their
    rows in it, and with nobody else's."""
    client, user_id = with_cleaner
    result = await _ws(
        client, {"type": "foyer/privacy/export", "user_id": user_id, "format": "json"}
    )
    rows = json.loads(result["content"])
    assert rows, result
    assert any(row["event_type"] == "disarmed" for row in rows)
    # Every row is about them: what they did, or — for the configuration row
    # that created their account — what was done to them. Nobody else's.
    assert all(
        row["user_id"] == user_id or row["detail"].get("item_id") == user_id
        for row in rows
    )
    # Named after the person, because the file is handed to them.
    assert "ana-cleaner" in result["filename"]


async def test_the_export_is_the_export_of_10_3_in_its_other_shape(hass, with_cleaner):
    """CSV as well, with the same columns: a second caller of the existing
    export and not a second export."""
    client, user_id = with_cleaner
    result = await _ws(
        client, {"type": "foyer/privacy/export", "user_id": user_id, "format": "csv"}
    )
    header = result["content"].splitlines()[0]
    assert header.split(",") == list(log_store.CSV_COLUMNS)


async def test_the_preview_says_what_each_key_found(hass, with_cleaner):
    client, user_id = with_cleaner
    counts = await _ws(client, {"type": "foyer/privacy/preview", "user_id": user_id})
    assert counts["by_id"] > 0
    assert counts["total"] >= counts["by_id"]
    # The export is at least as wide as the erasure: it carries the rows where
    # this person is the subject rather than the actor.
    assert counts["wide"] >= counts["total"]


# --- taking a person out, and leaving the events (§10.4) ---------------------------


async def test_erasing_a_person_keeps_every_event(hass, with_cleaner):
    """The acceptance, and the whole point of §10.4: the log still answers
    what happened, and no longer answers who."""
    client, user_id = with_cleaner
    before = len(await _rows(hass))
    disarms = [r for r in await _rows(hass) if r["event_type"] == "disarmed"]
    assert disarms

    result = await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": user_id, "code": OWNER_CODE}
    )
    assert result["success"], result
    assert result["removed"] > 0

    after = await _rows(hass)
    # Not one row fewer — and one more, which is the erasure recording itself
    # (§10.3's rule applied here, part 2 decision 2).
    assert len(after) == before + 1
    # And the disarm is still there, still saying when and where.
    survived = [r for r in after if r["event_type"] == "disarmed"]
    assert len(survived) == len(disarms)
    assert survived[0]["ts"] == disarms[0]["ts"]
    assert survived[0]["area_id"] == disarms[0]["area_id"]
    # But it no longer says who, nor through what.
    assert survived[0]["user_id"] is None
    assert survived[0]["user_name"] is None
    assert survived[0]["channel"] is None
    assert not any(CLEANER in json.dumps(row) for row in after)


async def test_erasing_a_person_is_not_deleting_a_user(hass, with_cleaner):
    """The two operations are separate on purpose: ``user_name`` is
    denormalised so that deleting a user does not erase the history."""
    client, user_id = with_cleaner
    await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": user_id, "code": OWNER_CODE}
    )
    await hass.async_block_till_done()
    # The person is still a user of this installation, with their code.
    assert hass.data[DOMAIN].config.user(user_id) is not None


async def test_the_erasure_is_recorded_and_does_not_name_the_person(hass, with_cleaner):
    """Deleting the log is logged (§10.3) and so is this — but the row that
    records an erasure must not carry the name it just removed."""
    client, user_id = with_cleaner
    await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": user_id, "code": OWNER_CODE}
    )
    rows = await _rows(hass, categories=["config"])
    erasures = [r for r in rows if r["event_type"] == "config_history_erased"]
    assert erasures, rows
    row = erasures[0]
    assert row["detail"]["changes"]["rows"] > 0
    assert CLEANER not in json.dumps(row)
    assert user_id not in json.dumps(row)


async def test_erasing_with_a_pseudonym_keeps_the_shape(hass, with_cleaner):
    client, user_id = with_cleaner
    await _ws(
        client,
        {
            "type": "foyer/privacy/erase",
            "user_id": user_id,
            "pseudonymise": True,
            "code": OWNER_CODE,
        },
    )
    rows = [r for r in await _rows(hass) if r["event_type"] == "disarmed"]
    pseudonym = hass.data[DOMAIN].config.user(user_id).pseudonym
    assert pseudonym and pseudonym.startswith("person-")
    assert rows[0]["user_name"] == pseudonym
    assert CLEANER not in json.dumps(rows[0])


async def test_erasing_is_refused_without_the_permission(
    hass, with_cleaner, hass_ws_client, hass_read_only_access_token
):
    """manage_users owns people; view_log only reads (part 2 decision 3)."""
    _, user_id = with_cleaner
    limited = await hass_ws_client(hass, hass_read_only_access_token)
    await limited.send_json(
        {"id": 91, "type": "foyer/privacy/erase", "user_id": user_id}
    )
    msg = await limited.receive_json()
    assert msg["result"]["success"] is False
    assert msg["result"]["reason"] == "not_permitted"
    # And nothing moved: the rows still say who.
    assert any(row["user_name"] == CLEANER for row in await _rows(hass))


async def test_exporting_is_refused_without_the_permission(
    hass, with_cleaner, hass_ws_client, hass_read_only_access_token
):
    """A read of the log is still a read of the log: view_log or nothing.

    The consequence, stated in docs/privacy.md rather than left to be found:
    somebody who is not an administrator of this installation cannot fetch
    their own rows, and a subject access request in a B&B or a small office
    goes through whoever administers it."""
    _, user_id = with_cleaner
    limited = await hass_ws_client(hass, hass_read_only_access_token)
    await limited.send_json(
        {
            "id": 92,
            "type": "foyer/privacy/export",
            "user_id": user_id,
            "format": "json",
        }
    )
    msg = await limited.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "not_permitted"


# --- the daily sweep (§10.4) --------------------------------------------------------


async def _sweep(hass) -> int:
    system = hass.data[DOMAIN]
    await system.log.async_flush()
    await system._async_pseudonymise()
    return len(await _rows(hass))


async def test_the_sweep_does_nothing_until_it_is_switched_on(hass, with_cleaner):
    """Off by default: it trades away the question the log exists to answer."""
    await _sweep(hass)
    assert any(row["user_name"] == CLEANER for row in await _rows(hass))


async def _switch_on(hass, client, days: int = 1, code: str = OWNER_CODE) -> dict:
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    log = {**settings["log"], "pseudonymise_after": days}
    result = await _ws(
        client,
        {
            "type": "foyer/config/settings",
            "settings": {**settings, "log": log},
            "code": code,
        },
    )
    await hass.async_block_till_done()
    return result


async def test_the_sweep_replaces_a_name_with_an_identifier(
    hass, with_cleaner, freezer
):
    """Past the delay the names are gone and the shape of the nights is not —
    the acceptance, with the clock moved instead of waited out.

    Two days past a delay of one, rather than thirty-one past thirty: the
    retention purge is thirty days for every category, and a clock moved that
    far forward deletes the very rows this is about.
    """
    client, user_id = with_cleaner
    assert (await _switch_on(hass, client, days=1))["success"]
    system = hass.data[DOMAIN]
    pseudonym = system.config.user(user_id).pseudonym

    freezer.tick(2 * 24 * 3600)
    await system._async_pseudonymise()

    rows = [r for r in await _rows(hass) if r["event_type"] == "disarmed"]
    assert rows
    assert all(row["user_name"] == pseudonym for row in rows)
    # The shape survives: same rows, same times, same areas.
    assert all(row["area_id"] for row in rows)
    assert not any(CLEANER in json.dumps(row) for row in await _rows(hass))


async def test_the_sweep_leaves_rows_that_are_not_old_enough(hass, with_cleaner):
    """It is a delay, not a switch: what happened this morning still says who."""
    client, _ = with_cleaner
    assert (await _switch_on(hass, client, days=30))["success"]
    await hass.data[DOMAIN]._async_pseudonymise()
    assert any(row["user_name"] == CLEANER for row in await _rows(hass))


async def test_switching_the_sweep_on_and_off_is_both_recorded(hass, with_cleaner):
    """The one configuration change whose absence from the record would be
    the most convenient (part 2 decision 5)."""
    client, _ = with_cleaner
    await _switch_on(hass, client, days=30)
    await _switch_on(hass, client, days=0)
    rows = [
        r
        for r in await _rows(hass, categories=["config"])
        if r["event_type"] == "config_pseudonymisation"
    ]
    assert len(rows) == 2
    assert {row["detail"]["changes"]["to"] for row in rows} == {30, None}


async def test_a_pseudonymisation_delay_out_of_range_is_refused(hass, with_cleaner):
    client, _ = with_cleaner
    result = await _switch_on(hass, client, days=4000)
    assert not result["success"]
    assert result["problems"][0]["field"] == "pseudonymise_after"


# --- leaving (§16) ------------------------------------------------------------------


async def test_removing_the_integration_leaves_no_entity_behind(hass, loaded):
    """The acceptance: hass removes the integration and the entity registry
    is empty of Foyer."""
    registry = er.async_get(hass)
    assert er.async_entries_for_config_entry(registry, loaded.entry_id)
    assert await hass.config_entries.async_remove(loaded.entry_id)
    await hass.async_block_till_done()
    assert not er.async_entries_for_config_entry(registry, loaded.entry_id)
    assert "foyer" not in hass.data.get("frontend_panels", {})


async def test_the_log_database_is_kept_unless_somebody_said_otherwise(
    hass, hass_ws_client, loaded, tmp_path
):
    """§16 says ask rather than guess, so keeping is what an installation
    that never answered gets."""
    path = hass.data[DOMAIN].log.path
    assert await hass.config_entries.async_remove(loaded.entry_id)
    await hass.async_block_till_done()
    assert await _exists(hass, path)


async def test_the_log_database_goes_when_the_switch_says_so(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    log = {**settings["log"], "delete_on_uninstall": True}
    result = await _ws(
        client,
        {"type": "foyer/config/settings", "settings": {**settings, "log": log}},
    )
    assert result["success"], result
    await hass.async_block_till_done()

    path = hass.data[DOMAIN].log.path
    assert await _exists(hass, path)
    assert await hass.config_entries.async_remove(loaded.entry_id)
    await hass.async_block_till_done()
    assert not await _exists(hass, path)


async def test_a_notification_foyer_put_up_comes_down_with_it(
    hass, loaded, monkeypatch
):
    """A persistent notification lives in memory, so the only ones that exist
    when Foyer is removed are the ones this process created — which is exactly
    the set `notices` keeps, and why there is a set at all."""
    from custom_components.foyer.runtime import notices

    dismissed: list[str] = []
    monkeypatch.setattr(
        notices.persistent_notification,
        "async_dismiss",
        lambda hass, notification_id: dismissed.append(notification_id),
    )

    notices.async_create(hass, "test", title=None, notification_id="foyer_test")
    await hass.async_block_till_done()

    assert await hass.config_entries.async_remove(loaded.entry_id)
    await hass.async_block_till_done()
    assert "foyer_test" in dismissed


async def test_the_retained_message_is_cleared_rather_than_left_talking(
    hass, hass_ws_client, loaded, monkeypatch
):
    """A retained message outlives the integration and keeps telling whoever
    connects next what the house was doing (§16, decision 83)."""
    from custom_components.foyer.runtime import mqtt

    published: list[tuple[str, str, bool]] = []

    async def fake_publish(hass, topic, payload, qos=0, retain=False):
        published.append((topic, payload, retain))

    async def fake_wait(hass):
        return True

    import sys
    import types

    import homeassistant.components as ha_components

    fake = types.SimpleNamespace(
        async_publish=fake_publish, async_wait_for_mqtt_client=fake_wait
    )
    # Both, and not one: `from homeassistant.components import mqtt` reads the
    # attribute on the package once anything has imported it for real, and
    # another test in this suite has.
    monkeypatch.setitem(sys.modules, "homeassistant.components.mqtt", fake)
    monkeypatch.setattr(ha_components, "mqtt", fake, raising=False)

    client = await hass_ws_client(hass)
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    result = await _ws(
        client,
        {
            "type": "foyer/config/settings",
            "settings": {**settings, "mqtt": {**settings["mqtt"], "enabled": True}},
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    published.clear()

    assert await hass.config_entries.async_remove(loaded.entry_id)
    await hass.async_block_till_done()

    cleared = [p for p in published if p[1] == "" and p[2]]
    assert cleared, published
    assert cleared[0][0].endswith("/state")
    assert mqtt is not None


async def test_the_zone_is_still_there_to_be_watched(hass, loaded):
    """A guard for the fixture above: the tests in this file that remove the
    entry must not leave the next one looking at a half-loaded system."""
    await _set(hass, ZONE, "off")
    assert hass.states.get(ZONE) is not None


# --- what the review found, kept found ---------------------------------------------


async def _config_row_about(hass, user_id: str) -> dict:
    rows = await _rows(hass, categories=["config"])
    return next(r for r in rows if r["detail"].get("item_id") == user_id)


async def test_erasing_a_person_does_not_blank_whoever_edited_their_account(
    hass, with_cleaner
):
    """A configuration row *about* somebody carries their id in the detail and
    somebody else in the user columns — whoever created the account. Blanking
    those columns would destroy the audit record of a third party who asked
    for nothing."""
    client, user_id = with_cleaner
    before = await _config_row_about(hass, user_id)
    assert before["user_name"]

    await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": user_id, "code": OWNER_CODE}
    )

    rows = await _rows(hass, categories=["config"])
    # The row is still there, still says who did the editing, and no longer
    # says which account it was about.
    kept = [r for r in rows if r["user_name"] == before["user_name"]]
    assert kept
    assert not any(r["detail"].get("item_id") == user_id for r in rows)


async def test_the_sweep_leaves_configuration_rows_about_a_person_alone(
    hass, with_cleaner, freezer
):
    """Stamping this person's pseudonym on a row somebody else wrote would not
    be minimisation but a false attribution: the row would say they edited
    their own account."""
    client, user_id = with_cleaner
    before = await _config_row_about(hass, user_id)
    editor = before["user_name"]
    assert (await _switch_on(hass, client, days=1))["success"]

    freezer.tick(2 * 24 * 3600)
    await hass.data[DOMAIN]._async_pseudonymise()

    after = await _config_row_about(hass, user_id)
    assert after["user_name"] == editor


async def test_two_people_with_one_name_are_not_merged(hass, hass_ws_client, loaded):
    """The name clause is qualified by the account, or erasing one person
    would erase the other's rows and the sweep would merge both histories
    under whichever pseudonym came first."""
    client = await hass_ws_client(hass)
    first = await _make_user(hass, client, name="Luca", new_code=CODE)
    second = await _make_user(hass, client, name="Luca", new_code="135790", code=CODE)
    system = hass.data[DOMAIN]
    # A row for each of them, written the way a keypad writes one.
    system.async_record(
        (
            system_row(
                dt_util.utcnow(), event_type="test", user_id=second, user_name="Luca"
            ),
        )
    )
    await system.log.async_flush()

    result = await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": first, "code": "135790"}
    )
    assert result["success"], result
    rows = await _rows(hass)
    # The other Luca's row is untouched.
    assert any(r["user_id"] == second and r["user_name"] == "Luca" for r in rows)


async def test_a_person_can_still_be_erased_after_a_sweep(hass, with_cleaner, freezer):
    """The pseudonym is one of the keys the erasure searches on. Without it,
    an installation with the sweep on could never erase anybody properly, and
    the mapping back to the name is still in the configuration."""
    client, user_id = with_cleaner
    assert (await _switch_on(hass, client, days=1))["success"]
    freezer.tick(2 * 24 * 3600)
    await hass.data[DOMAIN]._async_pseudonymise()
    pseudonym = hass.data[DOMAIN].config.user(user_id).pseudonym
    assert any(r["user_name"] == pseudonym for r in await _rows(hass))

    result = await _ws(
        client, {"type": "foyer/privacy/erase", "user_id": user_id, "code": OWNER_CODE}
    )
    assert result["success"] and result["removed"] > 0
    rows = await _rows(hass)
    assert not any(r["user_name"] == pseudonym for r in rows)
    disarms = [r for r in rows if r["event_type"] == "disarmed"]
    assert disarms and all(r["channel"] is None for r in disarms)


async def test_the_sweep_takes_the_name_out_of_the_detail_too(
    hass, hass_ws_client, loaded, freezer
):
    """A row's detail carries names by the side door — a configuration row
    summarises what changed by the name of the thing. A pseudonymisation that
    left them there would not have replaced the name at all."""
    client = await hass_ws_client(hass)
    user_id = await _make_user(hass, client, name="Ana Cleaner", new_code=CODE)
    system = hass.data[DOMAIN]
    system.async_record(
        (
            system_row(
                dt_util.utcnow(),
                event_type="test",
                user_id=user_id,
                user_name="Ana Cleaner",
                detail={"changes": {"devices": {"added": ["Ana Cleaner's tag"]}}},
            ),
        )
    )
    await system.log.async_flush()
    assert (await _switch_on(hass, client, days=1, code=CODE))["success"]

    freezer.tick(2 * 24 * 3600)
    await hass.data[DOMAIN]._async_pseudonymise()

    assert not any("Ana Cleaner" in json.dumps(r) for r in await _rows(hass))


async def test_saving_one_log_setting_keeps_the_other_two(hass, with_cleaner):
    """A save that moved a retention slider must not switch off a privacy
    setting it never mentioned."""
    client, _ = with_cleaner
    assert (await _switch_on(hass, client, days=30))["success"]
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    log = {"enabled": settings["log"]["enabled"], "retention_days": {"arming": 7}}
    result = await _ws(
        client,
        {
            "type": "foyer/config/settings",
            "settings": {**settings, "log": log},
            "code": OWNER_CODE,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.settings.log.pseudonymise_after == 30


async def test_a_client_cannot_choose_somebody_else_pseudonym(hass, with_cleaner):
    """It is the identifier a person's already-swept rows carry: a caller that
    could set it could merge two histories under one identifier."""
    client, user_id = with_cleaner
    mine = hass.data[DOMAIN].config.user(user_id).pseudonym
    result = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {
                "id": user_id,
                "name": CLEANER,
                "permissions": ["arm", "disarm"],
                "pseudonym": "person-chosen",
                "enabled": True,
            },
            "code": OWNER_CODE,
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()
    assert hass.data[DOMAIN].config.user(user_id).pseudonym == mine


async def test_a_configuration_it_cannot_read_stops_the_setup(
    hass, entry, hass_storage
):
    """Found in review, and it was the worst thing in this branch: a guard
    written for the removal landed in the setup, where `config is None` means
    "first run" — so an unreadable document was answered by seeding a fresh
    one over it, losing every area, user and code hash in silence."""
    hass.states.async_set(ZONE, "off")
    # Written by a major version this build does not understand, which is what
    # `migrate` refuses rather than reading half of.
    stored = {
        "version": 99,
        "minor_version": 1,
        "key": "foyer.config",
        "data": {"areas": [{"id": "a1", "name": "Casa"}]},
    }
    hass_storage["foyer.config"] = dict(stored)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    # And the document is exactly as it was: nothing seeded over it.
    assert hass_storage["foyer.config"] == stored


async def test_a_persons_own_configuration_changes_are_reachable(
    hass, hass_ws_client, loaded, hass_admin_user
):
    """A configuration row records the *Home Assistant* account that saved it,
    which is a different namespace from the Foyer user id every other row
    carries. Found in review: without this, erasing somebody left every
    change they had ever made from the panel with their name on it, and the
    preview said it had found nothing."""
    client = await hass_ws_client(hass)
    user_id = await _make_user(
        hass,
        client,
        name=CLEANER,
        new_code=CODE,
        permissions=["arm", "disarm", "edit_config"],
        ha_user_id=hass_admin_user.id,
    )
    # Something saved from the panel, as that person.
    system = hass.data[DOMAIN]
    settings = (await _ws(client, {"type": "foyer/config"}))["config"]["settings"]
    # With the code: this person holds one now, and §8.2 asks for it to edit.
    await _ws(
        client,
        {"type": "foyer/config/settings", "settings": settings, "code": CODE},
    )
    await hass.async_block_till_done()

    rows = await _rows(hass, categories=["config"])
    saved = [r for r in rows if r["event_type"] == "config_save"]
    assert saved and saved[0]["user_id"] == user_id, saved

    counts = await _ws(client, {"type": "foyer/privacy/preview", "user_id": user_id})
    assert counts["by_id"] > 0
    erased = await _ws(
        client,
        {"type": "foyer/privacy/erase", "user_id": user_id, "code": CODE},
    )
    assert erased["success"], erased
    left = [r for r in await _rows(hass) if CLEANER in json.dumps(r)]
    # Only the row recording the erasure, which names whoever performed it —
    # and here that is the same person, who performed it on themselves.
    assert [r["event_type"] for r in left] == ["config_history_erased"]
    assert system is not None
