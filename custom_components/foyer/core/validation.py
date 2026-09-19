"""Configuration validation, pure (SPEC §4, §5.3).

Every configuration write goes through ``validate`` in the backend before it is
stored: the panel's own checks are a courtesy, never the gate. A problem is a
stable code plus where it is, so the UI can translate it and put it next to
the field.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from .clock import parse_hhmm
from .models import (
    ARMED_HA_STATES,
    FAULT_STATES,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_CODE_LENGTH,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_LOCKOUT_FAILURES,
    MAX_LOCKOUT_SECONDS,
    MAX_MQTT_QOS,
    MAX_MQTT_TOPIC,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_CODE_LENGTH,
    MIN_LOCKOUT_FAILURES,
    MIN_LOCKOUT_SECONDS,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
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
    NumericOperator,
    NumericTrigger,
    Permission,
    ProfileAction,
    ResponseProfile,
    RuntimeState,
    StateCondition,
    StateTrigger,
    TimeCondition,
    Zone,
)
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

    zones = {z.id: z for z in config.zones}
    for zone in config.zones:
        problems.extend(_zone_problems(zone, area_ids, scenario_ids))
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
    problems.extend(_user_problems(config, area_ids, scenario_ids))
    problems.extend(
        _device_problems(config, scenario_ids, {u.id for u in config.users})
    )
    problems.extend(_mqtt_problems(config))
    problems.extend(_security_problems(config))
    for profile in config.profiles:
        problems.extend(_profile_problems(profile))
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
    problems.extend(_params_problems(action, add))
    return problems


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
        if not service.startswith("notify."):
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
