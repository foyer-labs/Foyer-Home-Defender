"""Plain dataclasses for configuration, snapshot, events and decisions.

Nothing in this package may import ``homeassistant`` (SPEC §3, INV-1). Everything
here is data: no behaviour that touches the outside world.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class AreaState(StrEnum):
    """Area states (SPEC §5.1).

    Phase 0 has no delays, so ``arming`` and ``entry`` cannot occur yet and are
    deliberately absent rather than defined and unreachable.
    """

    DISARMED = "disarmed"
    ARMED = "armed"
    TRIGGERED = "triggered"


class Operation(StrEnum):
    """Operations subject to the code policy (SPEC §8.2)."""

    ARM = "arm"
    DISARM = "disarm"


class Moment(StrEnum):
    """Moments a response action can attach to (SPEC §6.1)."""

    ARMED = "armed"
    DISARMED = "disarmed"
    ARM_FAILED = "arm_failed"
    TRIGGERED = "triggered"
    ZONE_FAULT = "zone_fault"


class Reason(StrEnum):
    """Why a request was rejected. Stable identifiers: UIs translate them."""

    INVALID_STATE = "invalid_state"
    UNKNOWN_SCENARIO = "unknown_scenario"
    CODE_REQUIRED = "code_required"
    ZONE_FAULT = "zone_fault"
    ZONE_OPEN = "zone_open"


# Entity states that mean "we do not know" — a fault, never calm (INV-4).
FAULT_STATES: frozenset[str] = frozenset({"unavailable", "unknown"})


# --- configuration -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StateTrigger:
    """The zone is triggered while its entity is in one of ``states`` (SPEC §4.4).

    There is no default: every zone must say what "triggered" means (INV-5).
    """

    states: frozenset[str]

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("a StateTrigger needs at least one state (INV-5)")


@dataclass(frozen=True, slots=True)
class Zone:
    id: str
    name: str
    entity_id: str
    area_id: str
    trigger: StateTrigger


@dataclass(frozen=True, slots=True)
class Area:
    id: str
    name: str
    # Which alarm_control_panel state this area reports when armed (SPEC §4.5).
    ha_state_when_armed: str


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    areas: tuple[str, ...]
    ha_master_state: str


@dataclass(frozen=True, slots=True)
class NotificationAction:
    """Phase 0's single response action: a persistent notification.

    ``moments`` lists when it runs. The message itself is resolved from the
    translation files by the executor; the engine only names it.
    """

    id: str
    moments: frozenset[Moment]


@dataclass(frozen=True, slots=True)
class CodePolicy:
    """Whether each operation requires a code (SPEC §8.2).

    Phase 0 has no users and no codes, so the stored configuration sets both to
    False explicitly. The engine still enforces the policy, and fails closed: a
    request that needs a code is rejected because no code can be verified yet.
    """

    arm: bool
    disarm: bool

    def requires_code(self, operation: Operation) -> bool:
        return self.arm if operation is Operation.ARM else self.disarm


@dataclass(frozen=True, slots=True)
class FoyerConfig:
    areas: tuple[Area, ...]
    zones: tuple[Zone, ...]
    scenarios: tuple[Scenario, ...]
    actions: tuple[NotificationAction, ...]
    code_policy: CodePolicy

    def area(self, area_id: str) -> Area | None:
        return next((a for a in self.areas if a.id == area_id), None)

    def scenario(self, scenario_id: str) -> Scenario | None:
        return next((s for s in self.scenarios if s.id == scenario_id), None)

    def zones_in(self, area_ids: tuple[str, ...]) -> tuple[Zone, ...]:
        return tuple(z for z in self.zones if z.area_id in area_ids)


# --- snapshot ------------------------------------------------------------------


def _frozen(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    """Everything decide() may know about the world, passed in explicitly.

    ``entity_states`` maps entity ids to their current state; a missing key or
    ``None`` means the entity does not exist, which is a fault (INV-4).
    """

    area_states: Mapping[str, AreaState]
    active_scenario_id: str | None
    entity_states: Mapping[str, str | None]

    def __post_init__(self) -> None:
        object.__setattr__(self, "area_states", _frozen(self.area_states))
        object.__setattr__(self, "entity_states", _frozen(self.entity_states))


# --- events --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArmRequest:
    scenario_id: str
    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class DisarmRequest:
    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class ZoneStateChanged:
    entity_id: str
    new_state: str | None


Event = ArmRequest | DisarmRequest | ZoneStateChanged


# --- decision ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """An action that *should* run. The executor decides nothing about it."""

    action_id: str
    kind: str
    moment: Moment
    placeholders: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "placeholders", _frozen(self.placeholders))


@dataclass(frozen=True, slots=True)
class Decision:
    """What should happen in response to one event (INV-1). Executes nothing.

    ``area_states`` holds only the areas whose state changes, while
    ``active_scenario_id`` is always the scenario in force *after* the decision.
    ``accepted`` is False when a request was refused; ``reason`` and
    ``blocking_zones`` say why, so a UI or keypad can name the zone
    (SPEC §5.4, §9.1).
    """

    at: datetime
    accepted: bool
    reason: Reason | None = None
    area_states: Mapping[str, AreaState] = field(default_factory=dict)
    active_scenario_id: str | None = None
    blocking_zones: tuple[str, ...] = ()
    moments: tuple[Moment, ...] = ()
    actions: tuple[ActionIntent, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "area_states", _frozen(self.area_states))
