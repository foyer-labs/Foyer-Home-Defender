"""Phase 4 part 2 inside Home Assistant: automatic arming rules (§9.4).

The pure suite proves what a rule does to the state machine
(tests/core/test_rules.py). This proves the part only a real Home Assistant
can: that a phone leaving the house actually reaches the engine, that the
countdown's push carries a Cancel button and that pressing it — through Home
Assistant's own event, as the Companion app sends it — stops the arming, that
the two entities of §13 exist and say what is about to happen, and that a
suspension set from the panel survives into the next decision.
"""

from __future__ import annotations

from custom_components.foyer.const import (
    CANCEL_ACTION,
    CANCEL_PENDING_KEY,
    DOMAIN,
    MOBILE_APP_ACTION_EVENT,
)

from .conftest import ZONE
from .test_part2 import _IDS, _advance, _set, _ws

PERSON = "person.luca"
AUTO_SWITCH = "switch.foyer_auto_arming"
NEXT_ACTION = "sensor.foyer_next_auto_action"


def _system(hass):
    return hass.data[DOMAIN]


async def _notify_recorder(hass, name: str = "mobile_app_luca") -> list[dict]:
    calls: list[dict] = []

    async def record(call):
        calls.append(dict(call.data))

    hass.services.async_register("notify", name, record)
    return calls


async def _rule(hass, client, **overrides) -> str:
    """One contact, and one absence rule that announces itself to them."""
    saved = await _ws(
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
                        "actionable": True,
                    }
                ],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    contact_id = _system(hass).config.contacts[0].id
    scenario_id = _system(hass).config.scenarios[0].id
    item = {
        "name": "Empty house",
        "trigger": {
            "kind": "absence",
            "entity_ids": [PERSON],
            "minutes": 10,
            "weekdays": [],
        },
        "action": "arm",
        "scenario_id": scenario_id,
        "grace_seconds": 120,
        "notify_contact_ids": [contact_id],
        **overrides,
    }
    saved = await _ws(
        client, {"type": "foyer/config/save", "kind": "rule", "item": item}
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    return _system(hass).config.rules[0].id


async def test_a_phone_leaving_reaches_the_engine_and_the_house_announces(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    calls = await _notify_recorder(hass)

    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)

    assert len(calls) == 1, calls
    message = calls[0]
    assert "Empty house" in message["message"]
    # The Cancel button of §9.4, on the channel that declared itself
    # actionable, carrying which countdown it would stop.
    [action] = message["data"]["actions"]
    assert action["action"] == CANCEL_ACTION
    assert action[CANCEL_PENDING_KEY]
    # Announced, not done.
    assert hass.states.get("alarm_control_panel.foyer_casa").state == "disarmed"


async def test_the_button_in_the_push_stops_it(hass, loaded, hass_ws_client, freezer):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    calls = await _notify_recorder(hass)
    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    [action] = calls[0]["data"]["actions"]

    hass.bus.async_fire(
        MOBILE_APP_ACTION_EVENT,
        {"action": CANCEL_ACTION, CANCEL_PENDING_KEY: action[CANCEL_PENDING_KEY]},
    )
    await hass.async_block_till_done()
    assert not _system(hass).state.pending_rules

    await _advance(hass, freezer, 180)
    assert hass.states.get("alarm_control_panel.foyer_casa").state == "disarmed"


async def test_nobody_presses_anything_and_the_house_arms_itself(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)
    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    await _advance(hass, freezer, 130)

    panel = hass.states.get("alarm_control_panel.foyer_casa").state
    assert panel in ("arming", "armed_away")


async def test_the_two_entities_of_the_section_exist_and_report(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)

    assert hass.states.get(AUTO_SWITCH).state == "on"
    assert hass.states.get(NEXT_ACTION).state == "idle"

    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)

    upcoming = hass.states.get(NEXT_ACTION)
    assert upcoming.state == "arm"
    assert upcoming.attributes["rule"] == "Empty house"
    assert upcoming.attributes["counting_down"] is True


async def test_the_kill_switch_cancels_what_is_counting_down(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)
    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    assert _system(hass).state.pending_rules

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": AUTO_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()
    assert not _system(hass).state.pending_rules
    assert hass.states.get(AUTO_SWITCH).state == "off"

    await _advance(hass, freezer, 180)
    assert hass.states.get("alarm_control_panel.foyer_casa").state == "disarmed"


