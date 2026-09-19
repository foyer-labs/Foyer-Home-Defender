"""Automatic arming rules (SPEC §9.4), and the constraint §19 names.

Everything here runs with no Home Assistant instance: a rule is arithmetic
over the configuration, the state and the entities it is handed, which is what
lets the simulator rehearse a Tuesday at 23:00 without waiting for one.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.foyer.core import rules as rules_engine
from custom_components.foyer.core.engine import next_wakeup
from custom_components.foyer.core.models import (
    ActiveWindow,
    AreaState,
    Moment,
    RuleActionKind,
    RuleBlock,
    RuleGuards,
    RuleTriggerKind,
    Startup,
    Suspension,
    SuspensionKind,
)

from .helpers import LUCA, NOW, PARTNER, World, make_house, rule


def house(*rules, **settings_kwargs):
    config = make_house()
    settings = replace(config.settings, **settings_kwargs)
    return replace(config, rules=rules, settings=settings)


def empty(world: World) -> None:
    """Everybody leaves. Two state changes, as two phones would report."""
    world.person(LUCA, "not_home")
    world.person(PARTNER, "not_home")


# --- the countdown (§9.4) ----------------------------------------------------------


def test_an_empty_house_announces_before_it_arms():
    world = World(house(rule(notify_contact_ids=())))
    empty(world)
    assert not world.state.pending_rules  # thirty minutes have not passed

    decision = world.advance(30 * 60)
    pending = decision.state.pending_rules
    assert len(pending) == 1
    assert pending[0].action is RuleActionKind.ARM
    assert pending[0].seconds == 120
    assert Moment.AUTO_PENDING in decision.moments
    # Announced, not done: the house is still disarmed while it counts down.
    assert world.states()["ground"] == "disarmed"


def test_nobody_presses_anything_and_it_arms():
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    decision = world.advance(120)
    assert not decision.state.pending_rules
    assert world.states()["ground"] == "arming"
    # And when the exit delay ends, the row that says the house is armed
    # still names the rule that did it (§9.4).
    decision = world.advance(30)
    armed = [o for o in decision.occurrences if o.moment is Moment.ARMED]
    assert armed and armed[0].channel == "auto_rule"
    assert armed[0].detail["rule"] == "Empty house"


def test_cancel_stops_it_and_the_log_says_who():
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    pending_id = world.state.pending_rules[0].id

    decision = world.cancel(pending_id, user_id="luca", channel="ha_ui")
    assert decision.accepted
    assert not decision.state.pending_rules
    cancelled = [o for o in decision.occurrences if o.moment is Moment.AUTO_CANCELLED]
    assert cancelled and cancelled[0].user_id == "luca"

    # And it does not arm when the deadline would have passed.
    world.advance(300)
    assert world.states()["ground"] == "disarmed"


def test_cancelling_nothing_is_refused_rather_than_silent():
    world = World(house(rule()))
    decision = world.cancel()
    assert not decision.accepted
    assert decision.reason.value == "nothing_to_cancel"


def test_a_cancelled_rule_does_not_announce_itself_again():
    """Somebody said no. The house stays empty; that is not a new answer."""
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    world.cancel()
    for _ in range(4):
        world.advance(30 * 60)
    assert not world.state.pending_rules
    assert world.states()["ground"] == "disarmed"


def test_somebody_comes_home_and_the_rule_is_free_to_act_again():
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    world.cancel()
    world.person(LUCA, "home")
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules


def test_a_rule_with_no_grace_acts_at_once():
    world = World(house(rule(grace=0)))
    empty(world)
    decision = world.advance(30 * 60)
    assert not decision.state.pending_rules
    assert world.states()["ground"] == "arming"


# --- guards (§9.4, part 2 decision 4) ----------------------------------------------


def test_an_open_window_blocks_the_rule_and_the_log_says_so():
    world = World(house(rule(guards=RuleGuards(only_when_ready=True))))
    world.set("binary_sensor.kitchen_window", "on")
    empty(world)
    decision = world.advance(30 * 60)
    assert not decision.state.pending_rules
    blocked = [o for o in decision.occurrences if o.moment is Moment.AUTO_BLOCKED]
    assert blocked and blocked[0].detail["reason"] == RuleBlock.NOT_READY.value
    assert blocked[0].detail["rule"] == "Empty house"


def test_a_blocked_level_rule_acts_when_the_guard_clears():
    """The condition is still true: shutting the window is the answer to it."""
    world = World(house(rule(guards=RuleGuards(only_when_ready=True))))
    world.set("binary_sensor.kitchen_window", "on")
    empty(world)
    world.advance(30 * 60)
    decision = world.set("binary_sensor.kitchen_window", "off")
    assert decision.state.pending_rules


def test_the_block_is_written_once_not_at_every_wake_up():
    world = World(house(rule(guards=RuleGuards(only_when_ready=True))))
    world.set("binary_sensor.kitchen_window", "on")
    empty(world)
    world.advance(30 * 60)
    rows = 0
    for _ in range(5):
        decision = world.advance(60)
        rows += sum(1 for o in decision.occurrences if o.moment is Moment.AUTO_BLOCKED)
    assert rows == 0  # the first one was written when the block began


def test_a_blocked_time_rule_has_missed_its_turn():
    """23:00 happens once. The window shutting at 23:02 is not another one."""
    at = datetime(2026, 9, 14, 22, 30, tzinfo=UTC)
    world = World(
        house(
            rule(
                kind=RuleTriggerKind.TIME,
                at="23:00",
                entity_ids=(),
                guards=RuleGuards(only_when_ready=True),
                grace=0,
            )
        )
    )
    world.now = at
    world.set("binary_sensor.kitchen_window", "on")
    world.advance(45 * 60)  # 23:15, past the occurrence
    assert world.states()["ground"] == "disarmed"
    world.set("binary_sensor.kitchen_window", "off")
    world.advance(60)
    assert world.states()["ground"] == "disarmed"


def test_motion_inside_blocks_arming():
    world = World(house(rule(guards=RuleGuards(quiet_minutes=10))))
    empty(world)
    world.advance(29 * 60)
    # Somebody is in after all — a phone that lost the network, or the cat.
    world.set("binary_sensor.hall_pir", "on")
    world.set("binary_sensor.hall_pir", "off")
    decision = world.advance(60)
    assert not decision.state.pending_rules
    assert RuleBlock.MOTION.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    # Ten minutes of stillness later, the guard is satisfied.
    decision = world.advance(11 * 60)
    assert decision.state.pending_rules


def test_only_when_disarmed_blocks_an_armed_house():
    world = World(house(rule(guards=RuleGuards(only_when_disarmed=True))))
    world.arm("night")
    world.advance(30)
    empty(world)
    decision = world.advance(30 * 60)
    assert RuleBlock.NOT_DISARMED.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]


# --- the active window (§9.4) ------------------------------------------------------


def test_outside_its_window_a_rule_does_not_exist():
    world = World(house(rule(window=ActiveWindow(after="23:00", before="06:00"))))
    empty(world)
    decision = world.advance(30 * 60)  # 20:02, outside the window
    assert not decision.state.pending_rules
    assert not [o for o in decision.occurrences if o.moment is Moment.AUTO_BLOCKED]


def test_the_window_opening_is_a_wake_up_of_its_own():
    config = house(rule(window=ActiveWindow(after="23:00", before="06:00")))
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    due = next_wakeup(world.snapshot(), config, world.now)
    assert due is not None and due.astimezone(UTC).hour == 23


# --- suspensions and the boiler engineer (§9.4) ------------------------------------


def visitor(**kwargs) -> Suspension:
    return Suspension(
        id="boiler",
        kind=SuspensionKind.VISITOR,
        name="Boiler engineer",
        start=NOW,
        until=NOW + timedelta(hours=4),
        **kwargs,
    )


def test_an_expected_visitor_window_keeps_the_house_from_arming():
    world = World(house(rule()))
    world.suspend(visitor(), user_id="luca", channel="ha_ui")
    empty(world)
    decision = world.advance(30 * 60)
    assert not decision.state.pending_rules
    blocked = [o for o in decision.occurrences if o.moment is Moment.AUTO_BLOCKED]
    # Six months later this row still says why, which "rule suspended" never
    # would (§9.4).
    assert blocked and blocked[0].detail["name"] == "Boiler engineer"


def test_when_the_window_closes_the_house_arms_again():
    world = World(house(rule()))
    world.suspend(visitor())
    empty(world)
    world.advance(30 * 60)
    world.advance(4 * 3600)
    assert world.state.pending_rules


def test_a_visitor_window_may_substitute_a_reduced_scenario():
    world = World(house(rule()))
    world.suspend(visitor(reduced_scenario_id="night"))
    empty(world)
    decision = world.advance(30 * 60)
    pending = decision.state.pending_rules
    assert pending and pending[0].scenario_id == "night"
    assert pending[0].suspension_name == "Boiler engineer"


def test_skip_the_next_occurrence_is_spent_by_use():
    world = World(house(rule()))
    world.suspend(
        Suspension(id="once", kind=SuspensionKind.NEXT, rule_ids=("empty_house",))
    )
    empty(world)
    world.advance(30 * 60)
    assert not world.state.pending_rules
    assert not world.state.suspensions
    # The condition is still true, so the rule is free the moment it is asked
    # again — the suspension skipped one occurrence, not the evening.
    world.person(LUCA, "home")
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules


def test_a_suspension_can_be_lifted_by_hand():
    world = World(house(rule()))
    world.suspend(visitor())
    decision = world.suspend(suspension_id="boiler")
    assert decision.accepted
    assert not decision.state.suspensions


def test_a_suspension_for_an_unknown_rule_is_refused():
    world = World(house(rule()))
    decision = world.suspend(
        Suspension(id="x", kind=SuspensionKind.NEXT, rule_ids=("nope",))
    )
    assert not decision.accepted
    assert decision.reason.value == "unknown_rule"


# --- the kill switch (§9.4, §13) ---------------------------------------------------


def test_the_kill_switch_stops_the_whole_mechanism():
    world = World(house(rule()))
    world.auto_arming(False, user_id="luca", channel="ha_ui")
    empty(world)
    decision = world.advance(30 * 60)
    assert not decision.state.pending_rules
    assert RuleBlock.SWITCH_OFF.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]


def test_switching_it_off_cancels_a_countdown_already_running():
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules
    decision = world.auto_arming(False)
    assert not decision.state.pending_rules
    assert Moment.AUTO_CANCELLED in decision.moments


# --- the asymmetry, enforced (§9.4 points 2 and 3, §19) ----------------------------


def perimeter_house(*rules, **settings):
    config = house(*rules, **settings)
    areas = tuple(
        replace(a, is_perimeter=True) if a.id == "ground" else a for a in config.areas
    )
    return replace(config, areas=areas)


def test_a_disarm_rule_never_disarms_a_perimeter_area():
    """The regression test §19 names, asserted on the Decision itself."""
    config = perimeter_house(
        rule(
            "let_me_in",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            area_ids=("ground", "upstairs"),
            scenario_id=None,
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    assert world.states()["ground"] == "armed"

    empty(world)
    decision = world.person(LUCA, "home")

    disarmed = {o.area_id for o in decision.occurrences if o.moment is Moment.DISARMED}
    assert "upstairs" in disarmed
    assert "ground" not in disarmed
    assert decision.state.area("ground").state is AreaState.ARMED


def test_a_rule_naming_only_perimeter_areas_does_nothing_and_says_why():
    config = perimeter_house(
        rule(
            "let_me_in",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            area_ids=("ground",),
            scenario_id=None,
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    empty(world)
    decision = world.person(LUCA, "home")
    assert RuleBlock.PERIMETER.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    assert decision.state.area("ground").state is AreaState.ARMED


def test_automatic_disarming_is_off_until_it_is_turned_on():
    config = house(
        rule(
            "let_me_in",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            area_ids=("upstairs",),
            scenario_id=None,
            grace=0,
        )
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    empty(world)
    decision = world.person(LUCA, "home")
    assert RuleBlock.AUTO_DISARM_DISABLED.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    assert decision.state.area("upstairs").state is AreaState.ARMED


def test_a_scenario_switch_that_would_disarm_is_gated_like_a_disarm():
    """Part 2 decision 6: a switch disarms without saying the word."""
    config = house(
        rule(
            "to_night",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            action=RuleActionKind.SWITCH,
            scenario_id="night",
            grace=0,
        )
    )
    world = World(config)
    world.arm("away")  # ground, upstairs and garage
    world.advance(30)
    world.now = datetime(2026, 9, 14, 23, 0, tzinfo=UTC)
    decision = world.advance(1)
    assert RuleBlock.AUTO_DISARM_DISABLED.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    assert decision.state.active_scenario_id == "away"


def test_a_switch_leaves_the_perimeter_armed_rather_than_dropping_it():
    config = perimeter_house(
        rule(
            "to_garage",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            action=RuleActionKind.SWITCH,
            scenario_id="night",
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    # Night arms "ground" only, so switching to it from Away would drop
    # upstairs and the garage. Make the perimeter one of the dropped areas.
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
    world.now = datetime(2026, 9, 14, 23, 0, tzinfo=UTC)
    decision = world.advance(1)
    assert decision.state.active_scenario_id == "night"
    # Dropped by the switch, kept by the constraint.
    assert decision.state.area("ground").state is AreaState.ARMED
    assert decision.state.area("ground").scenario_id is None
    assert decision.state.area("garage").state is AreaState.DISARMED


# --- the walk test, and the restart (parts 2 decisions 11 and 12) ------------------


def test_no_rule_acts_during_a_walk_test():
    world = World(house(rule(minutes=2, grace=0)))
    empty(world)
    world.walk_test(True)
    decision = world.advance(3 * 60)
    assert RuleBlock.WALK_TEST.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]


def test_a_countdown_that_expired_during_an_outage_still_acts():
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules
    # Home Assistant was down for an hour; the deadline fell inside it.
    world.now += timedelta(hours=1)
    world.send(Startup(down_since=world.now - timedelta(hours=1)))
    assert world.states()["ground"] == "arming"
    assert world.state.area("ground").rule_id == "empty_house"


# --- triggers (§9.4) ---------------------------------------------------------------


def test_a_time_rule_fires_once_however_often_the_scheduler_wakes():
    config = house(
        rule(
            "at_eleven",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            weekdays=(0,),  # Monday; 2026-09-14 is one
            entity_ids=(),
            grace=0,
        )
    )
    world = World(config)
    world.now = datetime(2026, 9, 14, 22, 59, tzinfo=UTC)
    world.advance(120)
    assert world.states()["ground"] == "arming"
    world.disarm()
    for _ in range(5):
        world.advance(60)
    assert world.states()["ground"] == "disarmed"


def test_a_presence_rule_does_not_fire_on_a_baseline():
    """Somebody already at home has not arrived (§4.7's rule, again)."""
    config = house(
        rule(
            "welcome",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            area_ids=("upstairs",),
            scenario_id=None,
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    assert world.states()["upstairs"] == "armed"


def test_an_entity_rule_waits_for_its_minutes():
    config = house(
        rule(
            "garage_shut",
            kind=RuleTriggerKind.ENTITY,
            entity_ids=("cover.garage",),
            state="closed",
            minutes=10,
            grace=0,
        )
    )
    world = World(config)
    world.advance(9 * 60)
    assert world.states()["ground"] == "disarmed"
    world.advance(2 * 60)
    assert world.states()["ground"] == "arming"


def test_an_unreadable_person_is_not_evidence_that_nobody_is_in():
    world = World(house(rule(grace=0)))
    world.person(LUCA, "not_home")
    world.person(PARTNER, None)
    world.advance(60 * 60)
    assert world.states()["ground"] == "disarmed"


# --- the scheduler reads the same arithmetic (§11.2, INV-1) ------------------------


def test_next_wakeup_knows_when_a_countdown_ends():
    config = house(rule())
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    due = next_wakeup(world.snapshot(), config, world.now)
    assert due == world.state.pending_rules[0].due


def test_next_occurrence_is_the_next_matching_weekday():
    only_friday = rule(kind=RuleTriggerKind.TIME, at="07:00", weekdays=(4,))
    due = rules_engine.next_occurrence(only_friday, NOW, UTC)
    assert due is not None and due.weekday() == 4 and due.hour == 7
