"""What the follow-up to the second review settled (decisions 101-107).

The configuration gate is one pure function now, for the panel and for the
services, and the code checks and the tag and key commands are one path each
where they used to be two. The comparison tests pin that merging them changed
nothing. Pure: no Home Assistant.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from custom_components.foyer.core import authz
from custom_components.foyer.core.models import (
    Actor,
    ArmingDevice,
    Channel,
    CodeAttempt,
    CodeResult,
    DeviceKind,
    EntityState,
    KeyAction,
    KeyCommand,
    Moment,
    Operation,
    Permission,
    Reason,
    ZoneType,
)

from .helpers import NOW, WINDOW, World, make_house, user, zone

READER = user("reader", "Reader", permissions=frozenset({Permission.VIEW_LOG.value}))


def _gate(config, actor, *, permission=Permission.EDIT_CONFIG, **kwargs):
    return authz.may_configure(
        config, actor, Operation.EDIT_CONFIG, permission, NOW, **kwargs
    )


def _with_codes():
    return replace(make_house(), users=(user(), READER))


# --- decision 101: the administrator is asked for the code ------------------------


def test_an_unlinked_administrator_is_asked_for_the_code_once_codes_exist():
    admin = Actor(channel="ha_ui", is_admin=True, account="owner")
    assert _gate(_with_codes(), admin) is Reason.CODE_REQUIRED


def test_an_unlinked_administrator_needs_no_code_while_the_policy_is_inert():
    admin = Actor(channel="ha_ui", is_admin=True, account="owner")
    assert _gate(make_house(), admin) is None


def test_an_unlinked_administrator_reads_without_a_code():
    admin = Actor(channel="ha_ui", is_admin=True, account="owner")
    assert _gate(_with_codes(), admin, need_code=False) is None


def test_an_administrator_is_never_refused_for_want_of_a_permission():
    linked = Actor(
        user_id="reader", channel="ha_ui", identified=True, is_admin=True, account="a"
    )
    # Refused for the code, which applies to them, and never for the
    # permission, which the reader lacks.
    assert _gate(_with_codes(), linked) is Reason.CODE_REQUIRED
    with_code = replace(linked, code=CodeResult.VALID)
    assert _gate(_with_codes(), with_code) is None


def test_a_wrong_code_is_refused_even_for_an_administrator():
    admin = Actor(channel="ha_ui", is_admin=True, code=CodeResult.INVALID)
    assert _gate(_with_codes(), admin) is Reason.BAD_CODE


# --- decision 102: a claimed user grants nothing ----------------------------------


def test_a_claimed_user_does_not_lend_their_permission_to_read_the_log():
    claimed = Actor(user_id="reader", channel="api", claimed=True)
    assert (
        _gate(
            _with_codes(),
            claimed,
            permission=Permission.VIEW_LOG,
            need_code=False,
            open_while_inert=True,
        )
        is Reason.NOT_PERMITTED
    )


def test_the_same_person_established_by_their_code_may_read_it():
    named = Actor(user_id="reader", channel="api", code=CodeResult.VALID)
    assert (
        _gate(
            _with_codes(),
            named,
            permission=Permission.VIEW_LOG,
            need_code=False,
            open_while_inert=True,
        )
        is None
    )


# --- nobody named -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("open_while_inert", "expected"), [(True, None), (False, Reason.NOT_PERMITTED)]
)
def test_nobody_named_before_the_first_code(open_while_inert, expected):
    anybody = Actor(channel="api")
    assert _gate(make_house(), anybody, open_while_inert=open_while_inert) is expected


def test_nobody_named_once_codes_exist_is_refused_everywhere():
    anybody = Actor(channel="api")
    assert _gate(_with_codes(), anybody, open_while_inert=True) is Reason.NOT_PERMITTED


# --- one lockout path ----------------------------------------------------------------


def _wrong_codes(world: World, send, times: int):
    for _ in range(times):
        send(world)
        world.advance(1)


def test_wrong_codes_count_the_same_through_a_config_command_and_an_arming():
    wrong = Actor(channel="ha_ui", code=CodeResult.INVALID, account="guest")
    via_config = World(_with_codes())
    via_arming = World(_with_codes())
    _wrong_codes(
        via_config,
        lambda w: w.send(CodeAttempt(operation=Operation.ARM, actor=wrong)),
        5,
    )
    _wrong_codes(via_arming, lambda w: w.arm("away", actor=wrong), 5)
    assert via_config.state.lockouts == via_arming.state.lockouts
    key = authz.lockout_key(wrong)
    assert via_config.state.lockouts[key].until is not None

    locked_config = via_config.send(CodeAttempt(operation=Operation.ARM, actor=wrong))
    locked_arming = via_arming.arm("away", actor=wrong)
    assert [o.detail for o in locked_config.occurrences] == [
        o.detail for o in locked_arming.occurrences
    ]


def test_a_right_code_clears_the_run_the_same_way_on_both_paths():
    wrong = Actor(channel="ha_ui", code=CodeResult.INVALID, account="guest")
    right = replace(wrong, code=CodeResult.VALID, user_id="luca")
    worlds = []
    for send in (
        lambda w, a: w.send(CodeAttempt(operation=Operation.DISARM, actor=a)),
        lambda w, a: w.send(CodeAttempt(operation=Operation.ARM, actor=a)),
    ):
        world = World(_with_codes())
        _wrong_codes(world, lambda w, s=send: s(w, wrong), 3)
        send(world, right)
        worlds.append(world)
    assert all(authz.lockout_key(wrong) not in w.state.lockouts for w in worlds)


# --- one path for a tag and a key -----------------------------------------------------

TAG = "tag.luca"
KEY = "switch.key"


def _tag_world(entities=None) -> World:
    device = ArmingDevice(
        id="luca_tag",
        name="Luca's tag",
        kind=DeviceKind.TAG,
        entity_id=TAG,
        command=KeyCommand.TOGGLE,
        scenario_id="away",
    )
    world = World(replace(_with_codes(), devices=(device,)), entities)
    world.entities[TAG] = EntityState("2026-09-14T10:00:00+00:00", last_reported=NOW)
    world.advance(0)
    return world


def _key_world(entities=None) -> World:
    key = zone(
        "key",
        KEY,
        "garage",
        type=ZoneType.KEY,
        channel=Channel.KEY,
        key=KeyAction(on_activate=KeyCommand.TOGGLE, scenario_id="away"),
    )
    config = _with_codes()
    world = World(replace(config, zones=(*config.zones, key)), entities)
    world.set(KEY, "off")
    world.advance(0)
    return world


def _failed(decision):
    return [
        (o.scenario_id, o.zone_ids, o.detail.get("reason"))
        for o in decision.occurrences
        if o.moment is Moment.ARM_FAILED
    ]


def test_a_tag_and_a_key_refused_by_an_open_window_say_the_same():
    tag = _tag_world({WINDOW: "on"})
    key = _key_world({WINDOW: "on"})
    by_tag = _failed(tag.set(TAG, "2026-09-14T19:40:00+00:00"))
    by_key = _failed(key.set(KEY, "on"))
    assert by_tag == by_key
    assert by_tag and by_tag[0][2] == Reason.ZONE_OPEN.value


def test_a_tag_and_a_key_arm_and_disarm_alike():
    tag = _tag_world()
    key = _key_world()
    tag.set(TAG, "2026-09-14T19:40:00+00:00")
    key.set(KEY, "on")
    assert tag.states() == key.states()
    tag.advance(60)
    key.advance(60)
    assert tag.states() == key.states()
    assert "armed" in tag.states().values()

    tag.set(TAG, "2026-09-14T19:50:00+00:00")
    key.set(KEY, "off")
    key.set(KEY, "on")
    assert tag.states() == key.states()
    assert set(tag.states().values()) == {"disarmed"}


# --- the configuration row names the field, not the value --------------------------


def test_a_contact_row_says_which_field_changed_and_not_the_service():
    from custom_components.foyer.core.models import (
        Contact,
        ContactChannel,
        ContactChannelKind,
    )
    from custom_components.foyer.store.editing import config_diff

    def with_channel(service):
        channel = ContactChannel("push", ContactChannelKind.PUSH, service)
        return replace(
            make_house(), contacts=(Contact("c1", "Somebody", channels=(channel,)),)
        )

    before = with_channel("notify.mobile_app_somebodys_phone")
    after = with_channel("notify.mobile_app_somebodys_new_phone")
    changes = config_diff(before, after)["contacts"]["changed"]
    assert changes == {"c1": {"channels": []}}
    assert "mobile_app" not in repr(changes)


def test_a_rule_row_says_which_field_changed_and_not_who_it_watches():
    from custom_components.foyer.store.editing import config_diff

    from .helpers import rule

    before = replace(make_house(), rules=(rule(entity_ids=("person.somebody",)),))
    after = replace(
        make_house(), rules=(rule(entity_ids=("person.somebody_else",), grace=60),)
    )
    changes = config_diff(before, after)["rules"]["changed"]
    assert changes == {"Empty house": {"grace_seconds": [], "trigger": []}}
    assert "person." not in repr(changes)


# --- decision 105: alarm_ended ------------------------------------------------------


def _armed_house() -> World:
    world = World()
    world.arm("away")
    world.advance(60)
    assert world.area("ground").state.value == "armed"
    return world


def _ended(decision):
    return [
        (o.area_id, o.detail.get("cause"))
        for o in decision.occurrences
        if o.moment is Moment.ALARM_ENDED
    ]


def test_the_alarm_ends_at_the_siren_cutoff_and_not_again_at_the_disarm():
    world = _armed_house()
    world.set(WINDOW, "on")
    cutoff = world.advance(180)
    assert _ended(cutoff) == [("ground", "siren_cutoff")]
    assert world.area("ground").memory

    assert _ended(world.disarm()) == []


def test_a_disarm_during_the_alarm_ends_it():
    world = _armed_house()
    world.set(WINDOW, "on")
    world.advance(10)
    assert _ended(world.disarm()) == [("ground", "disarmed")]
    # And the cutoff that would have come does not come.
    assert _ended(world.advance(300)) == []


def test_an_ordinary_disarm_is_not_the_end_of_an_alarm():
    world = _armed_house()
    assert _ended(world.disarm()) == []


# --- decision 108: alarm_cleared ------------------------------------------------------


def _cleared(decision):
    return [o.area_id for o in decision.occurrences if o.moment is Moment.ALARM_CLEARED]


def test_the_memory_is_cleared_by_the_disarm_hours_after_the_cutoff():
    world = _armed_house()
    world.set(WINDOW, "on")
    assert _cleared(world.advance(180)) == []
    world.advance(3 * 3600)
    assert _cleared(world.disarm()) == ["ground"]


def test_a_disarm_during_the_alarm_ends_it_and_clears_it():
    world = _armed_house()
    world.set(WINDOW, "on")
    world.advance(10)
    decision = world.disarm()
    assert _ended(decision) == [("ground", "disarmed")]
    assert _cleared(decision) == ["ground"]


def test_an_ordinary_disarm_clears_nothing():
    world = _armed_house()
    assert _cleared(world.disarm()) == []
