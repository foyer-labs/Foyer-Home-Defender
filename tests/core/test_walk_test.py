"""The walk test: really armed, really reading, nothing answering (SPEC §11.3).

The feature exists to answer one question — *which zones never saw me* — and
the whole risk of it is that the house stops responding while somebody walks
around inside it. So the tests here are written against the safeguards as much
as against the feature: the auto-exit that cannot be switched off, the areas it
gives back exactly as it found them, and the sentence that decides the shape of
the whole thing:

    a walk test must never silence a smoke detector.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from custom_components.foyer.core.models import (
    MAX_WALK_TEST_TOTAL,
    AlarmKind,
    AreaState,
    Channel,
    CodePolicy,
    CodeResult,
    Moment,
    Reason,
    ZoneType,
)
from custom_components.foyer.core.response import SKIP_WALK_TEST, skip_reason

from .helpers import DOOR, HALL, TAMPER, WINDOW, World, make_house, user, zone

SMOKE = "binary_sensor.kitchen_smoke"


def answering(config, *moments_):
    """The shared house's default profile, taught to answer these moments.

    make_house() keeps a deliberately small profile so that most tests see a
    quiet house; these ones are about whether an action ran at all, so they
    need one that would have.
    """
    profile = config.profiles[0]
    return replace(
        config,
        profiles=(
            replace(
                profile,
                actions=(replace(profile.actions[0], moments=frozenset(moments_)),),
            ),
        ),
    )


def house_with_smoke():
    """The shared house plus a technical zone, which is the one that matters."""
    config = make_house()
    return replace(
        config,
        zones=(
            *config.zones,
            zone(
                "smoke",
                SMOKE,
                "ground",
                type=ZoneType.TECHNICAL,
                channel=Channel.TECHNICAL,
                always_on=True,
                bypassable=False,
            ),
        ),
    )


def moments(decision) -> list[Moment]:
    return [o.moment for o in decision.occurrences]


# --- entering and leaving ----------------------------------------------------------


def test_entering_arms_every_area():
    """Part 2 decision 2: every area, because §9.1's signature has no
    scenario in it and a walk is walked through the whole house."""
    world = World()
    decision = world.walk_test()

    assert decision.accepted
    assert world.states() == {
        "ground": "armed",
        "upstairs": "armed",
        "garage": "armed",
    }
    assert world.state.walk_test is not None
    assert set(world.state.walk_test.armed_areas) == {"ground", "upstairs", "garage"}
    assert Moment.WALK_TEST_STARTED in moments(decision)


def test_entering_does_not_wait_for_an_exit_delay():
    """The person is inside and about to walk: an area still counting down
    is an area watching nothing, and its zones would report as never having
    reacted."""
    world = World()
    world.walk_test()

    assert all(rt.state is AreaState.ARMED for rt in world.state.areas.values())
    assert all(rt.timer is None for rt in world.state.areas.values())


def test_leaving_disarms_only_what_the_walk_test_armed():
    """An area already armed when it started is left exactly as it was: the
    walk test borrowed nothing from it (part 2 decision 2)."""
    world = World()
    world.arm_area("upstairs")
    world.advance(30)
    assert world.area("upstairs").state is AreaState.ARMED

    world.walk_test()
    assert world.state.walk_test is not None
    assert "upstairs" not in world.state.walk_test.armed_areas

    world.walk_test(False)
    assert world.states() == {
        "ground": "disarmed",
        "upstairs": "armed",
        "garage": "disarmed",
    }


def test_a_blocked_area_does_not_stop_the_walk_test():
    """Part 2 decision 7: a window left open must not stop somebody finding
    out that the garage PIR is dead."""
    world = World(entities={WINDOW: "on"})
    decision = world.walk_test()

    assert decision.accepted
    assert decision.blocking_zones == ("window",)
    assert world.area("ground").state is AreaState.DISARMED
    assert world.area("upstairs").state is AreaState.ARMED
    assert world.state.walk_test is not None
    assert "ground" not in world.state.walk_test.armed_areas


def test_entering_twice_is_refused():
    world = World()
    world.walk_test()
    decision = world.walk_test()
    assert not decision.accepted
    assert decision.reason is Reason.INVALID_STATE
    # And leaving one that never started is refused the same way.
    world.walk_test(False)
    assert not world.walk_test(False).accepted


# --- what a detection does, and does not do ----------------------------------------


def test_a_detection_is_recorded_and_moves_nothing():
    """Part 2 decision 3. Forty zones walked would otherwise leave forty
    alarms in the log, and the master panel would be telling HomeKit,
    Google and Alexa that somebody had broken in for the whole walk."""
    world = World()
    world.walk_test()
    world.advance(10)
    decision = world.set(HALL, "on")

    assert world.area("ground").state is AreaState.ARMED
    assert world.area("ground").memory is False
    assert world.state.incident is None
    assert Moment.TRIGGERED not in moments(decision)
    assert Moment.INCIDENT_OPENED not in moments(decision)
    assert decision.actions == ()

    detections = world.state.walk_test.detections
    assert set(detections) == {"hall"}
    assert detections["hall"].count == 1


def test_a_second_detection_of_the_same_zone_counts():
    world = World()
    world.walk_test()
    world.advance(10)
    world.set(HALL, "on")
    world.advance(10)
    world.set(HALL, "off")
    world.advance(10)
    world.set(HALL, "on")

    detection = world.state.walk_test.detections["hall"]
    assert detection.count == 2
    assert detection.last > detection.first


def test_a_delayed_zone_does_not_start_an_entry_delay():
    """No entry delay either: the entry route is a path through the house
    like any other, and the walk test is not coming home."""
    world = World()
    world.walk_test()
    world.advance(10)
    world.set(DOOR, "on")

    assert world.area("ground").state is AreaState.ARMED
    assert world.area("ground").timer is None
    assert set(world.state.walk_test.detections) == {"door"}


# --- the sentence the feature is written against ------------------------------------


def test_a_walk_test_never_silences_a_smoke_detector():
    """§11.3: `always_on` zones stay **fully live**. The technical channel
    fires, its alarm stands, and its actions are really executed."""
    config = answering(house_with_smoke(), Moment.TECHNICAL_RAISED)
    world = World(config)
    world.walk_test()
    world.advance(10)
    decision = world.set(SMOKE, "on")

    assert Moment.TECHNICAL_RAISED in moments(decision)
    assert "smoke" in world.state.technical
    # Not recorded as a walk-test detection: it is live, not under test.
    assert "smoke" not in world.state.walk_test.detections
    # And the response really ran. This is the assertion that decides the
    # shape of the whole feature.
    assert [i.moment for i in decision.actions] == [Moment.TECHNICAL_RAISED]
    assert decision.inhibited == ()


def test_a_tamper_zone_alarms_during_a_walk_test():
    """The other half of the same rule: 24h, tamper and panic zones are
    `always_on` too, and somebody prising a siren off the wall during a walk
    test is exactly when it matters."""
    world = World(answering(make_house(), Moment.ARMED, Moment.TRIGGERED))
    world.walk_test()
    world.advance(10)
    decision = world.set(TAMPER, "on")

    assert world.area("ground").state is AreaState.TRIGGERED
    assert world.state.incident is not None
    assert [i.moment for i in decision.actions] == [Moment.TRIGGERED]
    assert decision.inhibited == ()
    assert decision.occurrences[0].detail["kind"] == AlarmKind.TAMPER.value


# --- inhibition -------------------------------------------------------------------


def test_the_arming_the_walk_test_performs_is_itself_inhibited():
    """§11.3 inhibits every action, and "the house has armed" is an action
    like the rest. The walk test's own announcement is not."""
    config = answering(make_house(), Moment.ARMED, Moment.WALK_TEST_STARTED)
    decision = World(config).walk_test()

    assert [i.moment for i in decision.inhibited] == [Moment.ARMED]
    assert [i.moment for i in decision.actions] == [Moment.WALK_TEST_STARTED]


