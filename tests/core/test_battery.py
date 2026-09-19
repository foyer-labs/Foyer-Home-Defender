"""A zone's battery: a warning that never blocks, and a fault when it is silent.

SPEC §4.2 gives a zone a ``battery_entity_id`` and §6.1 gives the system a
``low_battery`` moment; neither says what "low" means. Phase 3 part 1 decides
it: a global threshold, a warning that blocks nothing, and — the half that is
not a warning — a battery entity nobody can read is a fault like any other
(INV-4). These tests pin all three, because each one is a place where a wrong
default produces either an alarm nobody can arm or a dead sensor nobody hears
about.
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import (
    EntityState,
    Moment,
    Reason,
    Settings,
)
from custom_components.foyer.core.triggers import battery_low

from .helpers import DOOR, WINDOW, World, make_house

BATTERY = "sensor.front_door_battery"
FLAG = "binary_sensor.kitchen_window_battery"


def house(**settings):
    config = make_house()
    zones = tuple(
        replace(z, battery_entity_id=BATTERY)
        if z.entity_id == DOOR
        else replace(z, battery_entity_id=FLAG)
        if z.entity_id == WINDOW
        else z
        for z in config.zones
    )
    return replace(
        config,
        zones=zones,
        settings=replace(config.settings, **settings) if settings else config.settings,
    )


def world(level: str = "80", flag: str = "off", **settings) -> World:
    """A house whose batteries are already being watched.

    They are handed to the constructor rather than added afterwards, because
    the runtime subscribes to a zone's battery entity exactly as it does to
    the zone's own: a battery that is not in the snapshot is one Foyer has
    never read, which is a fault, and that is a different test.
    """
    return World(house(**settings), {BATTERY: level, FLAG: flag})


# --- what counts as low ------------------------------------------------------------


def test_a_numeric_battery_is_low_below_the_threshold():
    zone = house().zones[0]
    assert not battery_low(zone, EntityState("21"), 20)
    assert not battery_low(zone, EntityState("20"), 20)
    assert battery_low(zone, EntityState("19"), 20)


def test_a_battery_binary_sensor_is_low_when_it_is_on():
    """Home Assistant's own convention, read as it stands (part 1 decision 1)."""
    zone = replace(house().zones[0], battery_entity_id=FLAG)
    assert battery_low(zone, EntityState("on"), 20)
    assert not battery_low(zone, EntityState("off"), 20)


def test_a_zone_with_no_battery_entity_is_never_low():
    zone = replace(house().zones[0], battery_entity_id=None)
    assert not battery_low(zone, EntityState("1"), 20)


def test_an_unreadable_battery_is_not_low():
    """It is a fault instead. The same problem under two names would be
    reported twice and fixed once."""
    zone = house().zones[0]
    assert not battery_low(zone, EntityState("unavailable"), 20)
    assert not battery_low(zone, EntityState(None), 20)


def test_the_threshold_is_the_installations():
    zone = house().zones[0]
    assert battery_low(zone, EntityState("45"), 50)
    assert not battery_low(zone, EntityState("45"), 40)


# --- the moment --------------------------------------------------------------------


def test_a_battery_falling_below_the_threshold_is_announced_once():
    w = world()
    assert not [o for o in w.advance(0).occurrences if o.moment is Moment.LOW_BATTERY]
    w.entities[BATTERY] = EntityState("12", last_reported=w.now)
    decision = w.advance(1)
    low = [o for o in decision.occurrences if o.moment is Moment.LOW_BATTERY]
    assert [o.zone_id for o in low] == ["door"]
    assert low[0].detail["entity_id"] == BATTERY
    assert low[0].detail["threshold"] == "20"
    # And not again on the next tick: it is news once, like a fault.
    assert not [o for o in w.advance(1).occurrences if o.moment is Moment.LOW_BATTERY]


def test_a_replaced_battery_leaves_quietly_and_can_be_announced_again():
    w = world(level="12")
    w.advance(1)
    assert "door" in w.state.low_batteries
    w.entities[BATTERY] = EntityState("100", last_reported=w.now)
    decision = w.advance(1)
    assert "door" not in decision.state.low_batteries
    # No occurrence: "the cell is fine again" is not news, and a profile
    # written against low_battery would otherwise fire on the good news.
    assert not [o for o in decision.occurrences if o.moment is Moment.LOW_BATTERY]
    w.entities[BATTERY] = EntityState("5", last_reported=w.now)
    assert [
        o.zone_id for o in w.advance(1).occurrences if o.moment is Moment.LOW_BATTERY
    ] == ["door"]


