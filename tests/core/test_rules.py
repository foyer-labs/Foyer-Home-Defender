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
    Tick,
)

from .helpers import LUCA, NOW, PARTNER, World, closed_entities, make_house, rule


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


# --- the document, and what the editor refuses (§9.4, §19) -------------------------


def test_a_rule_round_trips_through_the_stored_document():
    from custom_components.foyer.store.schema import config_from_dict, config_to_dict

    config = house(
        rule(
            guards=RuleGuards(only_when_ready=True, quiet_minutes=15),
            window=ActiveWindow(weekdays=(0, 1, 2), after="22:00", before="06:00"),
        )
    )
    restored = config_from_dict(config_to_dict(config))
    assert restored.rules == config.rules


def test_the_state_of_a_countdown_survives_a_restart():
    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    config = house(rule())
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    restored = state_from_dict(state_to_dict(world.state), config)
    assert restored.pending_rules == world.state.pending_rules
    assert restored.rules == world.state.rules
    assert restored.auto_arming is True


def test_validation_refuses_the_rules_that_could_never_act():
    from custom_components.foyer.core.validation import validate

    def codes(*rules, **kwargs):
        return {p.code for p in validate(house(*rules, **kwargs))}

    assert "rule_without_people" in codes(rule(entity_ids=()))
    assert "unknown_scenario" in codes(rule(scenario_id="nope"))
    assert "rule_without_areas" in codes(
        rule(action=RuleActionKind.DISARM, scenario_id=None)
    )
    assert "rule_countdown_without_contacts" in codes(rule(grace=120))
    assert "rule_entity_invalid" in codes(rule(entity_ids=("switch.kitchen",)))
    assert "time_invalid" in codes(rule(kind=RuleTriggerKind.TIME, at="25:00"))
    assert "window_incomplete" in codes(rule(window=ActiveWindow(after="22:00")))


def test_a_disarm_rule_naming_only_the_perimeter_is_refused_at_save_time():
    """The engine takes those areas out; the editor says so before it does."""
    from custom_components.foyer.core.validation import validate

    config = perimeter_house(
        rule(
            action=RuleActionKind.DISARM,
            area_ids=("ground",),
            scenario_id=None,
            grace=0,
        ),
        allow_auto_disarm=True,
    )
    assert "rule_only_perimeter" in {p.code for p in validate(config)}


# --- the simulator reaches the rules (§11.2) ---------------------------------------


def test_the_simulator_rehearses_a_rule_at_a_hypothetical_hour():
    """§11.2 lets the operator pick a date and time. A rule that fires at
    23:00 on weekdays is exactly what somebody wants to rehearse at 11:00 on
    a Monday — and what the trace shows is read off the Decision, never
    predicted beside it (INV-1)."""
    from custom_components.foyer.core.simulate import SimulationRequest, run

    config = house(
        rule(
            "at_eleven",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            grace=0,
        )
    )
    request = SimulationRequest(
        start=datetime(2026, 9, 14, 22, 55, tzinfo=UTC),
        scenario_id=None,  # a disarmed house: the rule is what arms it
        horizon=3600,
    )
    simulation = run(config, request, closed_entities(config, request.start))
    moments = [o.moment for step in simulation.steps for o in step.occurrences]
    assert Moment.ARMED in moments or simulation.final.area("ground").state in (
        AreaState.ARMING,
        AreaState.ARMED,
    )


def test_the_trace_shows_the_guard_that_blocked_a_rule():
    from custom_components.foyer.core.simulate import SimulationRequest, run

    config = house(
        rule(
            "at_eleven",
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            guards=RuleGuards(only_when_ready=True),
            grace=0,
        )
    )
    request = SimulationRequest(
        start=datetime(2026, 9, 14, 22, 55, tzinfo=UTC),
        scenario_id=None,
        entities={"binary_sensor.kitchen_window": "on"},
        horizon=3600,
    )
    simulation = run(config, request, closed_entities(config, request.start))
    blocked = [
        o
        for step in simulation.steps
        for o in step.occurrences
        if o.moment is Moment.AUTO_BLOCKED
    ]
    assert blocked and blocked[0].detail["reason"] == RuleBlock.NOT_READY.value
    assert simulation.final.area("ground").state is AreaState.DISARMED


