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


class ContactChannelKind(StrEnum):
    """What a contact's channel is, for the person reading page 6 (SPEC §7.1).

    Foyer does not act on it: a channel is a `notify.*` service and whatever
    that service needs, and §1.2 is explicit that the transport is Home
    Assistant's job. The kind is what the address book shows beside the
    service, so "Luca, push then SMS then a call" reads as an order of
    priority rather than as three service names.
    """

    PUSH = "push"
    SMS = "sms"
    VOICE = "voice"
    CHAT = "chat"
    OTHER = "other"


class EscalationKind(StrEnum):
    """What is escalating. Two things do, and they never merge (§5.5, §5.6).

    An intrusion incident has one escalation, and the technical channel has
    "its own escalation, independent of any intrusion incident", with its own
    acknowledgement. Nothing else escalates (part 1 decision 2): a profile
    answering ``armed`` or ``zone_fault`` runs its actions and is done, and
    there is nothing there for anybody to acknowledge.
    """

    INCIDENT = "incident"
    TECHNICAL = "technical"


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

# How a notification carries the camera picture. There is no single answer:
# each transport reads its own key out of `data`, and a key it does not know
# is discarded in silence — which is what "I attached a camera and nothing
# arrived" looks like from the outside.
#
# `companion`  Home Assistant's own app: `image`, a link to the authenticated
#              camera proxy. The app is signed in, so it fetches the live
#              picture itself and nothing is written to disk.
# `telegram`   telegram_bot: `photo`, and it must be a FILE. Telegram's server
#              does the fetching, from outside the house, with no session —
#              so a relative proxy path is unreachable to it by construction.
#              Foyer takes the snapshot at the moment of the notification.
ATTACH_COMPANION = "companion"
ATTACH_TELEGRAM = "telegram"
NOTIFY_ATTACHMENTS: tuple[str, ...] = (ATTACH_COMPANION, ATTACH_TELEGRAM)


class NotifyImages(StrEnum):
    """Which pictures a notify action carries (§6.2.1, decision 92).

    ``NONE`` carries nothing. ``FIXED`` is the one camera the action names,
    exactly as before §6.2.1 existed. ``ZONE`` is the cameras of the zones
    behind the alarm — every zone of the incident, or every technical zone
    pending — at the moments that are an alarm and at no other.
    """

    NONE = "none"
    FIXED = "fixed"
    ZONE = "zone"


# At most this many cameras per notification (§6.2.1, decision 95). The bound
# is what keeps "every zone, every time" from burying the message it came
# with; past it, the message says how many were left out.
MAX_NOTIFY_CAMERAS = 4


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
    EDIT_CONFIG = "edit_config"
    # The last two have no caller until Phase 3 builds walk test and the real
    # action test. The policy of §8.2 is complete here on purpose: the table
    # is one thing, and half a table is how a setting quietly goes missing.
    WALK_TEST = "walk_test"
    TEST_ACTION = "test_action"
    # Cancelling an automatic rule's grace countdown (§9.4, part 2 decision
    # 3). Its own entry, defaulting to no code, for the shape of decision 77:
    # the button travels in a push and no push carries a code, so demanding
    # one by default would be a button that never works — but an installation
    # can raise it, and then the button refuses visibly rather than lying.
    # The rule itself is outside the policy entirely (part 2 decision 9):
    # nobody is there to be asked, and the authorisation happened when
    # somebody with edit_config saved the rule.
    CANCEL_AUTO_ACTION = "cancel_auto_action"


class Permission(StrEnum):
    """What a user is allowed to do at all (SPEC §8.3).

    Separate from the code policy: the policy asks whether this operation
    needs a code, a permission asks whether this person may ask for it. A
    permission the UI hides must still be refused when the command is sent
    by hand, which is why the check lives here and not in the panel.
    """

    ARM = "arm"
    DISARM = "disarm"
    FORCE_ARM = "force_arm"
    BYPASS_ZONE = "bypass_zone"
    CHANGE_SCENARIO = "change_scenario"
    EDIT_CONFIG = "edit_config"
    VIEW_LOG = "view_log"
    TEST_ACTIONS = "test_actions"
    WALK_TEST = "walk_test"
    MANAGE_USERS = "manage_users"


class CodeResult(StrEnum):
    """What the backend made of the code that came with a request.

    The engine is never given a code (INV-2): ``security/`` verifies it and
    the engine is told only this. ``NONE`` means nothing was supplied, which
    is not a failed attempt and never counts towards a lockout.
    """

    NONE = "none"
    VALID = "valid"
    INVALID = "invalid"


class LogCategory(StrEnum):
    """How the log groups what it records (SPEC §10.2).

    The last two are zone activity, split by whether the zone's area was
    watching it: ``zone_disarmed`` is the one category that is off by default,
    because a living-room PIR produces thousands of rows a day and thirty days
    of them bury every event that matters.
    """

    ARMING = "arming"
    ALARM = "alarm"
    ACTION = "action"
    CONFIG = "config"
    SECURITY = "security"
    SYSTEM = "system"
    ZONE_ARMED = "zone_armed"
    ZONE_DISARMED = "zone_disarmed"


class LogSeverity(StrEnum):
    """How loud a row is (SPEC §10.1). Only ``alarm`` means the house fired."""

    INFO = "info"
    WARNING = "warning"
    ALARM = "alarm"


class Outcome(StrEnum):
    """What became of the request a row records (SPEC §10.1)."""

    OK = "ok"
    BLOCKED = "blocked"
    BAD_CODE = "bad_code"
    FAILED = "failed"


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
    # One area's alarm is over: its siren cutoff ran, or it was disarmed with
    # its alarm memory set and the cutoff had not run yet. Raised once per
    # alarm per area, and never on an ordinary disarm (decision 105): the
    # moment for "switch the light off when the alarm is over", which the
    # incident's acknowledgement — belonging to no area — cannot serve.
    ALARM_ENDED = "alarm_ended"
    # A disarm cleared an area's alarm memory, whenever the alarm itself
    # ended (decision 108): the lamp that says "something happened while you
    # were out" goes off here, not at the cutoff hours earlier.
    ALARM_CLEARED = "alarm_cleared"
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

    # Somebody pressed the test button beside an action (§11.4). Not a
    # profile moment and never offered as one: nothing happened in the
    # house, and a profile answering a test by sounding the siren would be a
    # loop. It exists so the row the test leaves is filed as a test rather
    # than as the alarm it imitates.
    ACTION_TESTED = "action_tested"

    # A zone's battery has fallen below the threshold (§4.2, §6.1). Raised
    # once on the way down, like a fault, and cleared silently when the
    # battery is replaced: "the cell is fine again" is not news.
    LOW_BATTERY = "low_battery"

    # A disarm with a duress code (§8.1). Silent by definition: the house
    # behaves exactly as it does on an ordinary disarm, and this is the only
    # trace, for the log and for a profile that alerts somebody quietly.
    DURESS = "duress"

    # Moments no phase produces yet. They exist so a profile can be written
    # against them now and keep working when the phase that raises them lands;
    # the editor says which phase each one waits for.
    CODE_REJECTED = "code_rejected"
    LOCKOUT = "lockout"
    WALK_TEST_STARTED = "walk_test_started"  # Phase 3
    WALK_TEST_ENDED = "walk_test_ended"  # Phase 3
    ESCALATION_EXHAUSTED = "escalation_exhausted"

    # Steps that fell due while Home Assistant was down and were not sent
    # (part 1 decision 5). Not a profile moment and never offered as one:
    # there is no useful answer to "a notification did not go out four hours
    # ago" other than the row saying so, and the escalation is still running
    # for the steps that are still ahead.
    ESCALATION_SKIPPED = "escalation_skipped"

    # Automatic arming rules (§9.4). None of these is a profile moment and
    # none is ever offered as one: a rule's announcement goes to the contacts
    # the rule names (part 2 decision 2), and what the rule *did* is already
    # an `armed` or a `disarmed` carrying `channel: auto_rule`. These exist so
    # that the log can answer "why did it not arm last night?", which is the
    # one question §9.4 says silence must never be the answer to.
    AUTO_PENDING = "auto_pending"  # the countdown started
    AUTO_CANCELLED = "auto_cancelled"  # somebody pressed Cancel
    AUTO_BLOCKED = "auto_blocked"  # a guard, a suspension, the switch
    AUTO_SUSPENSION_SET = "auto_suspension_set"
    AUTO_SUSPENSION_CLEARED = "auto_suspension_cleared"
    AUTO_ARMING_SWITCHED = "auto_arming_switched"

    # System health (§12). A separate concept from zones: "the mains are
    # down" is not an intrusion and never enters the intrusion queue
    # (decision 27). Each of these is state with no acknowledgement — it
    # clears when the cause clears, not when somebody looks at it — so each
    # raised moment has the matching one that says it is over. A profile can
    # answer any of them; there is nothing to acknowledge.
    SYSTEM_POWER_LOST = "system_power_lost"
    SYSTEM_POWER_RESTORED = "system_power_restored"
    NOTIFICATION_CHANNEL_DOWN = "notification_channel_down"
    NOTIFICATION_CHANNEL_RESTORED = "notification_channel_restored"
    WATCHDOG_UNREACHABLE = "watchdog_unreachable"
    WATCHDOG_RECOVERED = "watchdog_recovered"
    # Many zones on one radio went quiet at once while the coordinator kept
    # answering (§12.5). *Suspected*, and the word is load-bearing: a
    # coordinator crash, a firmware update, a Zigbee channel change and a
    # power cut to a room of mains-powered routers all look like this.
    RF_INTERFERENCE_SUSPECTED = "rf_interference_suspected"
    RF_INTERFERENCE_CLEARED = "rf_interference_cleared"
    # The same silence with the coordinator itself gone: a different fault
    # with a different fix, and conflating the two teaches people to ignore
    # both.
    RADIO_COORDINATOR_DOWN = "radio_coordinator_down"
    RADIO_COORDINATOR_UP = "radio_coordinator_up"


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
    # Part 2 of Phase 4: nothing is counting down, or the countdown the
    # button names has already run or been cancelled. A refusal, not silence:
    # somebody pressed Cancel and is owed an answer either way.
    NOTHING_TO_CANCEL = "nothing_to_cancel"
    UNKNOWN_RULE = "unknown_rule"
    UNKNOWN_SUSPENSION = "unknown_suspension"
    # Phase 2: identity. BAD_CODE is a code that was supplied and did not
    # match; CODE_REQUIRED is one the policy wanted and nobody supplied.
    # Neither ever says whose code it was, or how close it came.
    BAD_CODE = "bad_code"
    LOCKED_OUT = "locked_out"
    NOT_PERMITTED = "not_permitted"
    USER_NOT_VALID = "user_not_valid"
    AREA_NOT_ALLOWED = "area_not_allowed"
    SCENARIO_NOT_ALLOWED = "scenario_not_allowed"
    # Part 2: a device that is not on page 8. Refused before the code is even
    # considered, so a caller cannot learn which codes exist by trying them
    # from an invented device (part 2 decision 1).
    DEVICE_NOT_REGISTERED = "device_not_registered"
    # The device endpoint's credential was missing or wrong (§9.2.1). Only
    # ever written to the log: the caller is answered 401 with no detail.
    BAD_TOKEN = "bad_token"
    # The instance that received this request has been unloaded — a reload,
    # which every configuration save performs, or the integration going. It
    # is a refusal rather than an accepted nothing (found in review): a
    # disarm answered "success" while nothing happened is the one answer an
    # alarm may never give.
    NOT_LOADED = "not_loaded"
    # A walk test is running (§11.3). Every area is armed by it, and its end
    # disarms them all, so an arming now would be undone without a word: the
    # walk test is ended first, then the house is armed.
    WALK_TEST_ACTIVE = "walk_test_active"


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
# The longest a timed exclusion may last. A holiday's worth and then some: a
# number without a bound overflowed the clock inside `decide` (second
# review), and an exclusion measured in years is a zone switched off in all
# but name — which is what disabling it is for.
MAX_BYPASS_SECONDS = 30 * 24 * 3600
MIN_SUPERVISION_TIMEOUT = 60
MAX_SUPERVISION_TIMEOUT = 7 * 24 * 3600

