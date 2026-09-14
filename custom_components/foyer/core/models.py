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


def _frozen(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(mapping))


# --- vocabulary ------------------------------------------------------------------


class AreaState(StrEnum):
    """Area states (SPEC §5.1). ``fault`` is an overlay, not a state."""

    DISARMED = "disarmed"
    ARMING = "arming"
    ARMED = "armed"
    ENTRY = "entry"
    TRIGGERED = "triggered"


class ZoneType(StrEnum):
    """Presets (SPEC §4.3). A label only: the engine never reads it."""

    INSTANT = "instant"
    DELAYED = "delayed"
    FOLLOWER = "follower"
    H24 = "24h"
    TAMPER = "tamper"
    TECHNICAL = "technical"
    PANIC = "panic"
    KEY = "key"


class Channel(StrEnum):
    """Which machine a zone feeds. Intrusion and technical never mix (§5.5)."""

    INTRUSION = "intrusion"
    TECHNICAL = "technical"
    KEY = "key"  # commands, does not alarm (§4.7)


class EntryMode(StrEnum):
    """What an intrusion zone does when it triggers in an armed area (§5.2)."""

    INSTANT = "instant"
    DELAYED = "delayed"
    FOLLOWER = "follower"


class AlarmKind(StrEnum):
    """What an intrusion trigger means, for events and the log (§4.3)."""

    INTRUSION = "intrusion"
    TAMPER = "tamper"
    PANIC = "panic"


class ArmPolicy(StrEnum):
    """What happens to a zone that is open at arming (§4.2, §5.4)."""

    BLOCK = "block"
    AUTO_BYPASS = "auto_bypass"
    ARM_AFTER_CLOSING = "arm_after_closing"
    IGNORE = "ignore"


class KeyCommand(StrEnum):
    ARM = "arm"
    DISARM = "disarm"
    TOGGLE = "toggle"


class KeyRelease(StrEnum):
    NONE = "none"
    DISARM = "disarm"


class NumericOperator(StrEnum):
    GT = "gt"
    LT = "lt"
    EQ = "eq"


class TimerKind(StrEnum):
    EXIT = "exit"
    HOLD = "hold"  # arm_after_closing: exit delay over, waiting for a zone to close
    ENTRY = "entry"
    SIREN = "siren"


class BypassReason(StrEnum):
    AUTO = "auto_bypass"  # open at arming with arm_policy auto_bypass
    FORCED = "forced"  # excluded by a forced arm


class Operation(StrEnum):
    """Operations subject to the code policy (SPEC §8.2)."""

    ARM = "arm"
    DISARM = "disarm"
    FORCE_ARM = "force_arm"
    CHANGE_SCENARIO = "change_scenario"


class Moment(StrEnum):
    """What happened. Every Occurrence carries one (SPEC §6.1).

    ``zone_rejoined`` is not a profile moment in §6.1; it exists so that the
    log can say when an automatically bypassed zone came back.
    """

    ARMED = "armed"
    DISARMED = "disarmed"
    ARM_FAILED = "arm_failed"
    FORCED_ARM = "forced_arm"
    ZONE_BYPASSED = "zone_bypassed"
    ZONE_REJOINED = "zone_rejoined"
    ENTRY_STARTED = "entry_started"
    TRIGGERED = "triggered"
    SIREN_CUTOFF = "siren_cutoff"
    ZONE_FAULT = "zone_fault"
    HA_RESTARTED = "ha_restarted"


class Reason(StrEnum):
    """Why a request was rejected. Stable identifiers: UIs translate them."""

    INVALID_STATE = "invalid_state"
    UNKNOWN_SCENARIO = "unknown_scenario"
    UNKNOWN_AREA = "unknown_area"
    NO_SCENARIO_FOR_MODE = "no_scenario_for_mode"
    AMBIGUOUS_MODE = "ambiguous_mode"
    ALARM_IN_PROGRESS = "alarm_in_progress"
    CODE_REQUIRED = "code_required"
    ZONE_FAULT = "zone_fault"
    ZONE_OPEN = "zone_open"
    ZONE_NOT_BYPASSABLE = "zone_not_bypassable"
    ARM_HOLD_EXPIRED = "arm_hold_expired"


# Entity states that mean "we do not know" — a fault, never calm (INV-4).
FAULT_STATES: frozenset[str] = frozenset({"unavailable", "unknown"})

