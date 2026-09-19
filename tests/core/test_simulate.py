"""The simulator (SPEC §11.2): the same engine, a fabricated world, nothing run.

The test that matters most in this file is
``test_the_simulator_and_the_runtime_reach_the_same_decision``. Everything
else here checks that the trace *reports* what happened; that one checks that
what happened is what the house would have done. If it ever fails, the fix is
never in the simulator — it is that a second evaluation path has appeared
somewhere upstream, and INV-1 has been broken.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.foyer.core.engine import decide
from custom_components.foyer.core.models import (
    ActionKind,
    AreaRuntime,
    AreaState,
    ArmRequest,
    ConditionMode,
    EntityState,
    Group,
    Moment,
    ProfileAction,
    Reason,
    ResponseProfile,
    RuntimeState,
    StateCondition,
    StateOperator,
    SystemSnapshot,
    Tick,
    TimeCondition,
    ZoneStateChanged,
)
from custom_components.foyer.core.response import (
    FROM_AREA,
    FROM_DEFAULT,
    FROM_GROUP,
    FROM_ZONE,
    SKIP_CONDITION,
    SKIP_HELD_BY_DELAY,
    SKIP_SILENT,
)
from custom_components.foyer.core.simulate import (
    MAX_HORIZON,
    STEP_SETUP,
    SimulationRequest,
    ZoneOverride,
    as_dict,
    inputs,
    run,
)

from .helpers import WINDOW, closed_entities, make_house, zone

START = datetime(2026, 9, 19, 19, 32, tzinfo=UTC)


def live(config):
    return closed_entities(config, START)


def simulate(config, **kwargs):
    kwargs.setdefault("start", START)
    return run(config, SimulationRequest(**kwargs), live(config))


def moments(simulation):
    return [(step.at, o.moment) for step in simulation.steps for o in step.occurrences]


def step_with(simulation, moment):
    return next(
        step
        for step in simulation.steps
        if any(o.moment is moment for o in step.occurrences)
    )


def batch_for(step, moment):
    return next(b for b in step.batches if b.moment == moment.value)


# --- the decision chain ------------------------------------------------------------


def test_a_delayed_zone_walks_the_whole_chain_to_triggered():
    """§11.2's worked example: armed, entry delay, expiry, triggered."""
    sim = simulate(
        make_house(),
        scenario_id="night",
        zones=(ZoneOverride("door", "on", at=60),),
    )
    kinds = [m for _, m in moments(sim)]
    assert Moment.ARMED in kinds
    assert Moment.ENTRY_STARTED in kinds
    assert Moment.TRIGGERED in kinds
    assert Moment.INCIDENT_OPENED in kinds

    entry = step_with(sim, Moment.ENTRY_STARTED)
    [change] = entry.areas
    assert (change.area_id, change.was, change.now) == (
        "ground",
        AreaState.ARMED.value,
        AreaState.ENTRY.value,
    )
    # Which delay, and when it runs out: the trace shows the timer itself,
    # not a number it worked out separately.
    assert change.timer_kind == "entry"
    assert change.timer_due == entry.at + timedelta(seconds=30)

    triggered = step_with(sim, Moment.TRIGGERED)
    assert triggered.at == entry.at + timedelta(seconds=30)


def test_the_setup_tick_is_marked_as_setup_and_decides_nothing():
    """The first reading of every sensor is a baseline, not an event (§4.7)."""
    sim = simulate(make_house(), scenario_id="night")
    assert sim.steps[0].kind == STEP_SETUP
    assert sim.steps[0].areas == ()


def test_a_disarmed_house_is_a_question_too():
    """No scenario: a 24h zone answers whatever the arming state (§4.3)."""
    sim = simulate(make_house(), zones=(ZoneOverride("tamper", "on"),))
    assert Moment.TRIGGERED in [m for _, m in moments(sim)]