async def test_the_boiler_engineer_window_keeps_the_house_open(
    hass, loaded, hass_ws_client, freezer
):
    """Tomorrow morning, expected between nine and one: it does not arm, and
    the log says why — by name, which is the whole reason the window is a
    first-class thing rather than a checkbox (§9.4)."""
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)

    now = dt_util.utcnow()
    result = await _ws(
        client,
        {
            "type": "foyer/auto/suspend",
            "kind": "visitor",
            "name": "Boiler engineer",
            "start": now.isoformat(),
            "until": (now + timedelta(hours=4)).isoformat(),
            "rule_ids": [],
        },
    )
    assert result["success"], result

    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)

    assert not _system(hass).state.pending_rules
    assert hass.states.get("alarm_control_panel.foyer_casa").state == "disarmed"
    rows = await _ws(client, {"type": "foyer/log/query", "limit": 100})
    blocked = [r for r in rows["rows"] if r["event_type"] == "auto_blocked"]
    assert blocked, rows["rows"]
    assert blocked[0]["detail"]["name"] == "Boiler engineer"


async def test_a_suspension_set_from_the_panel_holds_the_rule_back(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    rule_id = await _rule(hass, client)
    await _notify_recorder(hass)

    result = await _ws(
        client,
        {
            "type": "foyer/auto/suspend",
            "kind": "next",
            "rule_ids": [rule_id],
            "name": "Boiler engineer",
        },
    )
    assert result["success"], result
    assert len(_system(hass).state.suspensions) == 1

    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    assert not _system(hass).state.pending_rules
    # "Skip the next occurrence" is spent by use.
    assert not _system(hass).state.suspensions


async def test_a_rule_that_could_never_act_is_refused_at_save_time(
    hass, loaded, hass_ws_client
):
    client = await hass_ws_client(hass)
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "rule",
            "item": {
                "name": "Nothing to watch",
                "trigger": {"kind": "absence", "entity_ids": []},
                "action": "arm",
                "scenario_id": _system(hass).config.scenarios[0].id,
                "grace_seconds": 0,
            },
        },
    )
    assert not saved["success"]
    assert "rule_without_people" in {p["code"] for p in saved["problems"]}


async def test_the_zone_still_works_while_rules_exist(hass, loaded, hass_ws_client):
    """A rule watching people must not change what a door does."""
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _set(hass, ZONE, "on")
    assert hass.states.get("binary_sensor.foyer_zone_front_door").state == "on"


async def test_the_card_path_cancels_by_id(hass, loaded, hass_ws_client, freezer):
    """What the card sends: `foyer/auto/cancel` naming the countdown it is
    showing. The engine decides, as it does for every command (INV-2)."""
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)
    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    [pending] = _system(hass).state.pending_rules

    result = await _ws(client, {"type": "foyer/auto/cancel", "pending_id": pending.id})
    assert result["success"], result
    assert not _system(hass).state.pending_rules

    # And pressing it twice is refused rather than silent: there is nothing
    # left to cancel, and somebody pressed a button.
    # The next id of the shared counter, not a number of its own: a
    # connection takes only increasing ids, and a fixed one fell behind the
    # counter as soon as the suite before it grew.
    await client.send_json(
        {"id": next(_IDS), "type": "foyer/auto/cancel", "pending_id": pending.id}
    )
    again = await client.receive_json()
    assert again["result"]["success"] is False
    assert again["result"]["reason"] == "nothing_to_cancel"


async def test_the_status_the_card_reads_carries_the_countdown(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    await _notify_recorder(hass)
    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)

    status = await _ws(client, {"type": "foyer/status"})
    auto = status["auto"]
    assert auto["enabled"] is True
    [pending] = auto["pending"]
    assert pending["rule_name"] == "Empty house"
    assert pending["action"] == "arm"
    assert pending["seconds"] == 120
    assert auto["next"]["pending_id"] == pending["id"]


async def test_an_open_zone_is_named_ahead_and_the_outcome_reaches_the_phone(
    hass, loaded, hass_ws_client, freezer
):
    """Decisions 124 and 125, end to end: the countdown names the open zone,
    and the phone hears that the house did not arm, in words."""
    client = await hass_ws_client(hass)
    await _set(hass, PERSON, "home")
    await _rule(hass, client)
    calls = await _notify_recorder(hass)
    await _set(hass, ZONE, "on")
    zone_name = _system(hass).config.zones[0].name

    await _set(hass, PERSON, "not_home")
    await _advance(hass, freezer, 11 * 60)
    assert calls and zone_name in calls[-1]["message"], calls

    await _advance(hass, freezer, 125)
    outcome = calls[-1]
    assert "Empty house" in outcome["message"]
    assert zone_name in outcome["message"]
    # No Cancel button: there is nothing left to cancel.
    assert "actions" not in (outcome.get("data") or {})
    assert hass.states.get("alarm_control_panel.foyer_casa").state == "disarmed"
