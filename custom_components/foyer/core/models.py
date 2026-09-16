"""Plain dataclasses for configuration, snapshot, events and decisions.

Nothing in this package may import ``homeassistant`` (SPEC §3, INV-1). Everything
here is data: no behaviour that touches the outside world.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, tzinfo
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
    MANUAL = "manual"  # excluded by a person, with or without a duration


class ChimeMode(StrEnum):
    """What the chime plays (SPEC §6.6)."""

    SOUND = "sound"  # one sound on every target
    SPEECH = "speech"  # the zone's name, spoken through tts.speak


class ActionKind(StrEnum):
    """The action catalogue (SPEC §6.2).

    ``persistent_notification`` is not in §6.2: it is what Phase 0 did, and the
    global default profile inherits it at the 3.1 → 4.1 migration so that no
    installation loses a notification it already had. It needs no contact book,
    which ``notify`` will need from Phase 4 on.
    """

    NOTIFY = "notify"
    PERSISTENT_NOTIFICATION = "persistent_notification"
    SIREN = "siren"
    LIGHT = "light"
    CAMERA = "camera"
    SCENE = "scene"
    SWITCH = "switch"
    TTS = "tts"
    CALL_SERVICE = "call_service"
    DELAY = "delay"


# What a ``silent`` zone suppresses by default (part 3 decision 6): the action
# kinds that make a noise inside the house. The list is a global setting.
DEFAULT_SILENT_SUPPRESSES: tuple[str, ...] = (
    ActionKind.SIREN.value,
    ActionKind.TTS.value,
    "chime",
)
SILENCEABLE: frozenset[str] = frozenset({*(k.value for k in ActionKind), "chime"})

# Where camera snapshots and recordings go, relative to the configuration
# directory. Never ``www``: that is served without authentication (§10.4).
DEFAULT_CAMERA_DIR = "media/foyer"


class ConditionMode(StrEnum):
    """How an action's two conditions combine (part 3 decision 4)."""

    ALL = "all"
    ANY = "any"


class StateOperator(StrEnum):
    IS = "is"
    IS_NOT = "is_not"


class Operation(StrEnum):
    """Operations subject to the code policy (SPEC §8.2).

    ``acknowledge`` covers both the incident and the technical channel. §8.2
    does not list it: its policy is a Phase 2 question, but the check already
    runs so that Phase 2 changes policy, not plumbing.
    """

    ARM = "arm"
    DISARM = "disarm"
    FORCE_ARM = "force_arm"
    CHANGE_SCENARIO = "change_scenario"
    ACKNOWLEDGE = "acknowledge"
    BYPASS_ZONE = "bypass_zone"