# Walk test auto-exit (§5.3: global, 15 min, "mandatory, non-disableable").
# The window is pushed back by every detection, so a forty-zone house can be
# walked in one pass; MAX_WALK_TEST_TOTAL is the cap on the whole test,
# measured from the start and reachable by nothing (part 2 decision 4).
# `foyer.walk_test`'s `duration` may only ask for less than the configured
# window, never more (part 2 decision 5).
DEFAULT_WALK_TEST_TIMEOUT = 900
MIN_WALK_TEST_TIMEOUT = 60
MAX_WALK_TEST_TIMEOUT = 3600
MAX_WALK_TEST_TOTAL = 3 * 3600
# The cancellable countdown before an automatic rule acts (§9.4). 120 s for
# an arming, 0 for a disarming — the spec's own defaults, and the reason for
# the asymmetry is that an arming that surprises somebody is an annoyance they
# can stop, while a disarming nobody wanted is not improved by a warning.
DEFAULT_GRACE_SECONDS = 120
DEFAULT_DISARM_GRACE_SECONDS = 0
MAX_GRACE_SECONDS = 900
# How long a rule may hold a condition before acting, and how long a guard
# looks back for motion (§9.4). Minutes, because that is what the page asks
# for; the engine works in seconds like everything else.
MAX_RULE_MINUTES = 1440

# Verification windows: groups, cross-zone and trigger counting (§4.2, §4.8).
DEFAULT_VERIFICATION_WINDOW = 60
MIN_VERIFICATION_WINDOW = 1
MAX_VERIFICATION_WINDOW = 3600
MAX_TRIGGER_COUNT = 10

# What a numeric battery entity has to fall below to count as low (§4.2).
# 20 % is where alkaline and lithium cells in door contacts start reporting
# unreliably rather than where they die: the point of the warning is to be
# early enough to act on before a walk test finds the zone dead.
DEFAULT_LOW_BATTERY_THRESHOLD = 20
MIN_LOW_BATTERY_THRESHOLD = 1
MAX_LOW_BATTERY_THRESHOLD = 100

# System health (§12). Every number here was chosen rather than inherited,
# and the reasoning is in docs/system-health.md.
#
# The watchdog pings every quarter of an hour and gives up on one attempt
# after thirty seconds (§12.3). The interval is the trade the household
# makes: a shorter one tells the external service sooner that Home Assistant
# has died, a longer one costs less and matters less. Three consecutive
# failures — three quarters of an hour of silence — before Foyer says so
# locally, because a single blip on a domestic line is not news and an alarm
# that cries wolf about its own watchdog is an alarm nobody reads.
DEFAULT_WATCHDOG_INTERVAL = 900
MIN_WATCHDOG_INTERVAL = 60
MAX_WATCHDOG_INTERVAL = 86400
DEFAULT_WATCHDOG_TIMEOUT = 30
MIN_WATCHDOG_TIMEOUT = 5
MAX_WATCHDOG_TIMEOUT = 120
DEFAULT_WATCHDOG_FAILURES = 3
MIN_WATCHDOG_FAILURES = 1
MAX_WATCHDOG_FAILURES = 20

# RF interference (§12.5): N zones on one radio going quiet inside T seconds,
# gated on the coordinator still answering, and then still true after the
# confirmation window. The confirmation is what a coordinator reboot and a
# firmware update walk into instead of the siren.
DEFAULT_RF_ZONES = 4
MIN_RF_ZONES = 2
MAX_RF_ZONES = 50
# "or 40 % of the zones on that radio, whichever is lower" (§12.5).
RF_ZONE_FRACTION = 0.4
DEFAULT_RF_WINDOW = 60
MIN_RF_WINDOW = 5
MAX_RF_WINDOW = 3600
DEFAULT_RF_CONFIRM = 60
MIN_RF_CONFIRM = 0
MAX_RF_CONFIRM = 3600

# Notification channel health (§12.2). The sweep asks the service registry
# every quarter of an hour, which is a read in memory and costs nothing; two
# consecutive failed sends make a channel broken, because one failure is a
# provider with a hiccup and two is a pattern.
DEFAULT_CHANNEL_SWEEP = 900
MIN_CHANNEL_SWEEP = 60
MAX_CHANNEL_SWEEP = 86400
DEFAULT_CHANNEL_FAILURES = 2
MIN_CHANNEL_FAILURES = 1
MAX_CHANNEL_FAILURES = 10

# How long a problem has to last before it is worth a Home Assistant repair
# issue (§12.4). A zone that drops off for an hour is a flat battery being
# reported twice; a zone that has been gone for two days is a zone nobody has
# noticed, which is what Settings is for.
DEFAULT_REPAIR_AFTER = 2 * 24 * 3600

# Log retention (SPEC §10.3): per category, thirty days by default. Zero is
# not a value: "keep nothing" is what disabling the category is for.
DEFAULT_RETENTION_DAYS = 30
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 3650
# The one category off by default (§10.2): thousands of rows a day.
DEFAULT_LOG_DISABLED: frozenset[str] = frozenset({"zone_disarmed"})

# Codes (SPEC §8.1). The length is global because a keypad has to know how
# many digits to collect before it validates anything.
DEFAULT_CODE_LENGTH = 6
MIN_CODE_LENGTH = 4
MAX_CODE_LENGTH = 12

# Lockout (SPEC §8.4): N failures within W seconds lock the channel for L,
# growing exponentially each time it happens again.
DEFAULT_LOCKOUT_FAILURES = 5
DEFAULT_LOCKOUT_WINDOW = 300
DEFAULT_LOCKOUT_DURATION = 300
MIN_LOCKOUT_FAILURES = 2
MAX_LOCKOUT_FAILURES = 20
MIN_LOCKOUT_SECONDS = 10
MAX_LOCKOUT_SECONDS = 86400
# A lockout doubles on repetition up to this, so a keypad under attack does
# not end up locked for a fortnight while its owner stands in the rain.
MAX_LOCKOUT_BACKOFF = 3600
# Strikes fade: a channel that has behaved for a day starts again from the
# first step, or one bad night would punish the next month.
LOCKOUT_STRIKE_RESET = 86400

# The channels a request can arrive through (SPEC §9.1). Only some of them
# know who the person is without being told a code: on a shared keypad the
# code IS the identity, which is why the per-user exemption of §8.2 can never
# apply there. `nfc` is here for the per-user tag of part 2; a tag shared by
# the household is a keypad by another name and must be configured as one.
CHANNELS: tuple[str, ...] = (
    "ha_ui",
    "keypad",
    "nfc",
    "mqtt",
    "api",
    "automation",
    "key_zone",
    # §9.4: an automatic rule is a channel of its own, because the system is
    # acting as a user would and the log must be able to say so. It is the
    # engine's own word and never a claim a caller may make — §9.1 allows a
    # request to declare only `api` or `automation` (decision 84).
    "auto_rule",
)
IDENTIFYING_CHANNELS: frozenset[str] = frozenset({"ha_ui", "nfc"})

# Which channel a registered device speaks on (§9.3, part 2 decision 4). The
# channel is a property of the device, not a claim the message makes: it
# decides the lockout counter and whether the exemption of §8.2 may apply, so
# an automation writing `channel: nfc` must not be able to buy either.
DEVICE_CHANNELS: dict[str, str] = {"keypad": "keypad", "tag": "nfc"}

# MQTT (SPEC §9.2). Off until somebody turns it on: an alarm that starts
# listening on a broker nobody asked it to listen on is not a feature.
DEFAULT_MQTT_QOS = 1
MAX_MQTT_QOS = 2
# A topic is free text, but it is not free of rules: MQTT forbids wildcards in
# a topic you publish to or subscribe as a single destination, and an empty
# level is a topic nobody can debug.
MQTT_TOPIC_FORBIDDEN: frozenset[str] = frozenset({"+", "#"})
MAX_MQTT_TOPIC = 200


class RuleTriggerKind(StrEnum):
    """What an automatic rule watches (SPEC §9.4). A closed set of four.

    ``ABSENCE`` and ``ENTITY`` are conditions that stay true while they hold;
    ``PRESENCE`` and ``TIME`` happen once. See ``RuleTrigger.level``.
    """

    ABSENCE = "absence"
    PRESENCE = "presence"
    TIME = "time"
    ENTITY = "entity"


class RuleActionKind(StrEnum):
    """What an automatic rule does (SPEC §9.4). A closed set of three."""

    ARM = "arm"
    DISARM = "disarm"
    SWITCH = "switch"


class SuspensionKind(StrEnum):
    """The three ways automatic arming is held back (SPEC §9.4).

    ``UNTIL`` runs to a date and time, ``NEXT`` skips one occurrence of one
    rule, and ``VISITOR`` is the expected-visitor window: a named period —
    "09:00-13:00 tomorrow, Boiler engineer" — which may substitute a reduced
    scenario for the arming it suspends. Mechanically the same suspension; the
    difference is that in six months the log says *why*.
    """

    UNTIL = "until"
    NEXT = "next"
    VISITOR = "visitor"


