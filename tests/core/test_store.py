"""The stored documents: round trips, the seed, and the 1.1 → 2.1 migration."""

from __future__ import annotations

import itertools
import json

import pytest

from custom_components.foyer.core.models import (
    AreaState,
    ArmPolicy,
    BypassReason,
    Channel,
    EntryMode,
    EventTrigger,
    KeyAction,
    KeyCommand,
    Moment,
    NumericOperator,
    NumericTrigger,
    Zone,
    ZoneType,
)
from custom_components.foyer.store.migrations import MigrationError, migrate
from custom_components.foyer.store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    ConfigError,
    config_from_dict,
    config_to_dict,
    state_from_dict,
    state_to_dict,
)
from custom_components.foyer.store.seed import seed_config

from .helpers import DOOR, World

CURRENT = (STORAGE_VERSION, STORAGE_MINOR_VERSION)

# A document exactly as Phase 0 (v0.0.1) wrote it to .storage/foyer.config.
PHASE_0_DOCUMENT = {
    "areas": [{"id": "a1", "name": "Casa", "ha_state_when_armed": "armed_away"}],
    "zones": [
        {
            "id": "z1",
            "name": "Porta",
            "entity_id": "binary_sensor.porta",
            "area_id": "a1",
            "trigger": {"kind": "state", "states": ["on"]},
        }
    ],
    "scenarios": [
        {
            "id": "s1",
            "name": "Fuori casa",
            "areas": ["a1"],
            "ha_master_state": "armed_away",
        }
    ],
    "actions": [
        {
            "id": "n1",
            "kind": "notification",
            "moments": ["armed", "disarmed", "zone_fault"],
        }
    ],
    "code_policy": {"arm": False, "disarm": False},
}


def test_config_round_trips_through_the_stored_document(config):
    assert config_from_dict(config_to_dict(config)) == config


def test_every_trigger_form_and_key_zone_round_trip(config):
    from dataclasses import replace

    extra = (
        Zone(
            id="probe",
            name="Probe",
            entity_id="sensor.probe",
            area_id="garage",
            trigger=NumericTrigger(NumericOperator.GT, 40.5, 2.0, "level"),
        ),
        Zone(
            id="tag",
            name="Tag",
            entity_id="tag.front",
            area_id="ground",
            trigger=EventTrigger(),
            type=ZoneType.KEY,
            channel=Channel.KEY,
            key=KeyAction(KeyCommand.TOGGLE, "night"),
        ),
    )
    config = replace(config, zones=(*config.zones, *extra))
    assert config_from_dict(config_to_dict(config)) == config


def test_stored_document_is_plain_json_types(config):
    assert json.loads(json.dumps(config_to_dict(config))) == config_to_dict(config)


def test_invalid_document_raises_config_error(config):
    data = config_to_dict(config)
    data["zones"][0]["trigger"] = {"kind": "state", "states": []}
    with pytest.raises(ConfigError):
        config_from_dict(data)


def test_unknown_trigger_kind_is_rejected(config):
    data = config_to_dict(config)
    data["zones"][0]["trigger"] = {"kind": "voodoo"}
    with pytest.raises(ConfigError):
        config_from_dict(data)


def test_seed_wires_one_of_each_with_no_code_required():
    ids = (f"id{n}" for n in itertools.count())
    config = seed_config(
        area_name="Casa",
        scenario_name="Fuori casa",
        zone_entity_id="binary_sensor.porta",
        zone_name="Porta",
        trigger_states=["on"],
        new_id=lambda: next(ids),
    )

    assert [a.name for a in config.areas] == ["Casa"]
    assert config.scenarios[0].areas == (config.areas[0].id,)
    assert config.zones[0].trigger.states == {"on"}
    assert Moment.ZONE_FAULT in config.actions[0].moments
    assert config.code_policy.arm is False
    assert config.code_policy.disarm is False
    assert config_from_dict(config_to_dict(config)) == config


# --- the Phase 0 → Phase 1 migration --------------------------------------------------


def migrated():
    return config_from_dict(migrate((1, 1), CURRENT, PHASE_0_DOCUMENT))


def test_phase_0_document_migrates_to_a_valid_configuration():
    from custom_components.foyer.core.validation import validate

    config = migrated()
    assert validate(config) == []
    assert [a.name for a in config.areas] == ["Casa"]
    assert config.zones[0].entity_id == "binary_sensor.porta"