class Moment(StrEnum):
    """What happened. Every Occurrence carries one (SPEC §6.1).

    Not every moment is a profile moment in §6.1. ``zone_rejoined`` lets the
    log say when an automatically bypassed zone came back; the incident,
    verification and chime moments exist for the log and for the simulator's
    trace (§4.8, §5.6, §11.2). The technical moments are what the technical
    channel's own profile will attach to in part 3.
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
    TECHNICAL_RAISED = "technical_raised"
    TECHNICAL_ACKNOWLEDGED = "technical_acknowledged"
    TECHNICAL_CLEARED = "technical_cleared"
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_JOINED = "incident_joined"
    INCIDENT_ACKNOWLEDGED = "incident_acknowledged"
    INCIDENT_CLOSED = "incident_closed"
    VERIFICATION_PENDING = "verification_pending"
    VERIFICATION_SATISFIED = "verification_satisfied"
    VERIFICATION_EXPIRED = "verification_expired"
    CHIME = "chime"
    CHIME_SWITCHED = "chime_switched"

    # Moments no phase produces yet. They exist so a profile can be written
    # against them now and keep working when the phase that raises them lands;
    # the editor says which phase each one waits for.
    CODE_REJECTED = "code_rejected"  # Phase 2
    LOCKOUT = "lockout"  # Phase 2
    LOW_BATTERY = "low_battery"  # Phase 3
    WALK_TEST_STARTED = "walk_test_started"  # Phase 3
    WALK_TEST_ENDED = "walk_test_ended"  # Phase 3
    ESCALATION_EXHAUSTED = "escalation_exhausted"  # Phase 4


class Reason(StrEnum):
    """Why a request was rejected. Stable identifiers: UIs translate them."""

    INVALID_STATE = "invalid_state"
    UNKNOWN_SCENARIO = "unknown_scenario"
    UNKNOWN_AREA = "unknown_area"
    UNKNOWN_ZONE = "unknown_zone"
    NO_SCENARIO_FOR_MODE = "no_scenario_for_mode"
    AMBIGUOUS_MODE = "ambiguous_mode"
    ALARM_IN_PROGRESS = "alarm_in_progress"
    CODE_REQUIRED = "code_required"
    ZONE_FAULT = "zone_fault"
    ZONE_OPEN = "zone_open"
    ZONE_NOT_BYPASSABLE = "zone_not_bypassable"
    ARM_HOLD_EXPIRED = "arm_hold_expired"
    NOTHING_TO_ACKNOWLEDGE = "nothing_to_acknowledge"


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
# Verification windows: groups, cross-zone and trigger counting (§4.2, §4.8).
DEFAULT_VERIFICATION_WINDOW = 60
MIN_VERIFICATION_WINDOW = 1
MAX_VERIFICATION_WINDOW = 3600
MAX_TRIGGER_COUNT = 10


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
    ``tag.*`` fires on every scan and takes no event type.
    """

    event_type: str | None = None


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
    # Follower only: delayed zones, in any area, whose running entry window it
    # also inherits. Its own area's window is always inherited (§5.2).
    follows: tuple[str, ...] = ()
    arm_policy: ArmPolicy = ArmPolicy.BLOCK
    arm_hold_timeout: int | None = None  # None: inherit the global default
    allow_arm_when_faulted: bool = False
    bypassable: bool = True
    supervision_timeout: int | None = None  # None: not supervised
    enabled: bool = True
    key: KeyAction | None = None
    # Sound the chime when it opens while its area does not monitor it (§6.6).
    chime: bool = False
    # A second zone that confirms this one: the pair is a 2-of-2 group that
    # does not suppress its members (§4.8; part 2 decisions 4 and 9).
    cross_zone_id: str | None = None
    cross_zone_window: int = DEFAULT_VERIFICATION_WINDOW
    # N activations of this zone within the window before it alarms (§4.2).
    trigger_count: int = 1
    trigger_window: int = DEFAULT_VERIFICATION_WINDOW
    # Read only for this zone's own alarm (part 3 decision 1): everything else
    # responds from the area. None inherits the area's chain.
    response_profile_id: str | None = None
    # The response runs without the action kinds the global silent list names
    # (§4.2, part 3 decision 6).
    silent: bool = False


@dataclass(frozen=True, slots=True)
class Group:
    """An N-of-M verification group (SPEC §4.8).

    Membership is stored here, on the group, and nowhere else: a zone's
    ``group_id`` is derived from it. Members may sit in different areas; each
    acts in its own. ``area_id`` is where the group is shown and, in part 3,
    where its profile inherits from.
    """

    id: str
    name: str
    area_id: str
    members: tuple[str, ...]
    n: int
    window_seconds: int = DEFAULT_VERIFICATION_WINDOW
    suppress_members: bool = False
    # What a satisfied group does (§4.8). None inherits from its area.
    response_profile_id: str | None = None


@dataclass(frozen=True, slots=True)
class TimeCondition:
    """A daily window, which may cross midnight (SPEC §6.3)."""

    after: str  # "HH:MM"
    before: str


@dataclass(frozen=True, slots=True)
class StateCondition:
    """One entity, read from the snapshot so the simulator agrees (§6.3)."""

    entity_id: str
    operator: StateOperator
    state: str


Condition = TimeCondition | StateCondition

# At most two conditions per action (SPEC §6.3). The bound is the line between
# a response engine and a second automation engine, and it is enforced.
MAX_CONDITIONS = 2


@dataclass(frozen=True, slots=True)
class ProfileAction:
    """One action in a profile (SPEC §6.2).

    ``moments`` is when it runs; ``params`` is what the executor needs, already
    complete, so it never reads the configuration itself (INV-1). ``delay`` is
    the one kind that acts on the list rather than on the world: it holds the
    actions after it for ``seconds``.
    """

    id: str
    kind: ActionKind
    moments: frozenset[Moment]
    name: str = ""
    params: Mapping[str, Any] = field(default_factory=dict)
    conditions: tuple[Condition, ...] = ()
    condition_mode: ConditionMode = ConditionMode.ALL
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", _frozen(self.params))