class RuleBlock(StrEnum):
    """Why a rule that wanted to act did not (SPEC §9.4). Stable identifiers.

    Every one of these writes a row under ``system``: "why did it not arm last
    night?" is a question users ask, and silence is the worst possible answer.
    """

    SWITCH_OFF = "switch_off"  # switch.foyer_auto_arming is off
    SUSPENDED = "suspended"  # a suspension or a visitor window covers it
    WALK_TEST = "walk_test"  # a walk test is running (part 2 decision 11)
    NOT_DISARMED = "not_disarmed"
    NOT_READY = "not_ready"
    MOTION = "motion"
    # The rule would disarm, and automatic disarming has not been enabled
    # (§9.4 point 2). Not a UI default: the engine refuses it.
    AUTO_DISARM_DISABLED = "auto_disarm_disabled"
    # Every area the rule would disarm is a perimeter area (§9.4 point 3),
    # so there is nothing left for it to do.
    PERIMETER = "perimeter"
    # A disarm rule naming an area that no longer exists. Validation catches
    # it at save time, so this is what a deleted area leaves behind.
    UNKNOWN_AREA = "unknown_area"
    # The rule acted and the arming itself was refused for something a zone
    # can put right — an open window, a zone in fault. It tries again when
    # the areas it wants are ready, and not before: a rule that retried on a
    # timer would announce an arming every two minutes all night.
    NOT_READY_REFUSED = "not_ready_refused"
    # Refused for something no zone can put right: a scenario that has been
    # deleted, an alarm in progress, a permission. It waits like any rule
    # that has had its turn — until its condition goes false and true again.
    REFUSED = "refused"
    # An area the rule would disarm is in entry or already triggered. A rule
    # never silences an alarm: §4.6.1 says the same of a scenario switch, and
    # for the same reason — the siren stopping is a person saying they have
    # seen it, and a phone walking through the door is not that person.
    ALARM_IN_PROGRESS = "alarm_in_progress"
    # A `time` rule whose hour fell while Home Assistant was down. The row
    # exists because "why did it not arm last night?" has to have an answer
    # even when the answer is "nothing was running".
    MISSED = "missed"


class MqttDetail(StrEnum):
    """How much the retained state message says (§9.2, part 2 decision 3).

    The message is retained on a broker that is often shared, so everything in
    it is told to whoever connects next, including "the house is armed and
    nobody is in". The same reasoning as the watchdog's empty payload
    (decision 29), and the same answer: the least that still lets a keypad
    give feedback, with more available on request.

    ``MINIMAL``  master state, countdown, ready_to_arm, fault, last_result and
                 how many zones block arming — no names at all.
    ``STANDARD`` adds the active scenario and the per-area states, by name.
    ``FULL``     adds the open zones by name: §9.2 in full.
    """

    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class DeviceKind(StrEnum):
    """What a registered arming device is (SPEC §9.3).

    Two kinds, because two things decide everything that follows: whether a
    code can travel at all, and therefore which channel the request arrives on.

    ``KEYPAD`` is shared and carries a code, so the code is the identity
    (§8.2) and the channel is ``keypad``.
    ``TAG`` is a per-person token — an NFC tag, an RFID badge, a remote —
    where **possession is the credential** and no code exists to type. The
    channel is ``nfc``, it carries ``token=True``, and §9.3's plain statement
    holds: a stolen tag arms and disarms without knowing any code. The
    permissions and the validity window of the person it names still apply.
    """

    KEYPAD = "keypad"
    TAG = "tag"


class DeviceTransport(StrEnum):
    """How a keypad reaches the house, one and only one (§9.2.1, decision 98).

    ``MQTT`` is the broker, where a keypad is the name it gives (decision 81).
    ``HTTP`` is the device endpoint, where it is a token of its own — and
    then its name is refused on every other path, or whoever knows the name
    reaches the house through the broker and the token protects nothing.
    """

    MQTT = "mqtt"
    HTTP = "http"


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
    # Who the log attributes a turn of this key to (§4.7). A key carries no
    # code, so this is the only identity it can have — and a key nobody owns
    # is exactly the row that makes the log unreadable six months later.
    user_id: str | None = None


@dataclass(frozen=True, slots=True)
class ArmingDevice:
    """A thing that may command the alarm, declared before it may (SPEC §9.3).

    Page 8 is a white list, not an address book (part 2 decision 1): a
    ``device_id`` this configuration does not carry is refused, whatever code
    it brings, and the refusal is recorded and shown. The reason is narrow and
    worth stating — the lockout of §8.4 counts per channel and device, so a
    caller free to invent a device id is a caller free never to be locked out.

    A **keypad** is shared: it sends a ``device_id`` in its messages, carries a
    code, and the code is the identity. A **tag** is a person's: it is backed
    by a ``tag.*`` or ``event.*`` entity, it carries no code at all, and the
    identity is the ``user_id`` written here, exactly as a key zone's is
    (§4.7). ``ref`` is what a keypad puts in its messages; for a tag it is
    unused, because a scan arrives as a state change and not as a message.
    """

    id: str
    name: str
    kind: DeviceKind
    # What the device calls itself over MQTT or in a service call. Unique
    # across devices: two keypads answering to one name would share a lockout
    # counter and a line in the log that names neither.
    ref: str | None = None
    # A tag only: the entity a scan arrives on, and which event counts when
    # the entity is an `event.*` with more than one button.
    entity_id: str | None = None
    event_type: str | None = None
    # A tag only: whose it is, and what a scan does. Possession is the
    # credential, so this is the whole of the identity (§9.3).
    user_id: str | None = None
    command: KeyCommand = KeyCommand.TOGGLE
    scenario_id: str | None = None
    enabled: bool = True
    # A keypad only: the one path it may speak on (§9.2.1, decision 98).
    transport: DeviceTransport = DeviceTransport.MQTT
    # A keypad on the endpoint only: the SHA-256 of its token, hex. A random
    # token needs no slow hash, a guessed code does. Never returned by any
    # API, never in a backup or the diagnostics, never set by a restore — the
    # same treatment as the acknowledgement webhook (§9.2.1).
    token_hash: str | None = None

    @property
    def channel(self) -> str:
        return DEVICE_CHANNELS[self.kind.value]

    @property
    def token(self) -> bool:
        """Is possession the credential? Then no code can travel (§9.3)."""
        return self.kind is DeviceKind.TAG


@dataclass(frozen=True, slots=True)
class MqttSettings:
    """The MQTT contract's own settings (SPEC §9.2).

    Topics are configurable and not fixed, because people run more than one
    site against one broker and people have a topic hierarchy they are not
    going to restructure for a new integration. Empty means the default,
    ``foyer/<install_id>/…``, which the runtime resolves: storing the resolved
    value would freeze an installation id into a document that gets exported
    and imported elsewhere.
    """

    enabled: bool = False
    command_topic: str = ""
    state_topic: str = ""
    detail: MqttDetail = MqttDetail.MINIMAL
    # Retained, as §9.2 asks: a keypad that reboots needs the state without
    # having to ask for it. It is also why `detail` defaults to the least.
    retain: bool = True
    qos: int = DEFAULT_MQTT_QOS


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
    # The entity reporting this zone's battery, for diagnostics and the
    # low_battery moment (§4.2, §11.1). A `binary_sensor` is low when it is
    # on; a numeric `sensor` is low below the global threshold. It is read
    # separately from the zone's own entity on purpose: a contact that is
    # answering is not blind because its battery is at 15 %, so a low battery
    # warns and never blocks (Phase 3 part 1 decision 2). A battery entity
    # that cannot be read at all is a different matter and is a fault: it is
    # the sensor saying nothing about itself, which is INV-4 exactly.
    battery_entity_id: str | None = None
    # Whether somebody has confirmed the trigger against the real sensor
    # (INV-5). Every zone saved from the editor is, because the editor will not
    # save one that is not. A zone that arrives any other way — brought across
    # by an importer from a system that assumed `on` means alarm — carries a
    # proposal nobody has checked, and a zone like that may exist only switched
    # off: validation refuses it enabled, so it watches nothing until somebody
    # has looked (Phase 5 part 3 decision 4).
    trigger_confirmed: bool = True
    # The cameras that show this zone and the rooms around it, in the order
    # the household wants them (§6.2.1, decision 91). A notification set to
    # show the zone's cameras attaches these; the zone decides *where*.
    camera_entity_ids: tuple[str, ...] = ()


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

# How far from the start of an escalation a step may sit (§7.2). An hour is
# past the point where a step is still about this alarm: the neighbour of the
# spec's own example is reached at five minutes, and an installation that
# wants somebody told tomorrow wants an automation, not a step.
MAX_ESCALATION_OFFSET = 3600

# How late a step may be and still go out (part 1 decision 5). Steps that fell
# due while Home Assistant was down are skipped and recorded, because a
# notification four hours late is worse than none — but saving a setting
# reloads the integration, and a step lost to that would be a push nobody
# ever gets and nobody can explain. Sixty seconds is the same line
# journal.RELOAD_GAP_SECONDS draws between a reload and an outage.
ESCALATION_RESTART_GRACE = 60


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
    # Seconds from the start of the escalation, or None for an ordinary
    # action (§7.2, part 1 decision 1). An escalation step **is** an action:
    # the same notify, with the same conditions and the same contacts, put at
    # an offset instead of at once. The offset is the only thing that makes
    # it a step, so there is one editor, one executor and one trace line.
    #
    # An action carrying one is run by the escalation and never by the
    # ordinary sequence: see response.sequence(), which is the one place that
    # takes it out, so nothing can run a step twice.
    escalation_offset: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", _frozen(self.params))

    @property
    def is_step(self) -> bool:
        return self.escalation_offset is not None


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


class HealthCause(StrEnum):
    """Why ``binary_sensor.foyer_system_health`` is on (SPEC §13, §12).

    The causes are attributes of one entity rather than five entities,
    because the question a dashboard asks is "is anything wrong", and the
    answer to "what" belongs on page 14 where there is room to say it.
    """

    ZONE_FAULT = "zone_fault"
    MAINS_LOST = "mains_lost"
    # The mains entity itself cannot be read (INV-4). Deliberately not
    # "mains lost": a UPS integration that has not loaded yet would otherwise
    # announce a power cut at every restart. It carries no moment of its own
    # — there is nothing here for a response profile to do that answering a
    # power cut would not do wrongly — and it is visible on the health
    # sensor, on page 14 and in the diagnostics dump, which is where somebody
    # looking for "why does it not see my UPS" will be.
    MAINS_UNKNOWN = "mains_unknown"
    CHANNEL_DOWN = "channel_down"
    WATCHDOG_UNREACHABLE = "watchdog_unreachable"
    RF_INTERFERENCE = "rf_interference"
    COORDINATOR_DOWN = "coordinator_down"


