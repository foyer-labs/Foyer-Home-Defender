"""A duress code inside Home Assistant (SPEC §8.1, decisions 131-134).

tests/core/test_duress.py proves the engine's half: one `duress` for every
request the code comes with, answered by the default profile, silent, never
held back by a walk test. This is the other half — every way a code reaches
Foyer raises it, with the name of what was asked, and none of the screens a
glance would find shows it: the Overview's recent events, the last-event
sensor, an API device's log and its change notice.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import pytest

from custom_components.foyer.api import device_api
from custom_components.foyer.api.backup import backup_document
from custom_components.foyer.const import DOMAIN

from .conftest import MASTER, PANEL_ENTITY
from .test_part2 import _IDS, _advance, _state, _ws
from .test_phase2 import CODE, DURESS, _make_user
from .test_services import KEYPAD, SCENARIO, _call, _rows, _save

EVERYTHING = [
    "arm",
    "disarm",
    "bypass_zone",
    "change_scenario",
    "view_log",
    "edit_config",
    "manage_users",
    "test_actions",
]


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


async def _duress_rows(hass) -> list[dict]:
    return [r for r in await _rows(hass) if r["event_type"] == "duress"]


def _with(hass, device_id: str, **changes) -> None:
    """Give the endpoint's device other scopes, as page 8 would save them."""
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        devices=tuple(
            replace(d, **changes) if d.id == device_id else d
            for d in system.config.devices
        ),
    )


@pytest.fixture
async def house(hass, hass_ws_client, hass_client_no_auth, loaded):
    """One person with a code and a duress code, and a keypad on the endpoint."""
    client = await hass_ws_client(hass)
    await _make_user(
        hass, client, new_code=CODE, new_duress_code=DURESS, permissions=EVERYTHING
    )
    await _save(
        hass,
        client,
        "device",
        {
            "name": "Hall keypad",
            "kind": "keypad",
            "ref": KEYPAD,
            "transport": "http",
            "scopes": ["status", "arm", "disarm"],
        },
        code=CODE,
    )
    device_id = (await _config(client))["devices"][0]["id"]
    answer = await _ws(
        client, {"type": "foyer/device/token", "device_id": device_id, "code": CODE}
    )
    await hass.async_block_till_done()
    http = await hass_client_no_auth()
    return SimpleNamespace(
        client=client, http=http, token=answer["token"], device_id=device_id
    )


async def _post(house, body: dict):
    response = await house.http.post(
        "/api/foyer/device",
        json=body,
        headers={"Authorization": f"Bearer {house.token}"},
    )
    return await response.json()


# --- the panel: one `duress` per command, named for what it was ------------------


async def test_a_panel_command_names_what_it_was_for(hass, house):
    """Decision 134: a backup downloaded is not "edit the configuration". And
    the command answers exactly as it does for the ordinary code."""
    ordinary = await _ws(house.client, {"type": "foyer/config/export", "code": CODE})
    assert await _duress_rows(hass) == []

    coerced = await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
    assert coerced.keys() == ordinary.keys()
    assert coerced["document"]["config"] == ordinary["document"]["config"]
    (row,) = await _duress_rows(hass)
    assert row["detail"]["operation"] == "export_config"
    assert row["user_name"] == "Luca"
    assert row["category"] == "security" and row["severity"] == "alarm"
    assert row["area_id"] is None and row["incident_id"] is None


async def test_the_bus_hears_it_as_every_row(hass, house):
    """Decision 133: `foyer_event` carries it, which is how an automation of
    the household's answers duress — here for a log emptied under it."""
    heard: list[dict] = []

    @callback
    def listen(event) -> None:
        heard.append(event.data)

    hass.bus.async_listen("foyer_event", listen)
    answer = await _ws(house.client, {"type": "foyer/log/clear", "code": DURESS})
    await hass.async_block_till_done()

    assert answer["success"]
    duress = [e for e in heard if e["event_type"] == "duress"]
    assert [e["detail"]["operation"] for e in duress] == ["clear_log"]


