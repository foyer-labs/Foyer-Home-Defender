"""The mains known from devices outside the UPS (decision 162).

Most households have a plain UPS that says nothing, and a smart plug or an
energy monitor plugged in outside it. When the power goes, Home Assistant
stays up on the UPS and those devices go silent: their silence, all of them
together and for long enough, is the power cut.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import json

from custom_components.foyer.core import health
from custom_components.foyer.core.engine import next_wakeup
from custom_components.foyer.core.models import (
    MAINS_OUTSIDE_UPS,
    EntityState,
    HealthCause,
    HealthSettings,
    Moment,
    Startup,
)
from custom_components.foyer.store.migrations import migrate
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import World, make_house

PLUG = "switch.fridge_plug"
METER = "sensor.shelly_em_power"


def world(*entity_ids: str, delay: int = 120) -> World:
    config = replace(
        make_house(),
        health=HealthSettings(
            mains_mode=MAINS_OUTSIDE_UPS,
            mains_outside_entity_ids=entity_ids,
            mains_outside_delay=delay,
        ),
    )
    w = World(config)
    for entity_id in entity_ids:
        w.set(entity_id, "on")
    return w


def lost(w: World) -> bool:
    return Moment.SYSTEM_POWER_LOST in (w.last.moments if w.last else ())


def causes(w: World) -> tuple[HealthCause, ...]:
    return health.causes(w.state.health, w.config, w.snapshot())


def test_every_device_silent_for_the_delay_is_a_power_cut():
    w = world(PLUG, METER)
    w.set(PLUG, "unavailable")
    w.set(METER, "unavailable")
    assert not lost(w)

    w.advance(119)
    assert not lost(w)
    w.advance(1)
    assert lost(w)
    assert HealthCause.MAINS_LOST in causes(w)


def test_the_delay_runs_from_the_last_device_to_go_silent():
    w = world(PLUG, METER)
    w.set(PLUG, "unavailable")
    w.advance(100)
    w.set(METER, "unavailable")
    w.advance(100)
    assert not lost(w)
    # And the scheduler is told when to look again.
    due = next_wakeup(w.snapshot(), w.config, w.now)
    assert due == w.now + timedelta(seconds=20)
    w.advance(20)
    assert lost(w)


def test_one_device_still_answering_means_the_power_is_there():
    w = world(PLUG, METER)
    w.set(PLUG, "unavailable")
    w.advance(3600)
    assert w.state.health.mains_lost_since is None
    assert HealthCause.MAINS_LOST not in causes(w)
    assert HealthCause.MAINS_UNKNOWN not in causes(w)


def test_a_device_answering_again_is_the_power_back():
    w = world(PLUG)
    w.set(PLUG, "unavailable")
    w.advance(120)
    assert lost(w)
    w.advance(300)
    w.set(PLUG, "on")
    restored = next(
        o for o in w.last.occurrences if o.moment is Moment.SYSTEM_POWER_RESTORED
    )
    assert restored.detail["seconds"] == "300"
    assert w.state.health.mains_quiet_since == {}


def test_a_device_silent_before_foyer_saw_it_answer_is_not_a_power_cut():
    """At every restart each device is silent until its integration loads.
    What Foyer did not see happen, it does not claim to have seen: the
    mains is not known — a cause of its own, never a power cut."""
    w = world(PLUG)
    # Home Assistant comes back with the plug not loaded yet: Foyer's first
    # look at it, at the restart, is a silence it did not see begin.
    w.entities[PLUG] = EntityState("unavailable")
    w.send(Startup(down_since=w.now - timedelta(seconds=30), cause="ha_start"))
    w.advance(3600)

    assert w.state.health.mains_lost_since is None
    assert HealthCause.MAINS_UNKNOWN in causes(w)

    # It answers once, and from then on its silence counts.
    w.set(PLUG, "on")
    assert HealthCause.MAINS_UNKNOWN not in causes(w)
    w.set(PLUG, "unavailable")
    w.advance(120)
    assert lost(w)


def test_a_power_cut_outlives_a_restart():
    w = world(PLUG)
    w.set(PLUG, "unavailable")
    w.advance(120)
    assert lost(w)
    w.send(Startup(down_since=w.now - timedelta(seconds=30), cause="ha_start"))
    w.advance(60)
    assert w.state.health.mains_lost_since is not None
    assert HealthCause.MAINS_LOST in causes(w)


def test_a_device_removed_from_home_assistant_is_not_known():
    w = world(PLUG)
    w.set(PLUG, None)
    w.advance(3600)
    assert w.state.health.mains_lost_since is None
    assert HealthCause.MAINS_UNKNOWN in causes(w)


def test_the_silence_is_stored_and_what_answered_is_not():
    """A power cut must outlive a restart, so when each device went silent
    is written to disk; which devices have answered must not be, or a
    device still loading after a restart would count as one that just died."""
    w = world(PLUG, METER)
    w.set(PLUG, "unavailable")
    document = json.loads(json.dumps(state_to_dict(w.state)))
    restored = state_from_dict(document, w.config)

    assert restored.health.mains_quiet_since == {PLUG: w.now}
    assert w.state.health.mains_seen == {PLUG, METER}
    assert restored.health.mains_seen == frozenset()


def test_an_older_configuration_keeps_its_sensor():
    document = {"health": {"mains_entity_id": "binary_sensor.ups"}}
    migrated = migrate((8, 3), (8, 4), document)
    assert migrated["health"]["mains_mode"] == "sensor"
    assert migrated["health"]["mains_outside_entity_ids"] == []
    assert migrated["health"]["mains_outside_delay"] == 120