class ChannelFault(StrEnum):
    """What is wrong with a notification channel (SPEC §12.2).

    Two different certainties, and the panel says which: a service that is
    not in the registry cannot possibly work, while a run of failed sends is
    evidence. Keeping them apart is what lets the Contacts page say
    "integration removed" rather than "something went wrong".
    """

    MISSING_SERVICE = "missing_service"
    SEND_FAILED = "send_failed"


@dataclass(frozen=True, slots=True)
class Radio:
    """One radio integration whose zones are counted together (§12.5).

    ``entry_id`` is the Home Assistant config entry the radio *is*: Home
    Assistant has no general notion of a radio, and the config entry is the
    one thing every zone of one ZHA, Z-Wave JS or Zigbee2MQTT installation
    shares. Foyer derives the membership from it and never asks the household
    to assign forty zones by hand.

    ``coordinator_entity_id`` is named by hand, and it is the whole feature:
    eight sensors going quiet while the coordinator answers is interference,
    and eight sensors going quiet with the coordinator gone is a dead switch.
    Without it Foyer will not raise interference on this radio at all —
    guessing which entity is the coordinator would turn the gate that makes
    the heuristic useful into a second heuristic.
    """

    id: str
    name: str
    entry_id: str = ""
    coordinator_entity_id: str | None = None
    # Overrides for this radio, null meaning the global setting. A garden
    # with two beams on its own stick is not the house's forty contacts.
    n_zones: int | None = None
    window: int | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class WatchdogSettings:
    """The external watchdog (SPEC §12.3): a URL, pinged periodically.

    Tied to no vendor: healthchecks.io, Uptime Kuma, Cronitor or a URL
    somebody wrote themselves. If Home Assistant dies the pings stop and the
    external service raises the alarm, which is the only answer to a dead
    system being unable to report its own death.

    ``payload`` is off and stays off unless somebody turns it on, and the
    panel states the reason where the switch is (P-1, decision 29): a ping
    saying "armed, Night, nobody home" tells whoever holds the other end
    exactly when to come. The default heartbeat carries nothing at all.
    """

    enabled: bool = False
    url: str = ""
    interval: int = DEFAULT_WATCHDOG_INTERVAL
    timeout: int = DEFAULT_WATCHDOG_TIMEOUT
    failures: int = DEFAULT_WATCHDOG_FAILURES
    payload: bool = False


@dataclass(frozen=True, slots=True)
class HealthSettings:
    """What system health watches (SPEC §12). One block, like the chime.

    ``mains_entity_id`` is an entity picker and deliberately not a zone
    property. §12.1 is right that a UPS sensor is a zone of type
    ``technical`` and that the concept is what costs something — but §13
    wants one entity to know *which* zone the mains is, and answering that
    with a flag on a zone would mean a household that has no technical zone
    for it has no mains reading either. The picker works whether or not the
    same entity is also a zone; when it is, the zone keeps its own technical
    alarm and its own acknowledgement, unchanged.

    ``mains_lost_states`` is explicit for the reason INV-5 exists: a UPS
    binary sensor is ``on`` when the mains has failed, a smart plug's power
    sensor is ``off``, and a default that guesses produces a mains alarm that
    never fires. The zone wizard's rule applies here too — the panel proposes
    from the device class and the household confirms.
    """

    mains_entity_id: str | None = None
    mains_lost_states: tuple[str, ...] = ("on",)
    watchdog: WatchdogSettings = field(default_factory=WatchdogSettings)
    radios: tuple[Radio, ...] = ()
    rf_zones: int = DEFAULT_RF_ZONES
    rf_window: int = DEFAULT_RF_WINDOW
    rf_confirm: int = DEFAULT_RF_CONFIRM
    channel_sweep: int = DEFAULT_CHANNEL_SWEEP
    channel_failures: int = DEFAULT_CHANNEL_FAILURES
    repair_after: int = DEFAULT_REPAIR_AFTER

    def radio(self, radio_id: str | None) -> Radio | None:
        return next((r for r in self.radios if r.id == radio_id), None)

    def rf_threshold(self, radio: Radio, zones_on_radio: int) -> int:
        """N for this radio: the setting, or 40 % of its zones if that is lower.

        Never below two — one sensor going quiet is a flat battery, which is
        the sentence §12.5 opens with.
        """
        configured = radio.n_zones if radio.n_zones is not None else self.rf_zones
        # The floor applies to the fraction, not to the answer: without it a
        # radio with exactly two zones falls back to the configured four and
        # can never raise anything, which is the one size where two zones
        # dying together is the whole radio.
        fraction = max(MIN_RF_ZONES, int(zones_on_radio * RF_ZONE_FRACTION))
        return min(configured, fraction)

    def rf_window_of(self, radio: Radio) -> int:
        return radio.window if radio.window is not None else self.rf_window


@dataclass(frozen=True, slots=True)
class ContactChannel:
    """One way of reaching a contact (SPEC §7.1).

    ``service`` is any `notify.*` service, or a `notify` entity, present in
    the installation: Foyer discovers it from the service registry and does
    not know or care whether it is Twilio, Pushover, a GSM modem or Telegram
    (§1.2). ``target`` and ``data`` are whatever that transport needs — a
    phone number, a chat id, `priority: 2` — and travel untouched.

    ``actionable`` says the transport can carry a button that acknowledges
    the alarm: the Home Assistant Companion app can, an SMS cannot. It is
    declared rather than guessed from the service name, for the reason
    decision 90 already had: a transport discards a key it does not know
    without a word, so a guess is indistinguishable from working until the
    night it matters.
    """

    id: str
    kind: ContactChannelKind = ContactChannelKind.OTHER
    service: str = ""
    target: str = ""
    data: Mapping[str, Any] = field(default_factory=dict)
    actionable: bool = False
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", _frozen(self.data))


@dataclass(frozen=True, slots=True)
class Contact:
    """Somebody the house can reach, and in what order (SPEC §7.1).

    ``channels`` is ordered, highest priority first: the first enabled one is
    what a notification uses when nothing names another.

    ``quiet_start`` / ``quiet_end`` is a window during which only
    high-severity events reach this contact, and ``quiet_min_severity`` says
    what "high" means here (part 1 decision 3). The scale is the log's —
    info, warning, alarm (§10.1) — and not the profile's ``severity``, which
    §6.5 states is used for nothing but choosing an incident's escalation.
    The default is ``alarm``: inside the window a break-in gets through and a
    successful arming does not.

    ``linked_user_id`` is what makes "who acknowledged" answerable when the
    answer arrives from a push notification rather than from a code.
    """

    id: str
    name: str
    channels: tuple[ContactChannel, ...] = ()
    quiet_start: str | None = None
    quiet_end: str | None = None
    quiet_min_severity: LogSeverity = LogSeverity.ALARM
    linked_user_id: str | None = None
    enabled: bool = True

    def channel(self, channel_id: str | None) -> ContactChannel | None:
        """The named channel, or the highest-priority enabled one."""
        if channel_id is None:
            return next((c for c in self.channels if c.enabled), None)
        return next(
            (c for c in self.channels if c.id == channel_id and c.enabled), None
        )


@dataclass(frozen=True, slots=True)
class RuleTrigger:
    """What makes an automatic rule want to act (SPEC §9.4).

    A closed set of four, not an automation engine: the same boundary §6.3
    draws for an action's conditions. ``entity_ids`` are the people for
    ``absence`` and ``presence`` and the one entity for ``entity``;
    ``minutes`` is how long the condition must hold, and ``at`` with
    ``weekdays`` is the wall clock for ``time``.

    ``absence`` and ``entity`` describe a state of the world that stays true,
    and ``time`` and ``presence`` describe something that happens once. That
    difference is not cosmetic: it decides whether a rule a guard blocked acts
    two minutes later or has missed its turn (part 2 decision 4).
    """

    kind: RuleTriggerKind
    entity_ids: tuple[str, ...] = ()
    state: str | None = None  # entity: the state it must hold
    minutes: int = 0  # absence, entity: for how long
    at: str | None = None  # time: "HH:MM"
    weekdays: tuple[int, ...] = ()  # time: 0 = Monday; empty = every day

    @property
    def level(self) -> bool:
        """True when this trigger is a condition rather than an instant."""
        return self.kind in (RuleTriggerKind.ABSENCE, RuleTriggerKind.ENTITY)


@dataclass(frozen=True, slots=True)
class RuleGuards:
    """The three reasons a rule declines to act (SPEC §9.4).

    Every one of them is a reason a user will ask about the next morning, so a
    guard that blocks writes a row under ``system`` — once, when the block
    begins, because a level trigger is re-evaluated at every wake-up and a row
    per wake-up would bury the log it belongs to (part 2 decision 4).
    """

    only_when_disarmed: bool = False
    only_when_ready: bool = False
    # No interior zone has detected motion for this many minutes. None is off.
    quiet_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class ActiveWindow:
    """When a rule exists at all (SPEC §9.4): outside it, it simply does not.

    ``after``/``before`` are "HH:MM" on the installation's own clock and may
    cross midnight, exactly as an action's time condition does (§6.3).
    """

    weekdays: tuple[int, ...] = ()  # empty = every day
    after: str | None = None
    before: str | None = None


