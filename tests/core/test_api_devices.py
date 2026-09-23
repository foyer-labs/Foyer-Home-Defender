"""API devices: scopes, the unlock, the clear-text confirmation (SPEC §9.2.2).

The model half, pure. What the endpoint does with them is tested inside Home
Assistant (tests/ha/test_api_devices.py).
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import (
    ArmingDevice,
    DeviceKind,
    DeviceTransport,
)
from custom_components.foyer.core.validation import validate
from custom_components.foyer.store.migrations import migrate
from custom_components.foyer.store.schema import (
    config_from_dict,
    config_to_dict,
    device_from_dict,
    device_to_dict,
)

from .helpers import make_house


def _display(**changes) -> ArmingDevice:
    device = ArmingDevice(
        id="hall_display",
        name="Hall display",
        kind=DeviceKind.KEYPAD,
        ref="hall_display",
        transport=DeviceTransport.HTTP,
        scopes=frozenset({"status", "zones", "arm"}),
    )
    return replace(device, **changes)


def _problems(device: ArmingDevice) -> list[tuple[str, str | None]]:
    config = replace(make_house(), devices=(device,))
    return [(p.code, p.field) for p in validate(config) if p.kind == "device"]


# --- the migration keeps every keypad doing what it did ---------------------------


def test_an_endpoint_keypad_keeps_reading_the_state_and_arming():
    document = {
        "devices": [
            {"id": "k", "transport": "http"},
            {"id": "m", "transport": "mqtt"},
        ]
    }
    out = migrate((8, 1), (8, 2), document)
    http, mqtt = out["devices"]
    assert sorted(http["scopes"]) == ["arm", "disarm", "status"]
    assert http["free_scopes"] == ["status"]
    assert mqtt["scopes"] == []
    assert http["unlock_seconds"] == 120
    assert http["clear_text_confirmed"] is False


def test_scopes_survive_a_round_trip():
    device = _display(
        free_scopes=frozenset({"status", "zones"}),
        arm_scenario_ids=("away",),
        unlock_seconds=300,
        clear_text_confirmed=True,
    )
    assert device_from_dict(device_to_dict(device)) == device
    config = replace(make_house(), devices=(device,))
    assert config_from_dict(config_to_dict(config)).devices == (device,)


# --- validation ------------------------------------------------------------------


def test_a_well_formed_api_device_is_valid():
    assert _problems(_display()) == []


def test_an_action_can_never_be_free():
    """Decision 116: without a code a device only reads."""
    assert ("free_scope_not_a_read", "free_scopes") in _problems(
        _display(free_scopes=frozenset({"status", "arm"}))
    )


def test_scopes_mean_nothing_off_the_endpoint():
    assert ("scopes_need_endpoint", "scopes") in _problems(
        _display(transport=DeviceTransport.MQTT)
    )


def test_an_unknown_scope_is_refused():
    assert ("unknown_scope", "scopes") in _problems(
        _display(scopes=frozenset({"status", "open_the_door"}))
    )


def test_the_unlock_lasts_thirty_seconds_to_ten_minutes():
    assert ("unlock_out_of_range", "unlock_seconds") in _problems(
        _display(unlock_seconds=10)
    )
    assert ("unlock_out_of_range", "unlock_seconds") in _problems(
        _display(unlock_seconds=3600)
    )
    assert _problems(_display(unlock_seconds=30)) == []
    assert _problems(_display(unlock_seconds=600)) == []


def test_restrictions_name_real_scenarios_and_areas():
    problems = _problems(
        _display(
            arm_scenario_ids=("nowhere",),
            arm_area_ids=("attic",),
            disarm_area_ids=("cellar",),
        )
    )
    assert ("unknown_scenario", "arm_scenario_ids") in problems
    assert ("unknown_area", "arm_area_ids") in problems
    assert ("unknown_area", "disarm_area_ids") in problems
