"""Conversion between the stored JSON documents and the core dataclasses.

Pure: no Home Assistant imports, so every round trip is testable on its own.
Two documents live here: the configuration (``foyer.config``) and the runtime
state (``foyer.state``, INV-3). They are separate because one changes when a
person edits something and the other changes every time a door opens.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from datetime import datetime
from typing import Any

from ..core.models import (
    DEFAULT_CHANNEL_FAILURES,
    DEFAULT_CHANNEL_SWEEP,
    DEFAULT_MAINS_OUTSIDE_DELAY,
    DEFAULT_REPAIR_AFTER,
    DEFAULT_RF_CONFIRM,
    DEFAULT_RF_WINDOW,
    DEFAULT_RF_ZONES,
    DEFAULT_UNLOCK_SECONDS,
    DEFAULT_WATCHDOG_FAILURES,
    DEFAULT_WATCHDOG_INTERVAL,
    DEFAULT_WATCHDOG_TIMEOUT,
    MAINS_SENSOR,
    Acknowledgement,
    ActionKind,
    Activation,
    ActiveWindow,
    AlarmKind,
    Area,
    AreaRuntime,
    AreaState,
    ArmingDevice,
    ArmPolicy,
    AutoRule,
    BypassReason,
    Channel,
    ChannelFault,
    ChannelHealth,
    ChimeMode,
    ChimeSettings,
    ChimeTarget,
    CodePolicy,
    Condition,
    ConditionMode,
    Contact,
    ContactChannel,
    ContactChannelKind,
    Contributor,
    Detection,
    DeviceKind,
    DeviceTransport,
    EntryMode,
    Escalation,
    EscalationKind,
    EventTrigger,
    FoyerConfig,
    Group,
    HealthSettings,
    Incident,
    KeyAction,
    KeyCommand,
    KeyRelease,
    Lockout,
    LogCategory,
    LogSettings,
    LogSeverity,
    Moment,
    MqttDetail,
    MqttSettings,
    NumericOperator,
    NumericTrigger,
    PendingRuleAction,
    PendingRun,
    ProfileAction,
    Radio,
    RadioHealth,
    ResponseProfile,
    RuleActionKind,
    RuleBlock,
    RuleGuards,
    RuleRuntime,
    RuleTrigger,
    RuleTriggerKind,
    RunningAction,
    RuntimeState,
    Scenario,
    SecuritySettings,
    Settings,
    StateCondition,
    StateOperator,
    StateTrigger,
    Suspension,
    SuspensionKind,
    SystemHealth,
    TechnicalAlarm,
    TimeCondition,
    Timer,
    TimerKind,
    TriggerSpec,
    User,
    WalkTest,
    WatchdogHealth,
    WatchdogSettings,
    Zone,
    ZoneType,
    channel_key,
)

# Bump STORAGE_VERSION (breaking) or STORAGE_MINOR_VERSION (additive) together
# with a step in store/migrations. Home Assistant's Store calls the hook.
#
# 2.1 is a major bump on purpose: zone semantics (entry mode, channel, key
# zones) are not additive. A Phase 0 build reading this file would treat a key
# switch or a 24h zone as an ordinary instant zone, so it must refuse instead.
#
# 3.1 is a major bump for the same reason: a 2.x build reading it would store
# a technical zone and silently never act on it — a smoke detector switched
# off without a word. Refusing the file is the only safe downgrade.
# 4.1 is a major bump for the third time and for the third time the reason is
# the same: a 3.x build reading this file would find response profiles it does
# not understand and would run no action at all. Refusing it is the only safe
# downgrade.
#
# 4.2 is a *minor* step, and that is the whole point of the distinction: the
# event log's settings, the defaults for new areas and the message language
# are additive, and a 4.1 build reading this document ignores them and behaves
# exactly as it did. Nothing it would have protected goes unprotected.
# 5.1 is a major bump, and the reason is the sharpest one yet: a 4.x build
# reading this document would find users it does not understand, ignore every
# code in it and run the house with no codes at all — which is the exact state
# this phase exists to end. Refusing the file is the only safe downgrade.
#
# 5.2 is a *minor* step: arming devices and the MQTT settings are additive and
# a 5.1 build ignoring them is a build that neither listens on a broker nor
# reads a tag — it simply has no physical channels, exactly as it had none
# yesterday. Nothing it would have protected goes unprotected.
#
# 5.4 is a *minor* step: the walk test's timeout is one number in the
# settings, and the two moments the default profile gains announce a walk
# test a 5.3 build cannot enter at all. A 5.3 build reading this document is
# a build with no walk test, exactly as it was yesterday.
#
# 5.3 is a *minor* step for the same reason: a zone's battery entity and the
# threshold it is read against are additive, and a 5.2 build ignoring both is
# a build that never warns about a battery — which is precisely what it did
# yesterday. A low battery blocks nothing, so nothing it would have protected
# goes unprotected (Phase 3 part 1 decisions 1 and 2).
#
# 6.1 is a major bump, and the reason is the one that made 3.1 and 4.1 major:
# a 5.x build reading this document would find notify actions that name
# contacts instead of a service, ignore the contacts, and send nothing — an
# alarm that says nothing, which is the worst failure there is (decision 63).
# It would also find escalation steps it does not know are steps and run them
# all at once, which is the phone spam §5.6 exists to prevent. Refusing the
# file is the only safe downgrade.
#
# 7.1 is a major bump, though everything in it is additive, and the reason is
# decision 58's exactly: a 6.x build reading this document would ignore the
# automatic rules and never arm the house on its own, and — worse — would not
# know that an area is the perimeter, so a rule it gained later could disarm
# the one ring §9.4 says is never disarmed by a rule. Both failures are
# silent, and refusing the file is the only safe downgrade.
#
# 7.2 is a *minor* step, deliberately, and it is worth saying why it is not
# another 58: system health (§12) is additive and a 7.1 build reading this
# document is a build with no watchdog, no mains entity and no radios — which
# is exactly what it was yesterday. Nothing it would have protected goes
# unprotected, and the only thing it loses is a warning it never had.
#
# 7.3 is a *minor* step for the same reason as 7.2, and it is worth saying what
# a 7.2 build reading this document loses: it never pseudonymises an old row
# and it never takes the log database with it when somebody removes the
# integration — which is exactly what it did yesterday. Nothing it would have
# protected goes unprotected. The one thing to know about the downgrade is
# that a 7.2 build writing the document back drops each person's stored
# pseudonym, so a later upgrade mints new ones: rows already pseudonymised
# keep the identifier they were written with and stop linking to rows written
# afterwards. The alternative was deriving the pseudonym from the name, which
# §12.4 refused for the diagnostics dump and this module refuses again.
#
# 7.4 is a *minor* step, and it is the closest call of all the minor steps, so
# the reasoning is written out. A zone gains ``trigger_confirmed``, which only
# the Alarmo importer ever sets to false, and only on a zone it also switches
# off. A 7.3 build reading this document ignores the field: the imported zones
# stay switched off, as they arrived, and watch nothing — exactly what a 7.4
# build does with them. What the older build loses is the refusal: somebody
# who ticks "enabled" on such a zone in a 7.3 panel, without touching its
# trigger, is not made to confirm it first. That is a check the downgraded
# build never had rather than protection it had and lost — every zone it ever
# enabled itself went through the confirmation — and refusing the whole file
# to keep it would lock a household out of its alarm over a zone that is off.
# One consequence is not small and is stated rather than hidden: a 7.3 build
# that writes the document back drops the field, and the 7.3 → 7.4 step then
# reads every zone as confirmed, because it cannot tell an imported zone from
# any other. Downgrading after an import and upgrading again therefore
# forgets which zones were never checked. The zones are still off; what is
# lost is the refusal to switch them on without confirming.
#
# 8.1 is a major bump, and the reason is one field. The zone's cameras and the
# notify action's ``images`` selector are additive: a 7.4 build reading them
# would send the text of an alarm without its pictures, which is a
# disappointment and not a hole. A keypad's ``transport`` is not additive in
# that sense. A 7.4 build does not know it, so it would take an endpoint
# keypad for an ordinary one and accept its name over the broker — exactly
# the way round the token that decision 98 exists to close, reached by
# nothing more than installing an older release. Refusing the file is the
# only safe downgrade, as it was for decision 58. Both halves travel in the
# one step so that there is one migration to read and one to test.
#
# 8.2 is additive: API devices gain scopes (§9.2.2). An 8.1 build reading it
# ignores them and serves its keypads as it always did.
# 8.3 is additive too: a rule may exclude open zones (decision 126).
# 8.4 is additive: the mains may be known from devices outside the UPS
# (decision 162). An 8.3 build reading it ignores them and watches no mains,
# which is what it did for a house with no smart UPS anyway.
# 8.5 is additive: a disarm rule may name every area (decision 163). An 8.4
# build reading it finds the rule's list empty and refuses to act on it,
# which disarms less, never more.
STORAGE_VERSION = 8
STORAGE_MINOR_VERSION = 5

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
            profiles=tuple(profile_from_dict(p) for p in data["profiles"]),
            # Unknown keys ignored, so a document written by a newer *minor*
            # version — additive by contract — is read rather than refused
            # (found in review). Splatted into the constructor, one unknown
            # operation raised TypeError, `async_load` re-raised it and the
            # integration would not start at all: a downgrade that bricks is
            # exactly what the major/minor split exists to prevent.
            code_policy=_policy(data["code_policy"]),
            settings=settings_from_dict(data["settings"]),
            groups=tuple(group_from_dict(g) for g in data["groups"]),
            chime=chime_from_dict(data["chime"]),
            users=tuple(user_from_dict(u) for u in data["users"]),
            devices=tuple(device_from_dict(d) for d in data["devices"]),
            contacts=tuple(contact_from_dict(c) for c in data["contacts"]),
            rules=tuple(rule_from_dict(r) for r in data["rules"]),
            health=health_from_dict(data["health"]),
        )
    except (KeyError, TypeError, ValueError) as err:
        raise ConfigError(f"invalid Foyer configuration: {err!r}") from err


def config_to_dict(config: FoyerConfig) -> dict[str, Any]:
    return {
        "areas": [area_to_dict(a) for a in config.areas],
        "zones": [zone_to_dict(z) for z in config.zones],
        "scenarios": [scenario_to_dict(s) for s in config.scenarios],
        "groups": [group_to_dict(g) for g in config.groups],
        "profiles": [profile_to_dict(p) for p in config.profiles],
        "users": [user_to_dict(u) for u in config.users],
        "devices": [device_to_dict(d) for d in config.devices],
        "contacts": [contact_to_dict(c) for c in config.contacts],
        "rules": [rule_to_dict(r) for r in config.rules],
        "code_policy": {
            field.name: getattr(config.code_policy, field.name)
            for field in fields(CodePolicy)
        },
        "settings": settings_to_dict(config.settings),
        "chime": chime_to_dict(config.chime),
        "health": health_to_dict(config.health),
    }


def health_from_dict(h: dict[str, Any]) -> HealthSettings:
    w = h.get("watchdog") or {}
    return HealthSettings(
        mains_entity_id=h.get("mains_entity_id") or None,
        # The default only when the key is missing: an empty list the
        # household saved is refused by validation (INV-5), and reading it as
        # `on` hid that — a mains alarm on a power sensor that never fires
        # (second review).
        mains_lost_states=tuple(h.get("mains_lost_states", ("on",)) or ()),
        mains_mode=str(h.get("mains_mode") or MAINS_SENSOR),
        mains_outside_entity_ids=tuple(
            str(e) for e in h.get("mains_outside_entity_ids") or () if e
        ),
        mains_outside_delay=int(
            h.get("mains_outside_delay", DEFAULT_MAINS_OUTSIDE_DELAY)
        ),
        watchdog=WatchdogSettings(
            enabled=bool(w.get("enabled", False)),
            url=str(w.get("url", "")),
            interval=int(w.get("interval", DEFAULT_WATCHDOG_INTERVAL)),
            timeout=int(w.get("timeout", DEFAULT_WATCHDOG_TIMEOUT)),
            failures=int(w.get("failures", DEFAULT_WATCHDOG_FAILURES)),
            payload=bool(w.get("payload", False)),
        ),
        radios=tuple(radio_from_dict(r) for r in h.get("radios") or ()),
        rf_zones=int(h.get("rf_zones", DEFAULT_RF_ZONES)),
        rf_window=int(h.get("rf_window", DEFAULT_RF_WINDOW)),
        rf_confirm=int(h.get("rf_confirm", DEFAULT_RF_CONFIRM)),
        channel_sweep=int(h.get("channel_sweep", DEFAULT_CHANNEL_SWEEP)),
        channel_failures=int(h.get("channel_failures", DEFAULT_CHANNEL_FAILURES)),
        repair_after=int(h.get("repair_after", DEFAULT_REPAIR_AFTER)),
    )


def health_to_dict(h: HealthSettings) -> dict[str, Any]:
    return {
        "mains_entity_id": h.mains_entity_id,
        "mains_lost_states": list(h.mains_lost_states),
        "mains_mode": h.mains_mode,
        "mains_outside_entity_ids": list(h.mains_outside_entity_ids),
        "mains_outside_delay": h.mains_outside_delay,
        "watchdog": {
            "enabled": h.watchdog.enabled,
            "url": h.watchdog.url,
            "interval": h.watchdog.interval,
            "timeout": h.watchdog.timeout,
            "failures": h.watchdog.failures,
            "payload": h.watchdog.payload,
        },
        "radios": [radio_to_dict(r) for r in h.radios],
        "rf_zones": h.rf_zones,
        "rf_window": h.rf_window,
        "rf_confirm": h.rf_confirm,
        "channel_sweep": h.channel_sweep,
        "channel_failures": h.channel_failures,
        "repair_after": h.repair_after,
    }


def radio_from_dict(r: dict[str, Any]) -> Radio:
    return Radio(
        id=str(r["id"]),
        name=str(r["name"]),
        entry_id=str(r.get("entry_id", "")),
        coordinator_entity_id=r.get("coordinator_entity_id") or None,
        n_zones=_opt_int(r.get("n_zones")),
        window=_opt_int(r.get("window")),
        enabled=bool(r.get("enabled", True)),
    )


def radio_to_dict(r: Radio) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "entry_id": r.entry_id,
        "coordinator_entity_id": r.coordinator_entity_id,
        "n_zones": r.n_zones,
        "window": r.window,
        "enabled": r.enabled,
    }


def settings_from_dict(s: dict[str, Any]) -> Settings:
    return Settings(
        siren_duration=int(s["siren_duration"]),
        arm_hold_timeout=int(s["arm_hold_timeout"]),
        default_profile_id=s.get("default_profile_id") or None,
        technical_profile_id=s.get("technical_profile_id") or None,
        silent_suppresses=tuple(s["silent_suppresses"]),
        camera_dir=s["camera_dir"],
        log=log_from_dict(s["log"]),
        default_entry_delay=int(s["default_entry_delay"]),
        default_exit_delay=int(s["default_exit_delay"]),
        language=s.get("language") or None,
        wizard_done=bool(s["wizard_done"]),
        low_battery_threshold=int(s["low_battery_threshold"]),
        walk_test_timeout=int(s["walk_test_timeout"]),
        ack_webhook_id=s.get("ack_webhook_id") or None,
        allow_auto_disarm=bool(s["allow_auto_disarm"]),
        security=security_from_dict(s["security"]),
        mqtt=mqtt_from_dict(s["mqtt"]),
    )


def settings_to_dict(s: Settings) -> dict[str, Any]:
    return {
        "siren_duration": s.siren_duration,
        "arm_hold_timeout": s.arm_hold_timeout,
        "default_profile_id": s.default_profile_id,
        "technical_profile_id": s.technical_profile_id,
        "silent_suppresses": list(s.silent_suppresses),
        "camera_dir": s.camera_dir,
        "log": log_to_dict(s.log),
        "default_entry_delay": s.default_entry_delay,
        "default_exit_delay": s.default_exit_delay,
        "language": s.language,
        "wizard_done": s.wizard_done,
        "low_battery_threshold": s.low_battery_threshold,
        "walk_test_timeout": s.walk_test_timeout,
        "ack_webhook_id": s.ack_webhook_id,
        "allow_auto_disarm": s.allow_auto_disarm,
        "security": security_to_dict(s.security),
        "mqtt": mqtt_to_dict(s.mqtt),
    }


def mqtt_from_dict(data: dict[str, Any]) -> MqttSettings:
    return MqttSettings(
        enabled=bool(data["enabled"]),
        command_topic=str(data.get("command_topic") or ""),
        state_topic=str(data.get("state_topic") or ""),
        detail=MqttDetail(data["detail"]),
        retain=bool(data["retain"]),
        qos=int(data["qos"]),
    )


def mqtt_to_dict(s: MqttSettings) -> dict[str, Any]:
    return {
        "enabled": s.enabled,
        "command_topic": s.command_topic,
        "state_topic": s.state_topic,
        "detail": s.detail.value,
        "retain": s.retain,
        "qos": s.qos,
    }


def contact_from_dict(c: dict[str, Any]) -> Contact:
    return Contact(
        id=c["id"],
        name=c["name"],
        channels=tuple(channel_from_dict(ch) for ch in c.get("channels", ())),
        quiet_start=c.get("quiet_start") or None,
        quiet_end=c.get("quiet_end") or None,
        quiet_min_severity=LogSeverity(c.get("quiet_min_severity", "alarm")),
        linked_user_id=c.get("linked_user_id") or None,
        enabled=bool(c.get("enabled", True)),
    )


def contact_to_dict(c: Contact) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "channels": [channel_to_dict(ch) for ch in c.channels],
        "quiet_start": c.quiet_start,
        "quiet_end": c.quiet_end,
        "quiet_min_severity": c.quiet_min_severity.value,
        "linked_user_id": c.linked_user_id,
        "enabled": c.enabled,
    }


def channel_from_dict(c: dict[str, Any]) -> ContactChannel:
    return ContactChannel(
        id=c["id"],
        kind=ContactChannelKind(c.get("kind", "other")),
        service=c.get("service", ""),
        target=c.get("target", ""),
        data=dict(c.get("data") or {}),
        actionable=bool(c.get("actionable", False)),
        enabled=bool(c.get("enabled", True)),
    )


def channel_to_dict(c: ContactChannel) -> dict[str, Any]:
    return {
        "id": c.id,
        "kind": c.kind.value,
        "service": c.service,
        "target": c.target,
        "data": dict(c.data),
        "actionable": c.actionable,
        "enabled": c.enabled,
    }


def device_from_dict(d: dict[str, Any]) -> ArmingDevice:
    return ArmingDevice(
        id=d["id"],
        name=d["name"],
        kind=DeviceKind(d["kind"]),
        ref=d.get("ref") or None,
        entity_id=d.get("entity_id") or None,
        event_type=d.get("event_type") or None,
        user_id=d.get("user_id") or None,
        command=KeyCommand(d["command"]),
        scenario_id=d.get("scenario_id") or None,
        enabled=bool(d.get("enabled", True)),
        transport=DeviceTransport(d.get("transport") or DeviceTransport.MQTT.value),
        # Only a hex string is a hash: anything else hand-edited into the
        # file would make every request to the endpoint fail on comparison.
        token_hash=_token_hash(d.get("token_hash")),
        scopes=frozenset(d.get("scopes") or ()),
        free_scopes=frozenset(
            d.get("free_scopes") if d.get("free_scopes") is not None else ("status",)
        ),
        arm_scenario_ids=_ids_or_none(d.get("arm_scenario_ids")),
        arm_area_ids=_ids_or_none(d.get("arm_area_ids")),
        disarm_area_ids=_ids_or_none(d.get("disarm_area_ids")),
        unlock_seconds=int(d.get("unlock_seconds") or DEFAULT_UNLOCK_SECONDS),
        clear_text_confirmed=bool(d.get("clear_text_confirmed", False)),
    )


def _ids_or_none(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    return tuple(str(v) for v in value)


def _token_hash(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if not all(c in "0123456789abcdef" for c in value):
        raise ConfigError("a device token hash must be hexadecimal")
    return value


def device_to_dict(d: ArmingDevice) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "kind": d.kind.value,
        "ref": d.ref,
        "entity_id": d.entity_id,
        "event_type": d.event_type,
        "user_id": d.user_id,
        "command": d.command.value,
        "scenario_id": d.scenario_id,
        "enabled": d.enabled,
        "transport": d.transport.value,
        # A credential: the panel, a backup and the diagnostics all strip it
        # (api/backup.py, core/dump.py). It is here because this is the
        # document the installation keeps for itself.
        "token_hash": d.token_hash,
        "scopes": sorted(d.scopes),
        "free_scopes": sorted(d.free_scopes),
        "arm_scenario_ids": _list_or_none(d.arm_scenario_ids),
        "arm_area_ids": _list_or_none(d.arm_area_ids),
        "disarm_area_ids": _list_or_none(d.disarm_area_ids),
        "unlock_seconds": d.unlock_seconds,
        "clear_text_confirmed": d.clear_text_confirmed,
    }


def _list_or_none(value: tuple[str, ...] | None) -> list[str] | None:
    return None if value is None else list(value)


def security_from_dict(data: dict[str, Any]) -> SecuritySettings:
    return SecuritySettings(
        code_length=int(data["code_length"]),
        lockout_failures=int(data["lockout_failures"]),
        lockout_window=int(data["lockout_window"]),
        lockout_duration=int(data["lockout_duration"]),
    )


def security_to_dict(s: SecuritySettings) -> dict[str, Any]:
    return {
        "code_length": s.code_length,
        "lockout_failures": s.lockout_failures,
        "lockout_window": s.lockout_window,
        "lockout_duration": s.lockout_duration,
    }


def _policy(data: Mapping[str, Any]) -> CodePolicy:
    known = {f.name for f in fields(CodePolicy)}
    return CodePolicy(**{k: bool(v) for k, v in data.items() if k in known})


def user_from_dict(u: dict[str, Any]) -> User:
    """Read a user, hashes and all.

    The hashes live here and nowhere else: this document is the only place
    they exist, no API ever returns them, and the panel changes a code by
    sending a new one, never by reading the old one back (INV-2).
    """
    return User(
        id=u["id"],
        name=u["name"],
        code_hash=u.get("code_hash") or None,
        duress_code_hash=u.get("duress_code_hash") or None,
        ha_user_id=u.get("ha_user_id") or None,
        permissions=frozenset(u.get("permissions") or ()),
        allowed_area_ids=(
            None if u.get("allowed_area_ids") is None else tuple(u["allowed_area_ids"])
        ),
        allowed_scenario_ids=(
            None
            if u.get("allowed_scenario_ids") is None
            else tuple(u["allowed_scenario_ids"])
        ),
        valid_from=_dt(u.get("valid_from")),
        valid_until=_dt(u.get("valid_until")),
        code_exempt_when_identified=bool(u.get("code_exempt_when_identified", False)),
        enabled=bool(u.get("enabled", True)),
        pseudonym=u.get("pseudonym") or None,
    )


def user_to_dict(u: User) -> dict[str, Any]:
    return {
        "id": u.id,
        "name": u.name,
        "code_hash": u.code_hash,
        "duress_code_hash": u.duress_code_hash,
        "ha_user_id": u.ha_user_id,
        "permissions": sorted(u.permissions),
        "allowed_area_ids": (
            None if u.allowed_area_ids is None else list(u.allowed_area_ids)
        ),
        "allowed_scenario_ids": (
            None if u.allowed_scenario_ids is None else list(u.allowed_scenario_ids)
        ),
        "valid_from": _iso(u.valid_from),
        "valid_until": _iso(u.valid_until),
        "code_exempt_when_identified": u.code_exempt_when_identified,
        "enabled": u.enabled,
        "pseudonym": u.pseudonym,
    }


def log_from_dict(data: dict[str, Any]) -> LogSettings:
    """Read back sparse: only categories the user moved away from the
    documented default are kept.

    Two reasons. A stale key from an older document would otherwise sit in the
    settings for ever, invisible and inert; and a category left alone keeps
    following §10.2 even if a later version revises what that default is.
    """
    known = {c.value for c in LogCategory}
    default = LogSettings()
    after = data.get("pseudonymise_after")
    return LogSettings(
        enabled={
            k: bool(v)
            for k, v in (data.get("enabled") or {}).items()
            if k in known and bool(v) is not default.is_enabled(k)
        },
        retention_days={
            k: int(v)
            for k, v in (data.get("retention_days") or {}).items()
            if k in known and int(v) != default.retention(k)
        },
        pseudonymise_after=None if after in (None, "", 0) else int(after),
        delete_on_uninstall=bool(data.get("delete_on_uninstall", False)),
    )


def log_to_dict(log: LogSettings) -> dict[str, Any]:
    """Written in full, every category explicit: the settings page reads this
    document, and a sparse map would show a blank field where the default is."""
    return {
        "enabled": {c.value: log.is_enabled(c.value) for c in LogCategory},
        "retention_days": {c.value: log.retention(c.value) for c in LogCategory},
        "pseudonymise_after": log.pseudonymise_after,
        "delete_on_uninstall": log.delete_on_uninstall,
    }


def condition_from_dict(c: dict[str, Any]) -> Condition:
    kind = c.get("kind")
    if kind == "time":
        return TimeCondition(after=c["after"], before=c["before"])
    if kind == "state":
        return StateCondition(
            entity_id=c["entity_id"],
            operator=StateOperator(c["operator"]),
            state=c["state"],
        )
    raise ConfigError(f"unsupported condition kind: {kind!r}")


def condition_to_dict(c: Condition) -> dict[str, Any]:
    if isinstance(c, TimeCondition):
        return {"kind": "time", "after": c.after, "before": c.before}
    return {
        "kind": "state",
        "entity_id": c.entity_id,
        "operator": c.operator.value,
        "state": c.state,
    }


def action_from_dict(a: dict[str, Any]) -> ProfileAction:
    return ProfileAction(
        id=a["id"],
        kind=ActionKind(a["kind"]),
        moments=frozenset(Moment(m) for m in a["moments"]),
        name=a.get("name", ""),
        params=dict(a.get("params") or {}),
        conditions=tuple(condition_from_dict(c) for c in a.get("conditions", ())),
        condition_mode=ConditionMode(a.get("condition_mode", "all")),
        enabled=bool(a.get("enabled", True)),
        escalation_offset=_opt_int(a.get("escalation_offset")),
    )


def action_to_dict(a: ProfileAction) -> dict[str, Any]:
    return {
        "id": a.id,
        "kind": a.kind.value,
        "moments": sorted(m.value for m in a.moments),
        "name": a.name,
        "params": dict(a.params),
        "conditions": [condition_to_dict(c) for c in a.conditions],
        "condition_mode": a.condition_mode.value,
        "enabled": a.enabled,
        "escalation_offset": a.escalation_offset,
    }


def profile_from_dict(p: dict[str, Any]) -> ResponseProfile:
    return ResponseProfile(
        id=p["id"],
        name=p["name"],
        severity=int(p["severity"]),
        actions=tuple(action_from_dict(a) for a in p["actions"]),
    )


def profile_to_dict(p: ResponseProfile) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "severity": p.severity,
        "actions": [action_to_dict(a) for a in p.actions],
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
        response_profile_id=g.get("response_profile_id") or None,
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
        "response_profile_id": g.response_profile_id,
    }


def chime_from_dict(c: dict[str, Any]) -> ChimeSettings:
    return ChimeSettings(
        targets=tuple(
            ChimeTarget(
                entity_id=t["entity_id"],
                quiet_start=t.get("quiet_start") or None,
                quiet_end=t.get("quiet_end") or None,
            )
            for t in c["targets"]
        ),
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
        "targets": [
            {
                "entity_id": t.entity_id,
                "quiet_start": t.quiet_start,
                "quiet_end": t.quiet_end,
            }
            for t in c.targets
        ],
        "mode": c.mode.value,
        "sound": c.sound,
        "tts_entity": c.tts_entity,
        "volume": c.volume,
        "quiet_start": c.quiet_start,
        "quiet_end": c.quiet_end,
        "during_exit": c.during_exit,
    }


def _opt_bool(value: Any) -> bool | None:
    """None stays None: "inherit" and "no" are different answers (§8.2)."""
    return None if value is None else bool(value)


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)


def area_from_dict(a: dict[str, Any]) -> Area:
    return Area(
        id=a["id"],
        name=a["name"],
        ha_state_when_armed=a["ha_state_when_armed"],
        default_entry_delay=int(a["default_entry_delay"]),
        default_exit_delay=int(a["default_exit_delay"]),
        response_profile_id=a.get("response_profile_id") or None,
        require_code_to_arm=_opt_bool(a.get("require_code_to_arm")),
        require_code_to_disarm=_opt_bool(a.get("require_code_to_disarm")),
        is_perimeter=bool(a["is_perimeter"]),
    )


def area_to_dict(a: Area) -> dict[str, Any]:
    return {
        "id": a.id,
        "name": a.name,
        "ha_state_when_armed": a.ha_state_when_armed,
        "default_entry_delay": a.default_entry_delay,
        "default_exit_delay": a.default_exit_delay,
        "response_profile_id": a.response_profile_id,
        "require_code_to_arm": a.require_code_to_arm,
        "require_code_to_disarm": a.require_code_to_disarm,
        "is_perimeter": a.is_perimeter,
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
        response_profile_id=s.get("response_profile_id") or None,
        require_code_to_arm=_opt_bool(s.get("require_code_to_arm")),
        require_code_to_disarm=_opt_bool(s.get("require_code_to_disarm")),
        allowed_user_ids=(
            None if s.get("allowed_user_ids") is None else tuple(s["allowed_user_ids"])
        ),
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
        "response_profile_id": s.response_profile_id,
        "require_code_to_arm": s.require_code_to_arm,
        "require_code_to_disarm": s.require_code_to_disarm,
        "allowed_user_ids": (
            None if s.allowed_user_ids is None else list(s.allowed_user_ids)
        ),
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
            user_id=key.get("user_id") or None,
        ),
        chime=bool(z["chime"]),
        cross_zone_id=z.get("cross_zone_id") or None,
        cross_zone_window=int(z["cross_zone_window"]),
        trigger_count=int(z["trigger_count"]),
        trigger_window=int(z["trigger_window"]),
        response_profile_id=z.get("response_profile_id") or None,
        silent=bool(z["silent"]),
        battery_entity_id=z.get("battery_entity_id") or None,
        # Strictly: only a real `true` confirms, so a hand-edited "false" is
        # not read as the truthy string it is.
        trigger_confirmed=z.get("trigger_confirmed", True) is True,
        camera_entity_ids=tuple(str(c) for c in z.get("camera_entity_ids") or ()),
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
            "user_id": z.key.user_id,
        },
        "chime": z.chime,
        "cross_zone_id": z.cross_zone_id,
        "cross_zone_window": z.cross_zone_window,
        "trigger_count": z.trigger_count,
        "trigger_window": z.trigger_window,
        "response_profile_id": z.response_profile_id,
        "silent": z.silent,
        "battery_entity_id": z.battery_entity_id,
        "trigger_confirmed": z.trigger_confirmed,
        "camera_entity_ids": list(z.camera_entity_ids),
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


def rule_from_dict(r: dict[str, Any]) -> AutoRule:
    trigger = r["trigger"]
    guards = r["guards"]
    window = r["window"]
    return AutoRule(
        id=r["id"],
        name=r["name"],
        trigger=RuleTrigger(
            kind=RuleTriggerKind(trigger["kind"]),
            entity_ids=tuple(trigger.get("entity_ids", ())),
            state=trigger.get("state") or None,
            minutes=int(trigger.get("minutes", 0)),
            at=trigger.get("at") or None,
            weekdays=tuple(int(d) for d in trigger.get("weekdays", ())),
        ),
        action=RuleActionKind(r["action"]),
        scenario_id=r.get("scenario_id") or None,
        area_ids=tuple(r.get("area_ids", ())),
        window=ActiveWindow(
            weekdays=tuple(int(d) for d in window.get("weekdays", ())),
            after=window.get("after") or None,
            before=window.get("before") or None,
        ),
        guards=RuleGuards(
            only_when_disarmed=bool(guards.get("only_when_disarmed", False)),
            only_when_ready=bool(guards.get("only_when_ready", False)),
            quiet_minutes=_opt_int(guards.get("quiet_minutes")),
        ),
        grace_seconds=int(r["grace_seconds"]),
        notify_contact_ids=tuple(r.get("notify_contact_ids", ())),
        enabled=bool(r["enabled"]),
        exclude_open_zones=bool(r.get("exclude_open_zones", False)),
        all_areas=bool(r.get("all_areas", False)),
    )


def rule_to_dict(r: AutoRule) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "trigger": {
            "kind": r.trigger.kind.value,
            "entity_ids": list(r.trigger.entity_ids),
            "state": r.trigger.state,
            "minutes": r.trigger.minutes,
            "at": r.trigger.at,
            "weekdays": list(r.trigger.weekdays),
        },
        "action": r.action.value,
        "scenario_id": r.scenario_id,
        "area_ids": list(r.area_ids),
        "window": {
            "weekdays": list(r.window.weekdays),
            "after": r.window.after,
            "before": r.window.before,
        },
        "guards": {
            "only_when_disarmed": r.guards.only_when_disarmed,
            "only_when_ready": r.guards.only_when_ready,
            "quiet_minutes": r.guards.quiet_minutes,
        },
        "grace_seconds": r.grace_seconds,
        "notify_contact_ids": list(r.notify_contact_ids),
        "enabled": r.enabled,
        "exclude_open_zones": r.exclude_open_zones,
        "all_areas": r.all_areas,
    }


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


def _health_from(
    data: dict[str, Any] | None, config: FoyerConfig, zone_ids: set[str]
) -> SystemHealth:
    """System health, restored (§12, INV-3).

    Read with defaults throughout: a state file written before this phase
    restores as "nothing known yet", and the first sweep after the restart
    says what is true. Channels and radios the configuration no longer has
    are dropped here, like every other map in this function.
    """
    data = data or {}
    known = set(health_channels(config))
    radio_ids = {r.id for r in config.health.radios}
    w = data.get("watchdog") or {}
    return SystemHealth(
        mains_lost_since=_dt(data.get("mains_lost_since")),
        channels={
            key: ChannelHealth(
                fault=ChannelFault(ch["fault"]) if ch.get("fault") else None,
                since=_dt(ch.get("since")),
                failures=int(ch.get("failures", 0)),
                last_ok=_dt(ch.get("last_ok")),
                last_failed=_dt(ch.get("last_failed")),
                present=ch.get("present"),
            )
            for key, ch in (data.get("channels") or {}).items()
            if key in known
        },
        watchdog=WatchdogHealth(
            failures=int(w.get("failures", 0)),
            down_since=_dt(w.get("down_since")),
            last_ok=_dt(w.get("last_ok")),
            last_attempt=_dt(w.get("last_attempt")),
            last_error=str(w.get("last_error", "")),
            ever_ok=bool(w.get("ever_ok", False)),
            announced=bool(w.get("announced", False)),
        ),
        radios={
            radio_id: RadioHealth(
                suspected_since=_dt(r.get("suspected_since")),
                confirmed=bool(r.get("confirmed", False)),
                zone_ids=tuple(z for z in r.get("zone_ids", ()) if z in zone_ids),
                coordinator_down_since=_dt(r.get("coordinator_down_since")),
                coordinator_announced=bool(r.get("coordinator_announced", False)),
            )
            for radio_id, r in (data.get("radios") or {}).items()
            # Disabled radios keep their health here so the engine can end
            # what they were reporting with a row on the next call, but a
            # radio the configuration has dropped entirely is handled the
            # same way — the engine, not this function, writes that ending.
            if radio_id in radio_ids
        },
        quiet_since={
            zone_id: _required_dt(at)
            for zone_id, at in (data.get("quiet_since") or {}).items()
            if zone_id in zone_ids
        },
        unknown_zones=frozenset(
            z for z in (data.get("unknown_zones") or ()) if z in zone_ids
        ),
        acknowledged_issues=frozenset(data.get("acknowledged_issues") or ()),
        # When each device outside the UPS went silent: kept, so a power cut
        # outlives a restart. Which of them Foyer has *seen* answer is not
        # stored at all (decision 162): after a restart it must start empty,
        # or a device still loading would be taken for one that just died.
        mains_quiet_since={
            e: _required_dt(at)
            for e, at in (data.get("mains_quiet_since") or {}).items()
            if e in config.health.mains_outside_entity_ids
        },
    )


def health_channels(config: FoyerConfig) -> dict[str, str]:
    """Every channel key the configuration holds, disabled ones included: a
    fault survives the switch that disabled the channel, as a radio's does
    (third review). Spelled out here rather than imported from
    ``core.health``, because a store module must not depend on the engine."""
    return {
        channel_key(contact.id, channel.id): channel.service
        for contact in config.contacts
        for channel in contact.channels
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
                "user_id": rt.user_id,
                "device_id": rt.device_id,
                "claimed": rt.claimed,
                "locked_address": rt.locked_address,
                "skipped_exit": rt.skipped_exit,
                "rule_id": rt.rule_id,
                "rule_name": rt.rule_name,
            }
            for area_id, rt in state.areas.items()
        },
        "active_scenario_id": state.active_scenario_id,
        "bypassed": {z: r.value for z, r in state.bypassed.items()},
        "active_zones": sorted(state.active_zones),
        "seen_zones": sorted(state.seen_zones),
        "seen_devices": sorted(state.seen_devices),
        "in_clear": sorted(state.in_clear),
        "faults": sorted(state.faults),
        # The zones already known to be low (§4.2). Without it, every restart
        # — and every configuration save, which reloads the entry — re-raised
        # LOW_BATTERY for every flat cell in the house, with a log row and a
        # notification each time (found in review). The latch exists exactly
        # so that it is said once, on the way down.
        "low_batteries": sorted(state.low_batteries),
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
        "bypass_until": {z: due.isoformat() for z, due in state.bypass_until.items()},
        "pending_runs": [
            {
                "id": r.id,
                "profile_id": r.profile_id,
                "moment": r.moment.value,
                "index": r.index,
                "due": r.due.isoformat(),
                "area_id": r.area_id,
                "zone_id": r.zone_id,
                "incident_id": r.incident_id,
                "silent": r.silent,
                "placeholders": dict(r.placeholders),
            }
            for r in state.pending_runs
        ],
        "running": [
            {
                "action_id": r.action_id,
                "kind": r.kind,
                "entity_ids": list(r.entity_ids),
                "until": _iso(r.until),
                "restore": r.restore,
                "area_id": r.area_id,
                "incident_id": r.incident_id,
                # Which channel started it (§5.5). Lost here, a smoke sounder
                # came back from a restart as an intrusion one, and the next
                # disarm of its area switched it off (found in review).
                "technical": r.technical,
                # And whether it answered `duress`: its revert after a
                # restart is still one of the duress's rows (decision 133).
                "duress": r.duress,
            }
            for r in state.running
        ],
        "run_seq": state.run_seq,
        # The walk test, timeout and all: §5.3 lists the auto-exit among the
        # timers, and INV-3 persists pending timers. A restart that lost it
        # would leave a house inhibited with nothing due to end it.
        "walk_test": _walk_test_to(state.walk_test),
        # Escalation progress (INV-3 names it): what is running, since when,
        # and which steps have already gone out. An alarm nobody answered is
        # still unanswered after a restart.
        "escalations": [
            {
                "kind": e.kind.value,
                "profile_id": e.profile_id,
                "moment": e.moment.value,
                "started_at": e.started_at.isoformat(),
                "severity": e.severity,
                "done": list(e.done),
                "reference": e.reference,
            }
            for e in state.escalations
        ],
        # Automatic arming (§9.4). The countdown is a timer like any other
        # and INV-3 persists timers: a restart must not lose an announced
        # arming, nor the suspension somebody set for tomorrow morning.
        "auto_arming": state.auto_arming,
        "pending_rules": [
            {
                "id": p.id,
                "rule_id": p.rule_id,
                "rule_name": p.rule_name,
                "action": p.action.value,
                "due": p.due.isoformat(),
                "started_at": p.started_at.isoformat(),
                "scenario_id": p.scenario_id,
                "area_ids": list(p.area_ids),
                "suspension_name": p.suspension_name,
            }
            for p in state.pending_rules
        ],
        "suspensions": [
            {
                "id": sus.id,
                "kind": sus.kind.value,
                "rule_ids": list(sus.rule_ids),
                "name": sus.name,
                "start": _iso(sus.start),
                "until": _iso(sus.until),
                "reduced_scenario_id": sus.reduced_scenario_id,
                "created_at": _iso(sus.created_at),
                "user_id": sus.user_id,
                "user_name": sus.user_name,
            }
            for sus in state.suspensions
        ],
        "rules": {
            rule_id: {
                "since": _iso(rt.since),
                "latched": rt.latched,
                "blocked": rt.blocked.value if rt.blocked else None,
                "last_occurrence": _iso(rt.last_occurrence),
                "seen": rt.seen,
                "schedule": rt.schedule,
                "retrying": rt.retrying,
            }
            for rule_id, rt in state.rules.items()
        },
        "pending_seq": state.pending_seq,
        "health": {
            "mains_lost_since": _iso(state.health.mains_lost_since),
            "channels": {
                key: {
                    "fault": ch.fault.value if ch.fault else None,
                    "since": _iso(ch.since),
                    "failures": ch.failures,
                    "last_ok": _iso(ch.last_ok),
                    "last_failed": _iso(ch.last_failed),
                    "present": ch.present,
                }
                for key, ch in state.health.channels.items()
            },
            "watchdog": {
                "failures": state.health.watchdog.failures,
                "down_since": _iso(state.health.watchdog.down_since),
                "last_ok": _iso(state.health.watchdog.last_ok),
                "last_attempt": _iso(state.health.watchdog.last_attempt),
                "last_error": state.health.watchdog.last_error,
                "ever_ok": state.health.watchdog.ever_ok,
                "announced": state.health.watchdog.announced,
            },
            "radios": {
                radio_id: {
                    "suspected_since": _iso(r.suspected_since),
                    "confirmed": r.confirmed,
                    "zone_ids": list(r.zone_ids),
                    "coordinator_down_since": _iso(r.coordinator_down_since),
                    "coordinator_announced": r.coordinator_announced,
                }
                for radio_id, r in state.health.radios.items()
            },
            "quiet_since": {
                zone_id: at.isoformat()
                for zone_id, at in state.health.quiet_since.items()
            },
            "unknown_zones": sorted(state.health.unknown_zones),
            "acknowledged_issues": sorted(state.health.acknowledged_issues),
            "mains_quiet_since": {
                e: at.isoformat() for e, at in state.health.mains_quiet_since.items()
            },
        },
        "lockouts": {
            key: {
                "failures": [at.isoformat() for at in lock.failures],
                "until": _iso(lock.until),
                "strikes": lock.strikes,
                "locked_at": _iso(lock.locked_at),
            }
            for key, lock in state.lockouts.items()
        },
    }


def _walk_test_to(walk: WalkTest | None) -> dict[str, Any] | None:
    if walk is None:
        return None
    return {
        "started_at": walk.started_at.isoformat(),
        "until": walk.until.isoformat(),
        "hard_until": walk.hard_until.isoformat(),
        "window": walk.window,
        "armed_areas": list(walk.armed_areas),
        "detections": {
            zone_id: {
                "first": d.first.isoformat(),
                "last": d.last.isoformat(),
                "count": d.count,
            }
            for zone_id, d in walk.detections.items()
        },
        "user_id": walk.user_id,
        "user_name": walk.user_name,
        "channel": walk.channel,
        "device_id": walk.device_id,
    }


def _walk_test_from(
    data: dict[str, Any] | None, area_ids: set[str], zone_ids: set[str]
) -> WalkTest | None:
    if not data:
        return None
    return WalkTest(
        started_at=_required_dt(data["started_at"]),
        until=_required_dt(data["until"]),
        hard_until=_required_dt(data["hard_until"]),
        window=int(data["window"]),
        armed_areas=tuple(a for a in data.get("armed_areas", ()) if a in area_ids),
        detections={
            zone_id: Detection(
                first=_required_dt(d["first"]),
                last=_required_dt(d["last"]),
                count=int(d.get("count", 1)),
            )
            for zone_id, d in (data.get("detections") or {}).items()
            if zone_id in zone_ids
        },
        user_id=data.get("user_id"),
        user_name=data.get("user_name"),
        channel=data.get("channel"),
        device_id=data.get("device_id"),
    )


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
            {
                "at": a.at.isoformat(),
                "channel": a.channel,
                "via": a.via,
                "user_id": a.user_id,
                "user_name": a.user_name,
                "contact_id": a.contact_id,
            }
            for a in incident.acknowledgements
        ],
        "actions_started": list(incident.actions_started),
        "escalation_exhausted": incident.escalation_exhausted,
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
            Acknowledgement(
                at=at,
                channel=a.get("channel"),
                via=a["via"],
                user_id=a.get("user_id"),
                user_name=a.get("user_name"),
                contact_id=a.get("contact_id"),
            )
        )
    return Incident(
        id=data["id"],
        opened_at=opened,
        contributors=tuple(contributors),
        acknowledged=bool(data.get("acknowledged", False)),
        acknowledgements=tuple(acknowledgements),
        actions_started=tuple(data.get("actions_started", ())),
        # Additive, read with a default: an older file restores as "not yet
        # exhausted", which is what it meant before this existed.
        escalation_exhausted=bool(data.get("escalation_exhausted", False)),
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
        device_ids = {d.id for d in config.devices}
        rule_ids = {r.id for r in config.rules}
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
                user_id=rt.get("user_id"),
                device_id=rt.get("device_id"),
                claimed=bool(rt.get("claimed", False)),
                locked_address=rt.get("locked_address") or None,
                skipped_exit=bool(rt.get("skipped_exit", False)),
                rule_id=rt.get("rule_id"),
                rule_name=rt.get("rule_name"),
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
            seen_devices=frozenset(
                d for d in data.get("seen_devices", ()) if d in device_ids
            ),
            in_clear=frozenset(d for d in data.get("in_clear", ()) if d in device_ids),
            faults=frozenset(z for z in data.get("faults", ()) if z in zone_ids),
            # Filtered against the live configuration like every other set
            # here: a zone that has gone is not a battery anybody can replace.
            low_batteries=frozenset(
                z for z in data.get("low_batteries", ()) if z in zone_ids
            ),
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
            bypass_until={
                z: _required_dt(due)
                for z, due in data.get("bypass_until", {}).items()
                if z in zone_ids
            },
            # A sequence held by a delay, and whatever is still switched on:
            # both survive a restart (part 3 decision 5). A run whose profile
            # is gone is dropped when it is resumed, not here.
            pending_runs=tuple(
                PendingRun(
                    id=r["id"],
                    profile_id=r["profile_id"],
                    moment=Moment(r["moment"]),
                    index=int(r["index"]),
                    due=_required_dt(r["due"]),
                    area_id=r.get("area_id"),
                    zone_id=r.get("zone_id"),
                    incident_id=r.get("incident_id"),
                    silent=bool(r.get("silent", False)),
                    placeholders=dict(r.get("placeholders") or {}),
                )
                for r in data.get("pending_runs", ())
            ),
            running=tuple(
                RunningAction(
                    action_id=r["action_id"],
                    kind=r["kind"],
                    entity_ids=tuple(r["entity_ids"]),
                    until=_dt(r.get("until")),
                    restore=r.get("restore"),
                    area_id=r.get("area_id"),
                    incident_id=r.get("incident_id"),
                    technical=r.get("technical") is True,
                    duress=r.get("duress") is True,
                )
                for r in data.get("running", ())
            ),
            run_seq=int(data.get("run_seq", 0)),
            walk_test=_walk_test_from(data.get("walk_test"), area_ids, zone_ids),
            # A lockout that a restart clears is an invitation to restart
            # Home Assistant, so it is written down like everything else.
            lockouts={
                key: Lockout(
                    failures=tuple(_required_dt(at) for at in lock.get("failures", ())),
                    until=_dt(lock.get("until")),
                    strikes=int(lock.get("strikes", 0)),
                    locked_at=_dt(lock.get("locked_at")),
                )
                for key, lock in data.get("lockouts", {}).items()
            },
            # An escalation whose profile the configuration no longer has is
            # restored all the same, and the engine ends it on the next call
            # with a row saying why. Dropping it here would make the same
            # event — a policy deleted while it was running — appear in the
            # log or not depending on whether the deletion happened before
            # or after a restart.
            escalations=tuple(
                Escalation(
                    kind=EscalationKind(e["kind"]),
                    profile_id=e["profile_id"],
                    moment=Moment(e["moment"]),
                    started_at=_required_dt(e["started_at"]),
                    severity=int(e.get("severity", 1)),
                    done=tuple(e.get("done", ())),
                    reference=e.get("reference"),
                )
                for e in data.get("escalations", ())
            ),
            # Automatic arming (§9.4), all read with a default: a state file
            # from an older build restores as "switch on, nothing counting
            # down, nothing suspended", which is a house that will announce
            # before it acts rather than one that will not.
            auto_arming=bool(data.get("auto_arming", True)),
            pending_rules=tuple(
                PendingRuleAction(
                    id=p["id"],
                    rule_id=p["rule_id"],
                    rule_name=p.get("rule_name", ""),
                    action=RuleActionKind(p["action"]),
                    due=_required_dt(p["due"]),
                    started_at=_required_dt(p["started_at"]),
                    scenario_id=p.get("scenario_id"),
                    area_ids=tuple(p.get("area_ids", ())),
                    suspension_name=p.get("suspension_name"),
                )
                for p in data.get("pending_rules", ())
            ),
            # A suspension that named rules and has lost every one of them
            # is dropped rather than filtered: an empty ``rule_ids`` means
            # *every* rule, so narrowing it to nothing would widen it to all
            # of them and suspend the whole house for a month.
            suspensions=tuple(
                Suspension(
                    id=sus["id"],
                    kind=SuspensionKind(sus["kind"]),
                    rule_ids=tuple(r for r in sus.get("rule_ids", ()) if r in rule_ids),
                    name=sus.get("name"),
                    start=_dt(sus.get("start")),
                    until=_dt(sus.get("until")),
                    reduced_scenario_id=sus.get("reduced_scenario_id"),
                    created_at=_dt(sus.get("created_at")),
                    user_id=sus.get("user_id"),
                    user_name=sus.get("user_name"),
                )
                for sus in data.get("suspensions", ())
                if not sus.get("rule_ids")
                or any(r in rule_ids for r in sus["rule_ids"])
            ),
            rules={
                rule_id: RuleRuntime(
                    since=_dt(rt.get("since")),
                    latched=bool(rt.get("latched", False)),
                    blocked=RuleBlock(rt["blocked"]) if rt.get("blocked") else None,
                    last_occurrence=_dt(rt.get("last_occurrence")),
                    seen=bool(rt.get("seen", False)),
                    schedule=rt.get("schedule")
                    if isinstance(rt.get("schedule"), str)
                    else None,
                    retrying=bool(rt.get("retrying", False)),
                )
                for rule_id, rt in data.get("rules", {}).items()
                if rule_id in rule_ids
            },
            pending_seq=int(data.get("pending_seq", 0)),
            health=_health_from(data.get("health"), config, zone_ids),
        )
    except (KeyError, TypeError, ValueError, AssertionError) as err:
        raise ConfigError(f"invalid Foyer runtime state: {err!r}") from err
