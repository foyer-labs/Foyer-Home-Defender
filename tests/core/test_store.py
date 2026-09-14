"""The stored document: round trip, seed, and the migration hook."""

from __future__ import annotations

import itertools

import pytest

from custom_components.foyer.core.models import Moment
from custom_components.foyer.store.migrations import MigrationError, migrate
from custom_components.foyer.store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    ConfigError,
    config_from_dict,
    config_to_dict,
)
from custom_components.foyer.store.seed import seed_config

CURRENT = (STORAGE_VERSION, STORAGE_MINOR_VERSION)


def test_config_round_trips_through_the_stored_document(config):
    assert config_from_dict(config_to_dict(config)) == config


def test_stored_document_is_plain_json_types(config):
    import json

    assert json.loads(json.dumps(config_to_dict(config))) == config_to_dict(config)


def test_invalid_document_raises_config_error(config):
    data = config_to_dict(config)
    data["zones"][0]["trigger"] = {"kind": "state", "states": []}

    with pytest.raises(ConfigError):
        config_from_dict(data)


def test_unknown_trigger_kind_is_rejected(config):
    data = config_to_dict(config)
    data["zones"][0]["trigger"] = {"kind": "numeric", "value": 3}

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
    assert [s.name for s in config.scenarios] == ["Fuori casa"]
    assert config.scenarios[0].areas == (config.areas[0].id,)
    assert config.zones[0].area_id == config.areas[0].id
    assert config.zones[0].trigger.states == {"on"}
    assert config.actions[0].moments == {
        Moment.ARMED,
        Moment.DISARMED,
        Moment.ZONE_FAULT,
    }
    assert not config.code_policy.arm
    assert not config.code_policy.disarm
    assert config_from_dict(config_to_dict(config)) == config


# --- migrations ----------------------------------------------------------------


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