@dataclass(frozen=True, slots=True)
class ResponseProfile:
    """A reusable, named list of actions (SPEC §6).

    ``severity`` is an integer the user orders and has exactly one use: which
    escalation an incident adopts when profiles of different strength
    contribute to it (§6.5). It changes nothing when a profile runs alone.
    """

    id: str
    name: str
    severity: int = 1
    actions: tuple[ProfileAction, ...] = ()


@dataclass(frozen=True, slots=True)
class ChimeTarget:
    """One chime target, with quiet hours of its own (part 3 decision 8).

    A `media_player` or `siren` entity, or a `notify.*` service or entity
    (decision 60). Its own quiet window, when set, replaces the global one:
    speakers all day, the phone only between nine and ten.
    """

    entity_id: str
    quiet_start: str | None = None
    quiet_end: str | None = None


@dataclass(frozen=True, slots=True)
class ChimeSettings:
    """The one global chime block (SPEC §6.6). Per-zone opt-in is Zone.chime.

    ``sound`` is the media to play on media players in sound mode; sirens
    beep in either mode. ``volume`` is a percentage, None to leave the
    player's volume alone. Quiet hours are local "HH:MM" times and may cross
    midnight. ``during_exit`` lets zones chime while their area counts down
    its exit delay (part 2 decision 7; off by default).
    """

    targets: tuple[ChimeTarget, ...] = ()
    mode: ChimeMode = ChimeMode.SOUND
    sound: str | None = None
    tts_entity: str | None = None
    volume: int | None = None
    quiet_start: str | None = None
    quiet_end: str | None = None
    during_exit: bool = False


@dataclass(frozen=True, slots=True)
class Area:
    id: str
    name: str
    # Which alarm_control_panel state this area reports when armed (SPEC §4.5).
    ha_state_when_armed: str
    default_entry_delay: int = DEFAULT_ENTRY_DELAY
    default_exit_delay: int = DEFAULT_EXIT_DELAY
    # The area is the unit of response (part 3 decision 1): this is what
    # answers for everything happening in it. None inherits from the scenario.
    response_profile_id: str | None = None


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    areas: tuple[str, ...]
    ha_master_state: str
    icon: str | None = None
    exit_delay_override: int | None = None
    siren_duration_override: int | None = None
    response_profile_id: str | None = None


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
    acknowledge: bool = False
    bypass_zone: bool = False

    def requires_code(self, operation: Operation) -> bool:
        return bool(getattr(self, operation.value))


@dataclass(frozen=True, slots=True)
class Settings:
    """Global settings the engine reads.

    ``default_profile_id`` is the end of every inheritance chain (§6);
    ``technical_profile_id`` is the technical channel's own default, separate
    because a smoke alarm must not respond differently depending on how the
    house is armed (part 3 decision 2). ``silent_suppresses`` names the action
    kinds a ``silent`` zone does not run (decision 6).
    """

    siren_duration: int = DEFAULT_SIREN_DURATION
    arm_hold_timeout: int = DEFAULT_ARM_HOLD_TIMEOUT
    default_profile_id: str | None = None
    technical_profile_id: str | None = None
    silent_suppresses: tuple[str, ...] = DEFAULT_SILENT_SUPPRESSES
    camera_dir: str = DEFAULT_CAMERA_DIR


