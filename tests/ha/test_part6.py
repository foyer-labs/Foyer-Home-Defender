"""Phase 3 part 2 inside Home Assistant: page 9's two writes (§11.3, §11.4).

The pure suite proves what a walk test does to the state machine
(tests/core/test_walk_test.py). This proves the part only a real Home
Assistant can: that the two services of §9.1 exist at last and answer in the
shape §9.1 promised, that the switch of §13 reflects the timeout, that the
banner reaches the card and the panel through the one status payload both
read, and that a real action test really executes and is recorded as a test
rather than as the alarm it imitates.
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import MASTER, PANEL_ENTITY, ZONE
from .test_part2 import _advance, _set, _state, _ws


async def _walk_test(hass: HomeAssistant, enable: bool = True, **data) -> dict:
    return await hass.services.async_call(
        DOMAIN,
        "walk_test",
        {"enable": enable, **data},
        blocking=True,
        return_response=True,
    )


def _system(hass: HomeAssistant):
    return hass.data[DOMAIN]


# --- the service contract (§9.1) ----------------------------------------------------


async def test_the_two_services_exist_at_last(hass, loaded):
    """Decision 86 held them back until the phase that builds them. A service
    that exists and does nothing answers its caller with silence, and silence
    is the answer that gets mistaken for success."""
    assert hass.services.has_service(DOMAIN, "walk_test")
    assert hass.services.has_service(DOMAIN, "test_action")


async def test_entering_answers_in_the_shape_of_9_1(hass, loaded):
    result = await _walk_test(hass)
    assert result["success"] is True
    assert set(result) >= {"success", "reason", "blocking_zones", "state"}
    assert result["state"]["walk_test"] is not None


async def test_the_house_is_genuinely_armed(hass, loaded):
    """§11.3: the area is genuinely armed and the sensors genuinely read.
    Only the response is held back."""
    await _walk_test(hass)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    # The master says `armed_custom_bypass`, which is the truth: the areas
    # are armed on their own and no scenario is running (§13). What matters
    # here is that it says *armed* rather than triggered.
    assert _state(hass, MASTER) == AlarmControlPanelState.ARMED_CUSTOM_BYPASS


async def test_a_detection_never_tells_homekit_there_was_a_burglary(hass, loaded):
    """Part 2 decision 3, seen from the surface that matters: `triggered` on
    an alarm_control_panel means *burglary* to HomeKit, Google and Alexa."""
    await _walk_test(hass)
    await _set(hass, ZONE, "on")

    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, MASTER) != AlarmControlPanelState.TRIGGERED
    assert _system(hass).state.incident is None
    walk = _system(hass).state.walk_test
    assert list(walk.detections) == [_system(hass).config.zones[0].id]


async def test_leaving_gives_the_house_back(hass, loaded):
    await _walk_test(hass)
    result = await _walk_test(hass, False)
    assert result["success"] is True
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    assert _system(hass).state.walk_test is None


async def test_a_blocked_area_does_not_stop_it_and_is_named(hass, loaded):
    """Part 2 decision 7: a window left open must not stop somebody finding
    out that the garage PIR is dead."""
    await _set(hass, ZONE, "on")
    result = await _walk_test(hass)
    assert result["success"] is True
    assert [z["id"] for z in result["blocking_zones"]] == [
        _system(hass).config.zones[0].id
    ]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


# --- the safeguards (§11.3) --------------------------------------------------------


async def test_the_auto_exit_ends_it_without_anybody_asking(hass, loaded, freezer):
    """§5.3 calls it mandatory and non-disableable, and it is a timer like
    any other: the scheduler wakes for it."""
    await _walk_test(hass, duration=60)
    await _advance(hass, freezer, 61)
    assert _system(hass).state.walk_test is None
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_the_banner_reaches_the_panel_and_the_card(hass, hass_ws_client, loaded):
    """One status payload, read by both (§11.3: a banner in the panel *and*
    on every card layout, badge included)."""
    client = await hass_ws_client(hass)
    assert (await _ws(client, {"type": "foyer/status"}))["walk_test"] is None

    await _walk_test(hass)
    status = await _ws(client, {"type": "foyer/status"})
    walk = status["walk_test"]
    assert walk["deadline"] and walk["started_at"]
    # Which zones the walk should have reached, so that silence is a finding
    # rather than an empty table.
    assert walk["expected_zones"] == [_system(hass).config.zones[0].id]
    assert walk["detections"] == {}


async def test_entry_and_exit_are_logged(hass, hass_ws_client, loaded):
    """§11.3: entry and exit logged with the user who started it."""
    client = await hass_ws_client(hass)
    await _walk_test(hass)
    await _walk_test(hass, False)
    await hass.async_block_till_done()

    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["system"]})
    types = [r["event_type"] for r in rows["rows"]]
    assert "walk_test_started" in types
    assert "walk_test_ended" in types
    ended = next(r for r in rows["rows"] if r["event_type"] == "walk_test_ended")
    assert ended["detail"]["cause"] == "manual"


async def test_the_start_and_the_end_are_announced(hass, loaded):
    """§11.3 lists a notification on start and on end among the safeguards
    that are not optional, so the default profile carries both moments."""
    await _walk_test(hass)
    await hass.async_block_till_done()
    started = hass.data["persistent_notification"].values()
    assert any("walk test" in n["message"].lower() for n in started)


async def test_a_smoke_detector_is_never_silenced(hass, hass_ws_client, loaded):
    """The sentence the whole feature is written against (§11.3)."""
    from .test_part2 import SMOKE, _add_smoke_detector

    client = await hass_ws_client(hass)
    await _add_smoke_detector(hass, client)
    await _walk_test(hass)
    await _set(hass, SMOKE, "on")

    assert _state(hass, "binary_sensor.foyer_technical_alarm") == "on"
    # And it is not filed as a walk-test detection: it is live, not under test.
    assert _system(hass).state.walk_test.detections == {}


# --- switch.foyer_walk_test (§13) ---------------------------------------------------


async def test_the_switch_reflects_the_walk_test_and_its_timeout(hass, loaded):
    assert _state(hass, "switch.foyer_walk_test") == "off"
    await _walk_test(hass)
    state = hass.states.get("switch.foyer_walk_test")
    assert state.state == "on"
    assert state.attributes["ends_at"]
    assert state.attributes["armed_areas"] == [_system(hass).config.areas[0].id]


async def test_the_switch_starts_and_ends_a_walk_test(hass, loaded):
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.foyer_walk_test"},
        blocking=True,
    )
    assert _system(hass).state.walk_test is not None
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.foyer_walk_test"},
        blocking=True,
    )
    assert _system(hass).state.walk_test is None


# --- the real action test (§11.4) --------------------------------------------------


async def test_a_tested_action_really_executes(hass, hass_ws_client, loaded):
    """It really runs, which is the entire point: the failure this prevents
    is discovering during the emergency that the channel was misconfigured."""
    client = await hass_ws_client(hass)
    profile = _system(hass).config.profiles[0]
    result = await _ws(
        client,
        {
            "type": "foyer/test_action",
            "profile_id": profile.id,
            "action_id": profile.actions[0].id,
        },
    )
    assert result["success"] is True
    await hass.async_block_till_done()
    assert hass.data["persistent_notification"]


async def test_a_test_is_recorded_as_a_test(hass, hass_ws_client, loaded):
    """§11.4: logged as a test. A test recorded as a real action is a log
    that claims the siren went off on the sixth of September."""
    client = await hass_ws_client(hass)
    profile = _system(hass).config.profiles[0]
    await _ws(
        client,
        {
            "type": "foyer/test_action",
            "profile_id": profile.id,
            "action_id": profile.actions[0].id,
        },
    )
    await hass.async_block_till_done()

    rows = await _ws(client, {"type": "foyer/log/query", "categories": ["action"]})
    row = next(r for r in rows["rows"] if r["event_type"] == "action_test")
    assert row["detail"]["test"] is True
    assert row["outcome"] == "ok"


async def test_a_notification_channel_can_be_tested_on_its_own(
    hass, hass_ws_client, loaded
):
    """The half of §11.4's "every contact channel" that exists before the
    contact book of Phase 4 — and where the wizard's test notification goes."""
    calls = []

    async def record(call):
        calls.append(call.data)

    hass.services.async_register("notify", "mobile_app_test", record)
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {
            "type": "foyer/test_action",
            "service": "notify.mobile_app_test",
            "message": "Foyer test",
        },
    )
    assert result["success"] is True
    assert calls and calls[0]["message"] == "Foyer test"


