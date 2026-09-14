"""Arming: exit delay, preconditions and the four arm policies (SPEC §5.2 to §5.4)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core.models import (
    AreaState,
    ArmPolicy,
    BypassReason,
    Moment,
    Reason,
    TimerKind,
)

from .helpers import BATH, DOOR, HALL, NOW, PATIO, WINDOW, World, make_house

# --- exit delay ----------------------------------------------------------------


def test_arming_waits_for_each_areas_own_exit_delay(world):
    decision = world.arm("away", channel="ha_ui")

    assert decision.accepted
    assert world.states() == {
        "ground": "arming",
        "upstairs": "arming",
        "garage": "arming",
    }
    assert world.area("ground").timer.kind is TimerKind.EXIT
    assert world.area("ground").timer.due == NOW + timedelta(seconds=30)
    assert decision.moments == ()  # nothing is armed yet

    world.advance(10)
    assert world.states()["garage"] == "armed"
    world.advance(10)
    assert world.states() == {
        "ground": "arming",
        "upstairs": "armed",
        "garage": "armed",
    }
    decision = world.advance(10)
    assert world.states()["ground"] == "armed"
    assert [(o.moment, o.area_id, o.channel) for o in decision.occurrences] == [
        (Moment.ARMED, "ground", "ha_ui")
    ]


def test_scenario_exit_override_replaces_the_area_delay(world):
    world.arm("night")
    assert world.area("ground").timer.due == NOW + timedelta(seconds=5)


def test_zero_exit_delay_skips_arming():
    config = make_house()
    config = replace(
        config, areas=tuple(replace(a, default_exit_delay=0) for a in config.areas)
    )
    world = World(config)

    decision = world.arm("away")

    assert set(world.states().values()) == {"armed"}
    assert [o.moment for o in decision.occurrences].count(Moment.ARMED) == 3


def test_armed_notification_names_every_area_once():
    config = make_house()
    config = replace(
        config, areas=tuple(replace(a, default_exit_delay=0) for a in config.areas)
    )
    decision = World(config).arm("away")

    armed = [a for a in decision.actions if a.moment is Moment.ARMED]
    assert len(armed) == 1
    assert armed[0].placeholders["area"] == "Ground floor, Upstairs, Garage"
    assert armed[0].placeholders["scenario"] == "Away"


def test_zones_are_not_monitored_during_the_exit_delay(world):
    world.arm("away")
    world.set(WINDOW, "on")
    world.set(WINDOW, "off")

    assert world.states()["ground"] == "arming"
    world.advance(30)
    assert world.states()["ground"] == "armed"


# --- preconditions (§5.4) --------------------------------------------------------


def test_open_block_zone_refuses_arming_and_names_it():
    world = World(entities={WINDOW: "on"})

    decision = world.arm("away")

    assert not decision.accepted
    assert decision.reason is Reason.ZONE_OPEN
    assert decision.blocking_zones == ("window",)
    assert set(world.states().values()) == {"disarmed"}
    assert decision.actions == ()


@pytest.mark.parametrize("fault_state", ["unavailable", "unknown", None])
def test_faulted_zone_refuses_arming(fault_state):
    """INV-4: an entity we cannot see is a fault, never 'closed'."""
    world = World(entities={DOOR: fault_state})

    decision = world.arm("away")

    assert decision.reason is Reason.ZONE_FAULT
    assert decision.blocking_zones == ("door",)


def test_entity_missing_from_the_snapshot_is_a_fault(world):
    del world.entities[DOOR]
    assert world.arm("away").reason is Reason.ZONE_FAULT


def test_faults_are_reported_before_open_zones():
    world = World(entities={DOOR: "unavailable", WINDOW: "on"})
    decision = world.arm("away")
    assert (decision.reason, decision.blocking_zones) == (Reason.ZONE_FAULT, ("door",))


def test_allow_arm_when_faulted_lets_arming_proceed():
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, allow_arm_when_faulted=True) if z.id == "door" else z
            for z in config.zones
        ),
    )
    world = World(config, entities={DOOR: "unavailable"})

    assert world.arm("away").accepted
    world.advance(30)
    assert world.states()["ground"] == "armed"


def test_nc_contact_is_open_when_off():
    """INV-5: the zone's own trigger state decides, never 'on'."""
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, trigger=replace(z.trigger, states=frozenset({"off"})))
            if z.id == "window"
            else z
            for z in config.zones
        ),
    )
    assert (
        World(config, entities={WINDOW: "off"}).arm("away").reason is Reason.ZONE_OPEN
    )
    assert World(config, entities={WINDOW: "on"}).arm("away").accepted