def test_an_inhibited_action_never_reaches_the_actions_list():
    """Part 2 decision 1: the executor receives only what it must do, so a
    bug there cannot sound a siren during a walk test."""
    world = World()
    decision = world.walk_test()
    assert all(i not in decision.actions for i in decision.inhibited)


def test_skip_reason_is_the_one_place_that_says_why(monkeypatch):
    """A new reason belongs in response.skip_reason and nowhere else, or the
    trace would explain a skip the engine did not make."""
    from custom_components.foyer.core.models import ActionKind, ProfileAction
    from custom_components.foyer.core.response import PlanContext

    action = ProfileAction("a", ActionKind.SIREN, frozenset({Moment.TRIGGERED}))
    ctx = PlanContext(
        config=make_house(),
        snapshot=World().snapshot(),
        now=World().now,
        areas={},
    )
    assert (
        skip_reason(
            action,
            ctx,
            moment=Moment.TRIGGERED,
            suppressed=frozenset(),
            already_started=frozenset(),
            inhibited=True,
        )
        == SKIP_WALK_TEST
    )


def test_the_chime_is_held_back_too():
    """§6.6 needs no special case while the area is armed — but an area that
    failed to arm would chime through the whole walk."""
    from custom_components.foyer.core.models import ChimeSettings, ChimeTarget

    house = make_house()
    config = replace(
        house,
        chime=ChimeSettings(targets=(ChimeTarget("media_player.kitchen"),)),
        zones=tuple(
            replace(z, chime=True) if z.id == "window" else z for z in house.zones
        ),
    )
    world = World(config, entities={DOOR: "on"})  # blocks the ground floor
    world.walk_test()
    assert world.area("ground").state is AreaState.DISARMED

    world.advance(10)
    decision = world.set(WINDOW, "on")
    assert [i.kind for i in decision.actions] == []
    assert [i.kind for i in decision.inhibited] == ["chime"]