# The alarm_control_panel states an area or scenario may report when armed.
ARMED_HA_STATES: tuple[str, ...] = (
    "armed_home",
    "armed_away",
    "armed_night",
    "armed_vacation",
    "armed_custom_bypass",
)
CUSTOM_BYPASS = "armed_custom_bypass"

# Timer bounds (SPEC §5.3), in seconds.
MAX_EXIT_DELAY = 300
MAX_ENTRY_DELAY = 300
MAX_SIREN_DURATION = 900  # EN 50131 reference for external sounders
DEFAULT_EXIT_DELAY = 30
DEFAULT_ENTRY_DELAY = 30
DEFAULT_SIREN_DURATION = 180
# arm_after_closing: how long after the exit delay a zone may stay open.
DEFAULT_ARM_HOLD_TIMEOUT = 300
MIN_ARM_HOLD_TIMEOUT = 60
MAX_ARM_HOLD_TIMEOUT = 1800
MIN_SUPERVISION_TIMEOUT = 60
MAX_SUPERVISION_TIMEOUT = 7 * 24 * 3600


# --- configuration -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StateTrigger:
    """Triggered while the entity is in one of ``states`` (SPEC §4.4).

    There is no default: every zone must say what "triggered" means (INV-5).
    """

    states: frozenset[str]

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("a StateTrigger needs at least one state (INV-5)")


@dataclass(frozen=True, slots=True)
class NumericTrigger:
    """Triggered while a number crosses ``value`` (SPEC §4.4).

    ``gt`` becomes active above ``value`` and inactive again only at or below
    ``value - hysteresis``; ``lt`` mirrors it. ``eq`` has no band. The number
    is the entity state, or ``attribute`` when set.
    """

    operator: NumericOperator
    value: float
    hysteresis: float = 0.0
    attribute: str | None = None


@dataclass(frozen=True, slots=True)
class EventTrigger:
    """A momentary trigger for ``event`` and ``tag`` entities (SPEC §4.4).

    ``event.*`` fires on each new event whose ``event_type`` attribute matches;
    ``tag.*`` fires on every scan and takes no event type. ``subtype`` is part
    of the spec's shape but has no Home Assistant counterpart yet, so the
    validator refuses it rather than store something that is never read.
    """

    event_type: str | None = None
    subtype: str | None = None


TriggerSpec = StateTrigger | NumericTrigger | EventTrigger


@dataclass(frozen=True, slots=True)
class KeyAction:
    """What a key zone does (SPEC §4.7). Disarm always means every area."""

    on_activate: KeyCommand
    scenario_id: str | None = None  # required for arm and toggle
    on_deactivate: KeyRelease = KeyRelease.NONE


@dataclass(frozen=True, slots=True)
class Zone:
    """One entity plus alarm semantics (SPEC §4.2).

    ``type`` is the preset the user started from and nothing else: the engine
    reads the explicit properties below, all of which stay editable.
    """

    id: str
    name: str
    entity_id: str
    area_id: str
    trigger: TriggerSpec
    type: ZoneType = ZoneType.INSTANT
    channel: Channel = Channel.INTRUSION
    entry_mode: EntryMode = EntryMode.INSTANT
    alarm_kind: AlarmKind = AlarmKind.INTRUSION
    always_on: bool = False
    entry_delay: int | None = None  # None: inherit the area default
    arm_policy: ArmPolicy = ArmPolicy.BLOCK
    arm_hold_timeout: int | None = None  # None: inherit the global default
    allow_arm_when_faulted: bool = False
    bypassable: bool = True
    supervision_timeout: int | None = None  # None: not supervised
    enabled: bool = True
    key: KeyAction | None = None


@dataclass(frozen=True, slots=True)
class Area:
    id: str
    name: str
    # Which alarm_control_panel state this area reports when armed (SPEC §4.5).
    ha_state_when_armed: str
    default_entry_delay: int = DEFAULT_ENTRY_DELAY
    default_exit_delay: int = DEFAULT_EXIT_DELAY


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    areas: tuple[str, ...]
    ha_master_state: str
    icon: str | None = None
    exit_delay_override: int | None = None
    siren_duration_override: int | None = None


@dataclass(frozen=True, slots=True)
class NotificationAction:
    """The single response action until response profiles exist.

    ``moments`` lists when it runs. The message itself is resolved from the
    translation files by the executor; the engine only names it.
    """

    id: str
    moments: frozenset[Moment]