@dataclass(frozen=True, slots=True)
class FoyerConfig:
    areas: tuple[Area, ...]
    zones: tuple[Zone, ...]
    scenarios: tuple[Scenario, ...]
    profiles: tuple[ResponseProfile, ...] = ()
    code_policy: CodePolicy = field(default_factory=CodePolicy)
    settings: Settings = field(default_factory=Settings)
    groups: tuple[Group, ...] = ()
    chime: ChimeSettings = field(default_factory=ChimeSettings)

    def area(self, area_id: str | None) -> Area | None:
        return next((a for a in self.areas if a.id == area_id), None)

    def group(self, group_id: str | None) -> Group | None:
        return next((g for g in self.groups if g.id == group_id), None)

    def profile(self, profile_id: str | None) -> ResponseProfile | None:
        return next((p for p in self.profiles if p.id == profile_id), None)

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
class TechnicalAlarm:
    """One technical zone in alarm or in memory (SPEC §5.5).

    It exists from the moment the zone fires until it has been acknowledged
    **and** the zone is back to normal, in either order. Whether the zone is
    still active is read from ``RuntimeState.active_zones``, never duplicated.
    """

    since: datetime
    acknowledged_at: datetime | None = None
    acknowledged_channel: str | None = None

    @property
    def acknowledged(self) -> bool:
        return self.acknowledged_at is not None


@dataclass(frozen=True, slots=True)
class Contributor:
    """A zone that joined an incident (SPEC §5.6).

    ``profile_id`` and ``severity`` are the zone's effective response profile
    when it joined: filled in part 3, read by Phase 4's escalation to pick
    the highest-severity contributor. They exist now so the incident model
    needs no migration then.
    """

    area_id: str
    zone_id: str | None
    at: datetime
    group_id: str | None = None
    profile_id: str | None = None
    severity: int | None = None


@dataclass(frozen=True, slots=True)
class Acknowledgement:
    """Who acknowledged, and how: an explicit command or a disarm (§7.2)."""

    at: datetime
    channel: str | None
    via: str  # "acknowledge" | "disarm"


@dataclass(frozen=True, slots=True)
class Incident:
    """The unit of an intrusion alarm, not the zone (SPEC §5.6).

    ``acknowledged`` is the current state; ``acknowledgements`` is the whole
    history, because a zone that joins after an acknowledgement clears it
    (part 2 decision 8) and both must stay on record. ``actions_started``
    records the actions this incident has set running, so that part 3 can
    union new ones without restarting them.
    """

    id: str
    opened_at: datetime
    contributors: tuple[Contributor, ...] = ()
    acknowledged: bool = False
    acknowledgements: tuple[Acknowledgement, ...] = ()
    actions_started: tuple[str, ...] = ()

    @property
    def area_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.area_id for c in self.contributors))

    @property
    def zone_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.zone_id for c in self.contributors if c.zone_id))


@dataclass(frozen=True, slots=True)
class Activation:
    """One activation held in a verification window (SPEC §4.2, §4.8).

    ``held`` is True when a group suppresses its members: the activation did
    nothing on its own and fires if the group is satisfied in time.
    """

    zone_id: str
    at: datetime
    held: bool = False


@dataclass(frozen=True, slots=True)
class PendingRun:
    """The rest of a profile's action list, held by a ``delay`` step (§6.2).

    It is state, not a task: the scheduler wakes at ``due`` and the engine
    emits the remaining actions, so a restart in the middle of a sequence
    resumes it instead of losing it (INV-3, part 3 decision 5). Everything the
    actions need is here, because the profile may have been edited since.
    """

    id: str
    profile_id: str
    moment: Moment
    index: int  # the next action in the profile's list
    due: datetime
    area_id: str | None = None
    zone_id: str | None = None
    incident_id: str | None = None
    silent: bool = False
    placeholders: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "placeholders", _frozen(self.placeholders))


