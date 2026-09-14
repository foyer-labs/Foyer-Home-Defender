"""Trigger and type proposals for the zone wizard (SPEC §4.4, INV-5).

A proposal is a starting point the user must confirm, never a silent default:
the zone wizard refuses to save a trigger that has not been confirmed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .models import FAULT_STATES, ZoneType


@dataclass(frozen=True, slots=True)
class TriggerProposal:
    options: tuple[str, ...]  # every state the user may pick
    proposed: tuple[str, ...]  # pre-selected, to be confirmed


@dataclass(frozen=True, slots=True)
class ZoneProposal:
    """What the wizard pre-fills for an entity. Everything needs confirming."""

    trigger_kind: str  # "state" | "numeric" | "event"
    options: tuple[str, ...]  # states, or event types, the user may pick
    proposed: tuple[str, ...]
    zone_type: ZoneType | None


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
    "device_tracker": TriggerProposal(("home", "not_home"), ()),
    "person": TriggerProposal(("home", "not_home"), ()),
}

# Domains the Phase 0 config flow offers: those with a discrete vocabulary.
SUPPORTED_DOMAINS: tuple[str, ...] = (
    "binary_sensor",
    "input_boolean",
    "switch",
    "cover",
    "lock",
)

# binary_sensor device classes -> the type a new zone most likely wants.
_TYPE_BY_DEVICE_CLASS: dict[str, ZoneType] = {
    "door": ZoneType.DELAYED,
    "garage_door": ZoneType.DELAYED,
    "window": ZoneType.INSTANT,
    "opening": ZoneType.INSTANT,
    "motion": ZoneType.INSTANT,
    "occupancy": ZoneType.INSTANT,
    "presence": ZoneType.INSTANT,
    "vibration": ZoneType.INSTANT,
    "tamper": ZoneType.TAMPER,
    "safety": ZoneType.H24,
    "smoke": ZoneType.TECHNICAL,
    "gas": ZoneType.TECHNICAL,
    "carbon_monoxide": ZoneType.TECHNICAL,
    "moisture": ZoneType.TECHNICAL,
    "heat": ZoneType.TECHNICAL,
    "cold": ZoneType.TECHNICAL,
    "power": ZoneType.TECHNICAL,
}


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


def propose_zone(
    entity_id: str, current_state: str | None, attributes: Mapping[str, Any]
) -> ZoneProposal:
    """What the zone wizard pre-fills for this entity."""
    domain = entity_id.split(".", 1)[0]
    device_class = attributes.get("device_class")

    if domain == "event":
        types = attributes.get("event_types") or ()
        options = tuple(str(t) for t in types)
        return ZoneProposal("event", options, options[:1], ZoneType.PANIC)
    if domain == "tag":
        return ZoneProposal("event", (), (), ZoneType.KEY)
    if domain == "sensor":
        # A number: the user chooses the operator and the threshold.
        technical = device_class in {"temperature", "humidity", "carbon_monoxide"}
        return ZoneProposal(
            "numeric", (), (), ZoneType.TECHNICAL if technical else ZoneType.INSTANT
        )

    trigger = propose_trigger(entity_id, current_state)
    zone_type: ZoneType | None = None
    if domain == "binary_sensor":
        zone_type = _TYPE_BY_DEVICE_CLASS.get(str(device_class), ZoneType.INSTANT)
    elif domain in {"cover", "lock"}:
        zone_type = ZoneType.DELAYED
    elif domain in {"switch", "input_boolean"}:
        zone_type = ZoneType.INSTANT
    return ZoneProposal("state", trigger.options, trigger.proposed, zone_type)


def invalid_trigger_states(states: list[str]) -> list[str]:
    """States that may not be trigger states: faults are faults (INV-4)."""
    return [s for s in states if s in FAULT_STATES]