@dataclass(frozen=True, slots=True)
class AutoRule:
    """One automatic arming rule (SPEC §9.4).

    A table, not a script. ``scenario_id`` is what ``arm`` and ``switch``
    target; ``area_ids`` is what ``disarm`` names — and never a perimeter
    area, which the engine enforces rather than the editor (§9.4 point 3).

    ``grace_seconds`` is the cancellable countdown: 120 s for an arming and 0
    for a disarming, by §9.4's defaults. ``notify_contact_ids`` is who hears
    the countdown and holds the Cancel button (part 2 decision 2) — the rule
    carries its own targets, as the chime does (decision 60), because the
    announcement is a property of the rule rather than the house answering
    something that happened to it.
    """

    id: str
    name: str
    trigger: RuleTrigger
    action: RuleActionKind
    scenario_id: str | None = None
    area_ids: tuple[str, ...] = ()
    window: ActiveWindow = field(default_factory=ActiveWindow)
    guards: RuleGuards = field(default_factory=RuleGuards)
    grace_seconds: int = DEFAULT_GRACE_SECONDS
    notify_contact_ids: tuple[str, ...] = ()
    enabled: bool = True


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
    # None inherits the global policy (§8.2). Where an area and a scenario
    # disagree the strictest explicit setting wins (decision 80).
    require_code_to_arm: bool | None = None
    require_code_to_disarm: bool | None = None
    # The outer defence ring (§4.5). An automatic rule never disarms it,
    # whatever the rule says and whichever action it uses: whoever walks in on
    # a stolen phone still finds every external door and window protected
    # (§9.4 point 3). Enforced in the engine, with its own regression test.
    is_perimeter: bool = False


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
    require_code_to_arm: bool | None = None
    require_code_to_disarm: bool | None = None
    # Who may use this scenario at all. None = everyone with the permission;
    # an empty tuple is a scenario nobody may arm, which validation refuses.
    allowed_user_ids: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class User:
    """A person, their code and what they may do (SPEC §8.1).

    Every user has their own code, and that is not a convenience: a shared
    code makes "who disarmed at 03:14?" unanswerable and turns the audit log
    into decoration. The hashes are written through the API and never
    returned by it, in any shape, to anyone.

    ``duress_code_hash`` disarms exactly as the ordinary code does and raises
    a silent event; nothing about the response may betray that it was used.

    ``code_exempt_when_identified`` is the per-user override of §8.2, off by
    default: it applies only on channels that identify the user by themselves,
    never on a shared keypad, where the code *is* the identity.
    """

    id: str
    name: str
    code_hash: str | None = None
    duress_code_hash: str | None = None
    ha_user_id: str | None = None
    permissions: frozenset[str] = frozenset()
    allowed_area_ids: tuple[str, ...] | None = None
    allowed_scenario_ids: tuple[str, ...] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    code_exempt_when_identified: bool = False
    enabled: bool = True
    # The stable opaque identifier a pseudonymised log row carries instead of
    # this person's name (§10.4, part 2 decision 4). Minted once when the
    # person is created and never recomputed: "the same person disarmed on
    # both nights" has to survive a rename, a year and a configuration
    # change, and a counter anchored to configuration order would renumber
    # everyone behind whoever was deleted.
    pseudonym: str | None = None

    def may(self, permission: str) -> bool:
        return permission in self.permissions

    def in_window(self, now: datetime) -> bool:
        """Inside the validity window, if there is one (guest codes, §8.1)."""
        if self.valid_from is not None and now < self.valid_from:
            return False
        return not (self.valid_until is not None and now > self.valid_until)

    def usable(self, now: datetime) -> bool:
        """Enabled, holding a code, and inside its validity window.

        This is what puts the policy in force (decision 78): a user somebody
        started creating and has not given a code to cannot verify anything,
        so they cannot make the house ask for one either.
        """
        return self.enabled and bool(self.code_hash) and self.in_window(now)


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    """Global code and lockout settings (SPEC §8.1, §8.4)."""

    code_length: int = DEFAULT_CODE_LENGTH
    lockout_failures: int = DEFAULT_LOCKOUT_FAILURES
    lockout_window: int = DEFAULT_LOCKOUT_WINDOW
    lockout_duration: int = DEFAULT_LOCKOUT_DURATION


@dataclass(frozen=True, slots=True)
class CodePolicy:
    """Whether each operation requires a code (SPEC §8.2).

    The defaults are that table's, which is what real panels do: arming the
    house you are standing in needs nothing, everything that lowers the guard
    needs a code. Acknowledging is the one the spec does not list, and it
    needs none (decision 77) because §7.2 already acknowledges from a push
    notification that carries no code.

    The policy is enforced server-side and nowhere else (INV-2), and it is
    inert while nobody holds a code (decision 78): see core.authz.
    """

    arm: bool = False
    disarm: bool = True
    force_arm: bool = True
    change_scenario: bool = True
    acknowledge: bool = False
    bypass_zone: bool = True
    edit_config: bool = True
    walk_test: bool = True
    test_action: bool = True
    # Cancelling an automatic rule's countdown (§9.4). No code, for the same
    # reason acknowledging needs none: the button lives in a push
    # notification, and no push carries a code. An installation may raise it,
    # and the button then refuses where somebody can see it refuse.
    cancel_auto_action: bool = False

    def requires_code(self, operation: Operation) -> bool:
        return bool(getattr(self, operation.value))


@dataclass(frozen=True, slots=True)
class LogSettings:
    """Which categories the log writes, and for how long (SPEC §10.2, §10.3).

    Both are sparse maps over ``LogCategory``: a category the user has never
    touched follows the documented default, so a new category added by a later
    version needs no migration to behave as the spec says it should.
    """

    enabled: Mapping[str, bool] = field(default_factory=dict)
    retention_days: Mapping[str, int] = field(default_factory=dict)
    # After how many days a row keeps a stable opaque identifier instead of a
    # name (§10.4). None is off, and off is the default: this trades away the
    # ability to answer "who disarmed that night" for rows older than N days,
    # which is the very question the log exists to answer. A real trade, not a
    # free safety feature, and the panel says so before the switch.
    pseudonymise_after: int | None = None
    # Whether removing the integration takes the log database with it (§16).
    # Off, so an installation that never answered keeps its history: §16 says
    # to ask rather than guess, and "keep" is the only answer that cannot
    # destroy something nobody meant to destroy (part 2 decision 9).
    delete_on_uninstall: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _frozen(self.enabled))
        object.__setattr__(self, "retention_days", _frozen(self.retention_days))

    def is_enabled(self, category: str) -> bool:
        return bool(self.enabled.get(category, category not in DEFAULT_LOG_DISABLED))

    def retention(self, category: str) -> int:
        return int(self.retention_days.get(category, DEFAULT_RETENTION_DAYS))


