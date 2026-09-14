"""Conversion between the stored JSON documents and the core dataclasses.

Pure: no Home Assistant imports, so every round trip is testable on its own.
Two documents live here: the configuration (``foyer.config``) and the runtime
state (``foyer.state``, INV-3). They are separate because one changes when a
person edits something and the other changes every time a door opens.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..core.models import (
    AlarmKind,
    Area,
    AreaRuntime,
    AreaState,
    ArmPolicy,
    BypassReason,
    Channel,
    CodePolicy,
    EntryMode,
    EventTrigger,
    FoyerConfig,
    KeyAction,
    KeyCommand,
    KeyRelease,
    Moment,
    NotificationAction,
    NumericOperator,
    NumericTrigger,
    RuntimeState,
    Scenario,
    Settings,
    StateTrigger,
    Timer,
    TimerKind,
    TriggerSpec,
    Zone,
    ZoneType,
)

# Bump STORAGE_VERSION (breaking) or STORAGE_MINOR_VERSION (additive) together
# with a step in store/migrations. Home Assistant's Store calls the hook.
#
# 2.1 is a major bump on purpose: zone semantics (entry mode, channel, key
# zones) are not additive. A Phase 0 build reading this file would treat a key
# switch or a 24h zone as an ordinary instant zone, so it must refuse instead.
STORAGE_VERSION = 2
STORAGE_MINOR_VERSION = 1

STATE_VERSION = 1
STATE_MINOR_VERSION = 1


class ConfigError(ValueError):
    """The stored document does not describe a valid configuration."""


# --- configuration -------------------------------------------------------------


def config_from_dict(data: dict[str, Any]) -> FoyerConfig:
    try:
        return FoyerConfig(
            areas=tuple(area_from_dict(a) for a in data["areas"]),
            zones=tuple(zone_from_dict(z) for z in data["zones"]),
            scenarios=tuple(scenario_from_dict(s) for s in data["scenarios"]),
            actions=tuple(
                NotificationAction(
                    id=a["id"], moments=frozenset(Moment(m) for m in a["moments"])
                )
                for a in data["actions"]
            ),
            code_policy=CodePolicy(
                **{k: bool(v) for k, v in data["code_policy"].items()}
            ),
            settings=Settings(
                siren_duration=int(data["settings"]["siren_duration"]),
                arm_hold_timeout=int(data["settings"]["arm_hold_timeout"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as err:
        raise ConfigError(f"invalid Foyer configuration: {err!r}") from err


def config_to_dict(config: FoyerConfig) -> dict[str, Any]:
    return {
        "areas": [area_to_dict(a) for a in config.areas],
        "zones": [zone_to_dict(z) for z in config.zones],
        "scenarios": [scenario_to_dict(s) for s in config.scenarios],
        "actions": [
            {
                "id": a.id,
                "kind": "notification",
                "moments": sorted(m.value for m in a.moments),
            }
            for a in config.actions
        ],
        "code_policy": {
            "arm": config.code_policy.arm,
            "disarm": config.code_policy.disarm,
            "force_arm": config.code_policy.force_arm,
            "change_scenario": config.code_policy.change_scenario,
        },
        "settings": {
            "siren_duration": config.settings.siren_duration,
            "arm_hold_timeout": config.settings.arm_hold_timeout,
        },
    }


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)


def area_from_dict(a: dict[str, Any]) -> Area:
    return Area(
        id=a["id"],
        name=a["name"],
        ha_state_when_armed=a["ha_state_when_armed"],
        default_entry_delay=int(a["default_entry_delay"]),
        default_exit_delay=int(a["default_exit_delay"]),
    )


def area_to_dict(a: Area) -> dict[str, Any]:
    return {
        "id": a.id,
        "name": a.name,
        "ha_state_when_armed": a.ha_state_when_armed,
        "default_entry_delay": a.default_entry_delay,
        "default_exit_delay": a.default_exit_delay,
    }


def scenario_from_dict(s: dict[str, Any]) -> Scenario:
    return Scenario(
        id=s["id"],
        name=s["name"],
        areas=tuple(s["areas"]),
        ha_master_state=s["ha_master_state"],
        icon=s.get("icon"),
        exit_delay_override=_opt_int(s.get("exit_delay_override")),
        siren_duration_override=_opt_int(s.get("siren_duration_override")),
    )


def scenario_to_dict(s: Scenario) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "areas": list(s.areas),
        "ha_master_state": s.ha_master_state,
        "icon": s.icon,
        "exit_delay_override": s.exit_delay_override,
        "siren_duration_override": s.siren_duration_override,
    }


def zone_from_dict(z: dict[str, Any]) -> Zone:
    key = z.get("key")
    return Zone(
        id=z["id"],
        name=z["name"],
        entity_id=z["entity_id"],
        area_id=z["area_id"],
        trigger=trigger_from_dict(z["trigger"]),
        type=ZoneType(z["type"]),
        channel=Channel(z["channel"]),
        entry_mode=EntryMode(z["entry_mode"]),
        alarm_kind=AlarmKind(z["alarm_kind"]),
        always_on=bool(z["always_on"]),
        entry_delay=_opt_int(z.get("entry_delay")),
        arm_policy=ArmPolicy(z["arm_policy"]),
        arm_hold_timeout=_opt_int(z.get("arm_hold_timeout")),
        allow_arm_when_faulted=bool(z["allow_arm_when_faulted"]),
        bypassable=bool(z["bypassable"]),
        supervision_timeout=_opt_int(z.get("supervision_timeout")),
        enabled=bool(z["enabled"]),
        key=None
        if key is None
        else KeyAction(
            on_activate=KeyCommand(key["on_activate"]),
            scenario_id=key.get("scenario_id"),
            on_deactivate=KeyRelease(key.get("on_deactivate", "none")),
        ),
    )


def zone_to_dict(z: Zone) -> dict[str, Any]:
    return {
        "id": z.id,
        "name": z.name,
        "entity_id": z.entity_id,
        "area_id": z.area_id,
        "trigger": trigger_to_dict(z.trigger),
        "type": z.type.value,
        "channel": z.channel.value,
        "entry_mode": z.entry_mode.value,
        "alarm_kind": z.alarm_kind.value,
        "always_on": z.always_on,
        "entry_delay": z.entry_delay,
        "arm_policy": z.arm_policy.value,
        "arm_hold_timeout": z.arm_hold_timeout,
        "allow_arm_when_faulted": z.allow_arm_when_faulted,
        "bypassable": z.bypassable,
        "supervision_timeout": z.supervision_timeout,
        "enabled": z.enabled,
        "key": None
        if z.key is None
        else {
            "on_activate": z.key.on_activate.value,
            "scenario_id": z.key.scenario_id,
            "on_deactivate": z.key.on_deactivate.value,
        },
    }


def trigger_from_dict(data: dict[str, Any]) -> TriggerSpec:
    kind = data.get("kind")
    if kind == "state":
        return StateTrigger(states=frozenset(data["states"]))
    if kind == "numeric":
        return NumericTrigger(
            operator=NumericOperator(data["operator"]),
            value=float(data["value"]),
            hysteresis=float(data.get("hysteresis", 0.0)),
            attribute=data.get("attribute") or None,
        )
    if kind == "event":
        return EventTrigger(
            event_type=data.get("event_type") or None,
            subtype=data.get("subtype") or None,
        )
    raise ConfigError(f"unsupported trigger kind: {kind!r}")


def trigger_to_dict(trigger: TriggerSpec) -> dict[str, Any]:
    if isinstance(trigger, StateTrigger):
        return {"kind": "state", "states": sorted(trigger.states)}
    if isinstance(trigger, NumericTrigger):
        return {
            "kind": "numeric",
            "operator": trigger.operator.value,
            "value": trigger.value,
            "hysteresis": trigger.hysteresis,
            "attribute": trigger.attribute,
        }
    return {
        "kind": "event",
        "event_type": trigger.event_type,
        "subtype": trigger.subtype,
    }


# --- runtime state (INV-3) -------------------------------------------------------


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _timer_from(data: dict[str, Any] | None) -> Timer | None:
    if data is None:
        return None
    due = _dt(data["due"])
    assert due is not None
    return Timer(TimerKind(data["kind"]), due, _dt(data.get("anchor")))


def _timer_to(timer: Timer | None) -> dict[str, Any] | None:
    if timer is None:
        return None
    return {
        "kind": timer.kind.value,
        "due": timer.due.isoformat(),
        "anchor": timer.anchor.isoformat() if timer.anchor else None,
    }


def state_to_dict(state: RuntimeState) -> dict[str, Any]:
    return {
        "areas": {
            area_id: {
                "state": rt.state.value,
                "scenario_id": rt.scenario_id,
                "timer": _timer_to(rt.timer),
                "memory": rt.memory,
                "forced": rt.forced,
                "resume": rt.resume.value if rt.resume else None,
                "resume_timer": _timer_to(rt.resume_timer),
                "causes": list(rt.causes),
                "channel": rt.channel,
            }
            for area_id, rt in state.areas.items()
        },
        "active_scenario_id": state.active_scenario_id,
        "bypassed": {z: r.value for z, r in state.bypassed.items()},
        "active_zones": sorted(state.active_zones),
        "seen_zones": sorted(state.seen_zones),
        "faults": sorted(state.faults),
    }


def state_from_dict(data: dict[str, Any], config: FoyerConfig) -> RuntimeState:
    """Restore the runtime state, keeping only what the configuration still has.

    An area deleted while Home Assistant was down simply does not come back; an
    area the document does not know starts disarmed. Anything unreadable raises
    ConfigError: the caller decides how loudly to fail.
    """
    try:
        area_ids = {a.id for a in config.areas}
        zone_ids = {z.id for z in config.zones}
        areas: dict[str, AreaRuntime] = {}
        for area_id, rt in data.get("areas", {}).items():
            if area_id not in area_ids:
                continue
            scenario_id = rt.get("scenario_id")
            areas[area_id] = AreaRuntime(
                state=AreaState(rt["state"]),
                scenario_id=scenario_id if config.scenario(scenario_id) else None,
                timer=_timer_from(rt.get("timer")),
                memory=bool(rt.get("memory", False)),
                forced=bool(rt.get("forced", False)),
                resume=AreaState(rt["resume"]) if rt.get("resume") else None,
                resume_timer=_timer_from(rt.get("resume_timer")),
                causes=tuple(z for z in rt.get("causes", ()) if z in zone_ids),
                channel=rt.get("channel"),
            )
        for area_id in area_ids - areas.keys():
            areas[area_id] = AreaRuntime()
        active = data.get("active_scenario_id")
        return RuntimeState(
            areas=areas,
            active_scenario_id=active if config.scenario(active) else None,
            bypassed={
                z: BypassReason(r)
                for z, r in data.get("bypassed", {}).items()
                if z in zone_ids
            },
            active_zones=frozenset(
                z for z in data.get("active_zones", ()) if z in zone_ids
            ),
            seen_zones=frozenset(
                z for z in data.get("seen_zones", ()) if z in zone_ids
            ),
            faults=frozenset(z for z in data.get("faults", ()) if z in zone_ids),
        )
    except (KeyError, TypeError, ValueError, AssertionError) as err:
        raise ConfigError(f"invalid Foyer runtime state: {err!r}") from err