async def test_every_command_the_code_is_sent_with_raises_it_again(hass, house):
    """The panel keeps a code for two minutes (§15.1), and every command
    sent with it in that time is one more thing the person was made to do."""
    for _ in range(2):
        answer = await _ws(
            house.client, {"type": "foyer/config/export", "code": DURESS}
        )
        assert answer["document"]

    rows = await _duress_rows(hass)
    assert [r["detail"]["operation"] for r in rows] == ["export_config"] * 2


async def test_a_configuration_saved_with_a_duress_code_is_saved(hass, house):
    area = (await _config(house.client))["areas"][0]
    area["name"] = "Home"
    await _save(hass, house.client, "area", area, code=DURESS)

    assert hass.data[DOMAIN].config.areas[0].name == "Home"
    (row,) = await _duress_rows(hass)
    assert row["detail"]["operation"] == "edit_config"


async def test_ones_own_duress_code_offered_as_a_new_code_is_not_a_use(hass, house):
    """A collision, counted as a wrong code (§8.4) and nothing more (§8.1).
    The one `duress` here is the gate's, because the gate's code was it."""
    user_id = hass.data[DOMAIN].config.users[0].id
    person = {"id": user_id, "name": "Luca", "permissions": EVERYTHING}
    answer = await _ws(
        house.client,
        {"type": "foyer/user/save", "user": person, "new_code": DURESS, "code": CODE},
    )
    assert answer["success"] is False
    assert await _duress_rows(hass) == []
    rejected = [r for r in await _rows(hass) if r["event_type"] == "code_rejected"]
    assert rejected

    answer = await _ws(
        house.client,
        {"type": "foyer/user/save", "user": person, "new_code": DURESS, "code": DURESS},
    )
    assert answer["success"] is False
    assert [r["detail"]["operation"] for r in await _duress_rows(hass)] == [
        "edit_config"
    ]


async def test_a_rehearsal_raises_it_and_its_trace_does_not_show_it(hass, house):
    """§11.2: the request raises `duress`; the trace is the ordinary code's."""
    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    trace = await _ws(
        house.client,
        {"type": "foyer/simulate", "scenario_id": scenario_id, "code": DURESS},
    )

    assert "duress" not in str(trace)
    (row,) = await _duress_rows(hass)
    assert row["detail"]["operation"] == "simulate"


# --- the services -----------------------------------------------------------------


async def test_a_service_raises_it_once_per_call(hass, house):
    """A restore that touches people asks the code once and the permission
    twice (decision 111); the code is spent once, and so is the duress."""
    system = hass.data[DOMAIN]
    document = backup_document(system.config)
    document["config"]["users"][0]["name"] = "Luca B."
    result = await _call(hass, "import_config", code=DURESS, document=document)
    await hass.async_block_till_done()

    assert result["success"], result
    assert hass.data[DOMAIN].config.users[0].name == "Luca B."
    assert [r["detail"]["operation"] for r in await _duress_rows(hass)] == [
        "import_config"
    ]


async def test_the_alarm_panel_entity_raises_it(hass, house):
    """Home Assistant's own card and the actions a signed-in account calls."""
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": MASTER, "code": DURESS},
        blocking=True,
    )
    await hass.async_block_till_done()

    (row,) = await _duress_rows(hass)
    assert row["detail"] == {"operation": "arm", "mode": "armed_away"}


# --- the device endpoint (§9.2.2) --------------------------------------------------


async def test_a_duress_code_unlocks_a_device_as_the_ordinary_one_does(hass, house):
    answer = await _post(house, {"action": "unlock", "code": DURESS})

    assert answer["success"] and answer["until"]
    rows = await _rows(hass, category="security")
    assert any(r["event_type"] == "device_unlocked" for r in rows)
    (row,) = await _duress_rows(hass)
    assert row["detail"]["operation"] == "unlock"
    assert row["device_id"] == house.device_id