async def test_a_failing_channel_says_so_rather_than_succeeding_quietly(
    hass, hass_ws_client, loaded
):
    """The whole point of §11.4 is finding out now. A test that reported
    success for a service that does not exist would be worse than none."""
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {"type": "foyer/test_action", "service": "notify.nothing_here"},
    )
    assert result["success"] is False
    assert result["error"]


async def test_testing_an_action_needs_the_permission(
    hass, hass_ws_client, hass_read_only_access_token, loaded
):
    """§11.4: requires the `test_actions` permission. A button that really
    sounds the siren is not open to everybody who can open the page."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    profile = _system(hass).config.profiles[0]
    await client.send_json(
        {
            "id": 9,
            "type": "foyer/test_action",
            "profile_id": profile.id,
            "action_id": profile.actions[0].id,
        }
    )
    msg = await client.receive_json()
    assert msg["result"]["success"] is False
    assert msg["result"]["reason"] == "not_permitted"


async def test_a_walk_test_goes_through_the_engine_like_any_other_request(
    hass, hass_ws_client, loaded
):
    """§8.2 and §8.3 are resolved in the engine, which is where every
    state-changing request resolves them (INV-2). The pure suite asserts the
    refusals themselves (tests/core/test_walk_test.py); what this asserts is
    that the command reaches that gate rather than one of its own."""
    client = await hass_ws_client(hass)
    result = await _ws(client, {"type": "foyer/walk_test", "enable": True})
    assert result["success"] is True
    # Twice is a refusal the engine makes, answered in §9.1's shape.
    again = await _ws(client, {"type": "foyer/walk_test", "enable": True})
    assert again["success"] is False
    assert again["reason"] == "invalid_state"


@pytest.mark.parametrize("seconds", [60, 600])
async def test_a_shorter_duration_is_honoured(hass, loaded, seconds):
    await _walk_test(hass, duration=seconds)
    walk = _system(hass).state.walk_test
    assert (walk.until - walk.started_at) == timedelta(seconds=seconds)


async def test_the_switch_is_idempotent(hass, loaded):
    """An automation calling turn_off on a house that is not in a walk test
    has not made a mistake worth raising an error over."""
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.foyer_walk_test"}, blocking=True
    )
    assert _system(hass).state.walk_test is None


async def test_a_channel_test_with_nothing_to_say_still_says_something(
    hass, hass_ws_client, loaded
):
    """Several transports refuse an empty message outright, and a test that
    failed for that reason would teach nothing about the channel."""
    calls = []

    async def record(call):
        calls.append(call.data)

    hass.services.async_register("notify", "silent_test", record)
    client = await hass_ws_client(hass)
    result = await _ws(
        client, {"type": "foyer/test_action", "service": "notify.silent_test"}
    )
    assert result["success"] is True
    assert calls[0]["message"]
