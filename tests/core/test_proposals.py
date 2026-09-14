"""Zone wizard trigger proposals (INV-5)."""

from __future__ import annotations

from custom_components.foyer.core.proposals import (
    invalid_trigger_states,
    propose_trigger,
)


def test_binary_sensor_proposes_on():
    proposal = propose_trigger("binary_sensor.door", "off")

    assert proposal.proposed == ("on",)
    assert set(proposal.options) == {"on", "off"}


def test_cover_proposes_open_and_opening():
    assert propose_trigger("cover.garage", "closed").proposed == ("open", "opening")


def test_unusual_current_state_is_offered_but_not_proposed():
    proposal = propose_trigger("cover.garage", "stopped")

    assert "stopped" in proposal.options
    assert "stopped" not in proposal.proposed


def test_fault_state_is_never_offered():
    for state in ("unavailable", "unknown"):
        assert state not in propose_trigger("binary_sensor.door", state).options


def test_fault_states_are_invalid_trigger_states():
    assert invalid_trigger_states(["on", "unavailable"]) == ["unavailable"]
    assert invalid_trigger_states(["on"]) == []
