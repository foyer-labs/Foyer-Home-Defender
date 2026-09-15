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
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    AreaState,
    ArmPolicy,
    Channel,
    ChimeMode,
    ChimeSettings,
    EntryMode,
    EventTrigger,
    FoyerConfig,
    KeyCommand,
    NumericOperator,
    NumericTrigger,
    RuntimeState,
    StateTrigger,
    Zone,
)
from .verification import cross_zone_id

# What the chime can play on (SPEC §6.6).
CHIME_DOMAINS: tuple[str, ...] = ("media_player", "siren")

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
    kind: str  # "area" | "zone" | "scenario" | "settings" | "action"
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
    return problems


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

    domains = [t.split(".", 1)[0] for t in chime.targets]
    if any(
        "." not in t or d not in CHIME_DOMAINS
        for t, d in zip(chime.targets, domains, strict=True)
    ):
        add("chime_target_invalid", "targets")
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
    return problems