def test_migration_preserves_phase_0_behaviour():
    """Instant zone, block policy, no delays: arming is immediate, as before."""
    config = migrated()
    zone, area = config.zones[0], config.areas[0]
    assert (zone.type, zone.channel, zone.entry_mode, zone.arm_policy) == (
        ZoneType.INSTANT,
        Channel.INTRUSION,
        EntryMode.INSTANT,
        ArmPolicy.BLOCK,
    )
    assert (area.default_exit_delay, area.default_entry_delay) == (0, 0)

    world = World(config, entities={"binary_sensor.porta": "off"})
    world.arm("s1")
    assert world.states() == {"a1": "armed"}
    world.set("binary_sensor.porta", "on")
    assert world.states() == {"a1": "triggered"}


def test_migration_keeps_the_code_policy_and_adds_the_required_notifications():
    config = migrated()
    assert config.code_policy.arm is False
    assert config.code_policy.disarm is False
    assert config.actions[0].moments == {
        Moment.ARMED,
        Moment.DISARMED,
        Moment.ZONE_FAULT,
        Moment.ARM_FAILED,
        Moment.ZONE_BYPASSED,
    }


def test_migration_does_not_touch_its_input():
    before = json.dumps(PHASE_0_DOCUMENT, sort_keys=True)
    migrate((1, 1), CURRENT, PHASE_0_DOCUMENT)
    assert json.dumps(PHASE_0_DOCUMENT, sort_keys=True) == before


def test_current_version_needs_no_step():
    data = {"areas": []}
    assert migrate(CURRENT, CURRENT, data) is data


def test_steps_run_in_order():
    steps = {
        (1, 1): (lambda d: {**d, "a": True}, (1, 2)),
        (1, 2): (lambda d: {**d, "b": d["a"]}, (2, 1)),
    }
    assert migrate((1, 1), (2, 1), {}, steps) == {"a": True, "b": True}


def test_missing_step_is_an_error_not_a_pass_through():
    with pytest.raises(MigrationError):
        migrate((1, 0), (1, 1), {}, {})


def test_newer_major_version_is_refused():
    with pytest.raises(MigrationError):
        migrate((STORAGE_VERSION + 1, 1), CURRENT, {})


def test_newer_minor_version_is_read_as_is():
    data = {"future_field": 1}
    assert migrate((STORAGE_VERSION, STORAGE_MINOR_VERSION + 1), CURRENT, data) == data


def test_step_that_does_not_advance_is_refused():
    with pytest.raises(MigrationError):
        migrate((1, 1), (1, 2), {}, {(1, 1): (lambda d: d, (1, 1))})


# --- runtime state (INV-3) ------------------------------------------------------------


def test_restart_persistence_round_trip_is_identical():
    """SPEC §19: arm, serialise, restore, assert identical state."""
    world = World()
    world.arm("away")
    world.advance(30)
    world.set(DOOR, "on")
    world.advance(31)  # triggered, siren running, memory set

    document = json.loads(json.dumps(state_to_dict(world.state)))
    assert state_from_dict(document, world.config) == world.state


def test_state_with_bypass_hold_and_resume_round_trips():
    world = World(
        entities={"binary_sensor.bath_window": "on", "binary_sensor.patio_door": "on"}
    )
    world.arm("away")
    world.advance(20)
    world.set("binary_sensor.siren_tamper", "on")
    assert world.state.bypassed == {"bath": BypassReason.AUTO}
    assert world.area("ground").resume is AreaState.ARMING

    document = json.loads(json.dumps(state_to_dict(world.state)))
    assert state_from_dict(document, world.config) == world.state


def test_restored_state_drops_what_the_configuration_no_longer_has(config):
    from dataclasses import replace

    world = World()
    world.arm("away")
    document = state_to_dict(world.state)
    smaller = replace(
        config,
        areas=tuple(a for a in config.areas if a.id != "garage"),
        zones=tuple(z for z in config.zones if z.area_id != "garage"),
        scenarios=tuple(s for s in config.scenarios if s.id != "away"),
    )

    state = state_from_dict(document, smaller)
    assert "garage" not in state.areas
    assert state.active_scenario_id is None
    assert state.areas["ground"].scenario_id is None
    assert state.areas["ground"].state is AreaState.ARMING


def test_unreadable_state_raises_config_error(config):
    with pytest.raises(ConfigError):
        state_from_dict({"areas": {"ground": {"state": "exploded"}}}, config)
