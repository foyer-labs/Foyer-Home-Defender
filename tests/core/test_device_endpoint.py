"""The device endpoint's half of identity (SPEC §9.2.1). Pure: no Home Assistant.

What reaches the engine from the endpoint is an Actor like any other. Three
things are new: a wrong token has no device to count against, so the lockout
of §8.4 counts per source address; a request that crossed the network in the
clear says so on every row it causes, and keeps page 8's warning up; and a
right token from an address locked out for wrong tokens is served, every row
it causes saying the address was locked (decision 135).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core import authz
from custom_components.foyer.core.journal import row_for
from custom_components.foyer.core.models import (
    ArmingDevice,
    CodeAttempt,
    CodeResult,
    DeviceKind,
    DeviceTransport,
    Moment,
    Operation,
    Reason,
    Settings,
)
from custom_components.foyer.core.validation import validate
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import World, make_house, user

KEYPAD = ArmingDevice(
    "hall",
    "Hall keypad",
    DeviceKind.KEYPAD,
    ref="keypad_hall",
    transport=DeviceTransport.HTTP,
    token_hash="ab" * 32,
)


def house():
    config = make_house()
    return replace(
        config,
        users=(user(),),
        devices=(KEYPAD,),
        settings=replace(config.settings, security=Settings().security),
    )


def bad_token(world: World, address: str = "192.0.2.7", *, encrypted=False):
    return world.send(
        CodeAttempt(
            None,
            actor=authz_actor(address=address, encrypted=encrypted),
        )
    )


def authz_actor(**kwargs):
    from custom_components.foyer.core.models import Actor

    return Actor(channel="keypad", code=CodeResult.INVALID, **kwargs)


def test_a_wrong_token_counts_against_its_address_and_locks_it():
    world = World(house())
    for _ in range(4):
        decision = bad_token(world)
        assert Moment.LOCKOUT not in decision.moments
    decision = bad_token(world)

    assert Moment.LOCKOUT in decision.moments
    assert authz.address_locked_until(world.state.lockouts, "192.0.2.7", world.now)
    # Another address is not locked, and no keypad's counter was spent.
    assert (
        authz.address_locked_until(world.state.lockouts, "192.0.2.8", world.now) is None
    )
    assert set(world.state.lockouts) == {"http:192.0.2.7"}


def test_the_row_says_token_and_address_and_not_encrypted():
    world = World(house())
    decision = bad_token(world)

    rejected = next(o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED)
    row = row_for(rejected, world.now)
    assert row.detail["reason"] == Reason.BAD_TOKEN.value
    assert row.detail["address"] == "192.0.2.7"
    assert row.detail["encrypted"] == "false"
    assert row.category == "security"


def test_an_idle_address_counter_is_dropped():
    world = World(house())
    bad_token(world)
    assert "http:192.0.2.7" in world.state.lockouts

    world.advance(authz.LOCKOUT_STRIKE_RESET + 1)
    assert "http:192.0.2.7" not in world.state.lockouts


def test_a_keypad_in_the_clear_is_remembered_until_it_arrives_encrypted():
    world = World(house())
    world.arm("away", channel="keypad", device_id="hall", encrypted=False)
    assert world.state.in_clear == frozenset({"hall"})

    # Across a restart, because a warning a reload hides is not permanent.
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.in_clear == frozenset({"hall"})

    # Refused for want of a code, and still a request that arrived encrypted.
    world.disarm(channel="keypad", device_id="hall", encrypted=True)
    assert world.state.in_clear == frozenset()


def test_every_row_a_request_in_the_clear_causes_says_so():
    world = World(house())
    world.arm("away", channel="keypad", device_id="hall", encrypted=False)
    decision = world.advance(30)  # the armed row belongs to the exit delay
    assert decision  # the timer's rows carry no actor

    world.disarm(
        channel="keypad",
        device_id="hall",
        encrypted=False,
        user_id="luca",
        code=CodeResult.VALID,
    )
    rows = [
        row_for(o, world.now) for o in world.last.occurrences if o.channel == "keypad"
    ]
    assert rows and all(r.detail.get("encrypted") == "false" for r in rows)


def test_a_tag_can_never_be_given_a_token():
    config = make_house()
    tag = ArmingDevice(
        "tag",
        "Luca's tag",
        DeviceKind.TAG,
        entity_id="tag.luca",
        user_id="luca",
        scenario_id="away",
        transport=DeviceTransport.HTTP,
    )
    problems = validate(replace(config, users=(user(),), devices=(tag,)))
    assert any(p.code == "tag_has_no_token" for p in problems)


def test_a_token_outside_the_endpoint_is_refused():
    config = replace(
        make_house(), devices=(replace(KEYPAD, transport=DeviceTransport.MQTT),)
    )
    assert any(p.code == "token_without_endpoint" for p in validate(config))


def test_a_locked_address_is_answered_before_the_engine_counts_again():
    world = World(house())
    for _ in range(5):
        bad_token(world)
    until = authz.address_locked_until(world.state.lockouts, "192.0.2.7", world.now)
    assert until is not None
    world.advance((until - world.now).total_seconds() + 1)
    assert (
        authz.address_locked_until(world.state.lockouts, "192.0.2.7", world.now) is None
    )
    # The counter survives for the strike it holds: the next lockout is longer.
    for _ in range(5):
        bad_token(world)
    again = authz.address_locked_until(world.state.lockouts, "192.0.2.7", world.now)
    assert again is not None and again - world.now > timedelta(seconds=300)


def test_the_operation_is_optional_for_a_token():
    """A state stream asks for nothing: the attempt carries no operation."""
    world = World(house())
    decision = world.send(CodeAttempt(Operation.ARM, actor=authz_actor(address="x")))
    rejected = next(o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED)
    assert rejected.detail["operation"] == "arm"


def test_a_stream_opening_records_only_whether_it_was_encrypted():
    from custom_components.foyer.core.models import Actor, DeviceContact

    world = World(house())
    decision = world.send(
        DeviceContact(Actor(channel="keypad", device_id="hall", encrypted=False))
    )
    assert decision.accepted and not decision.occurrences
    assert world.state.in_clear == frozenset({"hall"})


def test_a_credential_replaced_by_another_still_leaves_a_row():
    from custom_components.foyer.store.editing import config_diff

    config = make_house()
    moved = replace(
        config,
        health=replace(
            config.health,
            watchdog=replace(config.health.watchdog, url="https://b.example/y"),
        ),
    )
    before = replace(
        config,
        health=replace(
            config.health,
            watchdog=replace(config.health.watchdog, url="https://a.example/x"),
        ),
    )
    diff = config_diff(before, moved)
    assert diff["health"]["watchdog.url"] == []
    assert "example" not in str(diff)


def test_a_null_params_document_still_migrates():
    from custom_components.foyer.store.migrations import migrate

    out = migrate(
        (7, 4),
        (8, 1),
        {"profiles": [{"actions": [{"kind": "notify", "params": None}]}]},
    )
    assert out["profiles"][0]["actions"][0]["params"]["images"] == "none"


def test_a_request_s_notes_never_land_on_somebody_else_s_row():
    """An arming by another keypad whose exit delay runs out inside an endpoint
    request is that keypad's row: no address, and no note about the wrong
    keypad's transport (found in review)."""
    from custom_components.foyer.core.models import Actor

    garden = ArmingDevice("garden", "Garden", DeviceKind.KEYPAD, ref="keypad_garden")
    world = World(replace(house(), devices=(KEYPAD, garden)))
    world.arm("night", channel="keypad", device_id="garden", user_id="luca")
    world.now += timedelta(seconds=6)  # past the exit delay, before any Tick
    decision = world.send(
        CodeAttempt(
            None,
            actor=Actor(
                channel="keypad",
                code=CodeResult.INVALID,
                address="203.0.113.9",
                encrypted=False,
            ),
        )
    )
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert "address" not in armed.detail
    assert "encrypted" not in armed.detail


