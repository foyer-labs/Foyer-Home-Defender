"""The device endpoint's half of identity (SPEC §9.2.1). Pure: no Home Assistant.

What reaches the engine from the endpoint is an Actor like any other. Two
things are new: a wrong token has no device to count against, so the lockout
of §8.4 counts per source address; and a request that crossed the network in
the clear says so on every row it causes, and keeps page 8's warning up.
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
