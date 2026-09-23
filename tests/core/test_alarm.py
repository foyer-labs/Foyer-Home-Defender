"""Entry delay, triggering, siren cutoff and alarm memory (SPEC §5.2, §5.3)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core.models import (
    AreaState,
    Moment,
    Settings,
    TimerKind,
)

from .helpers import (
    BATH,
    DOOR,
    GARAGE,
    HALL,
    LANDING,
    NOW,
    TAMPER,
    WINDOW,
    World,
    make_house,
)


def armed_world(scenario: str = "away") -> World:
    world = World()
    world.arm(scenario)
    world.advance(30)
    assert world.state.area("ground").state is AreaState.ARMED
    return world


def at(world: World, seconds: float):
    return world.now + timedelta(seconds=seconds)


# --- entry ---------------------------------------------------------------------------


def test_delayed_zone_grants_the_entry_delay():
    world = armed_world()
    decision = world.set(DOOR, "on")

    rt = world.area("ground")
    assert rt.state is AreaState.ENTRY
    assert rt.timer.kind is TimerKind.ENTRY
    assert rt.timer.due == at(world, 30)
    assert decision.moments == (Moment.ENTRY_STARTED,)


def test_disarm_during_entry_is_the_normal_homecoming():
    world = armed_world()
    world.set(DOOR, "on")
    world.advance(20)
    decision = world.disarm(channel="ha_ui")

    assert set(world.states().values()) == {"disarmed"}
    assert world.state.active_scenario_id is None
    assert not world.area("ground").memory
    assert decision.occurrences[0].channel == "ha_ui"


def test_entry_delay_expiring_triggers():
    world = armed_world()
    world.set(DOOR, "on")
    world.advance(29)
    assert world.states()["ground"] == "entry"
    decision = world.advance(1)

    rt = world.area("ground")
    assert rt.state is AreaState.TRIGGERED
    assert rt.memory
    assert rt.timer.kind is TimerKind.SIREN
    assert rt.causes == ("door",)
    assert decision.moments == (Moment.TRIGGERED, Moment.INCIDENT_OPENED)
    assert decision.occurrences[0].detail["cause"] == "entry_expired"


def test_instant_zone_does_not_grant_entry():
    world = armed_world()
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "triggered"


def test_instant_zone_during_entry_triggers_at_once():
    world = armed_world()
    world.set(DOOR, "on")
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "triggered"
    assert world.area("ground").causes == ("door", "window")


def test_follower_without_entry_window_is_instant():
    world = armed_world()
    world.set(HALL, "on")
    assert world.states()["ground"] == "triggered"


def test_follower_inside_the_entry_window_inherits_the_remaining_delay():
    world = armed_world()
    world.set(DOOR, "on")
    due = world.area("ground").timer.due
    world.advance(10)
    world.set(HALL, "on")

    rt = world.area("ground")
    assert rt.state is AreaState.ENTRY
    assert rt.timer.due == due  # not restarted
    assert rt.causes == ("door", "hall")


def test_follower_in_another_area_is_not_covered_by_this_entry():
    world = armed_world()
    world.set(DOOR, "on")
    world.set(LANDING, "on")  # upstairs follower: no entry window upstairs
    assert world.states()["upstairs"] == "triggered"
    assert world.states()["ground"] == "entry"


def test_zone_entry_delay_overrides_the_area_default():
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, entry_delay=45) if z.id == "door" else z for z in config.zones
        ),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    assert world.area("ground").timer.due == at(world, 45)


def test_area_entry_default_applies_when_the_zone_inherits():
    world = armed_world()
    world.set(GARAGE, "open")
    assert world.area("garage").timer.due == at(world, 15)


def test_entry_delay_of_zero_triggers_immediately():
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, entry_delay=0) if z.id == "door" else z for z in config.zones
        ),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    assert world.states()["ground"] == "triggered"


def test_disarmed_and_arming_areas_ignore_ordinary_zones(world):
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "disarmed"
    world.set(WINDOW, "off")
    world.arm("away")
    world.set(WINDOW, "on")
    assert world.states()["ground"] == "arming"


def test_a_zone_staying_in_trigger_states_does_not_retrigger():
    world = armed_world()
    world.set(GARAGE, "opening")
    due = world.area("garage").timer.due
    world.advance(5)
    world.set(GARAGE, "open")
    assert world.area("garage").timer.due == due


# --- triggered and siren cutoff -------------------------------------------------------


def test_siren_cutoff_rearms_and_keeps_alarm_memory():
    world = armed_world()
    world.set(WINDOW, "on")
    assert world.area("ground").timer.due == at(world, 180)
    decision = world.advance(180)

    rt = world.area("ground")
    assert rt.state is AreaState.ARMED
    assert rt.memory
    assert rt.causes == ("window",)
    assert decision.moments == (Moment.SIREN_CUTOFF, Moment.ALARM_ENDED)


def test_later_triggers_join_without_restarting_the_siren():
    world = armed_world()
    world.set(WINDOW, "on")
    due = world.area("ground").timer.due
    world.advance(60)
    decision = world.set(HALL, "on")

    rt = world.area("ground")
    assert rt.timer.due == due
    assert rt.causes == ("window", "hall")
    # It joins the incident; nothing is triggered again.
    assert decision.moments == (Moment.INCIDENT_JOINED,)


def test_scenario_siren_override_and_global_default():
    config = make_house()
    config = replace(
        config,
        settings=Settings(siren_duration=240),
        scenarios=tuple(
            replace(s, siren_duration_override=60) if s.id == "night" else s
            for s in config.scenarios
        ),
    )
    world = World(config)
    world.arm("night")
    world.advance(5)
    world.set(WINDOW, "on")
    assert world.area("ground").timer.due == at(world, 60)

    world = World(config)
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "on")
    assert world.area("ground").timer.due == at(world, 240)


def test_disarm_from_triggered_clears_memory():
    world = armed_world()
    world.set(WINDOW, "on")
    world.disarm()
    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert not rt.memory
    assert rt.timer is None


def test_disarm_after_cutoff_clears_memory():
    world = armed_world()
    world.set(WINDOW, "on")
    world.advance(180)
    world.disarm()
    assert not world.area("ground").memory


# --- always_on zones (decision 3) -----------------------------------------------------


def test_always_on_zone_triggers_a_disarmed_area():
    world = World()
    decision = world.set(TAMPER, "on")

    assert world.states()["ground"] == "triggered"
    assert decision.occurrences[0].detail["kind"] == "tamper"


def test_cutoff_after_a_trigger_from_disarmed_returns_to_disarmed():
    """A 24h zone firing on a disarmed house must never arm it."""
    world = World()
    world.set(TAMPER, "on")
    world.advance(180)

    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert rt.memory
    assert world.state.active_scenario_id is None


def test_disarm_clears_memory_on_a_disarmed_area():
    world = World()
    world.set(TAMPER, "on")
    world.set(TAMPER, "off")
    world.advance(180)
    assert world.disarm().accepted
    assert not world.area("ground").memory


def test_cutoff_after_a_trigger_during_arming_resumes_arming():
    world = World()
    world.arm("away")
    world.advance(10)
    world.set(TAMPER, "on")
    world.set(TAMPER, "off")
    assert world.states()["ground"] == "triggered"

    world.advance(180)  # the exit deadline (t+30) is long past: completes now
    assert world.states()["ground"] == "armed"
    assert world.area("ground").memory


def test_cutoff_resumes_arming_with_the_original_deadline_when_it_is_still_ahead():
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
    world.advance(60)

    rt = world.area("ground")
    assert rt.state is AreaState.ARMING
    assert rt.timer.due == NOW + timedelta(seconds=300)


def test_always_on_zone_during_entry_triggers():
    world = armed_world()
    world.set(DOOR, "on")
    world.set(TAMPER, "on")
    assert world.states()["ground"] == "triggered"


def test_trigger_in_one_area_leaves_the_others_alone():
    world = armed_world()
    world.set(BATH, "on")
    assert world.states() == {
        "ground": "armed",
        "upstairs": "triggered",
        "garage": "armed",
    }


# --- followers across areas (decision 47) --------------------------------------------


def follows_door(*extra: str) -> World:
    """Upstairs' landing PIR follows the front door, which is in another area."""
    config = make_house()
    config = replace(
        config,
        zones=tuple(
            replace(z, follows=("door", *extra)) if z.id == "landing" else z
            for z in config.zones
        ),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    return world


def test_follower_inherits_the_entry_window_of_a_zone_it_follows_in_another_area():
    world = follows_door()
    world.set(DOOR, "on")
    due = world.area("ground").timer.due
    world.advance(5)
    decision = world.set(LANDING, "on")

    rt = world.area("upstairs")
    assert rt.state is AreaState.ENTRY
    assert rt.timer.due == due  # the same deadline, not a fresh delay
    entry = decision.occurrences[0]
    assert entry.moment is Moment.ENTRY_STARTED
    assert entry.detail["inherited_from"] == "door"

    world.disarm()
    assert set(world.states().values()) == {"disarmed"}


def test_an_inherited_entry_expires_into_an_alarm_like_any_other():
    world = follows_door()
    world.set(DOOR, "on")
    world.set(LANDING, "on")
    world.disarm("ground")  # only the perimeter: the landing's area still counts
    world.advance(30)
    assert world.states()["upstairs"] == "triggered"


def test_follower_is_instant_when_no_followed_zone_has_opened_a_window():
    world = follows_door()
    world.set(LANDING, "on")
    assert world.states()["upstairs"] == "triggered"


def test_follower_is_instant_after_the_followed_window_has_expired():
    world = follows_door()
    world.set(DOOR, "on")
    world.advance(30)  # ground triggered: the window is over
    world.set(LANDING, "on")
    assert world.states()["upstairs"] == "triggered"


def test_follower_takes_the_earliest_of_several_followed_windows():
    world = follows_door("garage_door")
    world.set(GARAGE, "open")  # garage entry: 15 s
    garage_due = world.area("garage").timer.due
    world.set(DOOR, "on")  # ground entry: 30 s
    world.set(LANDING, "on")
    assert world.area("upstairs").timer.due == garage_due