def test_block_zone_left_open_at_expiry_fails_only_its_area(world):
    world.arm("away")
    world.set(DOOR, "on")  # leaving through the front door, and not closing it
    world.advance(20)
    decision = world.advance(10)

    assert world.states() == {
        "ground": "disarmed",
        "upstairs": "armed",
        "garage": "armed",
    }
    failed = [o for o in decision.occurrences if o.moment is Moment.ARM_FAILED]
    assert [(o.area_id, o.zone_ids, o.detail["reason"]) for o in failed] == [
        ("ground", ("door",), "zone_open")
    ]
    assert world.state.active_scenario_id == "away"
    assert [a.moment for a in decision.actions] == [Moment.ARM_FAILED]


def test_block_zone_closed_before_expiry_arms(world):
    world.arm("away")
    world.set(DOOR, "on")
    world.set(DOOR, "off")
    world.advance(30)
    assert world.states()["ground"] == "armed"


def test_zone_faulting_during_exit_delay_fails_arming(world):
    world.arm("night")
    world.set(DOOR, "unavailable")
    decision = world.advance(5)

    assert world.states()["ground"] == "disarmed"
    assert Moment.ARM_FAILED in decision.moments


# --- auto_bypass -------------------------------------------------------------------


def test_auto_bypass_zone_open_at_arming_is_bypassed_at_expiry_and_rejoins():
    world = World(entities={BATH: "on"})
    assert world.arm("away").accepted

    decision = world.advance(20)
    assert world.states()["upstairs"] == "armed"
    assert world.state.bypassed == {"bath": BypassReason.AUTO}
    assert decision.bypassed_zones == ("bath",)
    assert Moment.ZONE_BYPASSED in decision.moments

    # Still open and bypassed: it cannot trigger.
    world.set(BATH, "on", note="attribute noise")
    assert world.states()["upstairs"] == "armed"

    decision = world.set(BATH, "off")
    assert world.state.bypassed == {}
    assert Moment.ZONE_REJOINED in decision.moments

    world.set(BATH, "on")
    assert world.states()["upstairs"] == "triggered"


def test_auto_bypass_zone_closed_during_exit_is_simply_armed():
    world = World(entities={BATH: "on"})
    world.arm("away")
    world.set(BATH, "off")
    world.advance(20)
    assert world.state.bypassed == {}


def test_disarm_clears_bypasses():
    world = World(entities={BATH: "on"})
    world.arm("away")
    world.advance(30)
    world.disarm()
    assert world.state.bypassed == {}


# --- ignore -------------------------------------------------------------------------


def test_ignore_zone_open_at_arming_arms_and_fires_on_its_next_opening():
    world = World(entities={HALL: "on"})  # hall PIR: follower, arm_policy ignore
    world.arm("night")
    world.advance(5)
    assert world.states()["ground"] == "armed"

    world.set(HALL, "off")
    world.set(HALL, "on")
    assert world.states()["ground"] == "triggered"


# --- arm_after_closing (decision 4) ---------------------------------------------------


def test_arm_after_closing_holds_arming_until_the_zone_closes():
    world = World(entities={PATIO: "on"})
    assert world.arm("night").accepted

    world.advance(5)
    rt = world.area("ground")
    assert rt.state is AreaState.ARMING
    assert rt.timer.kind is TimerKind.HOLD
    assert rt.timer.due == NOW + timedelta(seconds=5 + 300)  # global default cap

    decision = world.set(PATIO, "off")  # pulled shut from outside
    assert world.states()["ground"] == "armed"
    assert Moment.ARMED in decision.moments