# --- the auto-exit (§5.3) ----------------------------------------------------------


def test_the_timeout_ends_it_and_gives_the_house_back():
    world = World()
    world.walk_test()
    decision = world.advance(901)

    assert world.state.walk_test is None
    assert world.states() == {
        "ground": "disarmed",
        "upstairs": "disarmed",
        "garage": "disarmed",
    }
    ended = next(o for o in decision.occurrences if o.moment is Moment.WALK_TEST_ENDED)
    assert ended.detail["cause"] == "timeout"


def test_every_detection_pushes_the_timeout_back():
    """Part 2 decision 4: a forty-zone house takes longer than fifteen
    minutes to walk."""
    world = World()
    world.walk_test()
    for _ in range(3):
        world.advance(800)
        world.set(HALL, "on")
        world.set(HALL, "off")
        assert world.state.walk_test is not None

    world.advance(901)
    assert world.state.walk_test is None


def test_the_cap_ends_it_however_many_detections_there_are():
    """A walk test somebody forgot about, with a cat in front of a PIR
    keeping it alive, still ends."""
    world = World()
    world.walk_test()
    for _ in range(40):
        world.advance(600)
        world.set(HALL, "on")
        world.set(HALL, "off")
        if (walk := world.state.walk_test) is None:
            break
        # A detection pushes the window back, never past the cap.
        assert walk.until <= walk.hard_until

    assert world.state.walk_test is None
    assert (world.now - World().now).total_seconds() <= MAX_WALK_TEST_TOTAL + 900


@pytest.mark.parametrize(
    ("asked", "expected"),
    [(300, 300), (5400, 900), (None, 900), (1, 60)],
)
def test_duration_may_only_shorten(asked, expected):
    """Part 2 decision 5: §5.3 calls the auto-exit non-disableable, so there
    is no number a caller can send that lengthens it."""
    world = World()
    world.walk_test(duration=asked)
    walk = world.state.walk_test
    assert walk.window == expected
    assert (walk.until - walk.started_at).total_seconds() == expected


def test_the_auto_exit_is_scheduled_like_any_other_timer():
    """§5.3 lists it among the timers, so INV-3 persists it and the
    scheduler wakes for it: a restart must not leave a house inhibited with
    nothing due to end it."""
    from custom_components.foyer.core.engine import next_wakeup

    world = World()
    world.walk_test()
    assert next_wakeup(world.snapshot(), world.config, world.now) == (
        world.state.walk_test.deadline()
    )


def test_the_walk_test_survives_a_restart():
    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    world = World()
    world.walk_test()
    world.advance(10)
    world.set(HALL, "on")

    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.walk_test == world.state.walk_test


# --- what it found -----------------------------------------------------------------


def test_the_end_names_the_zones_that_never_reacted():
    """The point of the whole feature. A zone with no detection is either a
    door nobody opened or a PIR pointing at the wrong wall, and either way
    it is the finding."""
    world = World()
    world.walk_test()
    world.advance(10)
    world.set(HALL, "on")
    world.advance(10)
    world.set(DOOR, "on")

    decision = world.walk_test(False)
    ended = next(o for o in decision.occurrences if o.moment is Moment.WALK_TEST_ENDED)
    assert ended.detail["detected"] == "2"
    assert set(ended.zone_ids) == {"window", "patio", "landing", "bath", "garage_door"}
    assert "tamper" not in ended.zone_ids  # always_on: live, not under test


def test_the_person_who_started_it_is_on_both_rows():
    """§11.3: entry and exit logged with the user. The exit row is written
    by a timer, long after anybody pressed anything, so the name is kept."""
    config = replace(make_house(), users=(user(),))
    world = World(config)
    world.walk_test(user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    assert world.state.walk_test.user_name == "Luca"

    decision = world.advance(901)
    ended = next(o for o in decision.occurrences if o.moment is Moment.WALK_TEST_ENDED)
    assert (ended.user_id, ended.user_name) == ("luca", "Luca")


# --- identity (§8.2) ---------------------------------------------------------------


def test_the_code_policy_applies_to_entering():
    """§8.2 lists "enter walk test" as code required, and a rehearsal buys
    no exemption: there is one authorisation path, and this is it."""
    config = replace(make_house(), users=(user(),), code_policy=CodePolicy())
    world = World(config)

    refused = world.walk_test(user_id="luca", channel="ha_ui")
    assert not refused.accepted
    assert refused.reason is Reason.CODE_REQUIRED
    assert world.state.walk_test is None

    accepted = world.walk_test(user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    assert accepted.accepted


def test_a_person_without_the_permission_is_refused():
    config = replace(
        make_house(),
        users=(user(permissions=frozenset({"arm", "disarm"})),),
    )
    world = World(config)
    decision = world.walk_test(user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    assert not decision.accepted
    assert decision.reason is Reason.NOT_PERMITTED