async def test_a_refusal_before_the_engine_raises_it_and_counts_nothing(hass, house):
    """A device without the `exclude` scope refuses before the engine hears
    anything (decision 131): the duress, and nothing else — the same answer,
    and no lockout counter moved."""
    system = hass.data[DOMAIN]
    zone = system.config.zones[0]
    before = dict(system.state.lockouts)
    plain = await _post(house, {"action": "exclude", "zone": zone.id, "code": CODE})
    assert await _duress_rows(hass) == []

    coerced = await _post(house, {"action": "exclude", "zone": zone.id, "code": DURESS})

    assert coerced == plain
    assert coerced["reason"] == "scope_not_granted"
    (row,) = await _duress_rows(hass)
    assert row["detail"]["operation"] == "bypass_zone"
    assert row["detail"]["zone"] == zone.id
    assert dict(hass.data[DOMAIN].state.lockouts) == before


async def test_a_device_log_never_lists_it_and_pages_as_it_says(hass, house):
    """Decision 133: a display in the hall reads the log to whoever is there.
    Left out by the query, so a page of five is five rows."""
    _with(
        hass,
        house.device_id,
        scopes=frozenset({"status", "log"}),
        free_scopes=frozenset({"status", "log"}),
        clear_text_confirmed=True,
    )
    for _ in range(4):
        await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
        await _ws(house.client, {"type": "foyer/config/export", "code": CODE})
    assert len(await _duress_rows(hass)) == 4

    seen: list[dict] = []
    cursor = None
    while True:
        query = {"limit": "3", **({"before": cursor} if cursor else {})}
        response = await house.http.get(
            "/api/foyer/device/log",
            headers={"Authorization": f"Bearer {house.token}"},
            params=query,
        )
        body = await response.json()
        assert len(body["rows"]) == 3 or body["next"] is None
        seen.extend(body["rows"])
        cursor = body["next"]
        if cursor is None:
            break
    assert seen
    assert all(r["event_type"] != "duress" for r in seen)
    hidden = len([r for r in await _rows(hass) if r["event_type"] != "duress"])
    assert len(seen) == hidden