def test_arm_after_closing_still_waits_for_the_exit_delay():
    world = World(entities={PATIO: "on"})
    world.arm("night")
    world.set(PATIO, "off")
    assert world.states()["ground"] == "arming"
    world.advance(5)
    assert world.states()["ground"] == "armed"


def test_arm_after_closing_fails_when_the_cap_expires():
    world = World(entities={PATIO: "on"})
    world.arm("night")
    world.advance(5)
    decision = world.advance(300)

    assert world.states()["ground"] == "disarmed"
    failed = [o for o in decision.occurrences if o.moment is Moment.ARM_FAILED]
    assert failed[0].zone_ids == ("patio",)
    assert failed[0].detail["reason"] == Reason.ARM_HOLD_EXPIRED.value


def test_arm_after_closing_cap_is_configurable_per_zone():
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, arm_hold_timeout=90) if z.id == "patio" else z
            for z in config.zones
        ),
    )
    world = World(config, entities={PATIO: "on"})
    world.arm("night")
    world.advance(5)
    assert world.area("ground").timer.due == NOW + timedelta(seconds=95)
    world.advance(90)
    assert world.states()["ground"] == "disarmed"


def test_arm_after_closing_cap_counts_from_the_end_of_the_exit_delay():
    """A restart that delivers the exit expiry late does not extend the cap."""
    world = World(entities={PATIO: "on"})
    world.arm("night")
    world.advance(5 + 300 + 60)  # one late tick: exit and cap both long past
    assert world.states()["ground"] == "disarmed"


def test_block_zone_opened_while_held_fails_on_completion():
    world = World(entities={PATIO: "on"})
    world.arm("night")
    world.advance(5)
    world.set(WINDOW, "on")
    world.set(PATIO, "off")
    assert world.states()["ground"] == "disarmed"


# --- forced arm ----------------------------------------------------------------------


def test_forced_arm_bypasses_blocking_zones_and_says_so():
    world = World(entities={WINDOW: "on", DOOR: "unavailable"})

    decision = world.arm("night", force=True, channel="ha_ui")

    assert decision.accepted
    assert world.state.bypassed == {
        "door": BypassReason.FORCED,
        "window": BypassReason.FORCED,
    }
    forced = [o for o in decision.occurrences if o.moment is Moment.FORCED_ARM]
    assert forced[0].zone_ids == ("door", "window")
    assert forced[0].channel == "ha_ui"
    world.advance(5)
    assert world.states()["ground"] == "armed"


def test_forced_arm_is_never_implicit(world):
    world.entities[WINDOW] = replace(world.entities[WINDOW], state="on")
    assert world.arm("night").reason is Reason.ZONE_OPEN


def test_forced_arm_refuses_zones_that_may_not_be_bypassed():
    world = World(entities={"binary_sensor.siren_tamper": "unavailable"})
    decision = world.arm("night", force=True)
    assert decision.reason is Reason.ZONE_NOT_BYPASSABLE
    assert decision.blocking_zones == ("tamper",)


def test_forced_arm_also_bypasses_a_zone_left_open_at_expiry(world):
    world.arm("night", force=True)
    world.set(WINDOW, "on")
    world.advance(5)
    assert world.states()["ground"] == "armed"
    assert world.state.bypassed == {"window": BypassReason.FORCED}


def test_arm_policy_is_evaluated_per_zone():
    """block/auto_bypass/ignore on three zones, all open at arming."""
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, arm_policy=ArmPolicy.IGNORE) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config, entities={WINDOW: "on", BATH: "on"})
    assert world.arm("away").accepted
    world.advance(30)
    assert set(world.states().values()) == {"armed"}
    assert world.state.bypassed == {"bath": BypassReason.AUTO}


def test_arming_again_the_active_scenario_is_refused(world):
    world.arm("away")
    assert world.arm("away").reason is Reason.INVALID_STATE
