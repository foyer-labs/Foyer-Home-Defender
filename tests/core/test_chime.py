"""Chime: only where nothing watches the zone (SPEC §6.6, §19)."""

from __future__ import annotations

from dataclasses import replace
from zoneinfo import ZoneInfo

from custom_components.foyer.core.models import (
    Actor,
    ChimeMode,
    ChimeSettings,
    ChimeTarget,
    Moment,
    SetChime,
)

from .helpers import BATH, DOOR, WINDOW, World, make_house

KITCHEN = "media_player.kitchen"


def house(chime: ChimeSettings | None = None, zones=("window", "bath")):
    config = make_house()
    return replace(
        config,
        zones=tuple(
            replace(z, chime=True) if z.id in zones else z for z in config.zones
        ),
        chime=chime
        or ChimeSettings(
            targets=(ChimeTarget(KITCHEN),),
            mode=ChimeMode.SPEECH,
            tts_entity="tts.piper",
            volume=40,
        ),
    )


def chimes(decision) -> list[str]:
    return [o.zone_id for o in decision.occurrences if o.moment is Moment.CHIME]


def test_a_zone_chimes_while_its_area_is_disarmed():
    world = World(house())
    decision = world.set(WINDOW, "on")

    assert chimes(decision) == ["window"]
    [intent] = [a for a in decision.actions if a.kind == "chime"]
    assert intent.placeholders == {"zone": "Window"}
    assert dict(intent.params) == {
        "targets": (KITCHEN,),
        "mode": "speech",
        "sound": None,
        "tts_entity": "tts.piper",
        "volume": 40,
    }


def test_no_chime_where_the_zone_is_monitored():
    world = World(house())
    world.arm("away")
    world.advance(30)
    decision = world.set(WINDOW, "on")
    assert chimes(decision) == []
    assert Moment.TRIGGERED in decision.moments


def test_a_partial_scenario_leaves_other_areas_chiming():
    """§6.6: "not monitored by the active scenario", not "disarmed"."""
    world = World(house())
    world.arm("night")  # the ground floor only
    world.advance(5)
    assert chimes(world.set(BATH, "on")) == ["bath"]


def test_an_area_armed_on_its_own_is_monitored_too():
    """Decision 4 makes per-area arming possible: read per area."""
    world = World(house())
    world.arm_area("upstairs")
    world.advance(20)
    assert chimes(world.set(BATH, "on")) == []


def test_the_exit_delay_is_silent_unless_chosen():
    """Part 2 decision 7."""
    world = World(house())
    world.arm("away")
    assert chimes(world.set(BATH, "on")) == []

    chosen = World(house(replace(house().chime, during_exit=True)))
    chosen.arm("away")
    assert chimes(chosen.set(BATH, "on")) == ["bath"]


def test_zones_without_chime_and_installations_without_targets_stay_quiet():
    world = World(house())
    assert chimes(world.set(DOOR, "on")) == []  # chime is off on the door
    no_target = World(house(ChimeSettings()))
    assert chimes(no_target.set(WINDOW, "on")) == []


def test_the_switch_silences_it_and_is_recorded():
    world = World(house())
    decision = world.send(SetChime(False, actor=Actor(channel="ha_ui")))
    assert decision.moments == (Moment.CHIME_SWITCHED,)
    assert not world.state.chime_enabled
    assert chimes(world.set(WINDOW, "on")) == []

    world.set(WINDOW, "off")
    world.send(SetChime(True))
    assert chimes(world.set(WINDOW, "on")) == ["window"]
    assert world.send(SetChime(True)).moments == ()  # no change, nothing recorded


def test_quiet_hours_on_the_local_clock_crossing_midnight():
    rome = ZoneInfo("Europe/Rome")  # NOW is 19:32 UTC, 21:32 in Rome
    quiet = replace(house().chime, quiet_start="21:00", quiet_end="07:00")
    world = World(house(quiet))
    world.timezone = rome
    assert chimes(world.set(WINDOW, "on")) == []

    daytime = replace(quiet, quiet_start="23:00")
    world = World(house(daytime))
    world.timezone = rome
    assert chimes(world.set(WINDOW, "on")) == ["window"]