async def test_nothing_a_glance_finds_changes(hass, house):
    """The dashboard sensor and the stream's `log` notice read the same last
    row: a request whose only row is `duress` moves neither (decision 133)."""
    armed = await _post(house, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    assert armed["success"]
    _with(
        hass,
        house.device_id,
        scopes=frozenset({"status", "log"}),
        free_scopes=frozenset({"status", "log"}),
        clear_text_confirmed=True,
    )
    system = hass.data[DOMAIN]
    device = system.config.device(house.device_id)
    last = hass.states.get("sensor.foyer_last_event").state
    notice = device_api.fingerprints(hass, system, device, False)["log"]

    await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
    await hass.async_block_till_done()

    assert len(await _duress_rows(hass)) == 1
    assert hass.states.get("sensor.foyer_last_event").state == last != "duress"
    assert device_api.fingerprints(hass, system, device, False)["log"] == notice


async def test_a_failed_answer_to_it_is_not_the_last_event_either(hass, house):
    """The action rows that answer `duress` are its rows too: a notification
    that failed is news on a dashboard, and this one would be news of the
    wrong kind, on the tablet the code was typed at."""

    async def broken(call) -> None:
        raise HomeAssistantError("nobody home")

    hass.services.async_register("notify", "broken", broken)
    profile = (await _config(house.client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["duress"],
            "name": "",
            "params": {"service": "notify.broken", "message": "{{ user }}"},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, house.client, "profile", profile, code=CODE)
    system = hass.data[DOMAIN]
    last = system.last_row

    await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
    await hass.async_block_till_done()

    failed = [
        r
        for r in await _rows(hass, category="action")
        if r["detail"].get("moment") == "duress"
    ]
    assert failed and failed[0]["outcome"] == "failed"
    # What the sensor and the stream's notice read, read directly: the
    # failure is recorded after the decision has told the entities.
    assert system.last_row is last


async def test_the_built_in_message_says_what_was_asked_in_words(hass, house):
    """The house's own text for `duress` names the operation, translated —
    the engine hands an identifier — and has no empty place where an area
    used to go. A Home Assistant notification is the wrong answer to it
    (§6.1); it is used here only because it is the one that shows the text."""
    from homeassistant.components.persistent_notification import (
        DOMAIN as NOTIFICATIONS,
    )

    profile = (await _config(house.client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "persistent_notification",
            "moments": ["duress"],
            "name": "",
            "params": {},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, house.client, "profile", profile, code=CODE)
    await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
    await hass.async_block_till_done()

    (shown,) = [
        n
        for n in hass.data[NOTIFICATIONS].values()
        if n["notification_id"].endswith("_duress")
    ]
    assert shown["message"].startswith("Luca used a duress code at ")
    assert shown["message"].endswith("(Export the configuration).")


async def test_the_overview_asks_for_what_a_glance_may_find(hass, house):
    """The query the Overview's recent events send, and the one the log
    page sends: the row is on one and never on the other."""
    await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
    everything = await _ws(house.client, {"type": "foyer/log/query"})
    glance = await _ws(
        house.client,
        {
            "type": "foyer/log/query",
            "limit": 6,
            "categories": ["arming", "alarm", "security", "system"],
            "glance": True,
        },
    )

    assert any(r["event_type"] == "duress" for r in everything["rows"])
    assert all(r["event_type"] != "duress" for r in glance["rows"])
    # Six rows are still six: what is left out is left out by the query.
    shown = [
        r
        for r in everything["rows"]
        if r["category"] in ("arming", "alarm", "security", "system")
        and r["event_type"] != "duress"
    ]
    assert glance["total"] == len(shown)
    assert glance["rows"] == shown[:6]


# --- a keypad on the broker (§9.2) -------------------------------------------------


@pytest.fixture
def expected_lingering_timers() -> bool:
    """The MQTT component keeps its own periodic timers running."""
    return True


async def test_a_keypad_on_the_broker_raises_it(hass, house, mqtt_mock, freezer):
    import json

    from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

    await _save(
        hass,
        house.client,
        "device",
        {"name": "Garden keypad", "kind": "keypad", "ref": "keypad_garden"},
        code=CODE,
    )
    settings = (await _config(house.client))["settings"]
    settings["mqtt"] = {
        "enabled": True,
        "command_topic": "house/alarm/cmd",
        "state_topic": "house/alarm/state",
        "detail": "minimal",
        "retain": True,
        "qos": 1,
    }
    answer = await _ws(
        house.client,
        {"type": "foyer/config/settings", "settings": settings, "code": CODE},
    )
    assert answer["success"], answer
    await hass.async_block_till_done()

    async def send(payload: dict) -> None:
        async_fire_mqtt_message(hass, "house/alarm/cmd", json.dumps(payload))
        await hass.async_block_till_done()

    await send(
        {
            "action": "arm",
            "scenario": SCENARIO,
            "code": CODE,
            "device_id": "keypad_garden",
        }
    )
    await _advance(hass, freezer, 31)
    await send({"action": "disarm", "code": DURESS, "device_id": "keypad_garden"})
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    # An action the contract does not have is refused before the engine, and
    # still raises it; a device nobody declared never had its code read.
    await send({"action": "dance", "code": DURESS, "device_id": "keypad_garden"})
    await send({"action": "disarm", "code": DURESS, "device_id": "keypad_nobody"})

    rows = await _duress_rows(hass)  # newest first
    assert [r["detail"]["operation"] for r in rows] == ["unknown_action", "disarm"]
    assert all(r["channel"] == "keypad" for r in rows)


# --- the review of this item -------------------------------------------------------


async def _raw(client, message: dict) -> dict:
    """The whole answer, an error included: a refusal is part of what must
    be the same for both codes."""
    await client.send_json({"id": next(_IDS), **message})
    answer = await client.receive_json()
    answer.pop("id")
    return answer


@pytest.mark.parametrize(
    ("message", "operation"),
    [
        ({"type": "foyer/arm"}, "arm"),
        ({"type": "foyer/arm", "force": True}, "force_arm"),
        (
            {
                "type": "foyer/auto/suspend",
                "kind": "until",
                "start": "not a time",
                "until": "nor this",
            },
            "suspend_auto_arming",
        ),
    ],
)
async def test_a_panel_command_refused_before_the_engine_raises_it(
    hass, house, message, operation
):
    """Decision 131: refused after the code was read, and before the engine
    heard anything. The duress, the same error, and no counter moved."""
    before = dict(hass.data[DOMAIN].state.lockouts)
    plain = await _raw(house.client, {**message, "code": CODE})
    assert plain["success"] is False
    assert await _duress_rows(hass) == []

    coerced = await _raw(house.client, {**message, "code": DURESS})

    assert coerced == plain
    (row,) = await _duress_rows(hass)
    assert row["detail"] == {"operation": operation}
    assert dict(hass.data[DOMAIN].state.lockouts) == before


@pytest.mark.parametrize(
    ("changes", "body", "named"),
    [
        (
            {"arm_scenario_ids": ()},
            {"action": "arm", "scenario": SCENARIO},
            {"operation": "arm", "scenario": "SCENARIO"},
        ),
        (
            {"disarm_area_ids": ()},
            {"action": "disarm", "areas": ["AREA"]},
            {"operation": "disarm", "areas": "AREA"},
        ),
        ({}, {"action": "dance"}, {"operation": "unknown_action"}),
    ],
)
async def test_a_device_restriction_refused_before_the_engine_raises_it(
    hass, house, changes, body, named
):
    """The device's own lists, and an action the contract does not have:
    refused by the endpoint, named as the engine would name them."""
    system = hass.data[DOMAIN]
    ids = {"AREA": system.config.areas[0].id, "SCENARIO": system.config.scenarios[0].id}
    if "areas" in body:
        body = {**body, "areas": [ids["AREA"]]}
    named = {k: ids.get(v, v) for k, v in named.items()}
    _with(hass, house.device_id, **changes)
    before = dict(system.state.lockouts)
    plain = await _post(house, {**body, "code": CODE})
    assert plain["success"] is False
    assert await _duress_rows(hass) == []

    coerced = await _post(house, {**body, "code": DURESS})

    assert coerced == plain
    (row,) = await _duress_rows(hass)
    # What the request named, and nothing else it might have named; the
    # transport's own facts (`encrypted`) ride along as on every device row.
    targets = {"operation", "scenario", "mode", "area", "areas", "zone"}
    assert {k: v for k, v in row["detail"].items() if k in targets} == named
    assert dict(hass.data[DOMAIN].state.lockouts) == before


@pytest.mark.parametrize(
    ("message", "operation"),
    [
        ({"type": "foyer/privacy/erase", "user_id": "nobody"}, "erase_person"),
        ({"type": "foyer/alarmo/apply", "fingerprint": "none"}, "import_alarmo"),
        ({"type": "foyer/config/import"}, "import_config"),
    ],
)
async def test_each_panel_command_carries_its_own_name(hass, house, message, operation):
    """Decision 134: a command that is not `edit_config` in words is not
    named `edit_config` either, whatever it went on to answer."""
    if message["type"] == "foyer/config/import":
        message = {**message, "document": backup_document(hass.data[DOMAIN].config)}
    await _raw(house.client, {**message, "code": DURESS})
    await hass.async_block_till_done()

    assert [r["detail"]["operation"] for r in await _duress_rows(hass)] == [operation]


@pytest.mark.parametrize(
    ("service", "data"),
    [("export_log", {"format": "json"}), ("export_config", {})],
)
async def test_each_service_carries_its_own_name(hass, house, service, data):
    result = await _call(hass, service, code=DURESS, **data)

    assert result["success"], result
    assert [r["detail"]["operation"] for r in await _duress_rows(hass)] == [service]


async def test_one_action_answering_it_and_the_disarm_is_filed_under_each(
    hass, house, freezer
):
    """One notify ticked for `disarmed` and `duress`: two intents with one
    id. Paired by id, both rows took one moment, and the duress's answer
    was on the hall display, or the disarm's was hidden (review)."""
    hass.services.async_register("notify", "tell", lambda call: None)
    profile = (await _config(house.client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["disarmed", "duress"],
            "name": "",
            "params": {"service": "notify.tell", "message": "{{ user }}"},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, house.client, "profile", profile, code=CODE)
    system = hass.data[DOMAIN]
    (tell,) = [
        a.id
        for a in system.config.profiles[0].actions
        if {m.value for m in a.moments} == {"disarmed", "duress"}
    ]
    armed = await _ws(
        house.client,
        {
            "type": "foyer/arm",
            "scenario_id": system.config.scenarios[0].id,
            "code": CODE,
        },
    )
    assert armed["success"]
    await _advance(hass, freezer, 61)

    await _ws(house.client, {"type": "foyer/disarm", "code": DURESS})
    await hass.async_block_till_done()

    told = [
        r
        for r in await _rows(hass, category="action")
        if r["detail"].get("action_id") == tell
    ]
    assert sorted(r["detail"]["moment"] for r in told) == ["disarmed", "duress"]
    (duress,) = [r for r in told if r["detail"]["moment"] == "duress"]
    assert duress["area_id"] is None
    (disarmed,) = [r for r in told if r["detail"]["moment"] == "disarmed"]
    assert disarmed["area_id"] is not None

    _with(
        hass,
        house.device_id,
        scopes=frozenset({"status", "log"}),
        free_scopes=frozenset({"status", "log"}),
        clear_text_confirmed=True,
    )
    response = await house.http.get(
        "/api/foyer/device/log",
        headers={"Authorization": f"Bearer {house.token}"},
        params={"limit": "50"},
    )
    shown = [
        r for r in (await response.json())["rows"] if r["event_type"] == "action_notify"
    ]
    # The disarm's answer, once: what the ordinary code would have shown.
    (only,) = shown
    assert only["area"] is not None


async def test_a_broken_duress_channel_is_not_announced_at_the_request(hass, house):
    """Two duress sends that fail over a contact's channel: counted at once,
    "channel broken" went up on every screen seconds after the code was
    typed, naming the contact. It is counted at the sweep (review)."""
    from homeassistant.components.persistent_notification import (
        DOMAIN as NOTIFICATIONS,
    )

    async def broken(call) -> None:
        raise HomeAssistantError("token expired")

    hass.services.async_register("notify", "broken", broken)
    await _save(
        hass,
        house.client,
        "contact",
        {
            "name": "Anna",
            "channels": [{"id": "push", "kind": "push", "service": "notify.broken"}],
        },
        code=CODE,
    )
    contact_id = hass.data[DOMAIN].config.contacts[0].id
    profile = (await _config(house.client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["duress"],
            "name": "",
            "params": {
                "message": "{{ user }}",
                "contacts": [{"contact_id": contact_id}],
            },
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, house.client, "profile", profile, code=CODE)
    system = hass.data[DOMAIN]
    last = system.last_row

    def down() -> list:
        return [
            n
            for n in hass.data.get(NOTIFICATIONS, {}).values()
            if n["notification_id"].endswith("_notification_channel_down")
        ]

    for _ in range(2):
        await _ws(house.client, {"type": "foyer/config/export", "code": DURESS})
        await hass.async_block_till_done()

    assert system.last_row is last
    assert down() == []
    assert len(system._duress_sends) == 2

    await system._async_channel_sweep()
    await hass.async_block_till_done()

    # Still evidence about a real send: the sweep counts it.
    assert system._duress_sends == []
    assert down()
