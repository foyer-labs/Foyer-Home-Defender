"""Live zone diagnostics (SPEC §11.1): am I looking at the right sensor?

The two columns worth testing hardest are the two that would be worse than
absent if they were wrong: the trigger evaluation, which is why INV-5 exists,
and "blocks arming", which a household reads instead of trying to arm.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core.diagnostics import as_dict, diagnose, signal_of
from custom_components.foyer.core.models import (
    ArmingDevice,
    ArmPolicy,
    DeviceKind,
    EntityState,
    EventTrigger,
    StateTrigger,
    SystemSnapshot,
)

from .helpers import DOOR, GARAGE, NOW, WINDOW, World, make_house


def house(**kwargs):
    config = make_house()
    return replace(config, **kwargs) if kwargs else config


def rows(world: World):
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    return {
        row.zone_id: row for row in diagnose(snapshot, world.config, world.now).zones
    }


# --- the trigger evaluation column (INV-5) -----------------------------------------


def test_the_column_answers_would_this_count_as_triggered_right_now():
    world = World()
    assert rows(world)["window"].triggered is False
    world.set(WINDOW, "on")
    assert rows(world)["window"].triggered is True


def test_a_normally_closed_contact_reads_the_opposite_way_round():
    """The whole reason the column exists: `off` is an alarm here, and a
    table that assumed `on` would show this zone as calm while it fires."""
    config = house()
    config = replace(
        config,
        zones=tuple(
            replace(z, trigger=StateTrigger(frozenset({"off"})))
            if z.id == "window"
            else z
            for z in config.zones
        ),
    )
    world = World(config)
    row = rows(world)["window"]
    assert row.state == "off"
    assert row.triggered is True


def test_a_zone_whose_states_are_not_on_and_off_is_read_by_its_own_states():
    world = World()
    assert rows(world)["garage_door"].triggered is False
    world.set(GARAGE, "opening")
    assert rows(world)["garage_door"].triggered is True


def test_an_unreadable_zone_keeps_whatever_it_was_and_says_so_separately():
    """Going unavailable does not close a zone (triggers.is_active), and the
    table must not report a fault as calm — that is INV-4 exactly."""
    world = World()
    world.set(WINDOW, "on")
    world.set(WINDOW, "unavailable")
    row = rows(world)["window"]
    assert row.triggered is True
    assert row.available is False
    assert row.fault == "unavailable"


def test_an_event_zone_is_momentary_and_never_open():
    config = house()
    config = replace(
        config,
        zones=(
            *config.zones,
            replace(
                config.zones[0],
                id="tag",
                entity_id="tag.front",
                trigger=EventTrigger(None),
            ),
        ),
    )
    world = World(config, {"tag.front": "2026-09-19T10:00:00+00:00"})
    row = rows(world)["tag"]
    assert row.momentary is True
    assert row.triggered is False


# --- blocks arming -----------------------------------------------------------------


def test_an_open_blocking_zone_is_marked_and_says_why():
    world = World()
    world.set(WINDOW, "on")
    row = rows(world)["window"]
    assert row.blocks_arming is True
    assert row.blocks_because == "open"


def test_a_faulted_zone_blocks_for_a_different_reason():
    world = World()
    world.set(WINDOW, "unavailable")
    row = rows(world)["window"]
    assert row.blocks_arming is True
    assert row.blocks_because == "fault"


def test_an_auto_bypass_zone_that_is_open_does_not_block():
    world = World(entities={"binary_sensor.bath_window": "on"})
    row = rows(world)["bath"]
    assert row.triggered is True
    assert row.blocks_arming is False


def test_a_zone_allowed_to_arm_in_fault_does_not_block():
    config = house()
    config = replace(
        config,
        zones=tuple(
            replace(z, allow_arm_when_faulted=True) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)
    world.set(WINDOW, "unavailable")
    row = rows(world)["window"]
    assert row.fault == "unavailable"
    assert row.blocks_arming is False


def test_an_excluded_zone_stops_blocking_and_says_it_is_excluded():
    world = World()
    world.set(WINDOW, "on")
    world.bypass("window")
    row = rows(world)["window"]
    assert row.bypassed == "manual"
    assert row.blocks_arming is False


def test_the_column_agrees_with_the_engine_that_refuses_the_arming():
    """A table that said "ready" where arming refuses is worse than no table."""
    world = World()
    world.set(WINDOW, "on")
    world.set(DOOR, "unavailable")
    blocking = {z for z, row in rows(world).items() if row.blocks_arming}
    refused = world.arm("night")
    assert not refused.accepted
    # The refusal names one reason at a time (§5.4 orders them); the table
    # names every zone that would have to be dealt with.
    assert set(refused.blocking_zones) <= blocking


# --- everything else the table shows ------------------------------------------------


def test_a_missing_entity_is_reported_once_and_named():
    """The commonest mistake of all, and the first thing to check: a rename."""
    config = house()
    config = replace(
        config,
        zones=tuple(
            replace(z, entity_id="binary_sensor.renamed") if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)
    # Home Assistant does not have it at all, which is not the same as having
    # it unavailable: the entity was renamed and the zone still points at the
    # old name.
    del world.entities["binary_sensor.renamed"]
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    result = diagnose(snapshot, config, world.now)
    assert result.missing_entities == ("binary_sensor.renamed",)
    row = next(r for r in result.zones if r.zone_id == "window")
    assert row.state is None and row.available is False


def test_last_change_is_not_the_last_heartbeat():
    """§11.1 asks for the last change: a door shut for a week that checks in
    every hour has a recent heartbeat and a week-old change."""
    world = World()
    world.entities[WINDOW] = EntityState(
        "off",
        last_reported=NOW,
        last_changed=NOW - timedelta(days=7),
    )
    row = rows(world)["window"]
    assert row.last_reported == NOW
    assert row.last_changed == NOW - timedelta(days=7)


def test_supervision_shows_its_window_and_when_it_runs_out():
    config = house()
    config = replace(
        config,
        zones=tuple(
            replace(z, supervision_timeout=3600) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)
    row = rows(world)["window"]
    assert row.supervision_timeout == 3600
    assert row.supervision_due == NOW + timedelta(seconds=3600)


def test_a_zone_with_no_supervision_has_no_window_to_show():
    row = rows(World())["window"]
    assert row.supervision_timeout is None and row.supervision_due is None


def test_signal_quality_is_shown_where_the_entity_exposes_it():
    world = World()
    world.set(WINDOW, "off", linkquality=142)
    row = rows(world)["window"]
    assert row.signal is not None
    assert (row.signal.value, row.signal.unit) == (142.0, "lqi")


def test_a_zone_whose_entity_exposes_nothing_has_no_signal_column():
    assert rows(World())["window"].signal is None


def test_an_unknown_attribute_is_not_guessed_at_as_a_signal():
    """A number with no unit, presented as signal strength, misleads."""
    assert signal_of(EntityState("off", {"battery_voltage": 2.9})) is None
    assert signal_of(EntityState("off", {"rssi": -67})) is not None


def test_a_disabled_zone_is_listed_and_reports_no_fault():
    """It is still in the table — "why is this zone doing nothing?" is a
    question — but a zone that is switched off cannot be in fault."""
    config = house()
    config = replace(
        config,
        zones=tuple(
            replace(z, enabled=False) if z.id == "window" else z for z in config.zones
        ),
    )
    world = World(config)
    world.set(WINDOW, "unavailable")
    row = rows(world)["window"]
    assert row.enabled is False and row.fault is None
    assert row.blocks_arming is False


def test_every_mapped_zone_is_there():
    world = World()
    assert set(rows(world)) == {z.id for z in world.config.zones}


# --- arming devices (part 1 decision 3) --------------------------------------------


def with_devices():
    return house(
        devices=(
            ArmingDevice("k1", "Hall keypad", DeviceKind.KEYPAD, ref="keypad_hall"),
            ArmingDevice(
                "t1",
                "Luca's tag",
                DeviceKind.TAG,
                entity_id="tag.luca",
                user_id="luca",
            ),
        )
    )


def test_a_tag_whose_entity_has_gone_silent_is_visible():
    """ "The keypad by the door is dead" is exactly what §11.1 is for."""
    world = World(with_devices(), {"tag.luca": "unavailable"})
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    devices = {
        d.device_id: d for d in diagnose(snapshot, world.config, world.now).devices
    }
    assert devices["t1"].watchable is True
    assert devices["t1"].available is False


def test_a_keypad_has_no_entity_and_the_table_says_so_rather_than_healthy():
    """It speaks over MQTT; there is nothing to be available. Claiming it is
    fine would be a claim nothing supports."""
    world = World(with_devices())
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    devices = {
        d.device_id: d for d in diagnose(snapshot, world.config, world.now).devices
    }
    assert devices["k1"].watchable is False
    assert devices["k1"].available is False
    assert devices["k1"].state is None


def test_devices_are_a_table_of_their_own_never_rows_among_the_zones():
    world = World(with_devices())
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    result = diagnose(snapshot, world.config, world.now)
    assert {z.zone_id for z in result.zones}.isdisjoint(
        {d.device_id for d in result.devices}
    )


# --- the wire ----------------------------------------------------------------------


def test_the_table_crosses_the_wire_as_identifiers_never_sentences():
    import json

    world = World(with_devices())
    world.set(WINDOW, "on")
    snapshot = SystemSnapshot(world.state, world.entities, False, world.timezone)
    document = as_dict(diagnose(snapshot, world.config, world.now))
    assert json.loads(json.dumps(document)) == document
    row = next(z for z in document["zones"] if z["zone_id"] == "window")
    assert row["blocks_because"] == "open"
    assert row["triggered"] is True


def test_nothing_in_the_table_is_a_battery_the_zone_did_not_declare():
    row = rows(World())["window"]
    assert row.battery_entity_id is None
    assert row.battery_level is None
    assert row.battery_low is False


def test_arm_policy_ignore_never_blocks_however_open_it_is():
    world = World(entities={"binary_sensor.hall_pir": "on"})
    assert world.config.zone("hall").arm_policy is ArmPolicy.IGNORE
    assert rows(world)["hall"].blocks_arming is False
