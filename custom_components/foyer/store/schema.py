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
    Acknowledgement,
    Activation,
    AlarmKind,
    Area,
    AreaRuntime,
    AreaState,
    ArmPolicy,
    BypassReason,
    Channel,
    ChimeMode,
    ChimeSettings,
    CodePolicy,
    Contributor,
    EntryMode,
    EventTrigger,
    FoyerConfig,
    Group,
    Incident,
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
    TechnicalAlarm,
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
STORAGE_MINOR_VERSION = 3

# The runtime state grows additively and is read with defaults (a 1.1 file
# from an older build restores as "nothing technical, no incident, chime
# on"), so its version does not move: Home Assistant's Store would otherwise
# demand a migration function for a change that needs none.
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
            groups=tuple(group_from_dict(g) for g in data["groups"]),
            chime=chime_from_dict(data["chime"]),
        )
    except (KeyError, TypeError, ValueError) as err:
        raise ConfigError(f"invalid Foyer configuration: {err!r}") from err


def config_to_dict(config: FoyerConfig) -> dict[str, Any]:
    return {
        "areas": [area_to_dict(a) for a in config.areas],
        "zones": [zone_to_dict(z) for z in config.zones],
        "scenarios": [scenario_to_dict(s) for s in config.scenarios],
        "groups": [group_to_dict(g) for g in config.groups],
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
            "acknowledge": config.code_policy.acknowledge,
        },
        "settings": {
            "siren_duration": config.settings.siren_duration,
            "arm_hold_timeout": config.settings.arm_hold_timeout,
        },
        "chime": chime_to_dict(config.chime),
    }


def group_from_dict(g: dict[str, Any]) -> Group:
    return Group(
        id=g["id"],
        name=g["name"],
        area_id=g["area_id"],
        members=tuple(g["members"]),
        n=int(g["n"]),
        window_seconds=int(g["window_seconds"]),
        suppress_members=bool(g["suppress_members"]),
    )


def group_to_dict(g: Group) -> dict[str, Any]:
    return {
        "id": g.id,
        "name": g.name,
        "area_id": g.area_id,
        "members": list(g.members),
        "n": g.n,
        "window_seconds": g.window_seconds,
        "suppress_members": g.suppress_members,
    }


def chime_from_dict(c: dict[str, Any]) -> ChimeSettings:
    return ChimeSettings(
        targets=tuple(c["targets"]),
        mode=ChimeMode(c["mode"]),
        sound=c.get("sound") or None,
        tts_entity=c.get("tts_entity") or None,
        volume=_opt_int(c.get("volume")),
        quiet_start=c.get("quiet_start") or None,
        quiet_end=c.get("quiet_end") or None,
        during_exit=bool(c["during_exit"]),
    )


def chime_to_dict(c: ChimeSettings) -> dict[str, Any]:
    return {
        "targets": list(c.targets),
        "mode": c.mode.value,
        "sound": c.sound,
        "tts_entity": c.tts_entity,
        "volume": c.volume,
        "quiet_start": c.quiet_start,
        "quiet_end": c.quiet_end,
        "during_exit": c.during_exit,
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
        follows=tuple(z["follows"]),
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
        chime=bool(z["chime"]),
        cross_zone_id=z.get("cross_zone_id") or None,
        cross_zone_window=int(z["cross_zone_window"]),
        trigger_count=int(z["trigger_count"]),
        trigger_window=int(z["trigger_window"]),
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
        "follows": list(z.follows),
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
        "chime": z.chime,
        "cross_zone_id": z.cross_zone_id,
        "cross_zone_window": z.cross_zone_window,
        "trigger_count": z.trigger_count,
        "trigger_window": z.trigger_window,
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
        return EventTrigger(event_type=data.get("event_type") or None)
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
    return {"kind": "event", "event_type": trigger.event_type}


# --- runtime state (INV-3) -------------------------------------------------------


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _required_dt(value: str) -> datetime:
    parsed = _dt(value)
    if parsed is None:
        raise ValueError("missing timestamp")
    return parsed


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
        "technical": {
            zone_id: {
                "since": alarm.since.isoformat(),
                "acknowledged_at": _iso(alarm.acknowledged_at),
                "acknowledged_channel": alarm.acknowledged_channel,
            }
            for zone_id, alarm in state.technical.items()
        },
        "incident": _incident_to(state.incident),
        "incident_seq": state.incident_seq,
        "windows": {
            key: [
                {"zone_id": a.zone_id, "at": a.at.isoformat(), "held": a.held}
                for a in activations
            ]
            for key, activations in state.windows.items()
        },
        "chime_enabled": state.chime_enabled,
    }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _incident_to(incident: Incident | None) -> dict[str, Any] | None:
    if incident is None:
        return None
    return {
        "id": incident.id,
        "opened_at": incident.opened_at.isoformat(),
        "contributors": [
            {
                "area_id": c.area_id,
                "zone_id": c.zone_id,
                "at": c.at.isoformat(),
                "group_id": c.group_id,
                "profile_id": c.profile_id,
                "severity": c.severity,
            }
            for c in incident.contributors
        ],
        "acknowledged": incident.acknowledged,
        "acknowledgements": [
            {"at": a.at.isoformat(), "channel": a.channel, "via": a.via}
            for a in incident.acknowledgements
        ],
        "actions_started": list(incident.actions_started),
    }


def _incident_from(data: dict[str, Any] | None) -> Incident | None:
    """The open incident survives a restart (INV-3), even if the areas it
    touched were edited since: its record is what happened, not config."""
    if data is None:
        return None
    opened = _dt(data["opened_at"])
    assert opened is not None
    contributors = []
    for c in data.get("contributors", ()):
        at = _dt(c["at"])
        assert at is not None
        contributors.append(
            Contributor(
                area_id=c["area_id"],
                zone_id=c.get("zone_id"),
                at=at,
                group_id=c.get("group_id"),
                profile_id=c.get("profile_id"),
                severity=c.get("severity"),
            )
        )
    acknowledgements = []
    for a in data.get("acknowledgements", ()):
        at = _dt(a["at"])
        assert at is not None
        acknowledgements.append(
            Acknowledgement(at=at, channel=a.get("channel"), via=a["via"])
        )
    return Incident(
        id=data["id"],
        opened_at=opened,
        contributors=tuple(contributors),
        acknowledged=bool(data.get("acknowledged", False)),
        acknowledgements=tuple(acknowledgements),
        actions_started=tuple(data.get("actions_started", ())),
    )


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
            technical={
                zone_id: TechnicalAlarm(
                    since=_required_dt(alarm["since"]),
                    acknowledged_at=_dt(alarm.get("acknowledged_at")),
                    acknowledged_channel=alarm.get("acknowledged_channel"),
                )
                for zone_id, alarm in data.get("technical", {}).items()
                if zone_id in zone_ids
            },
            incident=_incident_from(data.get("incident")),
            incident_seq=int(data.get("incident_seq", 0)),
            windows={
                key: tuple(
                    Activation(
                        zone_id=a["zone_id"],
                        at=_required_dt(a["at"]),
                        held=bool(a.get("held", False)),
                    )
                    for a in activations
                    if a["zone_id"] in zone_ids
                )
                for key, activations in data.get("windows", {}).items()
            },
            chime_enabled=bool(data.get("chime_enabled", True)),
        )
    except (KeyError, TypeError, ValueError, AssertionError) as err:
        raise ConfigError(f"invalid Foyer runtime state: {err!r}") from err