def test_an_endpoint_keypad_s_later_rows_say_it_talks_in_the_clear():
    world = World(house())
    world.arm("night", channel="keypad", device_id="hall", encrypted=False)
    decision = world.advance(6)
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert armed.detail["encrypted"] == "false"


def test_a_keypad_moved_to_mqtt_is_no_longer_in_the_clear():
    world = World(house())
    world.arm("night", channel="keypad", device_id="hall", encrypted=False)
    assert world.state.in_clear == frozenset({"hall"})
    world.config = replace(
        world.config,
        devices=(replace(KEYPAD, transport=DeviceTransport.MQTT, token_hash=None),),
    )
    world.advance(1)
    assert world.state.in_clear == frozenset()


# --- a right token from a locked-out address (decision 135) ----------------------

LOCKED = {"address": "192.0.2.7", "address_locked": "true"}


def _locked(world: World, address: str = "192.0.2.7") -> None:
    """Lock an address out the way a guesser does: five wrong tokens."""
    for _ in range(5):
        bad_token(world, address)
    assert authz.address_locked_until(world.state.lockouts, address, world.now)


def _noted(detail: dict) -> bool:
    return all(detail.get(k) == v for k, v in LOCKED.items())


def test_a_right_token_from_a_locked_address_says_so_on_every_row_it_causes():
    """Served, and said: the arming's own `armed` row thirty seconds later
    too, as it carries the person — and the rows of a disarm at once."""
    world = World(house())
    _locked(world)
    world.arm("away", channel="keypad", device_id="hall", locked_address="192.0.2.7")
    decision = world.advance(30)
    armed = [o for o in decision.occurrences if o.moment is Moment.ARMED]
    assert armed and all(_noted(row_for(o, world.now).detail) for o in armed)

    decision = world.disarm(
        channel="keypad",
        device_id="hall",
        user_id="luca",
        code=CodeResult.VALID,
        locked_address="192.0.2.7",
    )
    assert decision.accepted
    rows = [
        row_for(o, world.now) for o in decision.occurrences if o.channel == "keypad"
    ]
    assert {r.event_type for r in rows} >= {"disarmed"}
    assert all(_noted(r.detail) for r in rows)