@dataclass(frozen=True, slots=True)
class RunningAction:
    """Something an action switched on that must be switched off again.

    A siren with a duration, a switch with an auto-revert. Recorded so that a
    disarm and the siren cutoff can stop it (§6.2), so an incident does not
    restart what is already running (§5.6), and so a restart does not leave it
    on for ever (INV-3).
    """

    action_id: str
    kind: str
    entity_ids: tuple[str, ...]
    until: datetime | None = None
    restore: str | None = None  # the state a switch goes back to
    area_id: str | None = None
    incident_id: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeState:
    """Everything that must survive a restart (INV-3).

    ``active_zones`` remembers which zones count as triggered, because a numeric
    trigger inside its hysteresis band, or an entity in fault, keeps whatever it
    was before. ``seen_zones`` are the zones read at least once: a zone's first
    readable value is its baseline, not an activation, so adding a key switch
    that is already on does not arm the house. ``faults`` holds the zones
    already announced as faulted, so each fault is announced once.

    ``technical`` is the technical channel's own state (§5.5): it never
    appears in an area. ``windows`` holds the activations of every
    verification window still open, keyed by core.verification; they expire
    through next_wakeup like any timer.
    """

    areas: Mapping[str, AreaRuntime] = field(default_factory=dict)
    active_scenario_id: str | None = None
    bypassed: Mapping[str, BypassReason] = field(default_factory=dict)
    active_zones: frozenset[str] = frozenset()
    seen_zones: frozenset[str] = frozenset()
    faults: frozenset[str] = frozenset()
    technical: Mapping[str, TechnicalAlarm] = field(default_factory=dict)
    incident: Incident | None = None
    incident_seq: int = 0
    windows: Mapping[str, tuple[Activation, ...]] = field(default_factory=dict)
    chime_enabled: bool = True
    # When a timed manual bypass ends. A manual bypass without an entry here
    # lasts until the area is disarmed (part 3 decision 10).
    bypass_until: Mapping[str, datetime] = field(default_factory=dict)
    pending_runs: tuple[PendingRun, ...] = ()
    running: tuple[RunningAction, ...] = ()
    run_seq: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "areas", _frozen(self.areas))
        object.__setattr__(self, "bypassed", _frozen(self.bypassed))
        object.__setattr__(self, "technical", _frozen(self.technical))
        object.__setattr__(self, "windows", _frozen(self.windows))
        object.__setattr__(self, "bypass_until", _frozen(self.bypass_until))

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

    ``timezone`` is the installation's, for anything read on the wall clock
    (chime quiet hours, and part 3's time conditions): the engine is given
    it like the clock, never looks it up.
    """

    state: RuntimeState
    entities: Mapping[str, EntityState]
    settling: bool = False
    timezone: tzinfo = UTC

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


@dataclass(frozen=True, slots=True)
class AcknowledgeIncident:
    """Acknowledge the open intrusion incident (SPEC §5.6)."""

    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class AcknowledgeTechnical:
    """Acknowledge every technical alarm pending now (§5.5, part 2 decision 11).

    A separate command from the incident's on purpose: a different channel,
    a different acknowledgement (§5.5).
    """

    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class BypassZone:
    """Exclude a zone by hand, or let it back in (§5.4, SPEC §16).

    ``seconds`` makes it a timed temporary bypass: the zone rejoins on its own
    when the time is up, with a notification, because a zone excluded and
    forgotten is exactly the window somebody comes through.
    """

    zone_id: str
    bypass: bool = True
    seconds: int | None = None
    code: str | None = None
    channel: str = "api"


@dataclass(frozen=True, slots=True)
class SetChime:
    """switch.foyer_chime: silence the chime, or let it sound again (§6.6)."""

    enabled: bool
    channel: str = "api"


Event = (
    ArmRequest
    | ArmModeRequest
    | ArmAreaRequest
    | DisarmRequest
    | ZoneStateChanged
    | Tick
    | Startup
    | AcknowledgeIncident
    | AcknowledgeTechnical
    | BypassZone
    | SetChime
)


# --- decision ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Occurrence:
    """One thing that happened, with enough context for a log row and a message.

    ``incident_id`` is set on every occurrence that belongs to the open
    incident, so the log can be read as "what happened that night" (§5.6).
    ``group_id`` names the verification group involved, when one is.
    """

    moment: Moment
    area_id: str | None = None
    zone_id: str | None = None
    scenario_id: str | None = None
    zone_ids: tuple[str, ...] = ()
    channel: str | None = None
    detail: Mapping[str, str] = field(default_factory=dict)
    incident_id: str | None = None
    group_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", _frozen(self.detail))


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """An action that *should* run. The executor decides nothing about it.

    ``params`` carries what the executor needs and must not look up itself,
    such as the chime's targets: the Decision is the whole instruction.
    """

    action_id: str
    kind: str
    moment: Moment
    # Which profile decided this, for the log and the simulator's trace.
    profile_id: str | None = None
    placeholders: Mapping[str, str] = field(default_factory=dict)
    # A variant of the message, e.g. "area" for an area armed outside any
    # scenario, which has no scenario name to show.
    variant: str | None = None
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "placeholders", _frozen(self.placeholders))
        object.__setattr__(self, "params", _frozen(self.params))


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
