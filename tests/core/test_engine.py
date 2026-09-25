"""Faults, supervision, restart, trigger forms and purity (INV-1, INV-3, INV-4)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core.engine import decide, next_wakeup
from custom_components.foyer.core.models import (
    AreaState,
    ArmRequest,
    DisarmRequest,
    EntityState,
    EventTrigger,
    Moment,
    NumericOperator,
    NumericTrigger,
    Startup,
    Tick,
    Zone,
    ZoneStateChanged,
    ZoneType,
)

from .helpers import DOOR, NOW, WINDOW, World, make_house

# --- faults (INV-4) -------------------------------------------------------------------


def test_zone_going_unavailable_is_announced_once_and_changes_no_state():
    world = World()
    world.arm("away")
    world.advance(30)

    first = world.set(DOOR, "unavailable")
    assert first.moments == (Moment.ZONE_FAULT,)
    assert first.occurrences[0].detail["cause"] == "unavailable"
    assert [a.moment for a in first.actions] == [Moment.ZONE_FAULT]
    assert world.states()["ground"] == "armed"

    again = world.set(DOOR, "unknown")
    assert again.moments == ()


def test_a_zone_coming_back_open_triggers():
    """It was closed before the fault; open now is a genuine activation."""
    world = World()
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "unavailable")
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "triggered"


def test_a_zone_coming_back_in_the_state_it_left_does_not_retrigger():
    world = World(entities={WINDOW: "on"})
    config = world.config
    world.config = replace(
        config,
        zones=tuple(
            replace(z, arm_policy=z.arm_policy.IGNORE) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "unavailable")
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "armed"


def test_fault_is_forgotten_when_it_clears_and_announced_again_next_time():
    world = World()
    world.set(DOOR, "unavailable")
    world.set(DOOR, "off")
    assert world.state.faults == frozenset()
    assert world.set(DOOR, "unavailable").moments == (Moment.ZONE_FAULT,)


def test_disabled_zones_do_not_exist():
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, enabled=False) if z.id == "window" else z for z in config.zones
        ),
    )
    world = World(config, entities={WINDOW: "unavailable"})
    assert world.arm("away").accepted
    assert world.state.faults == frozenset()


# --- supervision (decision 11) --------------------------------------------------------


def supervised_world() -> World:
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, supervision_timeout=3600) if z.id == "door" else z
            for z in config.zones
        ),
    )
    return World(config)


def test_supervision_lapse_is_a_fault():
    world = supervised_world()
    assert next_wakeup(world.snapshot(), world.config, world.now) == NOW + timedelta(
        seconds=3600, microseconds=1
    )

    world.advance(3599)
    assert world.state.faults == frozenset()
    decision = world.advance(2)

    assert decision.moments == (Moment.ZONE_FAULT,)
    assert decision.occurrences[0].detail["cause"] == "supervision"
    assert world.arm("away").blocking_zones == ("door",)


def test_a_heartbeat_without_a_state_change_keeps_supervision_happy():
    world = supervised_world()
    world.advance(3000)
    world.heartbeat(DOOR)  # same state, reported again
    world.advance(3000)
    assert world.state.faults == frozenset()


def test_a_heartbeat_clears_a_supervision_fault():
    world = supervised_world()
    world.advance(3601)
    world.heartbeat(DOOR)
    world.send(Tick())
    assert world.state.faults == frozenset()


# --- restart (INV-3) ------------------------------------------------------------------


def test_state_survives_a_round_trip_through_a_fresh_decide():
    world = World()
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    saved = world.state

    restored = World()
    restored.state = saved
    restored.entities = dict(world.entities)
    restored.now = world.now

    assert restored.states()["ground"] == "entry"
    restored.advance(30)
    assert restored.states()["ground"] == "triggered"


def test_timers_that_fell_due_while_down_fire_on_restore():
    world = World()
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    world.now += timedelta(minutes=10)  # Home Assistant was down

    decision = world.send(Startup(down_since=NOW + timedelta(seconds=31)))

    assert world.states()["ground"] == "triggered"
    assert world.area("ground").timer.due == world.now + timedelta(seconds=180)
    moments = decision.moments
    assert Moment.TRIGGERED in moments
    assert Moment.HA_RESTARTED in moments
    restart = next(o for o in decision.occurrences if o.moment is Moment.HA_RESTARTED)
    assert restart.detail["down_since"] == (NOW + timedelta(seconds=31)).isoformat()
    assert restart.detail["up_at"] == world.now.isoformat()


def test_a_door_opened_while_down_triggers_on_restore():
    world = World()
    world.arm("away")
    world.advance(30)
    world.entities[WINDOW] = EntityState("on", last_reported=world.now)
    world.send(Startup())
    assert world.states()["ground"] == "triggered"


def test_faults_are_held_back_while_settling_and_announced_at_startup():
    world = World()
    world.settling = True
    decision = world.set(DOOR, None)  # entity not loaded yet
    assert decision.moments == ()

    world.set(WINDOW, "off")  # an unrelated entity arrives: still quiet
    world.settling = False
    decision = world.send(Startup())
    # Not at the start itself: the startup grace holds it back (decision
    # 165), and announces it when the grace ends if it is still there.
    assert Moment.ZONE_FAULT not in decision.moments
    decision = world.advance(world.config.health.startup_grace)
    assert Moment.ZONE_FAULT in decision.moments


def test_alarms_are_never_held_back_while_settling():
    world = World()
    world.arm("away")
    world.advance(30)
    world.settling = True
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "triggered"


# --- trigger forms (§4.4) -------------------------------------------------------------


def numeric_world(**trigger) -> World:
    config = make_house()
    probe = Zone(
        id="probe",
        name="Probe",
        entity_id="sensor.probe",
        area_id="garage",
        trigger=NumericTrigger(**trigger),
        allow_arm_when_faulted=False,
    )
    world = World(
        replace(config, zones=(*config.zones, probe)), entities={"sensor.probe": "10"}
    )
    world.arm_area("garage")
    world.advance(10)
    return world


def test_numeric_trigger_with_hysteresis():
    world = numeric_world(operator=NumericOperator.GT, value=50, hysteresis=5)
    world.set("sensor.probe", "49")
    assert world.states()["garage"] == "armed"
    world.set("sensor.probe", "51")
    assert world.states()["garage"] == "triggered"
    world.disarm()
    world.arm_area("garage")
    world.set("sensor.probe", "47")  # inside the band: still active, still open
    assert "probe" in world.state.active_zones
    world.set("sensor.probe", "44")
    assert "probe" not in world.state.active_zones


def test_numeric_trigger_lt_and_attribute():
    config = make_house()
    probe = Zone(
        id="probe",
        name="Probe",
        entity_id="sensor.probe",
        area_id="garage",
        trigger=NumericTrigger(NumericOperator.LT, 20, attribute="level"),
    )
    world = World(replace(config, zones=(*config.zones, probe)))
    world.set("sensor.probe", "ok", level=50)
    assert "probe" not in world.state.active_zones
    world.set("sensor.probe", "ok", level=10)
    assert "probe" in world.state.active_zones


def test_non_numeric_value_is_a_fault():
    world = numeric_world(operator=NumericOperator.GT, value=50)
    decision = world.set("sensor.probe", "garbage")
    assert decision.moments == (Moment.ZONE_FAULT,)
    assert decision.occurrences[0].detail["cause"] == "not_numeric"


def event_world(entity_id: str, event_type: str | None) -> World:
    config = make_house()
    button = Zone(
        id="button",
        name="Panic button",
        entity_id=entity_id,
        area_id="ground",
        trigger=EventTrigger(event_type),
        type=ZoneType.PANIC,
        always_on=True,
        bypassable=False,
    )
    return World(
        replace(config, zones=(*config.zones, button)),
        entities={entity_id: "2026-09-14T19:00:00+00:00"},
    )


def test_event_trigger_fires_on_a_matching_new_event():
    world = event_world("event.panic_button", "press")
    world.set("event.panic_button", "2026-09-14T19:40:00+00:00", event_type="release")
    assert world.states()["ground"] == "disarmed"
    world.set("event.panic_button", "2026-09-14T19:41:00+00:00", event_type="press")
    assert world.states()["ground"] == "triggered"


def test_event_trigger_ignores_the_restore_after_unavailable():
    world = event_world("event.panic_button", "press")
    world.set("event.panic_button", "unavailable")
    world.set("event.panic_button", "2026-09-14T19:00:00+00:00", event_type="press")
    assert world.states()["ground"] == "disarmed"


def test_tag_trigger_fires_on_any_scan():
    world = event_world("tag.front", None)
    world.set("tag.front", "2026-09-14T19:41:00+00:00")
    assert world.states()["ground"] == "triggered"


def test_event_zones_are_never_open_at_arming():
    world = event_world("event.panic_button", "press")
    assert world.arm("away").accepted


# --- purity (INV-1) -------------------------------------------------------------------


def test_decide_is_deterministic_and_uses_only_the_clock_it_is_given():
    world = World()
    later = NOW + timedelta(hours=3)
    a = decide(world.snapshot(), ArmRequest("away"), world.config, later)
    b = decide(world.snapshot(), ArmRequest("away"), world.config, later)

    assert a == b
    assert a.at == later
    assert world.state.area("ground").state is AreaState.DISARMED


def test_decide_does_not_mutate_its_inputs():
    world = World()
    world.arm("away")
    snap = world.snapshot()
    # The values are frozen dataclasses: a shallow copy of each mapping is a
    # faithful record of what the snapshot held.
    before = (dict(snap.state.areas), dict(snap.entities), snap.state.bypassed.copy())

    decide(snap, DisarmRequest(), world.config, NOW)
    decide(snap, ZoneStateChanged(DOOR, EntityState("on")), world.config, NOW)
    decide(snap, Tick(), world.config, NOW + timedelta(hours=1))

    assert (
        dict(snap.state.areas),
        dict(snap.entities),
        snap.state.bypassed.copy(),
    ) == before


def test_snapshot_and_decision_are_immutable():
    world = World()
    decision = world.arm("away")

    with pytest.raises(TypeError):
        world.snapshot().entities["x"] = EntityState("on")  # type: ignore[index]
    with pytest.raises(TypeError):
        decision.state.areas["ground"] = None  # type: ignore[index]


def test_a_refused_request_still_processes_due_timers():
    world = World()
    world.arm("away")
    world.now += timedelta(seconds=30)
    decision = world.arm("away")
    assert not decision.accepted
    assert world.states()["ground"] == "armed"


def test_unrelated_entity_is_ignored():
    world = World()
    world.arm("away")
    world.advance(30)
    decision = world.set("light.kitchen", "on")
    assert decision.moments == ()
    assert set(world.states().values()) == {"armed"}