@dataclass(frozen=True, slots=True)
class Settings:
    """Global settings the engine reads.

    ``default_profile_id`` is the end of every inheritance chain (§6);
    ``technical_profile_id`` is the technical channel's own default, separate
    because a smoke alarm must not respond differently depending on how the
    house is armed (part 3 decision 2). ``silent_suppresses`` names the action
    kinds a ``silent`` zone does not run (decision 6); ``log`` is what the
    event log writes and keeps (§10.2).
    """

    siren_duration: int = DEFAULT_SIREN_DURATION
    arm_hold_timeout: int = DEFAULT_ARM_HOLD_TIMEOUT
    default_profile_id: str | None = None
    technical_profile_id: str | None = None
    silent_suppresses: tuple[str, ...] = DEFAULT_SILENT_SUPPRESSES
    camera_dir: str = DEFAULT_CAMERA_DIR
    log: LogSettings = field(default_factory=LogSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    mqtt: MqttSettings = field(default_factory=MqttSettings)
    # What new areas start with, so a household that wants 45 s sets it once.
    default_entry_delay: int = DEFAULT_ENTRY_DELAY
    default_exit_delay: int = DEFAULT_EXIT_DELAY
    # The language of what Foyer *sends out* — notifications, the spoken zone
    # name, the rendered log — not the panel's, which follows each Home
    # Assistant user. None means the language Home Assistant itself runs in.
    language: str | None = None
    # Whether the first-run wizard has been completed or dismissed (§15.1).
    # Installation state, not a preference: it belongs to the house, not to
    # whoever happens to open the panel.
    wizard_done: bool = False
    # Below what percentage a numeric battery entity counts as low (§4.2).
    # One setting for the installation rather than one field on each of forty
    # zones: the number is a property of the batteries a household buys, not
    # of the door they are behind (Phase 3 part 1 decision 1).
    low_battery_threshold: int = DEFAULT_LOW_BATTERY_THRESHOLD
    # How long a walk test runs without a detection before it ends itself
    # (§5.3, §11.3). Configurable because a bungalow and a farmhouse are not
    # the same walk, and capped in code because §5.3 calls the auto-exit
    # mandatory and non-disableable: there is no value here that switches it
    # off, and MAX_WALK_TEST_TOTAL bounds the whole test whatever this says.
    walk_test_timeout: int = DEFAULT_WALK_TEST_TIMEOUT
    # The webhook a voice provider posts a DTMF keypress to (§7.2), or None.
    # Off until somebody switches it on, and the reason is INV-6 rather than
    # taste: a Home Assistant webhook is not authenticated, so whoever holds
    # the URL can acknowledge an alarm in progress — which is to say, stop
    # the escalation that was on its way to the neighbour. It is one id,
    # long and random, generated when the feature is enabled and shown once;
    # the threat is written beside the switch and in
    # docs/notification-channels.md (part 1 decision 6).
    ack_webhook_id: str | None = None
    # Whether an automatic rule may leave the house less protected (§9.4
    # point 2). Off until somebody turns it on, and turning it on is where
    # the panel names the attack: a stolen phone disarms the house, GPS drift
    # of 200 metres disarms the house, a cloned MAC address on the home
    # network disarms the house. It gates every disarming action whatever the
    # trigger (part 2 decision 5), and a switch of scenario counts as one when
    # it would disarm anything (part 2 decision 6). It never reaches a
    # perimeter area, which nothing here can enable.
    allow_auto_disarm: bool = False


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
    users: tuple[User, ...] = ()
    devices: tuple[ArmingDevice, ...] = ()
    contacts: tuple[Contact, ...] = ()
    rules: tuple[AutoRule, ...] = ()
    health: HealthSettings = field(default_factory=HealthSettings)

    def rule(self, rule_id: str | None) -> AutoRule | None:
        return next((r for r in self.rules if r.id == rule_id), None)

    def contact(self, contact_id: str | None) -> Contact | None:
        return next((c for c in self.contacts if c.id == contact_id), None)

    def device(self, device_id: str | None) -> ArmingDevice | None:
        return next((d for d in self.devices if d.id == device_id), None)

    def device_by_ref(self, ref: str | None) -> ArmingDevice | None:
        """The device answering to the name a message put in ``device_id``.

        A disabled device is not found: switching one off must stop it
        commanding, not merely hide it from a list (part 2 decision 1).
        """
        if not ref:
            return None
        return next((d for d in self.devices if d.enabled and d.ref == ref), None)

    def user(self, user_id: str | None) -> User | None:
        return next((u for u in self.users if u.id == user_id), None)

    def user_of_ha(self, ha_user_id: str | None) -> User | None:
        if ha_user_id is None:
            return None
        return next((u for u in self.users if u.ha_user_id == ha_user_id), None)

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
    # Who armed it. The ``armed`` record is written when the exit delay ends,
    # long after the request, so the person has to be remembered here or the
    # log says an area armed itself. The device is remembered for the same
    # reason and answers a different question: which keypad, of the three.
    user_id: str | None = None
    device_id: str | None = None
    # Whether that name was claimed rather than established (decision 88).
    # Remembered for the same reason the name is.
    claimed: bool = False
    # Armed with no exit delay at all (§9.1). Remembered for the same reason
    # as `forced`: the row that says so is written when the area reaches
    # `armed`, and "why did it sound while I was still in the hall?" is a
    # question the log has to be able to answer.
    skipped_exit: bool = False
    # Which automatic rule armed this area (§9.4), remembered for exactly the
    # reason the user is: the ``armed`` row is written when the exit delay
    # ends, and "the rule's name recorded on every event" has to survive the
    # thirty seconds in between.
    rule_id: str | None = None
    rule_name: str | None = None


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
    """Who acknowledged, and how (§7.2).

    Four paths reach here: an explicit command, a disarm, a button in an
    actionable push notification and a DTMF keypress the voice provider fed
    back. Every one of them records who and through which channel, which is
    what §7.2 asks for — and when the push went to a contact who names no
    Foyer user, ``contact_id`` is the whole of the answer and ``user_id`` is
    empty (part 1 decision 7). A row that says "the push channel of Luca,
    nobody named" is honest; one that invented a person would not be.
    """

    at: datetime
    channel: str | None
    via: str  # "acknowledge" | "disarm" | "push" | "dtmf"
    user_id: str | None = None
    user_name: str | None = None
    contact_id: str | None = None


@dataclass(frozen=True, slots=True)
class Escalation:
    """An escalation in progress (SPEC §7.2). Persisted: INV-3 names it.

    ``profile_id`` is the policy in force — for an incident, the one
    belonging to the highest-severity contributing profile (§5.6), which can
    change while the incident grows. ``started_at`` is what every step's
    offset is measured from, so a policy adopted late finds its early steps
    already due and runs them at once rather than starting the clock again.

    ``done`` holds the action ids already reached, so a restart resumes where
    the escalation was instead of beginning again (INV-3). What it does *not*
    hold is the steps that fell due while Home Assistant was down: those are
    recorded as skipped and not sent (part 1 decision 5) — a notification
    four hours late is worse than none, and the log says which ones went
    missing and why.
    """

    kind: EscalationKind
    profile_id: str
    moment: Moment
    started_at: datetime
    severity: int = 1
    done: tuple[str, ...] = ()
    reference: str | None = None  # the incident id, when there is one


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
    # The escalation for this incident has run to its last step. Recorded
    # here because the Escalation itself is dropped when it is exhausted, so
    # without it the next zone to join found no escalation running and
    # started the whole list again — push, SMS, the neighbour, the voice call
    # — once per further zone of the same break-in (found in review).
    escalation_exhausted: bool = False

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
    # Whether this belongs to the technical channel (§5.5). It is here
    # because the channel is not derivable from the area: a technical
    # response carries the area of the zone that raised it, so a disarm of
    # that area — or the intrusion siren cutoff — would otherwise stop a
    # smoke sounder, which §5.5 says in as many words it may never do
    # (found in review).
    technical: bool = False


@dataclass(frozen=True, slots=True)
class Detection:
    """One zone seen during a walk test (SPEC §11.3).

    The point of the feature is not the count but its absence: a zone with no
    Detection at the end of the walk is a zone that never reacted, which is
    either a door nobody opened or a PIR pointing at the wrong wall.
    """

    first: datetime
    last: datetime
    count: int = 1


@dataclass(frozen=True, slots=True)
class WalkTest:
    """A walk test in progress (SPEC §11.3). State, so it survives a restart.

    It is in ``RuntimeState`` and not in memory because §5.3 lists the
    auto-exit among the timers, and INV-3 says pending timers are persisted:
    a walk test that a restart turned into "inhibited for ever, silently" is
    the worst thing this feature could do.

    ``until`` is pushed back by every detection and ``hard_until`` never
    moves (part 2 decision 4): a forty-zone house takes longer than fifteen
    minutes to walk, and a walk test somebody forgot about with a cat in
    front of a PIR must still end.

    ``armed_areas`` are the areas this walk test armed and will disarm when
    it ends — never one that was already armed before it started
    (part 2 decision 2).
    """

    started_at: datetime
    until: datetime
    hard_until: datetime
    window: int
    armed_areas: tuple[str, ...] = ()
    detections: Mapping[str, Detection] = field(default_factory=dict)
    # Who started it (§11.3: "entry and exit logged with the user"). Kept
    # here for the same reason AreaRuntime keeps it: the exit row is written
    # by a timer, long after the person pressed anything.
    user_id: str | None = None
    user_name: str | None = None
    channel: str | None = None
    device_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "detections", _frozen(self.detections))

    def deadline(self) -> datetime:
        """When it ends if nothing else happens: the nearer of the two."""
        return min(self.until, self.hard_until)


@dataclass(frozen=True, slots=True)
class PendingRuleAction:
    """An automatic rule's action, announced and waiting (SPEC §9.4).

    State with a due time, like every other timer this project has (INV-3,
    part 2 decision 1): a countdown built on ``asyncio.sleep`` would be the
    first one a restart could lose, and what it would lose is a house arming
    itself with nobody told.

    ``id`` is what the Cancel button carries back, so pressing the button on
    yesterday's notification cannot stop today's countdown. ``scenario_id``
    and ``area_ids`` are resolved when the countdown starts, not when it
    fires: an expected-visitor window substituting a reduced scenario has
    already been applied here, and the notification therefore names what will
    actually happen.
    """

    id: str
    rule_id: str
    rule_name: str
    action: RuleActionKind
    due: datetime
    started_at: datetime
    scenario_id: str | None = None
    area_ids: tuple[str, ...] = ()
    # The suspension that substituted this action, for the log row that
    # explains it six months later.
    suspension_name: str | None = None

    @property
    def seconds(self) -> int:
        return max(0, int((self.due - self.started_at).total_seconds()))


@dataclass(frozen=True, slots=True)
class Suspension:
    """Automatic arming held back, by hand (SPEC §9.4).

    Runtime state rather than configuration (part 2 decision 7): it expires
    like ``bypass_until``, it is an operational act three clicks from the card
    rather than a configuration edit, and ``core/`` never writes
    configuration. The ``name`` travels into every log row it explains — the
    row is what lasts, not the object.

    ``rule_ids`` empty means every rule, which is what an expected-visitor
    window is: the house is not to arm itself this morning, whichever rule
    would have done it.
    """

    id: str
    kind: SuspensionKind
    rule_ids: tuple[str, ...] = ()
    name: str | None = None
    start: datetime | None = None  # VISITOR: when the window opens
    until: datetime | None = None  # UNTIL, VISITOR: when it ends
    # VISITOR only: arm this instead of what the suspended rule would have
    # armed (§9.4). Nothing happens at the window's edges — it substitutes
    # (part 2 decision 8).
    reduced_scenario_id: str | None = None
    created_at: datetime | None = None
    user_id: str | None = None
    user_name: str | None = None

    def active(self, now: datetime) -> bool:
        """Whether it is covering anything right now."""
        if self.kind is SuspensionKind.NEXT:
            return True
        if self.start is not None and now < self.start:
            return False
        return self.until is None or now < self.until

    def covers(self, rule_id: str) -> bool:
        return not self.rule_ids or rule_id in self.rule_ids

    def expired(self, now: datetime) -> bool:
        """A NEXT suspension is spent by use, never by the clock."""
        return (
            self.kind is not SuspensionKind.NEXT
            and self.until is not None
            and now >= self.until
        )


@dataclass(frozen=True, slots=True)
class RuleRuntime:
    """What the engine remembers about one rule between wake-ups (§9.4).

    ``since`` is when the trigger's condition became true, which is what the
    "for N minutes" is measured from. ``latched`` is set when a level trigger
    has acted and cleared when its condition goes false again: without it, an
    ``absence`` rule that armed the house would ask to arm it again at every
    wake-up for the rest of the day.

    ``blocked`` is the guard currently holding the rule back, kept so the row
    is written once at the start of the block rather than at every wake-up
    (part 2 decision 4). ``last_occurrence`` is the wall-clock instant a
    ``time`` rule has already handled, so a rule that fires at 23:00 fires
    once even if the scheduler wakes twice.
    """

    since: datetime | None = None
    latched: bool = False
    blocked: RuleBlock | None = None
    last_occurrence: datetime | None = None
    # Whether this rule has been evaluated at least once. The baseline rule
    # this project applies everywhere else (§4.7, §9.3): a `presence` rule
    # saved while somebody is already at home has not seen them arrive, and
    # must not disarm the house the moment it is created.
    seen: bool = False
    # A `time` rule's hour and weekdays as they were when its baseline was
    # taken. A rule saved, or re-timed, after its hour today waits for the
    # next occurrence rather than acting at once (found in review) — the same
    # baseline rule, applied to a change of the rule itself.
    schedule: str | None = None


@dataclass(frozen=True, slots=True)
class Lockout:
    """One channel's failed attempts, and how long it stays shut (§8.4).

    ``strikes`` is how many times this channel has already been locked, which
    is what makes the next one longer. It is kept per channel and device, so
    somebody guessing at the garden keypad does not lock the hall one.
    """

    failures: tuple[datetime, ...] = ()
    until: datetime | None = None
    strikes: int = 0
    locked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ChannelHealth:
    """What Foyer knows about one contact channel (SPEC §12.2).

    ``failures`` counts consecutive failed sends and resets on the first
    success: one failure is a provider with a hiccup, a run of them is a
    channel. ``since`` is when it broke, which is what turns "it is broken"
    into "it has been broken since Tuesday" — the sentence that makes a
    repair issue worth raising.
    """

    fault: ChannelFault | None = None
    since: datetime | None = None
    failures: int = 0
    last_ok: datetime | None = None
    last_failed: datetime | None = None
    # Whether the last sweep found the service in the registry. None means no
    # sweep has run yet, which is not the same as "missing": an installation
    # that has just started has learned nothing, and reporting every channel
    # as broken for the first quarter of an hour would be its own alarm.
    present: bool | None = None


