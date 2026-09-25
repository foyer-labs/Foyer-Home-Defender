"""Zone faults held back for a while after Home Assistant starts (decision 165).

Zigbee2MQTT and other integrations bring their entities back a little after
Home Assistant says it has started. Every one of them was announced as a
zone fault at every restart. A fault is still a fault at once — it blocks
arming, it shows — but its announcement waits for the grace, and a zone back
in time never has one.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core import engine
from custom_components.foyer.core.models import (
    EntityState,
    HealthSettings,
    Moment,
    Startup,
)

from .helpers import World, make_house


def world(grace: int = 120) -> World:
    config = make_house()
    w = World(replace(config, health=HealthSettings(startup_grace=grace)))
    return w


def door(w: World) -> str:
    return w.config.zones[0].entity_id


def faults_announced(w: World) -> list[str]:
    return [
        o.zone_id
        for o in (w.last.occurrences if w.last else ())
        if o.moment is Moment.ZONE_FAULT
    ]


def restart(w: World, *, silent: bool = False) -> None:
    """Home Assistant comes back; with ``silent`` the door's integration has
    not loaded yet, so Foyer's first look at it after the start is a zone
    that is not answering."""
    if silent:
        w.entities[door(w)] = EntityState("unavailable")
    w.send(Startup(down_since=w.now - timedelta(seconds=20), cause="ha_start"))


def test_a_zone_back_within_the_grace_is_never_announced():
    w = world()
    restart(w, silent=True)
    assert faults_announced(w) == []
    zone_id = w.config.zones[0].id
    # Still a fault meanwhile: it blocks arming and shows (INV-4).
    assert zone_id in w.state.faults

    w.advance(40)
    w.set(door(w), "off")
    assert zone_id not in w.state.faults
    w.advance(120)
    assert faults_announced(w) == []


def test_a_zone_still_down_when_the_grace_ends_is_announced_then():
    w = world()
    restart(w, silent=True)
    due = engine.next_wakeup(w.snapshot(), w.config, w.now)
    assert due == w.now + timedelta(seconds=120)

    w.advance(120)
    assert faults_announced(w) == [w.config.zones[0].id]
    assert w.state.fault_grace_until is None


def test_after_the_grace_a_fault_is_announced_at_once_as_ever():
    w = world()
    restart(w)
    w.advance(121)
    w.set(door(w), "unavailable")
    assert faults_announced(w) == [w.config.zones[0].id]


def test_no_grace_announces_at_the_start_as_before():
    w = world(grace=0)
    restart(w, silent=True)
    assert faults_announced(w) == [w.config.zones[0].id]
