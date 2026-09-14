"""Configuration validation, pure (SPEC §4, §5.3).

Every configuration write goes through ``validate`` in the backend before it is
stored: the panel's own checks are a courtesy, never the gate. A problem is a
stable code plus where it is, so the UI can translate it and put it next to
the field.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from .models import (
    ARMED_HA_STATES,
    FAULT_STATES,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_SUPERVISION_TIMEOUT,
    AreaState,
    ArmPolicy,
    Channel,
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
    ):
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            add(Problem("duplicate_id", kind, dup))

    # Names become entity ids (areas, zones) and select options (scenarios):
    # two that slug to the same thing would collide.
    for kind, objects in (
        ("area", config.areas),
        ("zone", config.zones),
        ("scenario", config.scenarios),
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

    for zone in config.zones:
        problems.extend(_zone_problems(zone, area_ids, scenario_ids))

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
        if trigger.subtype is not None:
            add("subtype_not_supported", "trigger")

    if zone.channel is Channel.TECHNICAL:
        add("channel_not_available", "channel")
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

    new_zones = {z.id: z for z in new.zones}
    for zone in old.zones:
        changed = new_zones.get(zone.id)
        if changed == zone:
            continue
        touched = {zone.area_id} | ({changed.area_id} if changed else set())
        if touched & live_areas:
            problems.append(Problem("area_not_disarmed", "zone", zone.id))
    old_zone_ids = {z.id for z in old.zones}
    for zone in new.zones:
        if zone.id not in old_zone_ids and zone.area_id in live_areas:
            problems.append(Problem("area_not_disarmed", "zone", zone.id))

    active = state.active_scenario_id
    if active is not None and old.scenario(active) != new.scenario(active):
        problems.append(Problem("scenario_active", "scenario", active))
    return problems