# --- it warns, it does not block ---------------------------------------------------


def test_a_low_battery_never_blocks_arming_and_is_never_a_fault():
    w = world(level="3")
    w.advance(1)
    decision = w.arm("night")
    assert decision.accepted
    assert decision.reason is None
    assert decision.blocking_zones == ()
    assert "door" not in decision.state.faults


def test_every_arming_attempt_carries_the_zones_on_a_dying_cell():
    """Not once, and not only in the panel: on every channel, every time."""
    w = world(level="3")
    w.advance(1)
    assert w.arm("night").low_battery_zones == ("door",)
    w.disarm()
    assert w.arm("night").low_battery_zones == ("door",)


def test_a_refused_arming_still_says_which_batteries_are_low():
    """The refusal is about something else; the warning is still true."""
    w = world(level="3")
    w.set(WINDOW, "on")
    decision = w.arm("night")
    assert not decision.accepted
    assert decision.reason is Reason.ZONE_OPEN
    assert decision.low_battery_zones == ("door",)


def test_excluding_the_zone_takes_it_out_of_the_warning():
    """What the household is offered when the warning appears: an ordinary
    manual bypass, which is the mechanism that already exists (§5.4)."""
    w = world(level="3")
    w.advance(1)
    assert w.bypass("door").accepted
    assert w.arm("night").low_battery_zones == ()


def test_the_armed_row_records_which_zones_armed_on_a_low_battery():
    w = world(level="3")
    w.advance(1)
    w.arm("night")
    armed = [
        o
        for o in w.advance(60).occurrences
        if o.moment is Moment.ARMED and o.area_id == "ground"
    ]
    assert armed and armed[0].detail["low_battery"] == "door"
    assert armed[0].zone_ids == ("door",)


def test_an_area_with_no_low_battery_writes_no_such_detail():
    w = world()
    w.arm("night")
    armed = [o for o in w.advance(60).occurrences if o.moment is Moment.ARMED]
    assert armed and "low_battery" not in armed[0].detail


# --- the fault ---------------------------------------------------------------------


def test_a_battery_entity_that_cannot_be_read_faults_its_zone():
    w = world()
    w.entities[BATTERY] = EntityState("unavailable", last_reported=w.now)
    decision = w.advance(1)
    assert "door" in decision.state.faults
    fault = [o for o in decision.occurrences if o.moment is Moment.ZONE_FAULT]
    assert [o.zone_id for o in fault] == ["door"]
    assert fault[0].detail["cause"] == "battery_unavailable"


def test_a_faulted_battery_blocks_arming_like_any_other_fault():
    w = world()
    w.entities[BATTERY] = EntityState(None)
    w.advance(1)
    decision = w.arm("night")
    assert not decision.accepted
    assert decision.reason is Reason.ZONE_FAULT
    assert decision.blocking_zones == ("door",)


def test_a_missing_battery_entity_faults_nothing_when_no_zone_names_one():
    w = World(make_house())
    assert w.advance(1).state.faults == frozenset()


def test_the_zone_entity_is_read_before_the_battery():
    """Two faults at once report the one that matters: the door is silent,
    which is a bigger fact than its battery sensor also being silent."""
    w = world()
    w.set(BATTERY, "unavailable")
    w.set(DOOR, "unavailable")
    # Already faulted on the battery, so the door going silent adds no second
    # occurrence — what matters is that the cause the state now carries is
    # the door's, not the battery sensor's.
    assert w.state.faults == frozenset({"door"})
    fresh = World(house(), {BATTERY: "unavailable", DOOR: "unavailable"})
    fault = [o for o in fresh.last.occurrences if o.moment is Moment.ZONE_FAULT]
    assert ("door", "unavailable") in [(o.zone_id, o.detail["cause"]) for o in fault]


# --- the setting -------------------------------------------------------------------


def test_the_threshold_defaults_to_twenty_per_cent():
    assert Settings().low_battery_threshold == 20
