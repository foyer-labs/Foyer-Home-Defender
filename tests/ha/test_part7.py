"""Phase 4 part 1 inside Home Assistant: contacts, escalation, acknowledgement.

The pure suite proves what an escalation does to the state machine
(tests/core/test_escalation.py). This proves the part only a real Home
Assistant can: that a step reaches a real `notify.*` service with what that
transport needs, that the button in an actionable push comes back through
Home Assistant's own event and stops the policy, that the DTMF webhook does
not exist until somebody switches it on, and that the test button beside a
contact's channel really sends.
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util

from custom_components.foyer.const import ACK_ACTION, DOMAIN, MOBILE_APP_ACTION_EVENT

from .conftest import ZONE
from .test_part2 import _advance, _set, _ws


def _system(hass):
    return hass.data[DOMAIN]


async def _notify_recorder(hass, name: str = "mobile_app_luca") -> list[dict]:
    calls: list[dict] = []

    async def record(call):
        calls.append(dict(call.data))

    hass.services.async_register("notify", name, record)
    return calls


async def _address_book(hass, client, *, actionable: bool = False) -> dict:
    """One contact with two channels, and a policy that climbs between them."""
    contact = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "name": "Luca",
                "channels": [
                    {
                        "id": "push",
                        "kind": "push",
                        "service": "notify.mobile_app_luca",
                        "actionable": actionable,
                    },
                    {"id": "sms", "kind": "sms", "service": "notify.sms_gateway"},
                ],
            },
        },
    )
    assert contact["success"], contact
    # The save reloads the entry: wait for the new system before reading it.
    await hass.async_block_till_done()
    stored = _system(hass).config.contacts[0]
    profile = _system(hass).config.profiles[0]
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "profile",
            "item": {
                "id": profile.id,
                "name": profile.name,
                "severity": profile.severity,
                "actions": [
                    {
                        "id": "step0",
                        "kind": "notify",
                        "moments": ["triggered"],
                        "params": {
                            "message": "Alarm at home",
                            "contacts": [
                                {"contact_id": stored.id, "channel_id": "push"}
                            ],
                        },
                        "escalation_offset": 0,
                    },
                    {
                        "id": "step1",
                        "kind": "notify",
                        "moments": ["triggered"],
                        "params": {
                            "message": "Still nobody",
                            "contacts": [
                                {"contact_id": stored.id, "channel_id": "sms"}
                            ],
                        },
                        "escalation_offset": 60,
                    },
                ],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    return {"contact_id": _system(hass).config.contacts[0].id}


async def _break_in(hass, freezer) -> None:
    scenario = _system(hass).config.scenarios[0]
    await hass.services.async_call(
        DOMAIN, "arm", {"scenario_id": scenario.id}, blocking=True
    )
    await _advance(hass, freezer, 60)
    await _set(hass, ZONE, "on")


# --- the climb (§7.2) --------------------------------------------------------------


async def test_an_unacknowledged_alarm_climbs_to_the_next_channel(
    hass, hass_ws_client, loaded, freezer
):
    push = await _notify_recorder(hass)
    sms = await _notify_recorder(hass, "sms_gateway")
    client = await hass_ws_client(hass)
    await _address_book(hass, client)

    await _break_in(hass, freezer)
    assert [c["message"] for c in push] == ["Alarm at home"]
    assert sms == []

    await _advance(hass, freezer, 60)
    assert [c["message"] for c in sms] == ["Still nobody"]


async def test_an_acknowledgement_stops_the_climb(
    hass, hass_ws_client, loaded, freezer
):
    await _notify_recorder(hass)
    sms = await _notify_recorder(hass, "sms_gateway")
    client = await hass_ws_client(hass)
    await _address_book(hass, client)
    await _break_in(hass, freezer)

    await hass.services.async_call(DOMAIN, "acknowledge", {}, blocking=True)
    await _advance(hass, freezer, 120)
    assert sms == []


async def test_a_step_survives_a_restart(hass, hass_ws_client, loaded, freezer):
    """INV-3 lists escalation progress. An alarm nobody answered is still
    unanswered after a restart — and the step still ahead still goes out,
    which is the half of the phase's acceptance that a saved state alone
    does not prove."""
    await _notify_recorder(hass)
    sms = await _notify_recorder(hass, "sms_gateway")
    client = await hass_ws_client(hass)
    await _address_book(hass, client)
    await _break_in(hass, freezer)

    assert _system(hass).state.escalations != ()
    await hass.config_entries.async_reload(_entry_id(hass))
    await hass.async_block_till_done()
    assert _system(hass).state.escalations != ()

    await _advance(hass, freezer, 60)
    assert [c["message"] for c in sms] == ["Still nobody"]


def _entry_id(hass) -> str:
    return hass.config_entries.async_entries(DOMAIN)[0].entry_id


# --- the button in a push (§7.2) ---------------------------------------------------


async def test_an_actionable_channel_carries_the_button_and_the_button_answers(
    hass, hass_ws_client, loaded, freezer
):
    push = await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    book = await _address_book(hass, client, actionable=True)
    await _break_in(hass, freezer)

    actions = push[0]["data"]["actions"]
    assert actions[0]["action"] == ACK_ACTION
    assert actions[0]["foyer_contact"] == book["contact_id"]
    assert actions[0]["foyer_kind"] == "incident"

    hass.bus.async_fire(
        MOBILE_APP_ACTION_EVENT,
        {
            "action": ACK_ACTION,
            **{k: v for k, v in actions[0].items() if k != "action"},
        },
    )
    await hass.async_block_till_done()
    incident = _system(hass).state.incident
    assert incident.acknowledged
    last = incident.acknowledgements[-1]
    assert (last.via, last.contact_id) == ("push", book["contact_id"])


async def test_a_channel_that_is_not_actionable_carries_no_button(
    hass, hass_ws_client, loaded, freezer
):
    push = await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    await _address_book(hass, client, actionable=False)
    await _break_in(hass, freezer)

    assert "actions" not in (push[0].get("data") or {})


async def test_somebody_elses_notification_action_is_not_ours(
    hass, hass_ws_client, loaded, freezer
):
    await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    await _address_book(hass, client, actionable=True)
    await _break_in(hass, freezer)

    hass.bus.async_fire(MOBILE_APP_ACTION_EVENT, {"action": "SOMEBODY_ELSE"})
    await hass.async_block_till_done()
    assert not _system(hass).state.incident.acknowledged


# --- the DTMF webhook (§7.2, INV-6) ------------------------------------------------


async def test_the_webhook_does_not_exist_until_somebody_switches_it_on(
    hass, hass_ws_client, loaded
):
    """A Home Assistant webhook is not authenticated: whoever holds the URL
    can stop an escalation. So there is no URL until the household asks."""
    from homeassistant.components import webhook

    assert _system(hass).config.settings.ack_webhook_id is None

    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    assert result["success"], result
    await hass.async_block_till_done()
    webhook_id = _system(hass).config.settings.ack_webhook_id
    assert webhook_id and len(webhook_id) >= 32
    assert webhook.async_generate_path(webhook_id).endswith(webhook_id)


async def test_switching_it_off_forgets_the_url(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    first = _system(hass).config.settings.ack_webhook_id
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": False})
    await hass.async_block_till_done()
    assert _system(hass).config.settings.ack_webhook_id is None
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    # A new one, rather than reviving a URL somebody may still hold.
    assert _system(hass).config.settings.ack_webhook_id != first


async def test_a_keypress_on_the_webhook_acknowledges(
    hass, hass_ws_client, hass_client_no_auth, loaded, freezer
):
    await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    await _address_book(hass, client)
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    await _break_in(hass, freezer)

    webhook_id = _system(hass).config.settings.ack_webhook_id
    http = await hass_client_no_auth()
    response = await http.post(
        f"/api/webhook/{webhook_id}", json={"target": "incident"}
    )
    assert response.status == 200
    await hass.async_block_till_done()

    incident = _system(hass).state.incident
    assert incident.acknowledged
    assert incident.acknowledgements[-1].via == "dtmf"


# --- the test button beside a channel (§11.4) --------------------------------------


async def test_a_contact_channel_can_be_tested(hass, hass_ws_client, loaded):
    """The other half of §11.4. Phase 3 built the button beside an action and
    left this one to arrive with page 6; it is the same path, the same
    permission and the same code."""
    push = await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    book = await _address_book(hass, client)

    result = await _ws(
        client,
        {
            "type": "foyer/test_action",
            "contact_id": book["contact_id"],
            "channel_id": "push",
            "message": "Foyer test",
        },
    )
    assert result["success"] is True
    assert push and push[0]["message"] == "Foyer test"


async def test_testing_a_channel_is_recorded_as_a_test(hass, hass_ws_client, loaded):
    await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    book = await _address_book(hass, client)
    await _ws(
        client,
        {
            "type": "foyer/test_action",
            "contact_id": book["contact_id"],
            "channel_id": "push",
        },
    )
    await hass.async_block_till_done()
    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["action"]})
    row = next(r for r in rows["rows"] if r["event_type"] == "action_test")
    assert row["detail"]["test"] is True


async def test_a_test_needs_the_permission(
    hass, hass_ws_client, hass_read_only_access_token, loaded
):
    client = await hass_ws_client(hass)
    book = await _address_book(hass, client)
    limited = await hass_ws_client(hass, hass_read_only_access_token)
    await limited.send_json(
        {
            "id": 77,
            "type": "foyer/test_action",
            "contact_id": book["contact_id"],
            "channel_id": "push",
        }
    )
    msg = await limited.receive_json()
    assert msg["result"]["success"] is False
    assert msg["result"]["reason"] == "not_permitted"


# --- quiet hours (§7.1) ------------------------------------------------------------


async def test_quiet_hours_do_not_hold_back_a_break_in(
    hass, hass_ws_client, loaded, freezer
):
    """§7.1: inside the window only high-severity events get through, and a
    break-in is the event the window exists to let through."""
    from homeassistant.util import dt as dt_util

    # A window that certainly contains now, rather than a clock moved
    # backwards: the test client's own token would stop being valid.
    now = dt_util.now()
    window = {
        "quiet_start": (now - timedelta(hours=1)).strftime("%H:%M"),
        "quiet_end": (now + timedelta(hours=1)).strftime("%H:%M"),
    }
    push = await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    book = await _address_book(hass, client)
    contact = _system(hass).config.contact(book["contact_id"])
    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "id": contact.id,
                "name": contact.name,
                "channels": [
                    {
                        "id": c.id,
                        "kind": c.kind.value,
                        "service": c.service,
                        "actionable": c.actionable,
                    }
                    for c in contact.channels
                ],
                **window,
            },
        },
    )
    assert result["success"], result
    await hass.async_block_till_done()

    await _break_in(hass, freezer)
    assert [c["message"] for c in push] == ["Alarm at home"]


# --- what the review closed ---------------------------------------------------------


async def test_the_webhook_records_nothing_when_there_is_nothing_to_acknowledge(
    hass, hass_ws_client, hass_client_no_auth, loaded
):
    """The URL is unauthenticated (INV-6). Without this, anybody holding it
    could fill the log with refusals and bury the row that matters."""
    client = await hass_ws_client(hass)
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    webhook_id = _system(hass).config.settings.ack_webhook_id

    http = await hass_client_no_auth()
    for _ in range(3):
        assert (await http.post(f"/api/webhook/{webhook_id}")).status == 200
    await hass.async_block_till_done()

    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["alarm"]})
    assert rows["rows"] == []


async def test_a_push_that_does_not_say_which_alarm_acknowledges_both(
    hass, hass_ws_client, loaded, freezer
):
    """The app decides how much of the action it echoes back. When the answer
    comes back bare, the honest reading is that the person saw what they were
    sent — the same rule button.foyer_acknowledge follows."""
    await _notify_recorder(hass)
    client = await hass_ws_client(hass)
    await _address_book(hass, client, actionable=True)
    await _break_in(hass, freezer)

    hass.bus.async_fire(MOBILE_APP_ACTION_EVENT, {"action": ACK_ACTION})
    await hass.async_block_till_done()
    assert _system(hass).state.incident.acknowledged


async def test_the_webhook_id_cannot_be_chosen_through_the_settings(
    hass, hass_ws_client, loaded
):
    """An id a client could choose would eventually be one somebody could
    guess, and this URL stops an alarm."""
    client = await hass_ws_client(hass)
    settings = {**_public_settings(hass), "ack_webhook_id": "foyer"}
    result = await _ws(client, {"type": "foyer/config/settings", "settings": settings})
    assert result["success"], result
    await hass.async_block_till_done()
    assert _system(hass).config.settings.ack_webhook_id is None


def _public_settings(hass) -> dict:
    from custom_components.foyer.store.schema import settings_to_dict

    return settings_to_dict(_system(hass).config.settings)


async def test_a_notify_entity_still_gets_the_title(hass, hass_ws_client, loaded):
    """It carries a message and a title and nothing else. What it cannot
    carry is said in the log rather than dropped in silence."""
    calls: list[dict] = []

    async def record(call):
        calls.append(dict(call.data))

    hass.services.async_register("notify", "send_message", record)
    hass.states.async_set("notify.wall_tablet", "unknown")
    await hass.async_block_till_done()

    system = _system(hass)
    from custom_components.foyer.core.models import ActionIntent, Decision, Moment

    intent = ActionIntent(
        action_id="t",
        kind="notify",
        moment=Moment.ACTION_TESTED,
        params={
            "message": "Alarm",
            "title": "Foyer",
            "recipients": (
                {
                    "contact_id": "c",
                    "contact_name": "Luca",
                    "channel_id": "ch",
                    "kind": "push",
                    "service": "notify.wall_tablet",
                    "target": "",
                    "data": {"push": {"sound": "alarm"}},
                    "ack": True,
                },
            ),
        },
    )
    await system._executor.async_run(
        Decision(
            at=dt_util.utcnow(), accepted=True, state=system.state, actions=(intent,)
        )
    )
    assert calls and calls[0]["message"] == "Alarm"
    assert calls[0]["title"] == "Foyer"