def test_a_countdown_left_running_makes_the_trace_say_it_was_cut_short():
    from custom_components.foyer.core.simulate import SimulationRequest, run

    config = house(rule(minutes=1))
    request = SimulationRequest(
        start=NOW,
        scenario_id=None,
        entities={LUCA: "not_home", PARTNER: "not_home"},
        horizon=120,
    )
    simulation = run(config, request, closed_entities(config, request.start))
    assert simulation.final.pending_rules
    assert simulation.truncated


def test_stopping_the_mechanism_asks_the_same_policy_entry_as_cancel():
    """The kill switch and a suspension both stop the house arming itself,
    so an installation that raised the policy for Cancel has raised it for
    both. With no code held by anybody the policy is inert (decision 78)."""
    from dataclasses import replace as _replace

    from custom_components.foyer.core.models import CodePolicy, CodeResult

    from .helpers import user

    config = house(rule())
    config = _replace(
        config,
        users=(user(),),
        code_policy=CodePolicy(cancel_auto_action=True),
    )
    world = World(config)
    refused = world.auto_arming(False, user_id="luca", channel="ha_ui")
    assert not refused.accepted
    assert refused.reason.value == "code_required"
    assert refused.state.auto_arming is True

    accepted = world.auto_arming(
        False, user_id="luca", channel="ha_ui", code=CodeResult.VALID
    )
    assert accepted.accepted
    assert accepted.state.auto_arming is False


def test_the_house_going_quiet_is_a_wake_up_of_its_own():
    """Nothing else announces a hall that stops moving: without this the
    rule would wait for an unrelated entity to change."""
    config = house(rule(guards=RuleGuards(quiet_minutes=10)))
    world = World(config)
    empty(world)
    world.advance(29 * 60)
    world.set("binary_sensor.hall_pir", "on")
    world.set("binary_sensor.hall_pir", "off")
    world.advance(60)
    assert not world.state.pending_rules

    due = next_wakeup(world.snapshot(), config, world.now)
    assert due == world.now + timedelta(minutes=9)
    world.now = due
    assert world.send(Tick()).state.pending_rules


def test_a_visitor_window_lasts_the_morning_not_one_substitution():
    """The engineer is there until one. A window spent by its first
    substitution would arm the house around them at the second rule."""
    world = World(house(rule(), rule("second", minutes=45)))
    world.suspend(visitor(reduced_scenario_id="night"))
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules[0].scenario_id == "night"
    assert world.state.suspensions  # still covering the rest of the morning
    world.cancel()
    world.advance(20 * 60)
    assert world.state.pending_rules[0].scenario_id == "night"


def test_every_blocked_occurrence_of_a_time_rule_is_logged():
    """Monday's row is not an answer to Tuesday's silence."""
    config = house(
        rule(
            kind=RuleTriggerKind.TIME,
            at="23:00",
            entity_ids=(),
            guards=RuleGuards(only_when_ready=True),
            grace=0,
        )
    )
    world = World(config)
    world.now = datetime(2026, 9, 14, 22, 30, tzinfo=UTC)
    world.set("binary_sensor.kitchen_window", "on")
    rows = 0
    for night in range(3):  # three nights, the window open on each
        # 22:30 -> 23:15, then the same hour on the next two days.
        world.advance(45 * 60 if night == 0 else 24 * 3600)
        rows += sum(1 for r in world.blocked() if r == RuleBlock.NOT_READY.value)
    assert rows == 3


def test_a_rehearsal_knows_what_is_suspended_and_whether_the_switch_is_on():
    """ "Would it arm tomorrow morning, with the engineer expected?" is the
    question, and it cannot be answered by a run that starts from nothing."""
    from dataclasses import replace as _replace

    from custom_components.foyer.core.models import RuntimeState
    from custom_components.foyer.core.simulate import SimulationRequest, run as sim_run

    config = house(rule(minutes=1, grace=0))
    request = SimulationRequest(
        start=NOW,
        scenario_id=None,
        entities={LUCA: "not_home", PARTNER: "not_home"},
        horizon=600,
    )
    live = closed_entities(config, NOW)

    covered = sim_run(
        config,
        request,
        live,
        carry=RuntimeState(suspensions=(visitor(),)),
    )
    assert covered.final.area("ground").state is AreaState.DISARMED

    switched_off = sim_run(config, request, live, carry=RuntimeState(auto_arming=False))
    assert switched_off.final.area("ground").state is AreaState.DISARMED
    assert _replace(switched_off.final, auto_arming=True) is not None

    free = sim_run(config, request, live)
    assert free.final.area("ground").state is not AreaState.DISARMED


