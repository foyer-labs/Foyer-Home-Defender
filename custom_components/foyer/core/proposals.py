"""Trigger-state proposals for the zone wizard (SPEC §4.4, INV-5).

A proposal is a starting point the user must confirm, never a silent default.
Phase 0 supports state triggers only, so only domains whose states are discrete
are offered; numeric and event triggers come with the zone types.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import FAULT_STATES


@dataclass(frozen=True, slots=True)
class TriggerProposal:
    options: tuple[str, ...]  # every state the user may pick
    proposed: tuple[str, ...]  # pre-selected, to be confirmed


_BY_DOMAIN: dict[str, TriggerProposal] = {
    "binary_sensor": TriggerProposal(("on", "off"), ("on",)),
    "input_boolean": TriggerProposal(("on", "off"), ("on",)),
    "switch": TriggerProposal(("on", "off"), ("on",)),
    "cover": TriggerProposal(
        ("open", "opening", "closed", "closing"), ("open", "opening")
    ),
    "lock": TriggerProposal(
        ("locked", "locking", "unlocked", "unlocking", "open", "opening", "jammed"),
        ("unlocked", "open", "opening"),
    ),
}

SUPPORTED_DOMAINS: tuple[str, ...] = tuple(_BY_DOMAIN)


def propose_trigger(entity_id: str, current_state: str | None) -> TriggerProposal:
    domain = entity_id.split(".", 1)[0]
    base = _BY_DOMAIN.get(domain, TriggerProposal((), ()))
    options = list(base.options)
    # Offer the state the entity is in right now, so an unusual integration's
    # vocabulary is visible — but never a fault state, which is not a trigger.
    if (
        current_state
        and current_state not in FAULT_STATES
        and current_state not in options
    ):
        options.append(current_state)
    return TriggerProposal(tuple(options), base.proposed)


def invalid_trigger_states(states: list[str]) -> list[str]:
    """States that may not be trigger states: faults are faults (INV-4)."""
    return [s for s in states if s in FAULT_STATES]
