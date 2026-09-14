"""Scenarios, area-only arming, the master panel and key zones (SPEC §4.6, §4.7, §13).

Decisions 5, 8, 9, 10 and 13 of 2026-09-14 settle what the spec left open.
"""

from __future__ import annotations

from dataclasses import replace
import itertools
import random

import pytest

from custom_components.foyer.core.engine import master_state
from custom_components.foyer.core.models import (
    AreaRuntime,
    AreaState,
    Channel,
    CodePolicy,
    KeyAction,
    KeyCommand,
    KeyRelease,
    Moment,
    Reason,
    RuntimeState,
    Scenario,
    StateTrigger,
    Zone,
    ZoneType,
)

from .helpers import DOOR, WINDOW, World, make_house

KEY = "input_boolean.key_switch"


def with_scenarios(*extra: Scenario):
    config = make_house()
    return replace(config, scenarios=(*config.scenarios, *extra))


# --- one area on its own (decision 5) -------------------------------------------------


def test_area_panel_arms_only_its_area(world):
    decision = world.arm_area("garage", channel="ha_ui")

    assert decision.accepted
    assert world.states() == {
        "ground": "disarmed",
        "upstairs": "disarmed",
        "garage": "arming",
    }
    assert world.area("garage").scenario_id is None
    assert world.state.active_scenario_id is None
    world.advance(10)
    assert master_state(world.state, world.config) == (
        AreaState.ARMED,
        "armed_custom_bypass",
    )


def test_area_arm_uses_the_areas_own_exit_delay(world):
    world.arm_area("upstairs")
    assert (world.area("upstairs").timer.due - world.now).total_seconds() == 20


def test_area_arm_is_refused_when_not_disarmed(world):
    world.arm_area("garage")
    assert world.arm_area("garage").reason is Reason.INVALID_STATE
    assert world.arm_area("nope").reason is Reason.UNKNOWN_AREA


def test_area_arm_checks_that_areas_zones():
    world = World(entities={WINDOW: "on"})
    assert world.arm_area("ground").reason is Reason.ZONE_OPEN
    assert world.arm_area("garage").accepted


def test_area_armed_outside_the_scenario_makes_the_master_custom():
    world = World()
    world.arm("night")
    world.advance(5)
    assert master_state(world.state, world.config) == (AreaState.ARMED, "armed_night")

    world.arm_area("garage")
    world.advance(10)
    assert world.state.active_scenario_id == "night"
    assert master_state(world.state, world.config) == (
        AreaState.ARMED,
        "armed_custom_bypass",
    )

    world.disarm("garage")
    assert master_state(world.state, world.config) == (AreaState.ARMED, "armed_night")


# --- master panel (decision 8) --------------------------------------------------------


def test_master_mode_arms_the_one_scenario_with_that_mode(world):
    assert world.arm_mode("armed_night").accepted
    assert world.state.active_scenario_id == "night"


def test_master_mode_with_no_scenario_is_refused(world):
    assert world.arm_mode("armed_vacation").reason is Reason.NO_SCENARIO_FOR_MODE


def test_master_mode_shared_by_two_scenarios_is_refused():
    world = World(
        with_scenarios(Scenario("night2", "Night, garage", ("garage",), "armed_night"))
    )
    assert world.arm_mode("armed_night").reason is Reason.AMBIGUOUS_MODE
    assert set(world.states().values()) == {"disarmed"}


# --- switching scenario while armed (decisions 7 and 9) -------------------------------


def test_switching_scenario_disarms_areas_only_in_the_old_one():
    world = World()
    world.arm("away")
    world.advance(30)

    decision = world.arm("night", channel="ha_ui")

    assert decision.accepted
    assert world.states() == {
        "ground": "armed",
        "upstairs": "disarmed",
        "garage": "disarmed",
    }
    assert world.area("ground").scenario_id == "night"
    assert world.state.active_scenario_id == "night"
    assert {o.area_id for o in decision.occurrences if o.moment is Moment.DISARMED} == {
        "upstairs",
        "garage",
    }
    assert master_state(world.state, world.config) == (AreaState.ARMED, "armed_night")


def test_switching_scenario_arms_the_new_areas_through_their_exit_delay():
    world = World()
    world.arm("night")
    world.advance(5)
    world.arm("away")
    assert world.states() == {
        "ground": "armed",
        "upstairs": "arming",
        "garage": "arming",
    }


def test_switching_leaves_individually_armed_areas_alone():
    world = World(
        with_scenarios(Scenario("garage_only", "Garage", ("garage",), "armed_home"))
    )
    world.arm_area("upstairs")
    world.arm("night")
    world.advance(20)

    world.arm("garage_only")

    assert world.states() == {
        "ground": "disarmed",
        "upstairs": "armed",
        "garage": "arming",
    }
    assert world.area("upstairs").scenario_id is None


def test_an_area_already_armed_on_its_own_joins_the_new_scenario():
    world = World()
    world.arm_area("garage")
    world.advance(10)
    world.arm("away")
    assert world.area("garage").scenario_id == "away"
    world.advance(30)
    world.arm("night")
    assert world.states()["garage"] == "disarmed"  # it left with "away"


def test_switching_is_refused_while_an_alarm_is_in_progress():
    world = World()
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    assert world.arm("night").reason is Reason.ALARM_IN_PROGRESS
    assert world.states()["ground"] == "entry"


def test_switching_checks_only_the_areas_it_must_arm():
    world = World()
    world.arm("night")
    world.advance(5)
    world.set(WINDOW, "on")  # ground is armed and now in alarm: cannot switch
    assert world.arm("away").reason is Reason.ALARM_IN_PROGRESS


