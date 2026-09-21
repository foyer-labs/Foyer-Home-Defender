"""Configuration validation, pure (SPEC §4, §5.3).

Every configuration write goes through ``validate`` in the backend before it is
stored: the panel's own checks are a courtesy, never the gate. A problem is a
stable code plus where it is, so the UI can translate it and put it next to
the field.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re

from .clock import parse_hhmm
from .models import (
    ARMED_HA_STATES,
    FAULT_STATES,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_CHANNEL_FAILURES,
    MAX_CHANNEL_SWEEP,
    MAX_CODE_LENGTH,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_ESCALATION_OFFSET,
    MAX_EXIT_DELAY,
    MAX_GRACE_SECONDS,
    MAX_LOCKOUT_FAILURES,
    MAX_LOCKOUT_SECONDS,
    MAX_LOW_BATTERY_THRESHOLD,
    MAX_MQTT_QOS,
    MAX_MQTT_TOPIC,
    MAX_RETENTION_DAYS,
    MAX_RF_CONFIRM,
    MAX_RF_WINDOW,
    MAX_RF_ZONES,
    MAX_RULE_MINUTES,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MAX_WALK_TEST_TIMEOUT,
    MAX_WATCHDOG_FAILURES,
    MAX_WATCHDOG_INTERVAL,
    MAX_WATCHDOG_TIMEOUT,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_CHANNEL_FAILURES,
    MIN_CHANNEL_SWEEP,
    MIN_CODE_LENGTH,
    MIN_LOCKOUT_FAILURES,
    MIN_LOCKOUT_SECONDS,
    MIN_LOW_BATTERY_THRESHOLD,
    MIN_RETENTION_DAYS,
    MIN_RF_CONFIRM,
    MIN_RF_WINDOW,
    MIN_RF_ZONES,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    MIN_WALK_TEST_TIMEOUT,
    MIN_WATCHDOG_FAILURES,
    MIN_WATCHDOG_INTERVAL,
    MIN_WATCHDOG_TIMEOUT,
    MQTT_TOPIC_FORBIDDEN,
    NOTIFY_ATTACHMENTS,
    SILENCEABLE,
    ActionKind,
    AreaState,
    ArmPolicy,
    Channel,
    ChimeMode,
    ChimeSettings,
    DeviceKind,
    EntryMode,
    EventTrigger,
    FoyerConfig,
    KeyCommand,
    LogCategory,
    Moment,
    NumericOperator,
    NumericTrigger,
    Permission,
    ProfileAction,
    ResponseProfile,
    RuleActionKind,
    RuleTriggerKind,
    RuntimeState,
    StateCondition,
    StateTrigger,
    TimeCondition,
    Zone,
)
from .privacy import MAX_PSEUDONYMISE_DAYS, MIN_PSEUDONYMISE_DAYS
from .templates import unknown_variables
from .verification import cross_zone_id

# What the chime can play on (SPEC §6.6): speakers, sirens, and the free
# channels the house already has (decision 60).
CHIME_DOMAINS: tuple[str, ...] = ("media_player", "siren", "notify")

# Bounds for the action catalogue (SPEC §6.2).
MAX_ACTION_DELAY = 3600
MAX_CAMERA_DURATION = 300
MAX_SEVERITY = 10
# Which domains each action kind may target. An action that names the wrong
# domain fails at the worst possible time, so it is refused at save time.
ACTION_DOMAINS: dict[str, tuple[str, ...]] = {
    ActionKind.SIREN.value: ("siren", "switch"),
    ActionKind.LIGHT.value: ("light",),
    ActionKind.CAMERA.value: ("camera",),
    ActionKind.SCENE.value: ("scene",),
    ActionKind.SWITCH.value: ("switch", "input_boolean", "light"),
    ActionKind.TTS.value: ("tts",),
}
# Templates are checked wherever the user writes free text.
TEMPLATED_FIELDS: tuple[str, ...] = ("title", "message")

# Entity domains a zone may watch (SPEC §4.2).
ZONE_DOMAINS: tuple[str, ...] = (
    "binary_sensor",
    "sensor",
    "cover",
    "lock",
    "switch",
    "input_boolean",
    "device_tracker",
    "person",
    "event",
    "tag",
)
EVENT_DOMAINS: frozenset[str] = frozenset({"event", "tag"})

# What an `absence` or `presence` rule may watch (§9.4). Home Assistant's own
# presence entities and nothing else: a rule reading a switch as if it were a
# person is a rule whose owner will be surprised exactly once.
PRESENCE_DOMAINS: frozenset[str] = frozenset({"person", "device_tracker"})

# What a zone's battery entity may be (§4.2): a percentage, or Home
# Assistant's battery binary_sensor where ``on`` means low. Nothing else can
# be read as a battery without guessing, and guessing here produces a warning
# that never arrives or one that never stops.
BATTERY_DOMAINS: frozenset[str] = frozenset({"sensor", "binary_sensor"})


@dataclass(frozen=True, slots=True)
class Problem:
    code: str
    # "area" | "zone" | "scenario" | "group" | "profile" | "user" | "device"
    # | "settings" | "chime"
    kind: str
    ref: str | None = None  # the id of the offending object
    field: str | None = None


def _slug(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", name.casefold()).strip("_")


def _in_range(value: int | None, low: int, high: int) -> bool:
    return value is None or low <= value <= high


def validate(config: FoyerConfig) -> list[Problem]:
    problems: list[Problem] = []
    add = problems.append

    for kind, ids in (
        ("area", [a.id for a in config.areas]),
        ("zone", [z.id for z in config.zones]),
        ("scenario", [s.id for s in config.scenarios]),
        ("group", [g.id for g in config.groups]),
    ):
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            add(Problem("duplicate_id", kind, dup))

    # Names become entity ids (areas, zones) and select options (scenarios):
    # two that slug to the same thing would collide. Groups are read by name
    # in the trace, where two alike would be ambiguous.
    for kind, objects in (
        ("area", config.areas),
        ("zone", config.zones),
        ("scenario", config.scenarios),
        ("group", config.groups),
    ):
        seen: set[str] = set()
        for obj in objects:
            slug = _slug(obj.name)
            if slug and slug in seen:
                add(Problem("duplicate_name", kind, obj.id, "name"))
            seen.add(slug)

    area_ids = {a.id for a in config.areas}
    scenario_ids = {s.id for s in config.scenarios}

    for area in config.areas:
        if not area.name.strip():
            add(Problem("name_required", "area", area.id, "name"))
        if area.ha_state_when_armed not in ARMED_HA_STATES:
            add(Problem("invalid_ha_state", "area", area.id, "ha_state_when_armed"))
        if not _in_range(area.default_entry_delay, 0, MAX_ENTRY_DELAY):
            add(Problem("delay_out_of_range", "area", area.id, "default_entry_delay"))
        if not _in_range(area.default_exit_delay, 0, MAX_EXIT_DELAY):
            add(Problem("delay_out_of_range", "area", area.id, "default_exit_delay"))

    for scenario in config.scenarios:
        if not scenario.name.strip():
            add(Problem("name_required", "scenario", scenario.id, "name"))
        if not scenario.areas:
            add(Problem("scenario_without_areas", "scenario", scenario.id, "areas"))
        if any(a not in area_ids for a in scenario.areas):
            add(Problem("unknown_area", "scenario", scenario.id, "areas"))
        if scenario.ha_master_state not in ARMED_HA_STATES:
            add(Problem("invalid_ha_state", "scenario", scenario.id, "ha_master_state"))
        if not _in_range(scenario.exit_delay_override, 0, MAX_EXIT_DELAY):
            add(
                Problem(
                    "delay_out_of_range", "scenario", scenario.id, "exit_delay_override"
                )
            )
        if not _in_range(scenario.siren_duration_override, 1, MAX_SIREN_DURATION):
            add(
                Problem(
                    "siren_out_of_range",
                    "scenario",
                    scenario.id,
                    "siren_duration_override",
                )
            )

    settings = config.settings
    profile_ids = {p.id for p in config.profiles}
    for label, ref in (
        ("default_profile_id", settings.default_profile_id),
        ("technical_profile_id", settings.technical_profile_id),
    ):
        if ref is not None and ref not in profile_ids:
            add(Problem("unknown_profile", "settings", None, label))
    if any(kind not in SILENCEABLE for kind in settings.silent_suppresses):
        add(Problem("unknown_action_kind", "settings", None, "silent_suppresses"))
    if not _valid_directory(settings.camera_dir):
        # Never www: Home Assistant serves it without authentication, and the
        # inside of a house is not something to publish (part 3 decision 7).
        add(Problem("camera_dir_invalid", "settings", None, "camera_dir"))
    if not _in_range(settings.siren_duration, 1, MAX_SIREN_DURATION):
        add(Problem("siren_out_of_range", "settings", None, "siren_duration"))
    if not _in_range(
        settings.arm_hold_timeout, MIN_ARM_HOLD_TIMEOUT, MAX_ARM_HOLD_TIMEOUT
    ):
        add(Problem("hold_out_of_range", "settings", None, "arm_hold_timeout"))
    if not _in_range(
        settings.low_battery_threshold,
        MIN_LOW_BATTERY_THRESHOLD,
        MAX_LOW_BATTERY_THRESHOLD,
    ):
        add(Problem("battery_out_of_range", "settings", None, "low_battery_threshold"))
    if not _in_range(
        settings.walk_test_timeout, MIN_WALK_TEST_TIMEOUT, MAX_WALK_TEST_TIMEOUT
    ):
        # §5.3 calls the walk test's auto-exit mandatory and non-disableable,
        # so there is no value here that switches it off — only a shorter or
        # a longer one, both bounded.
        add(Problem("walk_test_out_of_range", "settings", None, "walk_test_timeout"))

    zones = {z.id: z for z in config.zones}
    for zone in config.zones:
        problems.extend(_zone_problems(zone, area_ids, scenario_ids))
        # INV-5, on every path that stores a configuration — the editor, a
        # restore, an import — and not only on the editor's: a trigger nobody
        # confirmed may exist, but it may not watch anything.
        if zone.enabled and not zone.trigger_confirmed:
            add(Problem("trigger_not_confirmed", "zone", zone.id, "trigger"))
        if zone.follows and zone.entry_mode is not EntryMode.FOLLOWER:
            add(Problem("follows_needs_follower", "zone", zone.id, "follows"))
        for followed in zone.follows:
            target = zones.get(followed)
            if (
                target is None
                or target.id == zone.id
                or target.channel is not Channel.INTRUSION
                or target.entry_mode is not EntryMode.DELAYED
            ):
                add(Problem("follows_not_delayed", "zone", zone.id, "follows"))
                break
        if zone.cross_zone_id is not None:
            partner = zones.get(zone.cross_zone_id)
            if (
                partner is None
                or partner.id == zone.id
                or partner.channel is not Channel.INTRUSION
            ):
                add(Problem("cross_zone_invalid", "zone", zone.id, "cross_zone_id"))
            elif (
                partner.cross_zone_id == zone.id
                and partner.cross_zone_window != zone.cross_zone_window
            ):
                # One pair, one window: two different ones would make the
                # result depend on which zone happens to be read first.
                add(
                    Problem(
                        "cross_zone_window_mismatch",
                        "zone",
                        zone.id,
                        "cross_zone_window",
                    )
                )

    problems.extend(_group_problems(config, zones, area_ids))
    problems.extend(_chime_problems(config.chime))
    problems.extend(_log_problems(config))
    problems.extend(_health_problems(config))
    problems.extend(_user_problems(config, area_ids, scenario_ids))
    problems.extend(
        _device_problems(config, scenario_ids, {u.id for u in config.users})
    )
    problems.extend(_contact_problems(config))
    problems.extend(_mqtt_problems(config))
    problems.extend(_security_problems(config))
    for profile in config.profiles:
        problems.extend(_profile_problems(profile))
    # An action that names somebody the address book no longer has would
    # reach nobody and say nothing about it, which is the failure §7 exists
    # to prevent. Checked here rather than inside the action, because only
    # the whole configuration knows who the contacts are.
    for profile in config.profiles:
        for action in profile.actions:
            for ref in notify_contacts(action):
                contact = config.contact(ref.get("contact_id"))
                if contact is None:
                    problems.append(
                        Problem("unknown_contact", "action", action.id, "contacts")
                    )
                elif ref.get("channel_id") and not any(
                    ch.id == ref["channel_id"] for ch in contact.channels
                ):
                    problems.append(
                        Problem("unknown_channel", "action", action.id, "contacts")
                    )
    # A reference to a profile that does not exist would silently fall through
    # to the default, which is exactly the kind of "why is it quiet?" this
    # project exists to avoid.
    for kind, objects in (
        ("area", config.areas),
        ("zone", config.zones),
        ("scenario", config.scenarios),
        ("group", config.groups),
    ):
        for obj in objects:
            ref = obj.response_profile_id
            if ref is not None and ref not in profile_ids:
                problems.append(
                    Problem("unknown_profile", kind, obj.id, "response_profile_id")
                )
    problems.extend(_rule_problems(config))
    return problems


def _rule_problems(config: FoyerConfig) -> list[Problem]:
    """Automatic arming rules (SPEC §9.4).

    The closed model is the point, so everything here is a question of
    whether the rule can act at all: a trigger with nothing to watch, an
    action with nothing to arm, a disarm naming only the perimeter — each
    one is a rule that would sit on page 12 looking configured and never do
    anything, which is the failure mode this whole project is written
    against.

    What is *not* checked here is whether automatic disarming is enabled:
    that is a live condition, not a configuration error, and the engine says
    so at the moment it declines to act (§9.4 point 2).
    """
    problems: list[Problem] = []
    area_ids = {a.id for a in config.areas}
    scenario_ids = {s.id for s in config.scenarios}
    contact_ids = {c.id for c in config.contacts}
    ids = [r.id for r in config.rules]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem("duplicate_id", "rule", dup))
    seen: set[str] = set()
    for rule in config.rules:

        def add(code: str, field: str | None = None, ref: str = rule.id) -> None:
            problems.append(Problem(code, "rule", ref, field))

        if not rule.name.strip():
            add("name_required", "name")
        slug = _slug(rule.name)
        if slug and slug in seen:
            # The rule's name is on every row it writes (§9.4). Two rules
            # alike would make the log unable to answer which one acted.
            add("duplicate_name", "name")
        seen.add(slug)

        trigger = rule.trigger
        if trigger.kind in (RuleTriggerKind.ABSENCE, RuleTriggerKind.PRESENCE):
            if not trigger.entity_ids:
                add("rule_without_people", "trigger")
            for entity_id in trigger.entity_ids:
                if _domain(entity_id) not in PRESENCE_DOMAINS:
                    add("rule_entity_invalid", "trigger")
        elif trigger.kind is RuleTriggerKind.ENTITY:
            if len(trigger.entity_ids) != 1 or not trigger.entity_ids[0]:
                add("rule_entity_required", "trigger")
            if not (trigger.state or "").strip():
                add("rule_state_required", "trigger")
        elif trigger.at is None or parse_hhmm(trigger.at) is None:
            add("time_invalid", "trigger")
        if trigger.level and not _in_range(trigger.minutes, 0, MAX_RULE_MINUTES):
            add("rule_out_of_range", "trigger")
        for weekdays, field in (
            (trigger.weekdays, "trigger"),
            (rule.window.weekdays, "window"),
        ):
            if any(day not in range(7) for day in weekdays):
                add("weekday_invalid", field)

        if rule.action is RuleActionKind.DISARM:
            if not rule.area_ids:
                add("rule_without_areas", "area_ids")
            for area_id in rule.area_ids:
                if area_id not in area_ids:
                    add("unknown_area", "area_ids")
            named = [config.area(a) for a in rule.area_ids]
            if named and all(a is not None and a.is_perimeter for a in named):
                # It would never do anything: §9.4 point 3 takes every area
                # it names out of the action. Better said here, once, than
                # by a row under `system` every evening.
                add("rule_only_perimeter", "area_ids")
        elif rule.scenario_id is None or rule.scenario_id not in scenario_ids:
            add("unknown_scenario", "scenario_id")

        window = rule.window
        for value, field in ((window.after, "after"), (window.before, "before")):
            if value is not None and parse_hhmm(value) is None:
                add("time_invalid", field)
        if (window.after is None) != (window.before is None):
            add("window_incomplete", "before")
        if not _in_range(rule.guards.quiet_minutes, 1, MAX_RULE_MINUTES):
            add("rule_out_of_range", "guards")
        if not _in_range(rule.grace_seconds, 0, MAX_GRACE_SECONDS):
            add("rule_out_of_range", "grace_seconds")
        for contact_id in rule.notify_contact_ids:
            if contact_id not in contact_ids:
                add("unknown_contact", "notify_contact_ids")
        if rule.grace_seconds > 0 and not rule.notify_contact_ids:
            # A countdown nobody is told about is a delay, not a grace
            # period: the Cancel button of §9.4 has to reach somebody.
            add("rule_countdown_without_contacts", "notify_contact_ids")
    return problems


def notify_contacts(action: ProfileAction) -> tuple[dict, ...]:
    """The contacts a notify action names, in order (SPEC §6.2, §7.1).

    One reader, used by validation, by the planner and by the simulator's
    trace, so that "who does this reach" has one answer. Each entry is
    ``{contact_id, channel_id}``; a channel of None means the contact's own
    order of priority decides, which is what §7.1 says an ordered channel
    list is for.
    """
    if action.kind is not ActionKind.NOTIFY:
        return ()
    out: list[dict] = []
    for ref in action.params.get("contacts") or ():
        if isinstance(ref, str):
            out.append({"contact_id": ref, "channel_id": None})
        elif isinstance(ref, dict) and ref.get("contact_id"):
            out.append(
                {
                    "contact_id": str(ref["contact_id"]),
                    "channel_id": str(ref["channel_id"])
                    if ref.get("channel_id")
                    else None,
                }
            )
    return tuple(out)


def _contact_problems(config: FoyerConfig) -> list[Problem]:
    """The address book (SPEC §7.1).

    Two rules carry weight. A contact **has at least one channel**: a person
    in the book with no way of reaching them is a step in an escalation that
    silently reaches nobody, and the whole of §7 is about not discovering
    that during the emergency. And a channel **names a `notify.*` service**,
    because that is what a channel is — Foyer orchestrates transports, it
    does not implement them (§1.2).
    """
    problems: list[Problem] = []
    ids = [c.id for c in config.contacts]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem("duplicate_id", "contact", dup))
    user_ids = {u.id for u in config.users}
    seen: set[str] = set()
    for contact in config.contacts:

        def add(code: str, field: str | None = None, ref: str = contact.id) -> None:
            problems.append(Problem(code, "contact", ref, field))

        if not contact.name.strip():
            add("name_required", "name")
        slug = _slug(contact.name)
        if slug and slug in seen:
            # Two contacts alike are two the trace and the log cannot tell
            # apart, and "notified Luca" would then answer nothing.
            add("duplicate_name", "name")
        seen.add(slug)
        if contact.linked_user_id and contact.linked_user_id not in user_ids:
            add("unknown_user", "linked_user_id")
        if not contact.channels:
            add("contact_without_channels", "channels")
        channel_ids = [ch.id for ch in contact.channels]
        if len(set(channel_ids)) != len(channel_ids):
            add("duplicate_id", "channels")
        for channel in contact.channels:
            if not str(channel.service or "").startswith("notify."):
                add("notify_service_required", "channels")
            if not isinstance(channel.data, Mapping):
                add("data_invalid", "channels")
        for field in ("quiet_start", "quiet_end"):
            value = getattr(contact, field)
            if value is not None and parse_hhmm(value) is None:
                add("time_invalid", field)
        if (contact.quiet_start is None) != (contact.quiet_end is None):
            add("quiet_hours_incomplete", "quiet_end")
    return problems


def _user_problems(
    config: FoyerConfig, area_ids: set[str], scenario_ids: set[str]
) -> list[Problem]:
    """People, their scope and their validity (SPEC §8.1).

    Codes are not checked here: this module is pure and never sees one. What
    it can check is everything around them — that the scope points at things
    that exist, that a window is not closed before it opens, and that one
    Home Assistant account is linked to at most one person, or "who did this"
    would have two answers.
    """
    problems: list[Problem] = []
    ids = [u.id for u in config.users]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem("duplicate_id", "user", dup))
    linked: set[str] = set()
    for user in config.users:
        if not user.name.strip():
            problems.append(Problem("name_required", "user", user.id, "name"))
        if user.ha_user_id:
            if user.ha_user_id in linked:
                problems.append(
                    Problem("ha_user_already_linked", "user", user.id, "ha_user_id")
                )
            linked.add(user.ha_user_id)
        for permission in sorted(user.permissions):
            if permission not in {p.value for p in Permission}:
                problems.append(
                    Problem("unknown_permission", "user", user.id, "permissions")
                )
        if user.allowed_area_ids is not None and any(
            a not in area_ids for a in user.allowed_area_ids
        ):
            problems.append(
                Problem("unknown_area", "user", user.id, "allowed_area_ids")
            )
        if user.allowed_scenario_ids is not None and any(
            s not in scenario_ids for s in user.allowed_scenario_ids
        ):
            problems.append(
                Problem("unknown_scenario", "user", user.id, "allowed_scenario_ids")
            )
        if (
            user.valid_from is not None
            and user.valid_until is not None
            and user.valid_until <= user.valid_from
        ):
            problems.append(Problem("window_inverted", "user", user.id, "valid_until"))
        # An exemption on somebody no Home Assistant account points at can
        # never apply, and reads as a setting that does nothing.
        if user.code_exempt_when_identified and not user.ha_user_id:
            problems.append(
                Problem(
                    "exemption_needs_a_linked_account",
                    "user",
                    user.id,
                    "code_exempt_when_identified",
                )
            )
    user_ids = {u.id for u in config.users}
    for scenario in config.scenarios:
        allowed = scenario.allowed_user_ids
        if allowed is None:
            continue
        if not allowed:
            # A scenario nobody may arm is not a restriction, it is a scenario
            # that does not work. "Everyone" is the empty answer, not this.
            problems.append(
                Problem("no_user_allowed", "scenario", scenario.id, "allowed_user_ids")
            )
        for user_id in allowed:
            if user_id not in user_ids:
                problems.append(
                    Problem("unknown_user", "scenario", scenario.id, "allowed_user_ids")
                )
    for zone in config.zones:
        if zone.key is not None and zone.key.user_id not in (None, *user_ids):
            problems.append(Problem("unknown_user", "zone", zone.id, "key"))
    return problems


def _device_problems(
    config: FoyerConfig, scenario_ids: set[str], user_ids: set[str]
) -> list[Problem]:
    """Arming devices, and what each kind cannot do without (SPEC §9.3).

    Two rules carry weight beyond tidiness.

    A **tag never has a ``ref``**. A ref is what a message puts in its
    ``device_id`` field, and a tag's whole nature is that it carries no code:
    a tag with a ref would be an identity anybody on the broker could claim by
    typing its name, with no code to stop them.

    A **tag always names a person**. §8.2 calls it a *per-user* NFC tag, and
    that is the only reason it counts as a channel that identifies: a token
    nobody owns is a shared credential, which is a keypad by another name and
    must be configured as one, with a code.
    """
    problems: list[Problem] = []
    ids = [d.id for d in config.devices]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem("duplicate_id", "device", dup))
    refs: set[str] = set()
    for device in config.devices:

        def add(code: str, field: str | None = None, ref: str = device.id) -> None:
            problems.append(Problem(code, "device", ref, field))

        if not device.name.strip():
            add("name_required", "name")
        if device.kind is DeviceKind.KEYPAD:
            if not (device.ref or "").strip():
                add("ref_required", "ref")
            elif device.ref in refs:
                # Two keypads answering to one name would share a lockout
                # counter and produce a log row that names neither of them.
                add("duplicate_ref", "ref")
            if device.entity_id or device.user_id:
                add("keypad_has_no_entity", "entity_id")
        else:
            if device.ref:
                add("tag_has_no_ref", "ref")
            if not device.entity_id or _domain(device.entity_id) not in EVENT_DOMAINS:
                add("tag_entity_required", "entity_id")
            if not device.user_id:
                add("tag_needs_a_user", "user_id")
            elif device.user_id not in user_ids:
                add("unknown_user", "user_id")
            if device.command is not KeyCommand.DISARM:
                if not device.scenario_id:
                    add("scenario_required", "scenario_id")
                elif device.scenario_id not in scenario_ids:
                    add("unknown_scenario", "scenario_id")
        if device.ref:
            refs.add(device.ref)
    return problems


def _domain(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def _mqtt_problems(config: FoyerConfig) -> list[Problem]:
    """The MQTT contract's settings (SPEC §9.2).

    An empty topic is not a mistake: it means the default, which the runtime
    resolves from the installation id. A topic that is written down, though,
    is published to and subscribed to as one destination, so it may carry no
    wildcard and no empty level — and the two topics may not be the same one,
    or Foyer would answer its own commands.
    """
    problems: list[Problem] = []
    mqtt = config.settings.mqtt
    for field in ("command_topic", "state_topic"):
        topic = getattr(mqtt, field)
        if topic and not _valid_topic(topic):
            problems.append(Problem("topic_invalid", "settings", None, field))
    if mqtt.command_topic and mqtt.command_topic == mqtt.state_topic:
        problems.append(Problem("topics_identical", "settings", None, "state_topic"))
    if not _in_range(mqtt.qos, 0, MAX_MQTT_QOS):
        problems.append(Problem("qos_out_of_range", "settings", None, "qos"))
    return problems


def _valid_topic(topic: str) -> bool:
    if len(topic) > MAX_MQTT_TOPIC or topic.strip() != topic:
        return False
    levels = topic.split("/")
    return all(level and not (set(level) & MQTT_TOPIC_FORBIDDEN) for level in levels)


def _security_problems(config: FoyerConfig) -> list[Problem]:
    """The code length and the lockout numbers (§8.1, §8.4)."""
    problems: list[Problem] = []
    security = config.settings.security
    if not _in_range(security.code_length, MIN_CODE_LENGTH, MAX_CODE_LENGTH):
        problems.append(
            Problem("code_length_out_of_range", "settings", None, "code_length")
        )
    if not _in_range(
        security.lockout_failures, MIN_LOCKOUT_FAILURES, MAX_LOCKOUT_FAILURES
    ):
        problems.append(
            Problem("lockout_out_of_range", "settings", None, "lockout_failures")
        )
    for field in ("lockout_window", "lockout_duration"):
        if not _in_range(
            getattr(security, field), MIN_LOCKOUT_SECONDS, MAX_LOCKOUT_SECONDS
        ):
            problems.append(Problem("lockout_out_of_range", "settings", None, field))
    return problems


def _valid_directory(path: str) -> bool:
    """A relative directory under the configuration folder, and not ``www``."""
    if not path or path.startswith(("/", "\\")) or ":" in path:
        return False
    parts = re.split(r"[\\/]+", path.strip("/"))
    return bool(parts) and all(parts) and ".." not in parts and parts[0] != "www"


def _profile_problems(profile: ResponseProfile) -> list[Problem]:
    problems: list[Problem] = []

    def add(code: str, field: str | None = None, ref: str = profile.id) -> None:
        problems.append(Problem(code, "profile", ref, field))

    if not profile.name.strip():
        add("name_required", "name")
    if not 1 <= profile.severity <= MAX_SEVERITY:
        add("severity_out_of_range", "severity")
    ids = [a.id for a in profile.actions]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        add("duplicate_id", None, dup)
    for action in profile.actions:
        problems.extend(_action_problems(action))
    return problems


def _action_problems(action: ProfileAction) -> list[Problem]:
    problems: list[Problem] = []

    def add(code: str, field: str | None = None) -> None:
        problems.append(Problem(code, "action", action.id, field))

    if not action.moments:
        add("moments_required", "moments")
    if len(action.conditions) > MAX_CONDITIONS:
        # The bound of §6.3 is the line between a response engine and a second
        # automation engine. It is enforced, not documented.
        add("too_many_conditions", "conditions")
    for condition in action.conditions:
        if isinstance(condition, TimeCondition):
            if parse_hhmm(condition.after) is None or (
                parse_hhmm(condition.before) is None
            ):
                add("time_invalid", "conditions")
            elif condition.after == condition.before:
                # An empty window would silence the action for ever.
                add("empty_window", "conditions")
        elif isinstance(condition, StateCondition) and (
            "." not in condition.entity_id or not condition.state
        ):
            add("condition_entity_invalid", "conditions")
    for field in TEMPLATED_FIELDS:
        value = action.params.get(field)
        if isinstance(value, str) and unknown_variables(value):
            add("unknown_variable", field)
    problems.extend(_escalation_problems(action, add))
    problems.extend(_params_problems(action, add))
    return problems


# What an escalation step may be, and what it may answer (SPEC §7.2, part 1
# decisions 1 and 2). A step reaches a person: it is a notification, at an
# offset. A siren scheduled five minutes out would outlive the cutoff of
# §5.3, and a step on ``armed`` would be an escalation nobody can
# acknowledge, because only an incident and a technical alarm have an
# acknowledgement at all.
ESCALATION_KINDS: frozenset[ActionKind] = frozenset(
    {ActionKind.NOTIFY, ActionKind.PERSISTENT_NOTIFICATION}
)
ESCALATION_MOMENTS: frozenset[Moment] = frozenset(
    {Moment.TRIGGERED, Moment.TECHNICAL_RAISED}
)


def _escalation_problems(action: ProfileAction, add) -> list[Problem]:
    if action.escalation_offset is None:
        return []
    if not _in_range(action.escalation_offset, 0, MAX_ESCALATION_OFFSET):
        add("escalation_offset_out_of_range", "escalation_offset")
    if action.kind not in ESCALATION_KINDS:
        add("escalation_kind_invalid", "escalation_offset")
    if not action.moments <= ESCALATION_MOMENTS:
        add("escalation_moment_invalid", "moments")
    return []


def _params_problems(action: ProfileAction, add) -> list[Problem]:
    """What each action kind needs to be runnable at all (SPEC §6.2)."""
    params = action.params
    entity_ids = params.get("entity_ids") or []
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]
    domains = ACTION_DOMAINS.get(action.kind.value)
    kind = action.kind

    def entity_field() -> str:
        return (
            "entity_id"
            if kind in (ActionKind.CAMERA, ActionKind.SCENE, ActionKind.TTS)
            else "entity_ids"
        )

    if kind is ActionKind.NOTIFY:
        service = str(params.get("service") or "")
        contacts = notify_contacts(action)
        # Both forms exist and both keep existing (part 1 decision 8): the
        # service every installation already writes, and the address book
        # §6.2 asks for. What is refused is naming neither — a notification
        # with no recipient — and naming both, which would leave "who did
        # this reach?" with two answers and the trace with one.
        if not service and not contacts:
            add("notify_target_required", "service")
        elif service and contacts:
            add("notify_target_ambiguous", "contacts")
        elif service and not service.startswith("notify."):
            add("notify_service_required", "service")
        if not str(params.get("message") or "").strip():
            add("message_required", "message")
        camera = params.get("camera_entity_id")
        if camera is not None and not str(camera).startswith("camera."):
            add("entity_domain", "camera_entity_id")
        attachment = params.get("attachment")
        if attachment is not None and str(attachment) not in NOTIFY_ATTACHMENTS:
            # Each transport reads its own key and discards the rest without a
            # word, so a value nobody implements is a picture that never
            # arrives and never explains itself.
            add("unknown_attachment", "attachment")
    elif kind is ActionKind.DELAY:
        if not _in_range(_int_or_none(params.get("seconds")), 1, MAX_ACTION_DELAY):
            add("delay_out_of_range", "seconds")
    elif kind is ActionKind.CALL_SERVICE:
        if not _is_slug(params.get("domain")) or not _is_slug(params.get("service")):
            add("service_required", "service")
        if params.get("data") is not None and not isinstance(params.get("data"), dict):
            add("data_invalid", "data")
    elif kind is ActionKind.TTS:
        if not str(params.get("entity_id") or "").startswith("tts."):
            add("entity_required", "entity_id")
        if not params.get("media_player_entity_ids"):
            add("entity_required", "media_player_entity_ids")
        if not str(params.get("message") or "").strip():
            add("message_required", "message")
    elif kind in (ActionKind.CAMERA, ActionKind.SCENE):
        entity = str(params.get("entity_id") or "")
        if not entity or entity.split(".", 1)[0] not in (domains or ()):
            add("entity_required", "entity_id")
        if kind is ActionKind.CAMERA:
            if params.get("mode") not in ("snapshot", "record"):
                add("camera_mode_invalid", "mode")
            if params.get("mode") == "record" and not _in_range(
                _int_or_none(params.get("duration")), 1, MAX_CAMERA_DURATION
            ):
                add("duration_out_of_range", "duration")
    elif domains is not None:
        if not entity_ids:
            add("entity_required", entity_field())
        elif any("." not in e or e.split(".", 1)[0] not in domains for e in entity_ids):
            add("entity_domain", entity_field())
        if kind is ActionKind.SIREN and not _in_range(
            _int_or_none(params.get("duration")), 1, MAX_SIREN_DURATION
        ):
            add("siren_out_of_range", "duration")
        if kind is ActionKind.SWITCH:
            if params.get("state") not in ("on", "off"):
                add("switch_state_invalid", "state")
            if params.get("revert_after") is not None and not _in_range(
                _int_or_none(params.get("revert_after")), 1, MAX_ACTION_DELAY
            ):
                add("delay_out_of_range", "revert_after")
        if kind is ActionKind.LIGHT and not _in_range(
            _int_or_none(params.get("brightness")), 0, 255
        ):
            add("brightness_out_of_range", "brightness")
    return []


def _int_or_none(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None if value is None else 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0  # not a number: out of every range


def _is_slug(value) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z0-9_]+", value))


def _group_problems(
    config: FoyerConfig, zones: dict[str, Zone], area_ids: set[str]
) -> list[Problem]:
    """Groups and cross-zone pairs share one engine, so one rule: a zone
    belongs to at most one of them, or its activation would count twice."""
    problems: list[Problem] = []
    memberships: dict[str, int] = {}
    for group in config.groups:

        def add(code: str, field: str | None = None, ref: str = group.id) -> None:
            problems.append(Problem(code, "group", ref, field))

        if not group.name.strip():
            add("name_required", "name")
        if group.area_id not in area_ids:
            add("unknown_area", "area_id")
        members = group.members
        if len(set(members)) != len(members) or len(members) < 2:
            add("group_members", "members")
        if any(
            m not in zones or zones[m].channel is not Channel.INTRUSION for m in members
        ):
            add("group_member_invalid", "members")
        if not 2 <= group.n <= max(len(set(members)), 2):
            add("group_threshold", "n")
        elif (
            len({m for m in set(members) if m in zones and zones[m].enabled}) < group.n
        ):
            # Enough members on paper, not enough switched on. The group
            # cannot be satisfied and the engine therefore ignores it, so the
            # page has to say why rather than leave a group that looks
            # configured and does nothing (found in review).
            add("group_members_disabled", "members")
        if not _in_range(
            group.window_seconds, MIN_VERIFICATION_WINDOW, MAX_VERIFICATION_WINDOW
        ):
            add("window_out_of_range", "window_seconds")
        for member in set(members):
            memberships[member] = memberships.get(member, 0) + 1
    pairs = {
        cross_zone_id(z.id, z.cross_zone_id)
        for z in config.zones
        if z.cross_zone_id is not None and z.cross_zone_id != z.id
    }
    for pair in pairs:
        for member in pair.removeprefix("cross:").split("+"):
            memberships[member] = memberships.get(member, 0) + 1
    for zone_id, count in sorted(memberships.items()):
        if count > 1:
            problems.append(Problem("zone_in_two_groups", "zone", zone_id))
    return problems


def _health_problems(config: FoyerConfig) -> list[Problem]:
    """System health (§12): the mains entity, the watchdog and the radios.

    The two rules worth naming here are the ones that would otherwise fail
    silently. A watchdog switched on with no URL pings nothing and reports a
    failure every quarter of an hour, which teaches the household to ignore
    the one warning that means Foyer cannot reach the outside world. And a
    radio with no coordinator entity cannot be gated at all — §12.5 is
    explicit that the gate is what separates interference from a dead
    switch — so it is refused rather than accepted as half a heuristic.
    """
    health = config.health
    problems: list[Problem] = []

    def add(code: str, field: str, item: str | None = None) -> None:
        problems.append(Problem(code, "health", item, field))

    entity = health.mains_entity_id
    if entity is not None and "." not in entity:
        add("health_entity_invalid", "mains_entity_id")
    if entity and not health.mains_lost_states:
        add("mains_states_required", "mains_lost_states")

    watchdog = health.watchdog
    if watchdog.enabled and not watchdog.url.startswith(("http://", "https://")):
        add("watchdog_url_required", "url")
    if not _in_range(watchdog.interval, MIN_WATCHDOG_INTERVAL, MAX_WATCHDOG_INTERVAL):
        add("health_out_of_range", "interval")
    if not _in_range(watchdog.timeout, MIN_WATCHDOG_TIMEOUT, MAX_WATCHDOG_TIMEOUT):
        add("health_out_of_range", "timeout")
    if not _in_range(watchdog.failures, MIN_WATCHDOG_FAILURES, MAX_WATCHDOG_FAILURES):
        add("health_out_of_range", "failures")
    if watchdog.timeout >= watchdog.interval:
        # A ping that may take longer than the gap to the next one is a
        # queue, not a heartbeat.
        add("watchdog_timeout_too_long", "timeout")

    for value, field, low, high in (
        (health.rf_zones, "rf_zones", MIN_RF_ZONES, MAX_RF_ZONES),
        (health.rf_window, "rf_window", MIN_RF_WINDOW, MAX_RF_WINDOW),
        (health.rf_confirm, "rf_confirm", MIN_RF_CONFIRM, MAX_RF_CONFIRM),
        (
            health.channel_sweep,
            "channel_sweep",
            MIN_CHANNEL_SWEEP,
            MAX_CHANNEL_SWEEP,
        ),
        (
            health.channel_failures,
            "channel_failures",
            MIN_CHANNEL_FAILURES,
            MAX_CHANNEL_FAILURES,
        ),
    ):
        if not _in_range(value, low, high):
            add("health_out_of_range", field)

    ids = [r.id for r in health.radios]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem("duplicate_id", "radio", dup))
    entry_ids = [r.entry_id for r in health.radios if r.entry_id]
    for dup in sorted({i for i in entry_ids if entry_ids.count(i) > 1}):
        # Two radios claiming one config entry would count the same zones
        # twice and gate them on two coordinators.
        problems.append(Problem("duplicate_radio_entry", "radio", dup))
    for radio in health.radios:
        if not radio.name.strip():
            problems.append(Problem("name_required", "radio", radio.id, "name"))
        if not radio.entry_id:
            problems.append(
                Problem("radio_entry_required", "radio", radio.id, "entry_id")
            )
        if radio.coordinator_entity_id and "." not in radio.coordinator_entity_id:
            problems.append(
                Problem(
                    "health_entity_invalid",
                    "radio",
                    radio.id,
                    "coordinator_entity_id",
                )
            )
        if radio.enabled and not radio.coordinator_entity_id:
            problems.append(
                Problem(
                    "coordinator_required", "radio", radio.id, "coordinator_entity_id"
                )
            )
        if radio.n_zones is not None and not _in_range(
            radio.n_zones, MIN_RF_ZONES, MAX_RF_ZONES
        ):
            problems.append(
                Problem("health_out_of_range", "radio", radio.id, "n_zones")
            )
        if radio.window is not None and not _in_range(
            radio.window, MIN_RF_WINDOW, MAX_RF_WINDOW
        ):
            problems.append(Problem("health_out_of_range", "radio", radio.id, "window"))
    return problems


def _log_problems(config: FoyerConfig) -> list[Problem]:
    """The event log's own numbers (§10.2, §10.4).

    Checked here as well as in `store/editing`, because a restored backup
    reaches the stored configuration through `validate` alone — and a
    retention of zero days is not a short retention, it is a purge that
    deletes the whole of a category every day it runs (found in review).
    """
    log = config.settings.log
    problems: list[Problem] = []
    if any(
        not MIN_RETENTION_DAYS <= log.retention(c.value) <= MAX_RETENTION_DAYS
        for c in LogCategory
    ):
        problems.append(Problem("retention_out_of_range", "settings", None, "log"))
    after = log.pseudonymise_after
    if after is not None and not (
        MIN_PSEUDONYMISE_DAYS <= after <= MAX_PSEUDONYMISE_DAYS
    ):
        problems.append(
            Problem("retention_out_of_range", "settings", None, "pseudonymise_after")
        )
    return problems


def _chime_problems(chime: ChimeSettings) -> list[Problem]:
    problems: list[Problem] = []

    def add(code: str, field: str) -> None:
        problems.append(Problem(code, "chime", None, field))

    ids = [t.entity_id for t in chime.targets]
    domains = [t.split(".", 1)[0] for t in ids]
    if any(
        "." not in t or d not in CHIME_DOMAINS
        for t, d in zip(ids, domains, strict=True)
    ):
        add("chime_target_invalid", "targets")
    if len(set(ids)) != len(ids):
        add("chime_target_invalid", "targets")
    for target in chime.targets:
        # A target's own quiet hours replace the global ones (decision 8), so
        # they follow the same rules: both ends, or neither.
        for field in ("quiet_start", "quiet_end"):
            value = getattr(target, field)
            if value is not None and parse_hhmm(value) is None:
                add("time_invalid", "targets")
        if (target.quiet_start is None) != (target.quiet_end is None):
            add("quiet_hours_incomplete", "targets")
    if chime.mode is ChimeMode.SPEECH and not (
        chime.tts_entity and chime.tts_entity.startswith("tts.")
    ):
        add("chime_tts_required", "tts_entity")
    if chime.mode is ChimeMode.SOUND and "media_player" in domains and not chime.sound:
        add("chime_sound_required", "sound")
    if not _in_range(chime.volume, 0, 100):
        add("volume_out_of_range", "volume")
    for field in ("quiet_start", "quiet_end"):
        value = getattr(chime, field)
        if value is not None and parse_hhmm(value) is None:
            add("time_invalid", field)
    if (chime.quiet_start is None) != (chime.quiet_end is None):
        add("quiet_hours_incomplete", "quiet_end")
    return problems


def _zone_problems(
    zone: Zone, area_ids: set[str], scenario_ids: set[str]
) -> list[Problem]:
    problems: list[Problem] = []

    def add(code: str, field: str | None = None) -> None:
        problems.append(Problem(code, "zone", zone.id, field))

    if not zone.name.strip():
        add("name_required", "name")
    if zone.area_id not in area_ids:
        add("unknown_area", "area_id")
    domain = zone.entity_id.split(".", 1)[0]
    if "." not in zone.entity_id or domain not in ZONE_DOMAINS:
        add("unsupported_domain", "entity_id")

    trigger = zone.trigger
    if isinstance(trigger, EventTrigger) != (domain in EVENT_DOMAINS):
        # Event and tag entities hold a timestamp: only an event trigger can
        # read them, and an event trigger can read nothing else.
        add("trigger_domain", "trigger")
    if isinstance(trigger, StateTrigger) and trigger.states & FAULT_STATES:
        # Unavailable and unknown are faults, never triggers (INV-4).
        add("fault_state_as_trigger", "trigger")
    if isinstance(trigger, NumericTrigger):
        if trigger.hysteresis < 0:
            add("negative_hysteresis", "trigger")
        if trigger.operator is NumericOperator.EQ and trigger.hysteresis:
            add("eq_hysteresis", "trigger")
    if isinstance(trigger, EventTrigger):
        if domain == "event" and not trigger.event_type:
            add("event_type_required", "trigger")
        if domain == "tag" and trigger.event_type:
            add("event_type_not_allowed", "trigger")

    if zone.channel is not Channel.INTRUSION:
        # Verification and chime exist for intrusion zones only: the
        # technical channel is live and single-shot, a key commands (§5.5).
        if zone.cross_zone_id is not None:
            add("intrusion_only", "cross_zone_id")
        if zone.trigger_count != 1:
            add("intrusion_only", "trigger_count")
        if zone.chime:
            add("intrusion_only", "chime")
        if zone.silent and zone.channel is Channel.KEY:
            # A key zone commands; it has no response to silence (§4.7).
            add("intrusion_only", "silent")
    if zone.channel is Channel.TECHNICAL and not zone.always_on:
        # The technical channel is live whatever the arming state (§5.5):
        # the property must say so, not contradict it.
        add("technical_always_on", "always_on")
    if zone.chime and zone.always_on:
        # Always monitored, so never "not monitored": it could never chime.
        add("chime_always_on", "chime")
    if not _in_range(zone.trigger_count, 1, MAX_TRIGGER_COUNT):
        add("count_out_of_range", "trigger_count")
    for field in ("trigger_window", "cross_zone_window"):
        if not _in_range(
            getattr(zone, field), MIN_VERIFICATION_WINDOW, MAX_VERIFICATION_WINDOW
        ):
            add("window_out_of_range", field)
    if zone.channel is Channel.KEY:
        key = zone.key
        if key is None:
            add("key_action_required", "key")
        elif key.on_activate in (KeyCommand.ARM, KeyCommand.TOGGLE) and (
            key.scenario_id not in scenario_ids
        ):
            add("key_scenario_required", "key")
        if zone.always_on:
            add("key_always_on", "always_on")
    elif zone.key is not None:
        add("key_action_not_allowed", "key")

    if zone.always_on and zone.entry_mode is not EntryMode.INSTANT:
        # A 24h zone fires whatever the arming state: no entry delay applies.
        add("always_on_must_be_instant", "entry_mode")
    if zone.arm_policy is ArmPolicy.AUTO_BYPASS and not zone.bypassable:
        add("auto_bypass_needs_bypassable", "arm_policy")
    if zone.arm_hold_timeout is not None:
        if zone.arm_policy is not ArmPolicy.ARM_AFTER_CLOSING:
            add("hold_needs_arm_after_closing", "arm_hold_timeout")
        elif not _in_range(
            zone.arm_hold_timeout, MIN_ARM_HOLD_TIMEOUT, MAX_ARM_HOLD_TIMEOUT
        ):
            add("hold_out_of_range", "arm_hold_timeout")
    if not _in_range(zone.entry_delay, 0, MAX_ENTRY_DELAY):
        add("delay_out_of_range", "entry_delay")
    if not _in_range(
        zone.supervision_timeout, MIN_SUPERVISION_TIMEOUT, MAX_SUPERVISION_TIMEOUT
    ):
        add("supervision_out_of_range", "supervision_timeout")
    if zone.battery_entity_id is not None:
        battery_domain = zone.battery_entity_id.split(".", 1)[0]
        if "." not in zone.battery_entity_id or battery_domain not in BATTERY_DOMAINS:
            add("unsupported_battery_domain", "battery_entity_id")
        elif zone.battery_entity_id == zone.entity_id:
            # The zone's own entity is not its battery: reading it as one
            # would make every open door a flat cell.
            add("battery_is_zone_entity", "battery_entity_id")
    return problems


def edit_conflicts(
    old: FoyerConfig, new: FoyerConfig, state: RuntimeState
) -> list[Problem]:
    """Changes refused while the parts they touch are live.

    An area that is not disarmed — or a scenario that is running — keeps the
    configuration it was armed with: editing a zone under an armed area changes
    what is protecting the house right now, without anyone disarming. Areas
    that are disarmed can be programmed while others stay armed.
    """
    live_areas = {
        a.id for a in old.areas if state.area(a.id).state is not AreaState.DISARMED
    }
    problems: list[Problem] = []
    old_areas = {a.id: a for a in old.areas}
    new_areas = {a.id: a for a in new.areas}
    for area_id in live_areas:
        if old_areas.get(area_id) != new_areas.get(area_id):
            problems.append(Problem("area_not_disarmed", "area", area_id))

    old_zones = {z.id: z for z in old.zones}
    new_zones = {z.id: z for z in new.zones}

    def areas_of(*zone_ids: str | None) -> set[str]:
        return {
            zones[z].area_id
            for zones in (old_zones, new_zones)
            for z in zone_ids
            if z in zones
        }

    for zone in old.zones:
        changed = new_zones.get(zone.id)
        if changed == zone:
            continue
        # A cross-zone partner is verified by this zone: changing the pair
        # changes what protects the partner's area too.
        touched = areas_of(
            zone.id, zone.cross_zone_id, changed.cross_zone_id if changed else None
        )
        if touched & live_areas:
            problems.append(Problem("area_not_disarmed", "zone", zone.id))
    for zone in new.zones:
        if zone.id not in old_zones and (
            areas_of(zone.id, zone.cross_zone_id) & live_areas
        ):
            problems.append(Problem("area_not_disarmed", "zone", zone.id))

    old_groups = {g.id: g for g in old.groups}
    new_groups = {g.id: g for g in new.groups}
    for group_id in old_groups.keys() | new_groups.keys():
        before, after = old_groups.get(group_id), new_groups.get(group_id)
        if before == after:
            continue
        touched = areas_of(
            *(before.members if before else ()), *(after.members if after else ())
        ) | {g.area_id for g in (before, after) if g is not None}
        if touched & live_areas:
            problems.append(Problem("area_not_disarmed", "group", group_id))

    active = state.active_scenario_id
    if active is not None and old.scenario(active) != new.scenario(active):
        problems.append(Problem("scenario_active", "scenario", active))

    # A response profile is what an armed area would do if something happened
    # now: changing it under an armed area changes that, without a disarm.
    live_profiles = _live_profiles(old, live_areas) | _live_profiles(new, live_areas)
    old_profiles = {p.id: p for p in old.profiles}
    new_profiles = {p.id: p for p in new.profiles}
    for profile_id in old_profiles.keys() | new_profiles.keys():
        if old_profiles.get(profile_id) == new_profiles.get(profile_id):
            continue
        if profile_id in live_profiles:
            problems.append(Problem("area_not_disarmed", "profile", profile_id))
    if live_areas and old.settings != new.settings:
        for field in (
            "default_profile_id",
            "technical_profile_id",
            "silent_suppresses",
        ):
            if getattr(old.settings, field) != getattr(new.settings, field):
                problems.append(Problem("area_not_disarmed", "settings", None, field))
    return problems


def _live_profiles(config: FoyerConfig, live_areas: set[str]) -> set[str]:
    """Every profile an area that is not disarmed could run right now."""
    out: set[str] = set()
    for area_id in live_areas:
        area = config.area(area_id)
        if area is None:
            continue
        out.update(
            ref
            for ref in (area.response_profile_id, config.settings.default_profile_id)
            if ref
        )
        for scenario in config.scenarios:
            if area_id in scenario.areas and scenario.response_profile_id:
                out.add(scenario.response_profile_id)
    for zone in config.zones:
        if zone.area_id in live_areas and zone.response_profile_id:
            out.add(zone.response_profile_id)
    for group in config.groups:
        members = {config.zone(m) for m in group.members}
        if group.response_profile_id and any(
            z is not None and z.area_id in live_areas for z in members
        ):
            out.add(group.response_profile_id)
    return out