@dataclass(frozen=True, slots=True)
class WatchdogHealth:
    """The external watchdog's own state (SPEC §12.3).

    Foyer watches the watchdog: repeated failures to reach the endpoint mean
    no internet-based notification would go out either, and the panel says
    so. ``ever_ok`` separates "it stopped working" from "it has never worked",
    which is almost always a URL somebody mistyped.
    """

    failures: int = 0
    down_since: datetime | None = None
    last_ok: datetime | None = None
    last_attempt: datetime | None = None
    last_error: str = ""
    ever_ok: bool = False
    # Whether the unreachable moment has already been raised for this outage,
    # so it is announced once rather than every quarter of an hour.
    announced: bool = False


@dataclass(frozen=True, slots=True)
class RadioHealth:
    """One radio's correlated-silence state (SPEC §12.5).

    ``suspected_since`` is when the threshold was first met and the
    confirmation window started; ``confirmed`` is when it was still true at
    the end of it and the moment was raised. Both persist, because a restart
    in the middle of a jamming attempt must not restart the count from zero.
    """

    suspected_since: datetime | None = None
    confirmed: bool = False
    zone_ids: tuple[str, ...] = ()
    coordinator_down_since: datetime | None = None
    coordinator_announced: bool = False


@dataclass(frozen=True, slots=True)
class SystemHealth:
    """The condition of the system itself (SPEC §12), beside the areas.

    State, not a channel with a memory: a mains failure that cleared itself at
    three in the morning is over, and system health says so rather than
    waiting for somebody to acknowledge it. That is the one deliberate
    difference from the technical channel (§5.5), which this sits beside:
    the technical channel is about the *house* and needs a person to say
    they have seen it, and this is about *Foyer*, where the only meaningful
    question is whether it is still true.

    ``quiet_since`` records when each zone's entity went unreadable, which is
    what the radio correlation of §12.5 counts. It is kept for every zone,
    not only those on a radio, because a zone's radio can be assigned after
    it has already gone quiet.
    """

    mains_lost_since: datetime | None = None
    # Keyed "<contact_id>:<channel_id>".
    channels: Mapping[str, ChannelHealth] = field(default_factory=dict)
    watchdog: WatchdogHealth = field(default_factory=WatchdogHealth)
    radios: Mapping[str, RadioHealth] = field(default_factory=dict)
    quiet_since: Mapping[str, datetime] = field(default_factory=dict)
    # Zones that are unreadable and whose silence began before Foyer was
    # watching: at a restart, or on a radio whose coordinator was gone. They
    # are NOT counted towards a burst, because "how long has this been
    # quiet" has no answer for them — and a battery device that has not been
    # interviewed yet looks exactly like a jammed one. A zone leaves this
    # set the moment it is readable again, and is countable from then on.
    #
    # It is the same rule §4.7 already applies to every zone's first reading
    # and decision 56 applies to the technical channel: what Foyer did not
    # see happen, it does not claim to have seen.
    unknown_zones: frozenset[str] = frozenset()
    # Repair issues somebody has marked as seen (§12.4, part 1 decision
    # 10). Here rather than in memory because the alternative is a card
    # that comes back five minutes after it was dismissed, and again after
    # every restart. An id leaves this set when its problem clears, so the
    # next occurrence raises the card again.
    acknowledged_issues: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "channels", _frozen(self.channels))
        object.__setattr__(self, "radios", _frozen(self.radios))
        object.__setattr__(self, "quiet_since", _frozen(self.quiet_since))

    def channel(self, key: str) -> ChannelHealth:
        return self.channels.get(key) or ChannelHealth()

    def radio(self, radio_id: str) -> RadioHealth:
        return self.radios.get(radio_id) or RadioHealth()

    @property
    def impaired_radios(self) -> frozenset[str]:
        """Radios Foyer must not act through right now (§12.5).

        Confirmed interference, and a coordinator that is itself gone: the
        second is the *more* certain blackout of the two, and announcing a
        Zigbee outage through a Zigbee siren is not a notification whichever
        of the two caused it.
        """
        return frozenset(
            r
            for r, h in self.radios.items()
            if h.confirmed or h.coordinator_down_since is not None
        )


def channel_key(contact_id: str, channel_id: str) -> str:
    """One name for a contact's channel, used by the state and the panel."""
    return f"{contact_id}:{channel_id}"


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
    # The same rule for arming devices (§9.3): a tag entity already carrying
    # the timestamp of a scan from last week is not somebody at the door.
    seen_devices: frozenset[str] = frozenset()
    # The endpoint keypads whose most recent request arrived unencrypted
    # (§9.2.1). Additive state, read with a default: an older file restores
    # as "none known", and the keypad's next request says which it is.
    in_clear: frozenset[str] = frozenset()
    faults: frozenset[str] = frozenset()
    # The zones already announced as running low (§4.2, §6.1), so the moment
    # is raised once on the way down rather than on every report. Additive
    # state, read with a default: an older file restores as "none known yet",
    # and the first reconcile after the restart announces what is low.
    low_batteries: frozenset[str] = frozenset()
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
    # Failed code attempts and lockouts, by channel and device (§8.4). Here
    # rather than in memory because a lockout that a restart clears is an
    # invitation to restart Home Assistant (INV-3).
    lockouts: Mapping[str, Lockout] = field(default_factory=dict)
    # The walk test in progress, or None (§11.3). Additive state, read with a
    # default: an older file restores as "no walk test", which is the safe
    # direction — a house that is answering rather than one that is not.
    walk_test: WalkTest | None = None
    # The escalations in progress (§7.2): at most one for the incident and
    # one for the technical channel, never merged (§5.5). Persisted, because
    # an alarm nobody has answered is still unanswered after a restart, and
    # INV-3 lists escalation progress by name.
    escalations: tuple[Escalation, ...] = ()
    # Automatic arming (§9.4). ``auto_arming`` is switch.foyer_auto_arming,
    # the global kill switch, and it is state rather than a setting for the
    # same reason the chime's switch is: it is turned off for an evening, from
    # a dashboard or a keypad, not configured. ``pending_rules`` are the
    # countdowns announced and not yet run, ``suspensions`` what is holding
    # rules back, and ``rules`` what the engine remembers about each rule
    # between wake-ups. All additive, all read with a default: an older state
    # file restores as "nothing pending, nothing suspended, switch on", which
    # is a house that will announce before it acts.
    auto_arming: bool = True
    pending_rules: tuple[PendingRuleAction, ...] = ()
    suspensions: tuple[Suspension, ...] = ()
    rules: Mapping[str, RuleRuntime] = field(default_factory=dict)
    pending_seq: int = 0
    # System health (§12). Persisted like everything else here, and for the
    # same reason: an outage a restart forgets is an outage that starts
    # counting again from zero every time Home Assistant reloads, which on a
    # house being configured is several times an hour. Additive, read with a
    # default: an older state file restores as "nothing known yet", and the
    # first sweep after the restart says what is true.
    health: SystemHealth = field(default_factory=SystemHealth)

    def __post_init__(self) -> None:
        object.__setattr__(self, "areas", _frozen(self.areas))
        object.__setattr__(self, "rules", _frozen(self.rules))
        object.__setattr__(self, "bypassed", _frozen(self.bypassed))
        object.__setattr__(self, "technical", _frozen(self.technical))
        object.__setattr__(self, "windows", _frozen(self.windows))
        object.__setattr__(self, "bypass_until", _frozen(self.bypass_until))
        object.__setattr__(self, "lockouts", _frozen(self.lockouts))

    def area(self, area_id: str) -> AreaRuntime:
        return self.areas.get(area_id) or AreaRuntime()

    def escalation(self, kind: EscalationKind) -> Escalation | None:
        return next((e for e in self.escalations if e.kind is kind), None)

    def rule(self, rule_id: str) -> RuleRuntime:
        return self.rules.get(rule_id) or RuleRuntime()

    def pending_rule(self, rule_id: str) -> PendingRuleAction | None:
        return next((p for p in self.pending_rules if p.rule_id == rule_id), None)


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
    # When the state itself last moved, which is not the same question as
    # when the entity last spoke: a door shut for a week that checks in every
    # hour has a recent ``last_reported`` and a week-old ``last_changed``.
    # §11.1 asks for this one, because "last change" is what tells somebody
    # they are looking at the wrong sensor.
    last_changed: datetime | None = None

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
    # Which radio each entity belongs to (§12.5), entity id to Radio.id.
    # Home Assistant has no general notion of a radio, so working it out is a
    # lookup through the entity registry and the config entries — which is
    # exactly the kind of thing INV-1 says the engine is handed rather than
    # performs. It covers the zones *and* the entities actions target, so
    # "do not notify over the affected radio" is decided here and not by an
    # executor guessing.
    radios: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", _frozen(self.entities))
        object.__setattr__(self, "radios", _frozen(self.radios))

    def radio_of(self, entity_id: str | None) -> str | None:
        return self.radios.get(entity_id or "")

    def entity(self, entity_id: str) -> EntityState:
        return self.entities.get(entity_id) or MISSING


# --- events --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Actor:
    """Who is asking, and what the backend already established about them.

    The engine never sees a code (INV-2). ``security/`` verifies what arrived
    and hands over this: which user it identified, whether the code was valid,
    and whether the channel identifies the person by itself. Everything the
    engine decides about identity is decided from this and the configuration.

    ``identified`` means the channel knows who this is without a code — the
    Home Assistant UI of a signed-in user linked to a Foyer user. It is the
    only thing that can activate the per-user exemption of §8.2, and it is
    checked against the channel as well, so a keypad claiming it changes
    nothing. ``is_admin`` marks the Home Assistant admin path, which is never
    locked out (§8.4), so nobody can shut themselves out of their own house.
    """

    user_id: str | None = None
    channel: str = "api"
    device_id: str | None = None
    code: CodeResult = CodeResult.NONE
    identified: bool = False
    duress: bool = False
    is_admin: bool = False
    # A channel where possession is the credential and no code can travel at
    # all: the key switch of §4.7, and the NFC tag of §9.3 whose security note
    # says plainly that a stolen tag arms and disarms without knowing a code.
    # The permissions and the validity window of the user it names still
    # apply; only the code policy cannot, because there is nothing to type.
    token: bool = False
    # The person was NAMED by the request rather than established by it: a
    # service call passing `user_id` with no code and no token (§9.1). It
    # grants nothing — that is resolved in core/authz — and it exists so the
    # log can say how it came by the name it carries. "Who disarmed at 03:14"
    # deserves no answer rather than a wrong one (decision 88).
    claimed: bool = False
    # Where the request came from, for the one caller that has no device to
    # count against: a request to the device endpoint carrying no token, or
    # the wrong one (§9.2.1). The lockout of §8.4 then counts per source
    # address. Nothing else sets it.
    address: str | None = None
    # The Home Assistant account behind a request that has no device: the
    # panel, the card, a service call made by a signed-in person. The lockout
    # of §8.4 counts per account there, so one account guessing locks itself
    # out and not the whole household (second review, decision 1).
    account: str | None = None
    # Whether the request crossed the network encrypted, as Home Assistant
    # judged it — directly, or behind a reverse proxy it trusts (§9.2.1).
    # None where the question does not arise; False is recorded on every row
    # the request causes, because the token and the code it carried could be
    # read on the way.
    encrypted: bool | None = None

    @property
    def code_verified(self) -> bool:
        return self.code is CodeResult.VALID