@pytest.mark.parametrize("operation", ["arm", "disarm", "force_arm", "change_scenario"])
def test_code_policy_fails_closed_for_every_operation(operation):
    """No code can be verified before Phase 2: a policy requiring one refuses."""
    config = replace(make_house(), code_policy=CodePolicy(**{operation: True}))
    world = World(config)
    if operation == "disarm":
        world.arm("night")
        decision = world.disarm(code="1234")
    elif operation == "force_arm":
        decision = world.arm("night", force=True, code="1234")
    elif operation == "change_scenario":
        world.arm("night")
        decision = world.arm("away", code="1234")
    else:
        decision = world.arm("night", code="1234")
    assert decision.reason is Reason.CODE_REQUIRED


def test_no_code_is_needed_by_default_in_phase_1(world):
    world.arm("night")
    assert world.arm("away").accepted  # change scenario, decision 7
    assert world.disarm().accepted


# --- disarm ---------------------------------------------------------------------------


def test_disarm_named_areas_only():
    world = World()
    world.arm("away")
    world.advance(30)
    world.disarm("upstairs")
    assert world.states() == {
        "ground": "armed",
        "upstairs": "disarmed",
        "garage": "armed",
    }
    assert world.state.active_scenario_id == "away"


def test_disarm_with_nothing_armed_is_refused(world):
    assert world.disarm().reason is Reason.INVALID_STATE
    assert world.disarm("nope").reason is Reason.UNKNOWN_AREA


def test_scenario_ends_when_its_last_area_is_disarmed():
    world = World()
    world.arm("away")
    for area in ("ground", "upstairs"):
        world.disarm(area)
    assert world.state.active_scenario_id == "away"
    world.disarm("garage")
    assert world.state.active_scenario_id is None


# --- master aggregation (SPEC §13), property style ------------------------------------


def test_master_aggregation_rule_holds_for_every_combination():
    config = make_house()
    order = [AreaState.TRIGGERED, AreaState.ENTRY, AreaState.ARMING, AreaState.ARMED]
    for combo in itertools.product(list(AreaState), repeat=len(config.areas)):
        state = RuntimeState(
            areas={
                a.id: AreaRuntime(state=s, scenario_id="away")
                for a, s in zip(config.areas, combo, strict=True)
            },
            active_scenario_id="away",
        )
        aggregate, mode = master_state(state, config)
        expected = next((s for s in order if s in combo), AreaState.DISARMED)
        assert aggregate is expected, combo
        if aggregate is AreaState.ARMED:
            all_armed = all(s is AreaState.ARMED for s in combo)
            assert mode == ("armed_away" if all_armed else "armed_custom_bypass")
        else:
            assert mode is None


def test_partially_armed_house_is_not_reported_disarmed():
    rng = random.Random(7)
    config = make_house()
    for _ in range(200):
        states = [
            rng.choice([AreaState.DISARMED, AreaState.ARMED]) for _ in config.areas
        ]
        state = RuntimeState(
            areas={
                a.id: AreaRuntime(state=s)
                for a, s in zip(config.areas, states, strict=True)
            }
        )
        aggregate, _ = master_state(state, config)
        assert (aggregate is AreaState.DISARMED) == all(
            s is AreaState.DISARMED for s in states
        )


# --- key zones (§4.7, decision 13) ----------------------------------------------------


def key_world(action: KeyAction) -> World:
    config = make_house()
    key = Zone(
        id="key",
        name="Key switch",
        entity_id=KEY,
        area_id="ground",
        trigger=StateTrigger(frozenset({"on"})),
        type=ZoneType.KEY,
        channel=Channel.KEY,
        key=action,
    )
    return World(replace(config, zones=(*config.zones, key)))


def test_key_zone_arms_its_scenario_and_disarms_on_release():
    world = key_world(KeyAction(KeyCommand.ARM, "night", KeyRelease.DISARM))

    world.set(KEY, "on")
    assert world.state.active_scenario_id == "night"
    assert world.area("ground").channel == "key_zone"

    world.set(KEY, "off")
    assert set(world.states().values()) == {"disarmed"}


def test_key_zone_disarm_means_every_area():
    world = key_world(KeyAction(KeyCommand.DISARM))
    world.arm("away")
    world.set(KEY, "on")
    assert set(world.states().values()) == {"disarmed"}


def test_key_zone_toggle():
    world = key_world(KeyAction(KeyCommand.TOGGLE, "night"))
    world.set(KEY, "on")
    assert world.states()["ground"] == "arming"
    world.set(KEY, "off")
    world.set(KEY, "on")
    assert world.states()["ground"] == "disarmed"


def test_key_zone_never_alarms():
    world = key_world(KeyAction(KeyCommand.DISARM))
    world.arm("away")
    world.advance(30)
    world.set(KEY, "on")
    assert "triggered" not in world.states().values()


def test_refused_key_arm_is_recorded_not_silent():
    world = key_world(KeyAction(KeyCommand.ARM, "night"))
    world.entities[WINDOW] = replace(world.entities[WINDOW], state="on")
    world.state = replace(
        world.state, active_zones=world.state.active_zones | {"window"}
    )

    decision = world.set(KEY, "on")

    assert decision.accepted  # the zone change itself was processed
    failed = [o for o in decision.occurrences if o.moment is Moment.ARM_FAILED]
    assert failed[0].zone_id == "key"
    assert failed[0].zone_ids == ("window",)
    assert failed[0].detail["reason"] == "zone_open"
