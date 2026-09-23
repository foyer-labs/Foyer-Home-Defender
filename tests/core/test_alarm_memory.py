"""Alarm memory: until the area is disarmed or armed again (SPEC §5.2).

Decisions 140 and 141, and the alarm memory tests §19 names. An accepted
arming starts a new watch, so it clears the memory of every area it takes out
of `disarmed` and raises `alarm_cleared` as a disarm does — and acknowledges
nothing: the incident and its escalation go on until somebody acknowledges it
or disarms. Nothing else that looks like arming clears it.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from custom_components.foyer.core.engine import AUTO_RULE_CHANNEL, KEY_ZONE_CHANNEL
from custom_components.foyer.core.journal import rows_for
from custom_components.foyer.core.models import (
    ActionKind,
    Actor,
    AlarmKind,
    AreaState,
    ArmAreaRequest,
    CodeResult,
    LogCategory,
    LogSeverity,
    Moment,
    Permission,
    Reason,
    RuleActionKind,
    RuleTriggerKind,
    Settings,
    ZoneType,
)

from .helpers import (
    PATIO,
    TAMPER,
    WINDOW,
    World,
    make_house,
    rule,
    user,
    zone,
)
from .test_escalation import escalating_house, notified, step
from .test_profiles import LAMP, action, house as profile_house, profile
from .test_review_2_followup import KEY, TAG, _key_world, _tag_world
from .test_rules import empty, house as rule_house, perimeter_house

VAULT = "binary_sensor.vault"


def cleared(decision) -> list[str]:
    return [o.area_id for o in decision.occurrences if o.moment is Moment.ALARM_CLEARED]


def cleared_row(decision, area_id: str = "ground"):
    [row] = [
        o
        for o in decision.occurrences
        if o.moment is Moment.ALARM_CLEARED and o.area_id == area_id
    ]
    return row


def remembered(world: World) -> World:
    """The tamper fires on a disarmed house and its cutoff runs: the ground
    floor is disarmed again, holding the memory of it (§5.2)."""
    world.set(TAMPER, "on")
    world.advance(180)
    world.set(TAMPER, "off")  # nothing open: the area could arm
    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert rt.memory and rt.causes == ("tamper",)
    return world


def vault_house():
    """The shared house, with a 24h zone upstairs as well."""
    config = make_house()
    vault = zone(
        "vault",
        VAULT,
        "upstairs",
        type=ZoneType.H24,
        alarm_kind=AlarmKind.INTRUSION,
        always_on=True,
        bypassable=False,
    )
    return replace(config, zones=(*config.zones, vault))


# --- an accepted arming clears it (decision 140) -------------------------------------


def test_an_accepted_arming_clears_the_memory_and_says_so():
    world = remembered(World(replace(make_house(), users=(user(),))))
    incident = world.state.incident
    assert incident is not None

    decision = world.arm_area(
        "ground", actor=Actor(user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    )

    assert decision.accepted
    rt = world.area("ground")
    assert rt.state is AreaState.ARMING
    assert not rt.memory and rt.causes == ()
    row = cleared_row(decision)
    # The row says what the disarm's row says: which zones, who, how, and
    # which night it belonged to.
    assert row.zone_ids == ("tamper",)
    assert row.channel == "ha_ui"
    assert (row.user_id, row.user_name) == ("luca", "Luca")
    assert row.incident_id == incident.id
    assert row.scenario_id is None  # armed on its own
    # No cause: it would reach a message's {{ reason }} (§6.4).
    assert "cause" not in row.detail


def test_the_log_row_is_the_alarm_row_a_disarm_writes():
    world = remembered(World(replace(make_house(), users=(user(),))))
    event = ArmAreaRequest(
        "ground", actor=Actor(user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    )
    decision = world.send(event)

    rows = rows_for(event, decision, world.config)
    [row] = [r for r in rows if r.event_type == Moment.ALARM_CLEARED.value]
    assert row.category is LogCategory.ALARM
    assert row.severity is LogSeverity.INFO
    assert (row.area_id, row.channel, row.user_name) == ("ground", "ha_ui", "Luca")
    assert row.incident_id == world.state.incident.id
    assert row.detail["zone_ids"] == ["tamper"]
    assert row.outcome == "ok"


def test_it_is_raised_once_for_each_area_the_arming_clears():
    world = World(vault_house())
    world.set(TAMPER, "on")
    world.set(VAULT, "on")
    world.advance(180)
    world.set(TAMPER, "off")
    world.set(VAULT, "off")
    assert world.area("ground").memory and world.area("upstairs").memory

    decision = world.arm("away")

    assert decision.accepted
    assert cleared(decision) == ["ground", "upstairs"]
    assert all(
        o.scenario_id == "away"
        for o in decision.occurrences
        if o.moment is Moment.ALARM_CLEARED
    )
    assert not world.area("ground").memory and not world.area("upstairs").memory


def test_only_the_areas_holding_memory_are_cleared():
    world = remembered(World())
    assert cleared(world.arm("away")) == ["ground"]


def test_the_disarm_that_follows_has_nothing_left_to_clear():
    world = remembered(World())
    world.arm("away")
    world.advance(60)
    assert world.area("ground").state is AreaState.ARMED
    assert cleared(world.disarm()) == []


def test_with_no_exit_delay_the_memory_is_cleared_before_the_area_arms():
    world = remembered(World())
    decision = world.arm("away", skip_exit_delay=True)

    ground = [
        o.moment
        for o in decision.occurrences
        if o.area_id == "ground" and o.moment in (Moment.ALARM_CLEARED, Moment.ARMED)
    ]
    assert ground == [Moment.ALARM_CLEARED, Moment.ARMED]
    assert world.area("ground").state is AreaState.ARMED
    assert not world.area("ground").memory


def test_a_forced_arming_clears_it_after_saying_it_was_forced():
    world = remembered(World())
    world.set(WINDOW, "on")
    decision = world.arm("away", force=True)

    assert decision.accepted
    moments = list(decision.moments)
    assert moments.index(Moment.FORCED_ARM) < moments.index(Moment.ALARM_CLEARED)
    assert not world.area("ground").memory


def test_a_profile_hears_it_at_the_arming():
    """Decision 108's lamp: "something happened while you were out" goes off
    when the house is armed again, as it does at a disarm."""
    config = profile_house(
        profile(
            "p",
            action(
                "lamp_off",
                ActionKind.SWITCH,
                Moment.ALARM_CLEARED,
                entity_ids=(LAMP,),
                state="off",
            ),
        )
    )
    world = remembered(World(config))
    decision = world.arm("away")
    assert [
        a.action_id for a in decision.actions if a.moment is Moment.ALARM_CLEARED
    ] == ["lamp_off"]


# --- whoever armed, an automatic rule included ---------------------------------------


def test_an_automatic_rule_arming_clears_it_and_the_row_names_the_rule():
    world = remembered(World(rule_house(rule(grace=0))))
    empty(world)
    decision = world.advance(30 * 60)

    assert world.area("ground").state is AreaState.ARMING
    row = cleared_row(decision)
    assert row.channel == AUTO_RULE_CHANNEL
    assert row.detail["rule"] == "Empty house"
    assert row.detail["rule_id"] == "empty_house"
    assert not world.area("ground").memory
    # The incident is another matter: a rule has seen nothing.
    assert world.state.incident is not None
    assert not world.state.incident.acknowledged


def test_a_key_switch_arming_clears_it():
    world = remembered(_key_world())
    decision = world.set(KEY, "on")
    assert cleared_row(decision).channel == KEY_ZONE_CHANNEL
    assert not world.area("ground").memory


def test_a_tag_arming_clears_it():
    world = remembered(_tag_world())
    decision = world.set(TAG, "2026-09-14T19:40:00+00:00")
    assert cleared_row(decision).channel == world.config.devices[0].channel
    assert not world.area("ground").memory


# --- clearing the memory is not taking note of the alarm (§5.6) ----------------------


def test_the_arming_acknowledges_nothing_and_the_escalation_carries_on():
    config = escalating_house(
        (
            step("s0", 0, "luca", "luca-push"),
            step("s1", 600, "luca", "luca-sms"),
            step("s2", 1200, "partner", "partner-push"),
        )
    )
    world = World(config)
    world.set(TAMPER, "on")
    assert notified(world.last) == ["luca/luca-push"]
    world.advance(180)  # cutoff: the ground floor is disarmed, in memory
    world.set(TAMPER, "off")
    incident = world.state.incident

    decision = world.arm("away")

    assert cleared(decision) == ["ground"]
    assert Moment.INCIDENT_ACKNOWLEDGED not in decision.moments
    assert world.state.incident == incident
    assert not world.state.incident.acknowledged
    assert world.state.escalations != ()
    # Armed now, and the next step still goes out when its time comes.
    decision = world.advance(420)
    assert world.area("ground").state is AreaState.ARMED
    assert notified(decision) == ["luca/luca-sms"]

    # Somebody who disarms has seen it: that is the acknowledgement.
    decision = world.disarm()
    assert Moment.INCIDENT_ACKNOWLEDGED in decision.moments
    assert world.state.escalations == ()
    assert cleared(decision) == []


# --- a refused arming leaves it (decision 141) ---------------------------------------


def _refused_by_an_open_window(world: World):
    world.set(WINDOW, "on")
    return world.arm("away")


def _refused_by_a_fault(world: World):
    world.set(WINDOW, None)
    return world.arm("away")


def _refused_during_a_walk_test(world: World):
    world.walk_test()
    return world.arm_area("ground")


def _refused_a_permission(world: World):
    world.config = replace(
        world.config,
        users=(user(permissions=frozenset({Permission.DISARM.value})),),
    )
    return world.arm("away", actor=Actor(user_id="luca", code=CodeResult.VALID))


@pytest.mark.parametrize(
    "refuse",
    [
        _refused_by_an_open_window,
        _refused_by_a_fault,
        _refused_during_a_walk_test,
        _refused_a_permission,
    ],
)
def test_a_refused_arming_leaves_the_memory(refuse):
    world = remembered(World())
    decision = refuse(world)
    assert not decision.accepted
    assert cleared(decision) == []
    assert world.area("ground").memory
    assert world.area("ground").causes == ("tamper",)


def test_a_key_switch_refused_by_an_open_window_leaves_it():
    world = remembered(_key_world({WINDOW: "on"}))
    decision = world.set(KEY, "on")
    assert Moment.ARM_FAILED in decision.moments
    assert cleared(decision) == []
    assert world.area("ground").memory


def test_an_area_already_armed_cannot_be_armed_again_and_keeps_it():
    world = World()
    world.arm("night")
    world.advance(5)
    world.set(WINDOW, "on")
    world.advance(180)  # cutoff: armed again, holding the memory
    world.set(WINDOW, "off")
    assert world.area("ground").state is AreaState.ARMED
    decision = world.arm_area("ground")
    assert decision.reason is Reason.INVALID_STATE
    assert cleared(decision) == []
    assert world.area("ground").memory


# --- accepted, then failed at the end of its exit delay ------------------------------


def test_an_arming_that_fails_at_its_exit_deadline_does_not_bring_it_back():
    world = remembered(World())
    assert cleared(world.arm("away")) == ["ground"]
    world.set(WINDOW, "on")  # opened during the exit delay
    decision = world.advance(30)

    assert Moment.ARM_FAILED in decision.moments
    assert cleared(decision) == []
    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert not rt.memory and rt.causes == ()


def test_an_arming_whose_hold_runs_out_does_not_bring_it_back_either():
    world = remembered(World())
    world.set(PATIO, "on")  # arm after closing: it holds, then gives up
    assert cleared(world.arm("away")) == ["ground"]
    world.advance(30)
    assert world.area("ground").state is AreaState.ARMING
    decision = world.advance(300)

    assert Moment.ARM_FAILED in decision.moments
    assert cleared(decision) == []
    assert not world.area("ground").memory


# --- the cutoff resuming an arming is not arming again -------------------------------


def test_the_cutoff_resuming_an_arming_keeps_the_memory():
    config = make_house()
    config = replace(
        config,
        areas=tuple(replace(a, default_exit_delay=300) for a in config.areas),
        settings=Settings(siren_duration=60),
    )
    world = World(config)
    world.arm("away")
    world.set(TAMPER, "on")
    world.set(TAMPER, "off")
    assert world.area("ground").state is AreaState.TRIGGERED

    resumed = world.advance(60)  # cutoff: the arming resumes
    assert world.area("ground").state is AreaState.ARMING
    assert world.area("ground").memory
    completed = world.advance(240)  # its original deadline
    assert world.area("ground").state is AreaState.ARMED
    assert world.area("ground").memory
    assert cleared(resumed) == [] and cleared(completed) == []


# --- an area staying armed through a switch was not armed again ----------------------


def test_a_switch_clears_the_areas_it_arms_and_not_the_ones_that_stay_armed():
    world = World(vault_house())
    world.arm("night")  # the ground floor only
    world.advance(5)
    world.set(WINDOW, "on")  # the armed ground floor alarms
    world.set(VAULT, "on")  # and the disarmed upstairs, through its 24h zone
    world.advance(180)
    world.set(WINDOW, "off")
    world.set(VAULT, "off")
    assert world.area("ground").state is AreaState.ARMED
    assert world.area("upstairs").state is AreaState.DISARMED
    assert world.area("ground").memory and world.area("upstairs").memory

    decision = world.arm("away")  # Night -> Away

    assert decision.accepted
    # Upstairs is armed by the switch and starts clean; the ground floor
    # stays armed, and keeps what happened while it was.
    assert cleared(decision) == ["upstairs"]
    assert not world.area("upstairs").memory
    assert world.area("ground").memory
    assert world.area("ground").causes == ("window",)
    assert cleared(world.disarm()) == ["ground"]


def test_a_perimeter_a_rule_keeps_armed_through_its_switch_keeps_it():
    config = perimeter_house(
        rule(
            "to_night",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            action=RuleActionKind.SWITCH,
            scenario_id="night",
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    config = replace(
        config,
        scenarios=tuple(
            replace(s, areas=("upstairs",)) if s.id == "night" else s
            for s in config.scenarios
        ),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "on")
    world.advance(180)
    world.set(WINDOW, "off")
    assert world.area("ground").memory

    world.now = datetime(2026, 9, 14, 23, 0, tzinfo=UTC)
    decision = world.advance(1)

    assert decision.state.active_scenario_id == "night"
    assert world.area("ground").state is AreaState.ARMED
    assert world.area("ground").scenario_id is None
    assert world.area("ground").memory
    assert cleared(decision) == []


# --- a walk test is not a watch ------------------------------------------------------


def test_a_walk_test_neither_arms_nor_clears_an_area_holding_memory():
    world = remembered(World())
    started = world.walk_test()
    assert "ground" not in world.state.walk_test.armed_areas
    assert "upstairs" in world.state.walk_test.armed_areas
    ended = world.walk_test(False)

    assert cleared(started) == [] and cleared(ended) == []
    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert rt.memory and rt.causes == ("tamper",)
    # And a real arming afterwards clears it as any arming does.
    assert cleared(world.arm("away")) == ["ground"]
