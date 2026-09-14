"""decide() — Phase 0 behaviour, tested with no Home Assistant anywhere."""

from __future__ import annotations

import copy
from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core.engine import decide
from custom_components.foyer.core.models import (
    AreaState,
    ArmRequest,
    CodePolicy,
    DisarmRequest,
    Moment,
    Reason,
    StateTrigger,
    ZoneStateChanged,
)

from .helpers import NOW, ZONE_ENTITY, snapshot

# --- arming --------------------------------------------------------------------


def test_arm_with_zone_closed_arms_the_area(config):
    decision = decide(snapshot(), ArmRequest("away"), config, NOW)

    assert decision.accepted
    assert decision.area_states == {"home": AreaState.ARMED}
    assert decision.active_scenario_id == "away"
    assert decision.moments == (Moment.ARMED,)
    assert decision.at == NOW


def test_arm_produces_the_notification_intent(config):
    decision = decide(snapshot(), ArmRequest("away"), config, NOW)

    assert [(a.action_id, a.moment) for a in decision.actions] == [
        ("notify", Moment.ARMED)
    ]
    assert dict(decision.actions[0].placeholders) == {
        "area": "Home",
        "scenario": "Away",
    }


def test_arm_with_zone_open_is_blocked_and_names_the_zone(config):
    decision = decide(snapshot(zone_state="on"), ArmRequest("away"), config, NOW)

    assert not decision.accepted
    assert decision.reason is Reason.ZONE_OPEN
    assert decision.blocking_zones == ("door",)
    assert decision.area_states == {}
    assert decision.actions == ()


@pytest.mark.parametrize("fault_state", ["unavailable", "unknown", None])
def test_arm_with_zone_in_fault_is_blocked(config, fault_state):
    """INV-4: an entity we cannot see is a fault, never 'closed'."""
    decision = decide(snapshot(zone_state=fault_state), ArmRequest("away"), config, NOW)

    assert not decision.accepted
    assert decision.reason is Reason.ZONE_FAULT
    assert decision.blocking_zones == ("door",)


def test_missing_entity_is_a_fault_not_absent(config):
    """An entity missing from the snapshot altogether also blocks arming."""
    empty = replace(snapshot(), entity_states={})
    decision = decide(empty, ArmRequest("away"), config, NOW)

    assert decision.reason is Reason.ZONE_FAULT


def test_trigger_states_are_the_zones_own_not_on(config):
    """INV-5: a zone whose trigger is 'off' (an NC contact) is open when 'off'."""
    nc = replace(
        config,
        zones=(replace(config.zones[0], trigger=StateTrigger(frozenset({"off"}))),),
    )

    assert decide(snapshot(zone_state="on"), ArmRequest("away"), nc, NOW).accepted
    blocked = decide(snapshot(zone_state="off"), ArmRequest("away"), nc, NOW)
    assert blocked.reason is Reason.ZONE_OPEN


def test_arm_unknown_scenario_is_rejected(config):
    decision = decide(snapshot(), ArmRequest("nope"), config, NOW)

    assert decision.reason is Reason.UNKNOWN_SCENARIO


def test_arm_when_already_armed_is_rejected(config):
    decision = decide(
        snapshot(AreaState.ARMED, scenario="away"), ArmRequest("away"), config, NOW
    )

    assert decision.reason is Reason.INVALID_STATE
    assert decision.active_scenario_id == "away"


# --- disarming -----------------------------------------------------------------


@pytest.mark.parametrize("state", [AreaState.ARMED, AreaState.TRIGGERED])
def test_disarm_returns_to_disarmed_and_clears_scenario(config, state):
    decision = decide(snapshot(state, scenario="away"), DisarmRequest(), config, NOW)

    assert decision.accepted
    assert decision.area_states == {"home": AreaState.DISARMED}
    assert decision.active_scenario_id is None
    assert [a.moment for a in decision.actions] == [Moment.DISARMED]


def test_disarm_when_disarmed_is_rejected(config):
    decision = decide(snapshot(), DisarmRequest(), config, NOW)

    assert decision.reason is Reason.INVALID_STATE


# --- code policy (INV-2) -------------------------------------------------------