def test_a_keypad_whose_address_is_not_locked_says_nothing_about_it():
    world = World(house())
    world.arm("night", channel="keypad", device_id="hall")
    decision = world.advance(6)
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert "address_locked" not in armed.detail
    assert "address" not in armed.detail


def test_the_note_survives_a_restart_inside_the_exit_delay():
    world = World(house())
    world.arm("away", channel="keypad", device_id="hall", locked_address="192.0.2.7")
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert {rt.locked_address for rt in restored.areas.values()} == {"192.0.2.7"}
    world.state = restored
    decision = world.advance(30)
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert _noted(armed.detail)


def test_a_right_token_neither_spends_nor_clears_the_address_counter():
    """The keypad's own wrong code counts against the keypad, never against
    the address its token came from; its valid code leaves both alone."""
    world = World(house())
    world.arm("night", channel="keypad", device_id="hall")
    _locked(world)
    before = world.state.lockouts["http:192.0.2.7"]

    decision = world.disarm(
        channel="keypad",
        device_id="hall",
        code=CodeResult.INVALID,
        locked_address="192.0.2.7",
    )
    rejected = next(o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED)
    row = row_for(rejected, world.now)
    assert _noted(row.detail)
    assert row.detail["reason"] == Reason.BAD_CODE.value
    assert world.state.lockouts["keypad:hall"].failures
    assert world.state.lockouts["http:192.0.2.7"] == before

    decision = world.disarm(
        channel="keypad",
        device_id="hall",
        user_id="luca",
        code=CodeResult.VALID,
        locked_address="192.0.2.7",
    )
    assert decision.accepted
    assert world.state.lockouts["http:192.0.2.7"] == before


def test_a_refusal_behind_a_locked_address_says_so():
    from custom_components.foyer.core.journal import rejection_row
    from custom_components.foyer.core.models import Actor, ArmRequest

    from .helpers import DOOR

    world = World(house())
    world.set(DOOR, "on")
    event = ArmRequest(
        "away",
        actor=Actor(channel="keypad", device_id="hall", locked_address="192.0.2.7"),
    )
    decision = world.send(event)
    assert decision.reason is Reason.ZONE_OPEN
    row = rejection_row(event, decision, world.config)
    assert row is not None and _noted(row.detail)


def test_a_locked_address_note_never_lands_on_somebody_else_s_row():
    """Another keypad's arming whose exit delay runs out inside the request
    is that keypad's row, and says nothing about this one's address."""
    from custom_components.foyer.core.models import Actor

    garden = ArmingDevice("garden", "Garden", DeviceKind.KEYPAD, ref="keypad_garden")
    world = World(replace(house(), devices=(KEYPAD, garden)))
    world.arm("night", channel="keypad", device_id="garden", user_id="luca")
    world.now += timedelta(seconds=6)  # past the exit delay, before any Tick
    decision = world.send(
        CodeAttempt(
            None,
            actor=Actor(
                channel="keypad",
                device_id="hall",
                code=CodeResult.INVALID,
                locked_address="203.0.113.9",
            ),
        )
    )
    armed = next(o for o in decision.occurrences if o.moment is Moment.ARMED)
    assert "address_locked" not in armed.detail
    rejected = next(o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED)
    assert rejected.detail["address_locked"] == "true"
    assert rejected.detail["address"] == "203.0.113.9"
