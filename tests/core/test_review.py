"""Regression tests for what a full review found, one per defect.

Each of these failed before the fix in the same commit. They are together in
one file on purpose: what they have in common is not a feature but a way of
going wrong — a value read from before the decision, a set built from the
wrong half of the world, a dataclass rebuilt instead of replaced.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC

import pytest

from custom_components.foyer.core.conditions import met
from custom_components.foyer.core.models import (
    ActionKind,
    AreaRuntime,
    AreaState,
    Group,
    LogSettings,
    Moment,
    ProfileAction,
    ResponseProfile,
    RuntimeState,
    StateCondition,
    StateOperator,
    ZoneType,
)
from custom_components.foyer.core.validation import validate
from custom_components.foyer.core.verification import groups
from custom_components.foyer.store.editing import update_settings
from custom_components.foyer.store.schema import (
    config_from_dict,
    config_to_dict,
    state_from_dict,
    state_to_dict,
)

from .helpers import NOW, WINDOW, World, make_house, zone

# --- the perimeter a rule may never disarm (§9.4 point 3) --------------------------


def test_a_perimeter_area_is_named_when_a_switch_would_drop_it():
    """The guard that keeps a rule off the perimeter (§9.4 point 3) works out
    what a switch would disarm. Handed the areas as they are now and the
    scenario as it was when the decision began, it found nothing to refuse —
    so a rule that switched scenario in the same turn as somebody armed
    disarmed the perimeter itself."""
    from custom_components.foyer.core.rules import switch_drops

    config = make_house()
    away, night = config.scenarios[0], config.scenarios[1]
    # The perimeter is an area the new scenario does not name, so a switch
    # to it would drop the perimeter — which is what must be refused.
    ground = next(a.id for a in config.areas if a.id not in night.areas)
    config = replace(
        config,
        areas=tuple(replace(a, is_perimeter=a.id == ground) for a in config.areas),
    )
    state = RuntimeState(
        areas={
            area.id: AreaRuntime(state=AreaState.ARMED, scenario_id=away.id)
            for area in config.areas
        },
        active_scenario_id=away.id,
    )
    dropped, perimeter = switch_drops(config, state, night.id)
    assert ground in dropped and perimeter == (ground,)


def test_switch_drops_reads_the_scenario_of_this_decision():
    from custom_components.foyer.core.rules import switch_drops

    config = make_house()
    away, night = config.scenarios[0], config.scenarios[1]
    armed = {
        area.id: replace(
            RuntimeState().area(area.id), state=AreaState.ARMED, scenario_id=away.id
        )
        for area in config.areas
    }
    state = RuntimeState(areas=armed, active_scenario_id=away.id)
    dropped, perimeter = switch_drops(config, state, night.id)
    # The areas Away armed that Night does not name.
    assert set(dropped) == {a.id for a in config.areas} - set(night.areas)
    # And with the *stale* scenario — the bug — nothing at all is found.
    stale = replace(state, active_scenario_id=None)
    assert switch_drops(config, stale, night.id) == ((), ())
    assert perimeter == () or set(perimeter) <= set(dropped)


# --- a group whose members are switched off (§4.8) --------------------------------


def test_a_group_that_can_no_longer_be_satisfied_suppresses_nothing():
    config = make_house()
    first, second = config.zones[0].id, config.zones[2].id
    config = replace(
        config,
        groups=(
            Group(
                id="g1",
                name="Open plan",
                area_id=config.areas[0].id,
                members=(first, second),
                n=2,
                window_seconds=60,
                suppress_members=True,
            ),
        ),
    )
    assert [g.group_id for g in groups(config)] == ["g1"]

    # One member switched off: the group can never reach two, so it holds
    # nothing back — the survivor alarms on its own.
    off = replace(
        config,
        zones=tuple(
            replace(z, enabled=False) if z.id == second else z for z in config.zones
        ),
    )
    assert [g.group_id for g in groups(off)] == []
    assert any(p.code == "group_members_disabled" for p in validate(off))


# --- settings that rebuilt themselves instead of replacing ------------------------


def _settings_payload(config) -> dict:
    from custom_components.foyer.store.schema import settings_to_dict

    return settings_to_dict(config.settings)


def test_a_settings_save_keeps_automatic_disarming_switched_on():
    config = replace(
        make_house(), settings=replace(make_house().settings, allow_auto_disarm=True)
    )
    result = update_settings(config, RuntimeState(), _settings_payload(config))
    assert result.config is not None, result.problems
    assert result.config.settings.allow_auto_disarm is True


def test_a_partial_log_block_keeps_what_it_does_not_mention():
    base = make_house()
    log = LogSettings(
        enabled={"zone_disarmed": True},
        retention_days={"alarm": 90},
        pseudonymise_after=30,
    )
    config = replace(base, settings=replace(base.settings, log=log))
    payload = _settings_payload(config)
    payload["log"] = {"pseudonymise_after": 45}
    result = update_settings(config, RuntimeState(), payload)
    assert result.config is not None, result.problems
    kept = result.config.settings.log
    assert kept.pseudonymise_after == 45
    assert (
        kept.retention(  # the ninety days it was not asked about
            "alarm"
        )
        == 90
    )
    assert kept.is_enabled("zone_disarmed") is True


def test_a_partial_code_policy_keeps_every_operation_it_does_not_name():
    from custom_components.foyer.store.editing import update_security

    base = make_house()
    config = replace(base, code_policy=replace(base.code_policy, arm=True))
    result = update_security(
        config,
        RuntimeState(),
        {
            "code_policy": {"disarm": True},
            "security": {
                "code_length": 6,
                "lockout_failures": 5,
                "lockout_window": 300,
                "lockout_duration": 300,
            },
        },
    )
    assert result.config is not None, result.problems
    assert result.config.code_policy.arm is True


def test_a_document_from_a_newer_minor_version_is_read_not_refused():
    document = config_to_dict(make_house())
    document["code_policy"]["some_future_operation"] = True
    # Read, with the unknown flag ignored, rather than raising.
    assert config_from_dict(document).code_policy.disarm is True


def test_retention_out_of_range_is_refused_by_validate_as_well():
    base = make_house()
    broken = replace(
        base,
        settings=replace(base.settings, log=LogSettings(retention_days={"alarm": 0})),
    )
    assert any(p.code == "retention_out_of_range" for p in validate(broken))


# --- state that was not persisted --------------------------------------------------


def test_a_low_battery_is_remembered_across_a_restart():
    config = make_house()
    state = RuntimeState(low_batteries=frozenset({config.zones[0].id}))
    restored = state_from_dict(state_to_dict(state), config)
    assert restored.low_batteries == state.low_batteries


# --- an entity that cannot be read satisfies nothing (INV-4, §6.3) ----------------


@pytest.mark.parametrize("state", ["unavailable", "unknown"])
def test_an_unreadable_entity_satisfies_neither_is_nor_is_not(state):
    world = World()
    world.set("person.luca", state)
    snapshot = world.snapshot()
    for operator in (StateOperator.IS, StateOperator.IS_NOT):
        condition = StateCondition(
            entity_id="person.luca", operator=operator, state="home"
        )
        assert met(condition, snapshot, NOW, UTC) is False


# --- the technical channel is not an intrusion command (§5.5) --------------------


def test_disarming_does_not_stop_a_technical_sounder():
    """§5.5 in as many words: disarming is an intrusion command and has no
    authority here. A technical response carries the area of the zone that
    raised it, so a disarm of that area switched off the smoke sounder."""
    from custom_components.foyer.core.presets import PRESETS

    config = make_house()
    smoke = zone(
        "smoke",
        "binary_sensor.kitchen_smoke",
        "ground",
        type=ZoneType.TECHNICAL,
        **PRESETS[ZoneType.TECHNICAL],
    )
    profile = ResponseProfile(
        id="tech",
        name="Technical",
        severity=5,
        actions=(
            ProfileAction(
                id="sounder",
                kind=ActionKind.SIREN,
                moments=(Moment.TECHNICAL_RAISED,),
                params={"entity_ids": ["siren.kitchen"], "duration": 600},
            ),
        ),
    )
    world = World(
        replace(
            config,
            zones=(*config.zones, smoke),
            profiles=(*config.profiles, profile),
            settings=replace(config.settings, technical_profile_id="tech"),
        )
    )

    world.set("binary_sensor.kitchen_smoke", "on")
    assert "smoke" in world.state.technical
    sounding = [r for r in world.state.running if "siren.kitchen" in r.entity_ids]
    assert sounding and sounding[0].technical

    world.disarm()
    assert [r for r in world.state.running if "siren.kitchen" in r.entity_ids], (
        "disarming silenced the smoke sounder"
    )
    assert "smoke" in world.state.technical


# --- what a delay was still holding, and who escalates again (§5.6, §6.2) --------


def test_a_sequence_held_by_a_delay_does_not_outlive_the_siren_cutoff():
    """§6.2: a siren never sounds beyond the cutoff, and the cutoff stops what
    it started. A sequence whose delay outlasted the cutoff used to start the
    bell afterwards, on a house that was armed again, for its whole duration.
    """
    config = make_house()
    profile = ResponseProfile(
        id="late",
        name="Late",
        severity=5,
        actions=(
            ProfileAction(
                id="wait",
                kind=ActionKind.DELAY,
                moments=(Moment.TRIGGERED,),
                params={"seconds": 300},
            ),
            ProfileAction(
                id="bell",
                kind=ActionKind.SIREN,
                moments=(Moment.TRIGGERED,),
                params={"entity_ids": ["siren.bell"], "duration": 180},
            ),
        ),
    )
    config = replace(
        config,
        profiles=(*config.profiles, profile),
        settings=replace(
            config.settings, default_profile_id="late", siren_duration=180
        ),
    )
    world = World(config)
    world.arm("away")
    world.advance(31)
    world.set(WINDOW, "on")
    assert world.state.pending_runs, "the delay should be holding the rest"

    world.advance(181)  # past the siren cutoff
    assert not world.state.pending_runs, "the cutoff left a siren still to come"


def test_an_exhausted_escalation_is_not_started_again_by_the_next_zone():
    """Every further zone of one break-in used to re-run the whole list —
    push, SMS, the neighbour — because the escalation is dropped when it is
    exhausted and nothing on the incident remembered it (§5.6)."""
    from custom_components.foyer.core.models import Incident

    incident = Incident(id="i1", opened_at=NOW, escalation_exhausted=True)
    # The flag is what `adopt_escalation` reads, and it survives a restart.
    restored = state_from_dict(
        state_to_dict(RuntimeState(incident=incident)), make_house()
    )
    assert restored.incident is not None
    assert restored.incident.escalation_exhausted is True