def test_an_arming_the_configuration_would_refuse_says_so_and_names_the_zone():
    """The most useful answer the simulator can give before a burglary."""
    config = make_house()
    entities = {**live(config), WINDOW: EntityState("on", last_reported=START)}
    sim = run(config, SimulationRequest(start=START, scenario_id="night"), entities)
    refused = next(s for s in sim.steps if not s.accepted)
    assert refused.reason == Reason.ZONE_OPEN.value
    assert refused.blocking_zones == ("window",)


# --- the profile, and where it came from -------------------------------------------


def test_the_trace_says_which_profile_answered_and_where_it_came_from():
    config = make_house()
    loud = ResponseProfile(
        "loud",
        "Loud",
        actions=(
            ProfileAction("siren", ActionKind.SIREN, frozenset({Moment.TRIGGERED})),
        ),
    )
    config = replace(
        config,
        profiles=(*config.profiles, loud),
        areas=tuple(
            replace(a, response_profile_id="loud") if a.id == "ground" else a
            for a in config.areas
        ),
    )
    sim = run(
        config,
        SimulationRequest(
            start=START, scenario_id="night", zones=(ZoneOverride("window", "on", 60),)
        ),
        live(config),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    assert (batch.profile_id, batch.source) == ("loud", FROM_AREA)


def test_a_zones_own_profile_answers_its_own_alarm_and_the_trace_says_zone():
    config = make_house()
    quiet = ResponseProfile(
        "quiet",
        "Quiet",
        actions=(
            ProfileAction(
                "ping",
                ActionKind.PERSISTENT_NOTIFICATION,
                frozenset({Moment.TRIGGERED}),
            ),
        ),
    )
    config = replace(
        config,
        profiles=(*config.profiles, quiet),
        zones=tuple(
            replace(z, response_profile_id="quiet") if z.id == "window" else z
            for z in config.zones
        ),
    )
    sim = run(
        config,
        SimulationRequest(
            start=START, scenario_id="night", zones=(ZoneOverride("window", "on", 60),)
        ),
        live(config),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    assert (batch.profile_id, batch.source) == ("quiet", FROM_ZONE)


def test_with_nothing_overriding_it_the_source_is_the_global_default():
    sim = simulate(make_house(), scenario_id="night")
    batch = batch_for(step_with(sim, Moment.ARMED), Moment.ARMED)
    assert batch.source == FROM_DEFAULT


# --- which actions ran, which did not, and why -------------------------------------


def with_conditional_profile(**kwargs):
    config = make_house()
    actions = (
        ProfileAction("siren", ActionKind.SIREN, frozenset({Moment.TRIGGERED})),
        ProfileAction(
            "night_light",
            ActionKind.LIGHT,
            frozenset({Moment.TRIGGERED}),
            conditions=(TimeCondition("22:00", "07:00"),),
        ),
        ProfileAction(
            "nas",
            ActionKind.CALL_SERVICE,
            frozenset({Moment.TRIGGERED}),
            conditions=(
                StateCondition("binary_sensor.nobody_home", StateOperator.IS, "on"),
            ),
            condition_mode=ConditionMode.ALL,
        ),
    )
    return replace(
        config,
        profiles=(ResponseProfile("default", "Default", actions=actions),),
        **kwargs,
    )


def test_a_skipped_action_says_which_condition_failed():
    """§11.2: "which were skipped AND WHY", well enough to act on."""
    config = with_conditional_profile()
    sim = run(
        config,
        SimulationRequest(
            start=START,  # 19:32, outside the 22:00-07:00 window
            scenario_id="night",
            zones=(ZoneOverride("window", "on", 60),),
            entities={"binary_sensor.nobody_home": "off"},
        ),
        live(config),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    by_id = {a.action_id: a for a in batch.actions}
    assert by_id["siren"].ran
    assert not by_id["night_light"].ran
    assert by_id["night_light"].skipped == SKIP_CONDITION
    assert by_id["night_light"].conditions == ("time 22:00-07:00",)
    assert by_id["nas"].skipped == SKIP_CONDITION
    assert by_id["nas"].conditions == ("binary_sensor.nobody_home is on",)


def test_the_hypothetical_clock_is_what_a_time_condition_is_read_against():
    """The same configuration, two hours later, is a different answer."""
    config = with_conditional_profile()
    late = START.replace(hour=23)
    sim = run(
        config,
        SimulationRequest(
            start=late,
            scenario_id="night",
            zones=(ZoneOverride("window", "on", 60),),
        ),
        closed_entities(config, late),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    assert {a.action_id for a in batch.actions if a.ran} == {"siren", "night_light"}


def test_an_entity_override_answers_the_other_half_of_the_question():
    config = with_conditional_profile()
    sim = run(
        config,
        SimulationRequest(
            start=START,
            scenario_id="night",
            zones=(ZoneOverride("window", "on", 60),),
            entities={"binary_sensor.nobody_home": "on"},
        ),
        live(config),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    assert next(a for a in batch.actions if a.action_id == "nas").ran


def test_a_silent_zone_shows_what_its_silence_suppressed():
    config = with_conditional_profile()
    config = replace(
        config,
        zones=tuple(
            replace(z, silent=True) if z.id == "window" else z for z in config.zones
        ),
    )
    sim = run(
        config,
        SimulationRequest(
            start=START, scenario_id="night", zones=(ZoneOverride("window", "on", 60),)
        ),
        live(config),
    )
    batch = batch_for(step_with(sim, Moment.TRIGGERED), Moment.TRIGGERED)
    siren = next(a for a in batch.actions if a.action_id == "siren")
    assert not siren.ran and siren.skipped == SKIP_SILENT


def test_an_action_a_delay_holds_back_is_named_as_held_not_as_skipped():
    """A held action is going to run. Calling it skipped would be a lie."""
    config = make_house()
    config = replace(
        config,
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "siren", ActionKind.SIREN, frozenset({Moment.TRIGGERED})
                    ),
                    ProfileAction(
                        "wait",
                        ActionKind.DELAY,
                        frozenset({Moment.TRIGGERED}),
                        params={"seconds": 30},
                    ),
                    ProfileAction(
                        "later",
                        ActionKind.LIGHT,
                        frozenset({Moment.TRIGGERED}),
                    ),
                ),
            ),
        ),
    )
    sim = run(
        config,
        SimulationRequest(
            start=START, scenario_id="night", zones=(ZoneOverride("window", "on", 60),)
        ),
        live(config),
    )
    step = step_with(sim, Moment.TRIGGERED)
    later = next(
        a for a in batch_for(step, Moment.TRIGGERED).actions if a.action_id == "later"
    )
    assert not later.ran and later.skipped == SKIP_HELD_BY_DELAY
    # And the trace says when it will run instead of leaving it hanging.
    assert any(s.kind == "delay" for s in step.scheduled)
    # It really does run, thirty seconds later, in the same trace.
    assert any(
        a.action_id == "later"
        for later_step in sim.steps
        for a in later_step.loose_actions
        if later_step.at == step.at + timedelta(seconds=30)
    )


def test_three_areas_arming_together_are_one_line_not_three():
    """The trace stands for what the house does, and the house sends one
    notification naming all three (response.plan_occurrences)."""
    sim = simulate(make_house(), scenario_id="away")
    step = step_with(sim, Moment.ARMED)
    armed = [b for b in step.batches if b.moment == Moment.ARMED.value]
    assert len(armed) == 1


# --- groups and incidents in the trace ---------------------------------------------


def group_house():
    config = make_house()
    loud = ResponseProfile(
        "loud",
        "Loud",
        actions=(
            ProfileAction(
                "siren",
                ActionKind.SIREN,
                frozenset({Moment.VERIFICATION_SATISFIED}),
            ),
        ),
    )
    return replace(
        config,
        zones=(
            *config.zones,
            zone("pir1", "binary_sensor.pir1", "ground"),
            zone("pir2", "binary_sensor.pir2", "ground"),
        ),
        groups=(
            Group(
                "openplan",
                "Open plan",
                "ground",
                ("pir1", "pir2"),
                2,
                60,
                False,
                response_profile_id="loud",
            ),
        ),
        profiles=(*config.profiles, loud),
    )


def test_group_evaluation_appears_in_the_trace_not_just_the_zone():
    """§4.8's simulator requirement, verbatim: 1 of 2, then 2 of 2."""
    config = group_house()
    sim = run(
        config,
        SimulationRequest(
            start=START,
            scenario_id="night",
            zones=(
                ZoneOverride("pir1", "on", at=60),
                ZoneOverride("pir2", "on", at=90),
            ),
        ),
        live(config),
    )
    pending = step_with(sim, Moment.VERIFICATION_PENDING)
    [occurrence] = [
        o for o in pending.occurrences if o.moment is Moment.VERIFICATION_PENDING
    ]
    assert (occurrence.detail["count"], occurrence.detail["n"]) == ("1", "2")
    assert occurrence.group_id == "openplan"

    satisfied = step_with(sim, Moment.VERIFICATION_SATISFIED)
    [occurrence] = [
        o for o in satisfied.occurrences if o.moment is Moment.VERIFICATION_SATISFIED
    ]
    assert (occurrence.detail["count"], occurrence.detail["n"]) == ("2", "2")
    # And the group's own profile answers it, named as the group's (§4.8).
    batch = batch_for(satisfied, Moment.VERIFICATION_SATISFIED)
    assert (batch.profile_id, batch.source) == ("loud", FROM_GROUP)


def test_incident_opening_and_joining_both_appear():
    config = make_house()
    sim = run(
        config,
        SimulationRequest(
            start=START,
            scenario_id="away",
            zones=(
                ZoneOverride("window", "on", at=60),
                ZoneOverride("bath", "on", at=75),
            ),
        ),
        live(config),
    )
    kinds = [m for _, m in moments(sim)]
    assert Moment.INCIDENT_OPENED in kinds
    assert Moment.INCIDENT_JOINED in kinds
    opened = step_with(sim, Moment.INCIDENT_OPENED)
    joined = step_with(sim, Moment.INCIDENT_JOINED)
    # One incident, not two: the second zone joins the first one's id (§5.6).
    ids = {
        o.incident_id
        for step in (opened, joined)
        for o in step.occurrences
        if o.incident_id
    }
    assert len(ids) == 1


# --- the guarantee -----------------------------------------------------------------


def test_the_simulator_and_the_runtime_reach_the_same_decision():
    """The assertion INV-1 exists for.

    The same configuration, the same world, the same clock and the same
    events, driven twice: once through the simulator's stepping loop and once
    by calling decide() directly as the runtime does. Every Decision must be
    identical — state, occurrences and actions. If this fails, a second
    evaluation path has appeared and *that* is the bug.
    """
    config = with_conditional_profile()
    request = SimulationRequest(
        start=START,
        scenario_id="night",
        zones=(ZoneOverride("window", "on", at=60),),
        entities={"binary_sensor.nobody_home": "on"},
    )
    entities = live(config)
    sim = run(config, request, entities)

    # The runtime, by hand: same snapshots, same clock, same events.
    state = RuntimeState(areas={a.id: AreaRuntime() for a in config.areas})
    world = dict(entities)
    world["binary_sensor.nobody_home"] = EntityState(
        "on", last_reported=START, last_changed=START
    )
    replayed = []
    for step in sim.steps:
        if step.kind == "zone":
            zone_ = config.zone(step.zone_id)
            event = ZoneStateChanged(
                zone_.entity_id,
                EntityState(
                    step.zone_state, last_reported=step.at, last_changed=step.at
                ),
            )
        elif step.kind == "request":
            event = ArmRequest(step.scenario_id)
        else:
            event = Tick()
        decision = decide(
            SystemSnapshot(state, world, False, UTC), event, config, step.at
        )
        state = decision.state
        if isinstance(event, ZoneStateChanged):
            world[event.entity_id] = event.new
        replayed.append(decision)

    assert len(replayed) == len(sim.steps)
    for decision, step in zip(replayed, sim.steps, strict=True):
        assert decision.at == step.at
        assert decision.accepted == step.accepted
        assert decision.occurrences == step.occurrences
    assert replayed[-1].state == sim.final


def test_nothing_in_a_run_touches_the_configuration_it_was_given():
    config = make_house()
    before = repr(config)
    simulate(config, scenario_id="away", zones=(ZoneOverride("door", "on", 60),))
    assert repr(config) == before


# --- bounds ------------------------------------------------------------------------


def test_a_run_says_plainly_when_it_stopped_short():
    """A trace that simply ends reads as "and then it was over"."""
    sim = simulate(
        make_house(),
        scenario_id="night",
        zones=(ZoneOverride("window", "on", at=60),),
        horizon=61,
    )
    assert sim.truncated


def test_a_quiet_run_is_not_truncated():
    sim = simulate(make_house(), scenario_id="night")
    assert not sim.truncated


def test_the_horizon_is_capped():
    sim = simulate(make_house(), scenario_id="night", horizon=MAX_HORIZON * 10)
    assert not sim.truncated  # it simply stops when nothing more is due


# --- the wire ----------------------------------------------------------------------


def test_the_trace_crosses_the_wire_as_identifiers_never_sentences():
    config = with_conditional_profile()
    sim = run(
        config,
        SimulationRequest(
            start=START, scenario_id="night", zones=(ZoneOverride("window", "on", 60),)
        ),
        live(config),
    )
    document = as_dict(sim, config)
    import json

    text = json.dumps(document)
    assert json.loads(text) == document
    # Nothing a person reads is decided here: the panel translates every one
    # of these (§15.2). A sentence in this payload would be a hard-coded
    # English string in the backend.
    step = next(s for s in document["steps"] if s["kind"] == "zone")
    assert set(step) >= {"at", "kind", "zone_id", "occurrences", "batches"}
    assert all(
        isinstance(o["moment"], str) and " " not in o["moment"]
        for s in document["steps"]
        for o in s["occurrences"]
    )


def test_the_inputs_of_a_run_are_recorded_well_enough_to_run_it_again():
    """§11.2: logged with its inputs, so a change can be justified after."""
    request = SimulationRequest(
        start=START,
        scenario_id="night",
        zones=(ZoneOverride("window", "on", 60),),
        entities={"binary_sensor.nobody_home": "on"},
    )
    recorded = inputs(request)
    assert recorded["scenario_id"] == "night"
    assert recorded["zones"] == [{"zone_id": "window", "state": "on", "at": 60}]
    assert recorded["entities"] == {"binary_sensor.nobody_home": "on"}
    assert recorded["start"] == START.isoformat()


@pytest.mark.parametrize("bad", ["nope", ""])
def test_an_override_naming_a_zone_that_is_gone_is_ignored_not_fatal(bad):
    sim = simulate(make_house(), scenario_id="night", zones=(ZoneOverride(bad, "on"),))
    assert sim.steps


def test_an_unknown_scenario_is_refused_in_the_trace_like_anywhere_else():
    sim = simulate(make_house(), scenario_id="nope")
    refused = next(s for s in sim.steps if not s.accepted)
    assert refused.reason == Reason.UNKNOWN_SCENARIO.value


# --- keeping the module honest -----------------------------------------------------


def test_the_simulator_arms_areas_on_their_own_too():
    sim = simulate(make_house(), area_ids=("garage",))
    armed = step_with(sim, Moment.ARMED)
    assert [c.area_id for c in armed.areas] == ["garage"]


def test_a_follower_inherits_the_entry_window_in_the_trace():
    """The case §5.2 is hardest to reason about, and the one worth seeing."""
    config = make_house()
    sim = run(
        config,
        SimulationRequest(
            start=START,
            scenario_id="night",
            zones=(
                ZoneOverride("door", "on", at=60),
                ZoneOverride("hall", "on", at=70),
            ),
        ),
        live(config),
    )
    entries = [
        (step.at, o.zone_id)
        for step in sim.steps
        for o in step.occurrences
        if o.moment is Moment.ENTRY_STARTED
    ]
    assert entries and entries[0][1] == "door"
    # The follower does not open a second window; it inherits the running one.
    triggered = step_with(sim, Moment.TRIGGERED)
    assert triggered.at == entries[0][0] + timedelta(seconds=30)