@dataclass(frozen=True, slots=True)
class CodePolicy:
    """Whether each operation requires a code (SPEC §8.2).

    There are no users and no codes before Phase 2, so the stored configuration
    sets every operation to False explicitly. The engine still enforces the
    policy and fails closed: a request that needs a code is refused, because no
    code can be verified yet.
    """

    arm: bool = False
    disarm: bool = False
    force_arm: bool = False
    change_scenario: bool = False

    def requires_code(self, operation: Operation) -> bool:
        return bool(getattr(self, operation.value))


@dataclass(frozen=True, slots=True)
class Settings:
    """Global settings the engine reads."""

    siren_duration: int = DEFAULT_SIREN_DURATION
    arm_hold_timeout: int = DEFAULT_ARM_HOLD_TIMEOUT


@dataclass(frozen=True, slots=True)
class FoyerConfig:
    areas: tuple[Area, ...]
    zones: tuple[Zone, ...]
    scenarios: tuple[Scenario, ...]
    actions: tuple[NotificationAction, ...] = ()
    code_policy: CodePolicy = field(default_factory=CodePolicy)
    settings: Settings = field(default_factory=Settings)

    def area(self, area_id: str | None) -> Area | None:
        return next((a for a in self.areas if a.id == area_id), None)

    def zone(self, zone_id: str | None) -> Zone | None:
        return next((z for z in self.zones if z.id == zone_id), None)

    def scenario(self, scenario_id: str | None) -> Scenario | None:
        return next((s for s in self.scenarios if s.id == scenario_id), None)

    def zones_in(self, area_ids: tuple[str, ...] | frozenset[str]) -> tuple[Zone, ...]:
        """Enabled zones in the given areas. Disabled zones do not exist."""
        return tuple(z for z in self.zones if z.enabled and z.area_id in area_ids)

    def entry_delay(self, zone: Zone) -> int:
        if zone.entry_delay is not None:
            return zone.entry_delay
        area = self.area(zone.area_id)
        return area.default_entry_delay if area else DEFAULT_ENTRY_DELAY

    def arm_hold_timeout(self, zone: Zone) -> int:
        if zone.arm_hold_timeout is not None:
            return zone.arm_hold_timeout
        return self.settings.arm_hold_timeout

    def exit_delay(self, area: Area, scenario: Scenario | None) -> int:
        if scenario is not None and scenario.exit_delay_override is not None:
            return scenario.exit_delay_override
        return area.default_exit_delay

    def siren_duration(self, scenario: Scenario | None) -> int:
        if scenario is not None and scenario.siren_duration_override is not None:
            return scenario.siren_duration_override
        return self.settings.siren_duration


# --- runtime state (persisted, INV-3) -------------------------------------------


@dataclass(frozen=True, slots=True)
class Timer:
    """A pending timer. The scheduler owns the clock; the engine owns meaning.

    ``anchor`` is when the exit delay ended, for a ``hold`` timer: the
    arm_after_closing cap counts from there.
    """

    kind: TimerKind
    due: datetime
    anchor: datetime | None = None


@dataclass(frozen=True, slots=True)
class AreaRuntime:
    """The live state of one area's machine (SPEC §5).

    ``scenario_id`` is the scenario that armed this area, or None when the area
    was armed on its own from its panel. ``resume`` and ``resume_timer`` record
    where the area goes back to at siren cutoff: the state it was in before it
    triggered, so a 24h zone firing on a disarmed house never arms it.
    """

    state: AreaState = AreaState.DISARMED
    scenario_id: str | None = None
    timer: Timer | None = None
    memory: bool = False
    forced: bool = False
    resume: AreaState | None = None
    resume_timer: Timer | None = None
    causes: tuple[str, ...] = ()
    channel: str | None = None  # how it was armed, for the ``armed`` record


@dataclass(frozen=True, slots=True)
class RuntimeState:
    """Everything that must survive a restart (INV-3).

    ``active_zones`` remembers which zones count as triggered, because a numeric
    trigger inside its hysteresis band, or an entity in fault, keeps whatever it
    was before. ``seen_zones`` are the zones read at least once: a zone's first
    readable value is its baseline, not an activation, so adding a key switch
    that is already on does not arm the house. ``faults`` holds the zones
    already announced as faulted, so each fault is announced once.
    """

    areas: Mapping[str, AreaRuntime] = field(default_factory=dict)
    active_scenario_id: str | None = None
    bypassed: Mapping[str, BypassReason] = field(default_factory=dict)
    active_zones: frozenset[str] = frozenset()
    seen_zones: frozenset[str] = frozenset()
    faults: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "areas", _frozen(self.areas))
        object.__setattr__(self, "bypassed", _frozen(self.bypassed))

    def area(self, area_id: str) -> AreaRuntime:
        return self.areas.get(area_id) or AreaRuntime()