@dataclass(frozen=True, slots=True)
class ArmRequest:
    """Arm a scenario, or switch to it while armed (SPEC §4.6)."""

    scenario_id: str
    actor: Actor = field(default_factory=Actor)
    force: bool = False
    # Arm with no exit delay at all (§9.1): the last person out, already
    # outside, pressing the key on the door frame. It needs no permission of
    # its own (part 2 decision 5) — whoever may arm may arm at once — but it
    # turns every delayed zone into an instant one, so the log records it.
    skip_exit_delay: bool = False


@dataclass(frozen=True, slots=True)
class ArmModeRequest:
    """Arm through the master panel: the one scenario reporting this mode."""

    mode: str
    actor: Actor = field(default_factory=Actor)
    force: bool = False
    # Arm with no exit delay at all (§9.1): the last person out, already
    # outside, pressing the key on the door frame. It needs no permission of
    # its own (part 2 decision 5) — whoever may arm may arm at once — but it
    # turns every delayed zone into an instant one, so the log records it.
    skip_exit_delay: bool = False


@dataclass(frozen=True, slots=True)
class ArmAreaRequest:
    """Arm one area on its own, outside any scenario, from its own panel."""

    area_id: str
    actor: Actor = field(default_factory=Actor)
    force: bool = False
    # Arm with no exit delay at all (§9.1): the last person out, already
    # outside, pressing the key on the door frame. It needs no permission of
    # its own (part 2 decision 5) — whoever may arm may arm at once — but it
    # turns every delayed zone into an instant one, so the log records it.
    skip_exit_delay: bool = False


@dataclass(frozen=True, slots=True)
class DisarmRequest:
    """Disarm ``area_ids``, or every area when None."""

    area_ids: tuple[str, ...] | None = None
    actor: Actor = field(default_factory=Actor)


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
    """Acknowledge the open intrusion incident (SPEC §5.6).

    ``via`` is which of the four paths of §7.2 this came from — an explicit
    command, a disarm, a button in an actionable push, a DTMF keypress — and
    ``contact_id`` is who the notification had gone to, which is the whole of
    the answer when that contact names no Foyer user (part 1 decision 7).
    """

    actor: Actor = field(default_factory=Actor)
    via: str = "acknowledge"
    contact_id: str | None = None


@dataclass(frozen=True, slots=True)
class AcknowledgeTechnical:
    """Acknowledge every technical alarm pending now (§5.5, part 2 decision 11).

    A separate command from the incident's on purpose: a different channel,
    a different acknowledgement (§5.5).
    """

    actor: Actor = field(default_factory=Actor)
    via: str = "acknowledge"
    contact_id: str | None = None


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
    actor: Actor = field(default_factory=Actor)


@dataclass(frozen=True, slots=True)
class SetChime:
    """switch.foyer_chime: silence the chime, or let it sound again (§6.6)."""

    enabled: bool
    actor: Actor = field(default_factory=Actor)


@dataclass(frozen=True, slots=True)
class CodeAttempt:
    """A code offered to a command the engine does not otherwise decide (§8.4).

    Configuration and log commands verify their own code — they never reach
    `decide()` — and therefore counted nothing: a wrong code there was an
    oracle with no lockout and no row, which is the one thing §8.4 exists to
    prevent (found in review). This event spends the same counter, writes the
    same rows and raises the same moments as any other refused code, so
    §8.2-§8.4 stay resolved in one place.
    """

    # None for a credential offered with no operation behind it yet: the
    # device endpoint refuses a wrong token before it reads what the request
    # asked for, and a state stream asks for nothing (§9.2.1).
    operation: Operation | None
    actor: Actor = field(default_factory=Actor)


@dataclass(frozen=True, slots=True)
class WalkTestRequest:
    """Enter or leave the walk test (§11.3, §9.1 ``foyer.walk_test``).

    ``duration`` may only ask for **less** than the installation's configured
    maximum (part 2 decision 5): the timeout of §5.3 is "mandatory,
    non-disableable", so a request for an hour gets the maximum and the §9.1
    answer says what it got.
    """

    enable: bool
    actor: Actor = field(default_factory=Actor)
    duration: int | None = None


@dataclass(frozen=True, slots=True)
class CancelAutoAction:
    """Stop an automatic rule's grace countdown (SPEC §9.4).

    ``pending_id`` names which countdown, so the button on a notification
    from an hour ago cannot stop the one running now; None cancels every
    countdown in progress, which is what the panel's single button does when
    only one is running. ``via`` and ``contact_id`` say where the answer came
    from, exactly as an acknowledgement does: a push can come back with no
    person attached to it, and then the contact and the channel are the whole
    of the answer (part 1 decision 7).
    """

    pending_id: str | None = None
    actor: Actor = field(default_factory=Actor)
    via: str = "command"
    contact_id: str | None = None


@dataclass(frozen=True, slots=True)
class SetAutoArming:
    """switch.foyer_auto_arming: the global kill switch (SPEC §9.4, §13)."""

    enabled: bool
    actor: Actor = field(default_factory=Actor)


@dataclass(frozen=True, slots=True)
class SetSuspension:
    """Suspend automatic arming, or lift a suspension (SPEC §9.4).

    One event for the three forms, because §9.4 says they are mechanically
    one thing: until a date and time, skip the next occurrence, or a named
    expected-visitor window. ``suspension`` None with an ``id`` lifts it.
    """

    suspension: Suspension | None = None
    suspension_id: str | None = None
    actor: Actor = field(default_factory=Actor)


@dataclass(frozen=True, slots=True)
class HealthReport:
    """What the runtime observed that the engine cannot see (SPEC §12).

    One event rather than three, because it is one kind of fact: somebody
    outside the engine went and looked. The watchdog's ping is an HTTP
    request, the sweep is a read of the service registry, and a send outcome
    is what the executor learned from a call that has already happened —
    none of which a pure function may do (INV-1). The engine is handed the
    observation and owns everything that follows from it: the counting, the
    thresholds, the moments and the state.

    Every field is optional and None means "nothing new about this": a
    watchdog ping carries only the watchdog.
    """

    watchdog: bool | None = None
    watchdog_error: str = ""
    # channel key -> whether its service is in the registry, from the sweep.
    channels_present: Mapping[str, bool] | None = None
    # channel key -> whether a real send just succeeded.
    channel_sends: Mapping[str, bool] | None = None

    def __post_init__(self) -> None:
        if self.channels_present is not None:
            object.__setattr__(self, "channels_present", _frozen(self.channels_present))
        if self.channel_sends is not None:
            object.__setattr__(self, "channel_sends", _frozen(self.channel_sends))


@dataclass(frozen=True, slots=True)
class DeviceContact:
    """A keypad reached the device endpoint and asked for nothing (§9.2.1).

    A state stream opening, or a `status` request. Nothing is decided; what
    the engine records is only whether it crossed the network encrypted,
    which is a fact about the keypad and keeps page 8's warning honest for a
    keypad that listens far more than it commands.
    """

    actor: Actor = field(default_factory=Actor)


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
    | WalkTestRequest
    | CodeAttempt
    | CancelAutoAction
    | SetAutoArming
    | SetSuspension
    | HealthReport
    | DeviceContact
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
    # Who asked, and from which device (§10.1). ``user_name`` travels with
    # the row and is denormalised into the log on purpose: deleting a user
    # must not erase the history of what that user did.
    user_id: str | None = None
    user_name: str | None = None
    device_id: str | None = None

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
    # Which run of a profile produced it, and under which answer — silent or
    # not, which incident — so the simulator's trace credits each intent to
    # the batch that built it and never to another batch of the same profile
    # and moment (found in review). The executor ignores all three.
    run_id: str = ""
    silent: bool = False
    incident_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "placeholders", _frozen(self.placeholders))
        object.__setattr__(self, "params", _frozen(self.params))


@dataclass(frozen=True, slots=True)
class ScheduledStep:
    """A step of a running escalation that has not happened yet (§7.2, §11.2).

    It is on the Decision rather than computed by whoever wants to show it,
    and that is the whole of INV-1 applied to a feature that is nothing but
    the future: the simulator's "escalation step 1 at +60s → Luca (SMS)" is
    read off the same object the runtime acts on, so the trace cannot
    describe a schedule the engine did not make.
    """

    kind: EscalationKind
    profile_id: str
    action_id: str
    index: int
    offset: int
    due: datetime
    contact_ids: tuple[str, ...] = ()
    channel_ids: tuple[str, ...] = ()


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
    # Zones in the areas this request would arm whose battery is running low
    # (§4.2). They do not block and they are not faults, so they never reach
    # ``blocking_zones`` — but every arming attempt carries them, on every
    # channel, because a warning that is shown once is a warning nobody sees
    # the morning it matters (Phase 3 part 1 decision 2). What to do about
    # them is the caller's: excluding one is an ordinary manual bypass.
    low_battery_zones: tuple[str, ...] = ()
    occurrences: tuple[Occurrence, ...] = ()
    actions: tuple[ActionIntent, ...] = ()
    # What the walk test held back (§11.3, part 2 decision 1). These intents
    # are built exactly as the ones above and then **not** given to the
    # executor: they are here so the panel and the log can say what would
    # have happened, and they are kept out of ``actions`` so that nothing
    # downstream has to remember not to run them. An executor with one more
    # condition to honour is an executor whose only possible mistake is
    # sounding the siren during a walk test.
    inhibited: tuple[ActionIntent, ...] = ()
    # The escalation steps still to come, earliest first (§7.2). Nothing is
    # executed from this: it is what the panel, the card and the simulator's
    # trace read so that "who will be called, and when" has exactly one
    # source — the engine that will do the calling.
    escalation: tuple[ScheduledStep, ...] = ()

    @property
    def active_scenario_id(self) -> str | None:
        return self.state.active_scenario_id

    @property
    def moments(self) -> tuple[Moment, ...]:
        return tuple(o.moment for o in self.occurrences)