# --- what the review of the pure engine found (all of it, asserted) ----------------


def test_an_arm_rule_cannot_disarm_the_perimeter_by_switching_scenario():
    """`arm Night` on a house running Away is a scenario switch (§4.6.1), so
    it meets the same two gates a `switch` meets — or "arm" would be the way
    round both of them."""
    config = perimeter_house(rule("to_night", scenario_id="night", grace=0))
    world = World(config)
    world.arm("away")
    world.advance(30)
    empty(world)
    decision = world.advance(30 * 60)
    assert RuleBlock.AUTO_DISARM_DISABLED.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    assert decision.state.active_scenario_id == "away"
    assert decision.state.area("ground").state is AreaState.ARMED


def test_an_arming_that_was_refused_tries_again_when_the_window_shuts():
    world = World(house(rule(grace=0)))
    world.set("binary_sensor.kitchen_window", "on")
    empty(world)
    decision = world.advance(30 * 60)
    assert Moment.ARM_FAILED in decision.moments
    assert world.states()["ground"] == "disarmed"

    decision = world.set("binary_sensor.kitchen_window", "off")
    assert world.states()["ground"] == "arming"


def test_a_tracker_that_lost_the_network_has_not_come_home():
    """An unreadable person is not an arrival — INV-4, applied to people."""
    config = house(
        rule(
            "welcome",
            kind=RuleTriggerKind.PRESENCE,
            entity_ids=(LUCA,),
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
    world.person(LUCA, "unavailable")
    world.person(LUCA, "home")
    assert world.states()["upstairs"] == "armed"


def test_skip_the_next_occurrence_skips_the_occurrence_not_one_evaluation():
    world = World(house(rule()))
    world.suspend(
        Suspension(id="once", kind=SuspensionKind.NEXT, rule_ids=("empty_house",))
    )
    empty(world)
    world.advance(30 * 60)
    assert not world.state.pending_rules
    for _ in range(3):
        world.advance(60)
    assert not world.state.pending_rules


def test_a_walk_test_does_not_spend_the_skip_somebody_asked_for():
    world = World(house(rule(minutes=2)))
    world.suspend(Suspension(id="once", kind=SuspensionKind.NEXT))
    empty(world)
    world.walk_test(True)
    world.advance(3 * 60)
    assert world.state.suspensions  # the walk test blocked it, not the skip


def test_a_suspension_that_loses_every_rule_it_named_is_dropped():
    """An empty rule list means *every* rule, so filtering must never empty
    one: a suspension of one deleted rule would become a month of silence."""
    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    config = house(rule())
    world = World(config)
    world.suspend(Suspension(id="x", kind=SuspensionKind.UNTIL, rule_ids=("gone",)))
    restored = state_from_dict(state_to_dict(world.state), config)
    assert restored.suspensions == ()


def test_the_sensor_does_not_announce_a_rule_that_has_had_its_turn():
    config = house(rule(grace=0))
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    world.advance(60)
    upcoming = rules_engine.next_action(config, world.state, world.now, UTC)
    assert upcoming is None


def test_a_countdown_whose_rule_was_deleted_says_so():
    from dataclasses import replace as _replace

    config = house(rule())
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules

    world.config = _replace(config, rules=())
    decision = world.advance(30)
    assert not decision.state.pending_rules
    assert Moment.AUTO_CANCELLED in decision.moments


def test_a_suspension_with_no_end_is_refused():
    """Three forms, and every one of them ends (§9.4). One that did not
    would be the kill switch under a name nobody would look for."""
    world = World(house(rule()))
    endless = world.suspend(Suspension(id="x", kind=SuspensionKind.UNTIL))
    assert not endless.accepted
    assert not world.state.suspensions

    named = world.suspend(
        Suspension(id="y", kind=SuspensionKind.VISITOR, name="Boiler engineer")
    )
    assert not named.accepted


def test_a_refused_arming_does_not_ask_again_every_two_minutes():
    """The countdown is an actionable push. A rule that restarted it after
    every refusal would say "the house will arm in two minutes" all night,
    about an arming that cannot happen."""
    world = World(house(rule()))
    world.set("binary_sensor.kitchen_window", "on")
    empty(world)
    world.advance(30 * 60)  # the countdown starts
    world.advance(130)  # it fires, and the arming is refused
    assert Moment.ARM_FAILED in (world.last.moments if world.last else ())
    assert not world.state.pending_rules

    announcements = 0
    for _ in range(6):
        decision = world.advance(130)
        announcements += sum(1 for m in decision.moments if m is Moment.AUTO_PENDING)
    assert announcements == 0
    assert not world.state.pending_rules

    # And it is not dead either: shutting the window is what releases it.
    decision = world.set("binary_sensor.kitchen_window", "off")
    assert decision.state.pending_rules


def test_a_rule_refused_for_something_no_zone_can_fix_waits_its_turn():
    """A deleted scenario is not an open window: there is nothing to shut,
    so the rule waits until the house fills and empties again."""
    from dataclasses import replace as _replace

    config = house(rule(grace=0))
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    world.disarm()
    world.config = _replace(config, scenarios=())

    failures = 0
    for _ in range(5):
        decision = world.advance(60)
        failures += sum(1 for m in decision.moments if m is Moment.ARM_FAILED)
    assert failures <= 1


def test_a_countdown_survives_a_reload_that_deleted_its_rule():
    """It is restored so the engine can cancel it with a row; filtering it
    out of the document is what made it vanish in silence."""
    from dataclasses import replace as _replace

    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    config = house(rule())
    world = World(config)
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules

    gone = _replace(config, rules=())
    restored = state_from_dict(state_to_dict(world.state), gone)
    assert restored.pending_rules

    world.config = gone
    world.state = restored
    decision = world.advance(30)
    assert not decision.state.pending_rules
    assert Moment.AUTO_CANCELLED in decision.moments


def test_a_skip_pressed_during_the_countdown_skips_the_occurrence():
    """The button says "skip the next occurrence". Spending it and then
    arming the house two minutes later is the opposite of that."""
    world = World(house(rule()))
    empty(world)
    world.advance(30 * 60)
    assert world.state.pending_rules

    world.suspend(
        Suspension(id="once", kind=SuspensionKind.NEXT, rule_ids=("empty_house",))
    )
    world.advance(130)  # the deadline: the suspension answers it
    assert not world.state.pending_rules
    assert not world.state.suspensions

    for _ in range(4):
        world.advance(130)
    assert not world.state.pending_rules
    assert world.states()["ground"] == "disarmed"


def test_a_rule_never_silences_an_alarm():
    """§4.6.1 refuses a scenario switch while an area is in entry or
    triggered. A rule is the same case and more so: disarming an area the
    incident touched acknowledges it and stops the escalation (§7.2)."""
    config = house(
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
    world.arm("night")
    world.advance(10)
    world.set("binary_sensor.kitchen_window", "on")  # instant zone: triggered
    assert world.states()["ground"] == "triggered"

    empty(world)
    decision = world.person(LUCA, "home")
    assert RuleBlock.ALARM_IN_PROGRESS.value in [
        o.detail.get("reason") for o in decision.occurrences
    ]
    assert decision.state.area("ground").state is AreaState.TRIGGERED
    assert decision.state.incident is not None
    assert not decision.state.incident.acknowledged


def test_an_hour_that_fell_while_the_system_was_down_is_recorded():
    config = house(rule(kind=RuleTriggerKind.TIME, at="23:00", entity_ids=(), grace=0))
    world = World(config)
    world.now = datetime(2026, 9, 14, 22, 30, tzinfo=UTC)
    world.advance(1)
    down_since = world.now
    world.now += timedelta(hours=2)  # 00:31, through the 23:00 occurrence

    decision = world.send(Startup(down_since=down_since))
    blocked = [o for o in decision.occurrences if o.moment is Moment.AUTO_BLOCKED]
    assert blocked and blocked[0].detail["reason"] == RuleBlock.MISSED.value
    # Recorded, not acted on: an arming nobody was told about is not a
    # kindness at half past midnight.
    assert world.states()["ground"] == "disarmed"


def test_an_arm_rule_keeps_a_perimeter_area_armed_when_it_may_disarm():
    """With automatic disarming enabled, an `arm` that behaves as a switch
    drops what it may and leaves the perimeter exactly as it was."""
    config = perimeter_house(
        rule("to_night", scenario_id="night", grace=0), allow_auto_disarm=True
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
    empty(world)
    decision = world.advance(30 * 60)

    assert decision.state.active_scenario_id == "night"
    assert decision.state.area("ground").state is AreaState.ARMED
    assert decision.state.area("ground").scenario_id is None
    assert decision.state.area("garage").state is AreaState.DISARMED


# --- every area (decision 163) -----------------------------------------------------


def _every_area():
    return perimeter_house(
        rule(
            "let_me_in",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            area_ids=(),
            scenario_id=None,
            grace=0,
            all_areas=True,
        ),
        allow_auto_disarm=True,
    )


def test_every_area_disarms_all_but_the_perimeter():
    world = World(_every_area())
    world.arm("away")
    world.advance(30)
    empty(world)
    decision = world.person(LUCA, "home")

    disarmed = {o.area_id for o in decision.occurrences if o.moment is Moment.DISARMED}
    assert "upstairs" in disarmed
    assert "ground" not in disarmed
    assert decision.state.area("ground").state is AreaState.ARMED


def test_every_area_follows_the_areas_the_house_has_now():
    """An area added after the rule was written is disarmed too: the rule
    names the house, not a list written once."""
    config = _every_area()
    assert rules_engine.named_areas(config, config.rules[0]) == tuple(
        a.id for a in config.areas
    )
    added = replace(
        config,
        areas=(*config.areas, replace(config.areas[-1], id="attic", name="Attic")),
    )
    assert "attic" in rules_engine.named_areas(added, added.rules[0])


def test_every_area_needs_no_list_to_be_saved():
    from custom_components.foyer.core.validation import validate

    codes = {p.code for p in validate(_every_area())}
    assert "rule_without_areas" not in codes
    assert "rule_only_perimeter" not in codes


# --- where "away" is, and a disarm with nothing to disarm (decision 166) ----------


def test_somebody_in_another_zone_is_away():
    """A person at work reads "Work", not `not_home`: they are still out."""
    world = World(house(rule(notify_contact_ids=())))
    world.person(LUCA, "Work")
    world.person(PARTNER, "not_home")
    decision = world.advance(30 * 60)
    assert Moment.AUTO_PENDING in decision.moments


def test_a_person_who_cannot_be_read_is_not_away():
    world = World(house(rule(notify_contact_ids=())))
    world.person(LUCA, "unknown")
    world.person(PARTNER, "not_home")
    decision = world.advance(30 * 60)
    assert Moment.AUTO_PENDING not in decision.moments
    assert not world.state.pending_rules


def _welcome_home(grace: int = 10):
    return house(
        rule(
            "welcome_home",
            kind=RuleTriggerKind.PRESENCE,
            action=RuleActionKind.DISARM,
            scenario_id=None,
            all_areas=True,
            grace=grace,
        ),
        allow_auto_disarm=True,
    )


def test_coming_home_to_a_disarmed_house_does_nothing_at_all():
    world = World(_welcome_home())
    empty(world)
    decision = world.person(LUCA, "home")

    assert not decision.state.pending_rules
    assert Moment.AUTO_PENDING not in decision.moments
    assert Moment.AUTO_BLOCKED not in decision.moments
    decision = world.advance(30)
    assert not decision.moments


def test_that_arrival_does_not_disarm_the_house_armed_later():
    """The arrival is spent: arming afterwards, with the person still home,
    must not be undone by a rule that already saw them come in."""
    world = World(_welcome_home(grace=0))
    empty(world)
    world.person(LUCA, "home")
    world.arm("away")
    world.advance(30)
    assert world.states()["ground"] == "armed"
    world.advance(600)
    assert world.states()["ground"] == "armed"


def test_coming_home_to_an_armed_house_still_disarms_it():
    world = World(_welcome_home(grace=0))
    world.arm("away")
    world.advance(30)
    empty(world)
    world.person(LUCA, "home")
    assert world.states()["ground"] == "disarmed"