# --- snapshot ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EntityState:
    """One Home Assistant entity as the engine may see it.

    ``state`` None means the entity does not exist, which is a fault (INV-4).
    ``last_reported`` is the last time the entity reported anything, changed or
    not: the heartbeat that supervision measures.
    """

    state: str | None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    last_reported: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", _frozen(self.attributes))


MISSING = EntityState(state=None)


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    """Everything decide() may know about the world, passed in explicitly.

    ``settling`` is True while Home Assistant is still starting and entities are
    still appearing: faults are not announced until it ends, so a restart does
    not produce one notification per zone. They are announced then if they
    persist. Alarms are never held back.
    """

    state: RuntimeState
    entities: Mapping[str, EntityState]
    settling: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", _frozen(self.entities))

    def entity(self, entity_id: str) -> EntityState:
        return self.entities.get(entity_id) or MISSING


# --- events --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArmRequest:
    """Arm a scenario, or switch to it while armed (SPEC §4.6)."""

    scenario_id: str
    code: str | None = None
    channel: str = "api"
    force: bool = False


@dataclass(frozen=True, slots=True)
class ArmModeRequest:
    """Arm through the master panel: the one scenario reporting this mode."""

    mode: str
    code: str | None = None
    channel: str = "api"
    force: bool = False


@dataclass(frozen=True, slots=True)
class ArmAreaRequest:
    """Arm one area on its own, outside any scenario, from its own panel."""

    area_id: str
    code: str | None = None
    channel: str = "api"
    force: bool = False


@dataclass(frozen=True, slots=True)
class DisarmRequest:
    """Disarm ``area_ids``, or every area when None."""

    area_ids: tuple[str, ...] | None = None
    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class ZoneStateChanged:
    """An entity changed. The snapshot still shows it as it was before."""

    entity_id: str
    new: EntityState


@dataclass(frozen=True, slots=True)
class Tick:
    """The scheduler's wake-up: timers may be due, supervision may have lapsed."""


@dataclass(frozen=True, slots=True)
class Startup:
    """Foyer is running again. ``down_since`` opens the gap in coverage.

    ``cause`` says why there was a gap: ``ha_start`` after Home Assistant
    itself restarted, ``reload`` when only Foyer was reloaded (a configuration
    change). Both are gaps, however short, and both are recorded.
    """

    down_since: datetime | None = None
    cause: str = "ha_start"


Event = (
    ArmRequest
    | ArmModeRequest
    | ArmAreaRequest
    | DisarmRequest
    | ZoneStateChanged
    | Tick
    | Startup
)


# --- decision ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Occurrence:
    """One thing that happened, with enough context for a log row and a message."""

    moment: Moment
    area_id: str | None = None
    zone_id: str | None = None
    scenario_id: str | None = None
    zone_ids: tuple[str, ...] = ()
    channel: str | None = None
    detail: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", _frozen(self.detail))


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """An action that *should* run. The executor decides nothing about it."""

    action_id: str
    kind: str
    moment: Moment
    placeholders: Mapping[str, str] = field(default_factory=dict)
    # A variant of the message, e.g. "area" for an area armed outside any
    # scenario, which has no scenario name to show.
    variant: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "placeholders", _frozen(self.placeholders))


@dataclass(frozen=True, slots=True)
class Decision:
    """What should happen in response to one event (INV-1). Executes nothing.

    ``state`` is the complete runtime state after the decision; the runtime
    stores it as it is. ``accepted`` is False when a request was refused, and
    ``reason`` and ``blocking_zones`` then say why, so a UI or keypad can name
    the zone (SPEC §5.4, §9.1). A refused request may still carry state: timers
    that fell due are processed whatever the event.
    """

    at: datetime
    accepted: bool
    state: RuntimeState
    reason: Reason | None = None
    blocking_zones: tuple[str, ...] = ()
    bypassed_zones: tuple[str, ...] = ()
    occurrences: tuple[Occurrence, ...] = ()
    actions: tuple[ActionIntent, ...] = ()

    @property
    def active_scenario_id(self) -> str | None:
        return self.state.active_scenario_id

    @property
    def moments(self) -> tuple[Moment, ...]:
        return tuple(o.moment for o in self.occurrences)