def test_code_policy_fails_closed_when_disarm_requires_a_code(config):
    """Phase 0 has no codes to verify, so a policy requiring one refuses."""
    strict = replace(config, code_policy=CodePolicy(arm=False, disarm=True))

    for code in (None, "", "1234"):
        decision = decide(
            snapshot(AreaState.ARMED, scenario="away"),
            DisarmRequest(code=code),
            strict,
            NOW,
        )
        assert not decision.accepted
        assert decision.reason is Reason.CODE_REQUIRED


def test_code_policy_fails_closed_when_arm_requires_a_code(config):
    strict = replace(config, code_policy=CodePolicy(arm=True, disarm=False))

    decision = decide(snapshot(), ArmRequest("away", code="1234"), strict, NOW)

    assert decision.reason is Reason.CODE_REQUIRED


# --- zone changes --------------------------------------------------------------


def test_zone_triggering_while_armed_triggers_the_area(config):
    decision = decide(
        snapshot(AreaState.ARMED, zone_state="off", scenario="away"),
        ZoneStateChanged(ZONE_ENTITY, "on"),
        config,
        NOW,
    )

    assert decision.area_states == {"home": AreaState.TRIGGERED}
    assert decision.moments == (Moment.TRIGGERED,)
    assert decision.active_scenario_id == "away"
    # The Phase 0 action is not attached to `triggered`.
    assert decision.actions == ()


def test_zone_triggering_while_disarmed_changes_nothing(config):
    decision = decide(
        snapshot(zone_state="off"), ZoneStateChanged(ZONE_ENTITY, "on"), config, NOW
    )

    assert decision.area_states == {}
    assert decision.moments == ()


def test_zone_retriggering_while_triggered_changes_nothing(config):
    decision = decide(
        snapshot(AreaState.TRIGGERED, zone_state="off", scenario="away"),
        ZoneStateChanged(ZONE_ENTITY, "on"),
        config,
        NOW,
    )

    assert decision.area_states == {}


def test_zone_going_unavailable_raises_a_fault_once(config):
    """INV-4: the fault is announced on the transition, and state is untouched."""
    first = decide(
        snapshot(AreaState.ARMED, zone_state="off", scenario="away"),
        ZoneStateChanged(ZONE_ENTITY, "unavailable"),
        config,
        NOW,
    )
    assert first.moments == (Moment.ZONE_FAULT,)
    assert [a.moment for a in first.actions] == [Moment.ZONE_FAULT]
    assert first.area_states == {}

    again = decide(
        snapshot(AreaState.ARMED, zone_state="unavailable", scenario="away"),
        ZoneStateChanged(ZONE_ENTITY, "unknown"),
        config,
        NOW,
    )
    assert again.moments == ()


def test_unrelated_entity_is_ignored(config):
    decision = decide(
        snapshot(AreaState.ARMED, scenario="away"),
        ZoneStateChanged("light.kitchen", "on"),
        config,
        NOW,
    )

    assert decision.area_states == {}
    assert decision.moments == ()


# --- purity (INV-1) ------------------------------------------------------------


def test_decide_is_deterministic_and_uses_only_the_clock_it_is_given(config):
    later = NOW + timedelta(hours=3)
    a = decide(snapshot(), ArmRequest("away"), config, later)
    b = decide(snapshot(), ArmRequest("away"), config, later)

    assert a == b
    assert a.at == later


def test_decide_does_not_mutate_its_inputs(config):
    snap = snapshot(AreaState.ARMED, scenario="away")
    before = (copy.deepcopy(dict(snap.area_states)), dict(snap.entity_states))

    decide(snap, DisarmRequest(), config, NOW)
    decide(snap, ZoneStateChanged(ZONE_ENTITY, "on"), config, NOW)

    assert (dict(snap.area_states), dict(snap.entity_states)) == before


def test_snapshot_and_decision_are_immutable(config):
    snap = snapshot()
    decision = decide(snap, ArmRequest("away"), config, NOW)

    with pytest.raises(TypeError):
        snap.area_states["home"] = AreaState.ARMED  # type: ignore[index]
    with pytest.raises(TypeError):
        decision.area_states["home"] = AreaState.DISARMED  # type: ignore[index]
