"""Configuration edits from the panel, validated in the backend (pure).

The panel sends whole objects; this module turns them into a new FoyerConfig
or into a list of problems. Nothing is trusted from the client: every edit is
parsed, validated as a complete configuration, and checked against what is
armed right now. The panel's own checks are a courtesy (INV-2).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields, replace
import re
from typing import Any
import uuid

from ..core.authz import DEFAULT_PERMISSIONS
from ..core.models import (
    MAX_RETENTION_DAYS,
    MIN_RETENTION_DAYS,
    SILENCEABLE,
    CodePolicy,
    DeviceKind,
    DeviceTransport,
    FoyerConfig,
    LogCategory,
    LogSettings,
    MqttSettings,
    RuntimeState,
    SecuritySettings,
    Settings,
    ZoneType,
)
from ..core.presets import preset
from ..core.privacy import (
    MAX_PSEUDONYMISE_DAYS,
    MIN_PSEUDONYMISE_DAYS,
    new_pseudonym,
)
from ..core.validation import Problem, edit_conflicts, notify_contacts, validate
from .schema import (
    ConfigError,
    area_from_dict,
    chime_from_dict,
    config_to_dict,
    contact_from_dict,
    device_from_dict,
    device_to_dict,
    group_from_dict,
    health_from_dict,
    log_from_dict,
    mqtt_from_dict,
    profile_from_dict,
    rule_from_dict,
    scenario_from_dict,
    security_from_dict,
    user_from_dict,
    user_to_dict,
    zone_from_dict,
)

KINDS = (
    "area",
    "zone",
    "scenario",
    "group",
    "profile",
    "user",
    "device",
    "contact",
    "rule",
)

# What a new area is given when the panel does not say. The delays come from
# the global settings, so a household that wants 45 s sets it once (§15.1).
_AREA_DEFAULTS: dict[str, Any] = {
    "ha_state_when_armed": "armed_away",
    "response_profile_id": None,
    # Not the perimeter until somebody says so (§4.5). Marking every area as
    # the outer ring would be safer in the abstract and a guess about their
    # house in practice, and a guess that quietly refuses the first disarm
    # rule they write is worse than a field they set deliberately.
    "is_perimeter": False,
}


def _area_defaults(config: FoyerConfig) -> dict[str, Any]:
    return {
        **_AREA_DEFAULTS,
        "default_entry_delay": config.settings.default_entry_delay,
        "default_exit_delay": config.settings.default_exit_delay,
    }


_ZONE_DEFAULTS: dict[str, Any] = {
    "entry_delay": None,
    "follows": [],
    "arm_hold_timeout": None,
    "allow_arm_when_faulted": False,
    "supervision_timeout": None,
    "enabled": True,
    "key": None,
    "chime": False,
    "cross_zone_id": None,
    "cross_zone_window": 60,
    "trigger_count": 1,
    "trigger_window": 60,
    "response_profile_id": None,
    "silent": False,
    "battery_entity_id": None,
}
_GROUP_DEFAULTS: dict[str, Any] = {
    "window_seconds": 60,
    "suppress_members": False,
    "response_profile_id": None,
}
_PROFILE_DEFAULTS: dict[str, Any] = {"severity": 1, "actions": []}
# A new person: the everyday permissions, no scope limits, no validity window.
# Not manage_users and not edit_config — handing out codes and rewriting the
# configuration are given deliberately, never by default (core.authz).
_USER_DEFAULTS: dict[str, Any] = {
    "code_hash": None,
    "duress_code_hash": None,
    "ha_user_id": None,
    "permissions": sorted(DEFAULT_PERMISSIONS),
    "allowed_area_ids": None,
    "allowed_scenario_ids": None,
    "valid_from": None,
    "valid_until": None,
    "code_exempt_when_identified": False,
    "enabled": True,
    "pseudonym": None,
}


# A new arming device. A keypad by default, because that is what somebody is
# holding when they open page 8; a tag is chosen deliberately, and then has to
# name its entity and its owner before it may exist at all (core.validation).
# A new contact: somebody with a name and no way of reaching them yet, which
# validation refuses to store — page 6 asks for the first channel in the same
# form, because a contact nobody can reach is a step that silently reaches
# nobody (§7.1). Quiet hours are off, and when they are set only what the log
# calls an alarm gets through (part 1 decision 3).
_CONTACT_DEFAULTS: dict[str, Any] = {
    "channels": [],
    "quiet_start": None,
    "quiet_end": None,
    "quiet_min_severity": "alarm",
    "linked_user_id": None,
    "enabled": True,
}


# A new automatic rule (§9.4): absence, the arming action, and the grace
# period §9.4 sets for one — two minutes, announced, cancellable. No guards
# and no active window, because a guard nobody asked for is a rule that does
# not act for a reason nobody can see.
_RULE_DEFAULTS: dict[str, Any] = {
    "trigger": {
        "kind": "absence",
        "entity_ids": [],
        "state": None,
        "minutes": 30,
        "at": None,
        "weekdays": [],
    },
    "action": "arm",
    "scenario_id": None,
    "area_ids": [],
    "window": {"weekdays": [], "after": None, "before": None},
    "guards": {
        "only_when_disarmed": False,
        "only_when_ready": False,
        "quiet_minutes": None,
    },
    "grace_seconds": 120,
    "notify_contact_ids": [],
    "enabled": True,
}


_DEVICE_DEFAULTS: dict[str, Any] = {
    "kind": "keypad",
    "ref": None,
    "entity_id": None,
    "event_type": None,
    "user_id": None,
    "command": "toggle",
    "scenario_id": None,
    "enabled": True,
}


@dataclass(frozen=True, slots=True)
class EditResult:
    config: FoyerConfig | None
    problems: tuple[Problem, ...] = ()
    id: str | None = None


def _fail(*problems: Problem) -> EditResult:
    return EditResult(config=None, problems=tuple(problems))


# What an id may be made of. Every id Foyer generates is a uuid's hex.
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def upsert(
    config: FoyerConfig,
    state: RuntimeState,
    kind: str,
    item: dict[str, Any],
    *,
    trigger_confirmed: bool = False,
    new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> EditResult:
    """Create or replace one area, zone or scenario."""
    if kind not in KINDS:
        return _fail(Problem("unknown_kind", kind))
    data = dict(item)
    data["id"] = data.get("id") or new_id()
    if not isinstance(data["id"], str) or not _SAFE_ID.fullmatch(data["id"]):
        # Ids are generated here; one a client chose is at least plain. An
        # id with a quote or an accent in it is escaped differently in the
        # log's JSON detail, and the erasure of §10.4 then misses the rows
        # about that person (second review).
        return _fail(Problem("invalid", kind, str(data["id"])[:64]))
    try:
        if kind == "area":
            obj = area_from_dict({**_area_defaults(config), **data})
            items = _replace_in(config.areas, obj)
            new = replace(config, areas=items)
        elif kind == "scenario":
            obj = scenario_from_dict(data)
            new = replace(config, scenarios=_replace_in(config.scenarios, obj))
        elif kind == "user":
            # The pseudonym is minted once and then carried, never recomputed
            # (§10.4, part 2 decision 4). The stored one wins over anything a
            # client sends: it is the identifier a person's already-swept rows
            # carry, so a caller that could choose it could merge two people's
            # histories under one identifier, or set it to somebody's name and
            # turn the whole sweep into a rename (found in review).
            known = config.user(data["id"])
            data["pseudonym"] = (known.pseudonym if known else None) or new_pseudonym(
                new_id()
            )
            obj = user_from_dict({**_USER_DEFAULTS, **data})
            new = replace(config, users=_replace_in(config.users, obj))
        elif kind == "device":
            obj = device_from_dict({**_DEVICE_DEFAULTS, **data})
            # The token is never the client's to set, and never the client's
            # to see (§9.2.1): it is whatever `set_device_token` last stored,
            # carried through every other save. A keypad taken off the
            # endpoint loses it there and then, so it cannot come back to
            # life the day the keypad is switched back.
            known = config.device(obj.id)
            keeps = (
                known is not None
                and obj.kind is DeviceKind.KEYPAD
                and obj.transport is DeviceTransport.HTTP
            )
            obj = replace(obj, token_hash=known.token_hash if keeps else None)
            new = replace(config, devices=_replace_in(config.devices, obj))
        elif kind == "contact":
            for channel in data.get("channels") or ():
                channel["id"] = channel.get("id") or new_id()
            obj = contact_from_dict({**_CONTACT_DEFAULTS, **data})
            new = replace(config, contacts=_replace_in(config.contacts, obj))
        elif kind == "rule":
            obj = rule_from_dict({**_RULE_DEFAULTS, **data})
            new = replace(config, rules=_replace_in(config.rules, obj))
        elif kind == "group":
            obj = group_from_dict({**_GROUP_DEFAULTS, **data})
            new = replace(config, groups=_replace_in(config.groups, obj))
        elif kind == "profile":
            data.setdefault("actions", [])
            for action in data["actions"]:
                action["id"] = action.get("id") or new_id()
            obj = profile_from_dict({**_PROFILE_DEFAULTS, **data})
            new = replace(config, profiles=_replace_in(config.profiles, obj))
        else:
            zone_type = ZoneType(data.get("type", "instant"))
            obj = zone_from_dict({**_ZONE_DEFAULTS, **preset(zone_type), **data})
            previous = config.zone(obj.id)
            # INV-5: a trigger is never saved unless the user confirmed it,
            # whatever the client claims to have shown. Enforced here.
            if (previous is None or previous.trigger != obj.trigger) and not (
                trigger_confirmed
            ):
                return _fail(
                    Problem("trigger_not_confirmed", "zone", obj.id, "trigger")
                )
            # Whether the trigger was confirmed is never the client's to say
            # in the item: it is this request's confirmation, or what the
            # stored zone already had. Otherwise an imported zone could be
            # switched on by sending `trigger_confirmed: true` in its body.
            obj = replace(
                obj,
                trigger_confirmed=trigger_confirmed
                or (previous is not None and previous.trigger_confirmed),
            )
            new = replace(config, zones=_replace_in(config.zones, obj))
    except (ConfigError, KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", kind, data["id"]))
    return _check(config, new, state, data["id"])


def delete(
    config: FoyerConfig, state: RuntimeState, kind: str, item_id: str
) -> EditResult:
    """Remove one object. Refused while something still depends on it."""
    if kind == "area":
        if config.area(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        if any(z.area_id == item_id for z in config.zones):
            return _fail(Problem("area_has_zones", kind, item_id))
        if any(item_id in s.areas for s in config.scenarios):
            return _fail(Problem("area_in_scenario", kind, item_id))
        if any(g.area_id == item_id for g in config.groups):
            return _fail(Problem("area_has_groups", kind, item_id))
        new = replace(config, areas=tuple(a for a in config.areas if a.id != item_id))
    elif kind == "zone":
        if config.zone(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        # Say why, instead of letting validation report a dangling reference:
        # a group or a cross-zone partner must be edited first, knowingly.
        if any(item_id in g.members for g in config.groups):
            return _fail(Problem("zone_in_group", kind, item_id))
        if any(z.cross_zone_id == item_id for z in config.zones):
            return _fail(Problem("zone_is_cross_partner", kind, item_id))
        new = replace(config, zones=tuple(z for z in config.zones if z.id != item_id))
    elif kind == "user":
        if config.user(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        # A key zone pointing at this person would lose the only identity it
        # has, and a scenario's guest list would quietly widen. Say so.
        if any(z.key is not None and z.key.user_id == item_id for z in config.zones):
            return _fail(Problem("user_holds_a_key", kind, item_id))
        # A tag is nothing but the person it names (§9.3): deleting them would
        # leave a token that opens the house and belongs to nobody.
        if any(d.user_id == item_id for d in config.devices):
            return _fail(Problem("user_holds_a_tag", kind, item_id))
        if any(
            s.allowed_user_ids is not None and item_id in s.allowed_user_ids
            for s in config.scenarios
        ):
            return _fail(Problem("user_in_scenario", kind, item_id))
        new = replace(config, users=tuple(u for u in config.users if u.id != item_id))
    elif kind == "contact":
        if config.contact(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        # An action still naming this person would quietly reach nobody, and
        # a step that reaches nobody is the failure §7 exists to prevent. Say
        # so instead, and let the profile be edited knowingly.
        if any(
            item_id in (r["contact_id"] for r in notify_contacts(a))
            for p in config.profiles
            for a in p.actions
        ):
            return _fail(Problem("contact_in_use", kind, item_id))
        new = replace(
            config, contacts=tuple(c for c in config.contacts if c.id != item_id)
        )
    elif kind == "rule":
        if config.rule(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        new = replace(config, rules=tuple(r for r in config.rules if r.id != item_id))
    elif kind == "device":
        if config.device(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        new = replace(
            config, devices=tuple(d for d in config.devices if d.id != item_id)
        )
    elif kind == "group":
        if config.group(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        new = replace(config, groups=tuple(g for g in config.groups if g.id != item_id))
    elif kind == "profile":
        if config.profile(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        # Deleting a profile something still points at would silently move
        # that thing back to the default: say so instead.
        if item_id in _referenced_profiles(config):
            return _fail(Problem("profile_in_use", kind, item_id))
        new = replace(
            config, profiles=tuple(p for p in config.profiles if p.id != item_id)
        )
    elif kind == "scenario":
        if config.scenario(item_id) is None:
            return _fail(Problem("not_found", kind, item_id))
        if any(z.key and z.key.scenario_id == item_id for z in config.zones):
            return _fail(Problem("scenario_in_use", kind, item_id))
        new = replace(
            config, scenarios=tuple(s for s in config.scenarios if s.id != item_id)
        )
    else:
        return _fail(Problem("unknown_kind", kind))
    return _check(config, new, state, item_id)


def _referenced_profiles(config: FoyerConfig) -> set[str]:
    """Every profile id the configuration points at."""
    refs = {
        config.settings.default_profile_id,
        config.settings.technical_profile_id,
        *(a.response_profile_id for a in config.areas),
        *(z.response_profile_id for z in config.zones),
        *(s.response_profile_id for s in config.scenarios),
        *(g.response_profile_id for g in config.groups),
    }
    return {ref for ref in refs if ref}


# The one field of the settings block a caller may never choose, only ask for
# (§7.2, part 1 decision 6). The whole of what protects an unauthenticated
# webhook is that nobody can guess its address, so the id is generated and
# handed down through ``webhook_id`` — never read out of the settings a
# client sends, however much permission that client holds.
KEEP_WEBHOOK = object()


def update_settings(
    config: FoyerConfig,
    state: RuntimeState,
    settings: dict[str, Any],
    *,
    webhook_id: str | object | None = KEEP_WEBHOOK,
) -> EditResult:
    """The global settings block. Unknown keys are ignored; known ones keep
    their current value when the caller leaves them out."""
    current = config.settings
    try:
        silent = settings.get("silent_suppresses", list(current.silent_suppresses))
        new = replace(
            config,
            settings=Settings(
                siren_duration=int(settings["siren_duration"]),
                arm_hold_timeout=int(settings["arm_hold_timeout"]),
                default_profile_id=settings.get(
                    "default_profile_id", current.default_profile_id
                )
                or None,
                technical_profile_id=settings.get(
                    "technical_profile_id", current.technical_profile_id
                )
                or None,
                silent_suppresses=tuple(
                    kind for kind in silent if isinstance(kind, str)
                ),
                camera_dir=str(settings.get("camera_dir", current.camera_dir)),
                log=_log_from(settings.get("log"), current.log),
                default_entry_delay=int(
                    settings.get("default_entry_delay", current.default_entry_delay)
                ),
                default_exit_delay=int(
                    settings.get("default_exit_delay", current.default_exit_delay)
                ),
                language=settings.get("language", current.language) or None,
                wizard_done=bool(settings.get("wizard_done", current.wizard_done)),
                low_battery_threshold=int(
                    settings.get("low_battery_threshold", current.low_battery_threshold)
                ),
                walk_test_timeout=int(
                    settings.get("walk_test_timeout", current.walk_test_timeout)
                ),
                # The DTMF webhook's id (§7.2). Deliberately NOT read from
                # ``settings``: an id a client could choose would eventually
                # be one somebody could guess, and this URL stops an alarm.
                # It changes only through the command that generates it.
                ack_webhook_id=(
                    current.ack_webhook_id
                    if webhook_id is KEEP_WEBHOOK
                    else (webhook_id or None)  # type: ignore[arg-type]
                ),
                mqtt=_mqtt_from(settings.get("mqtt"), current.mqtt),
                # Page 11 does not own these — page 7 does, through
                # update_security — so a settings save must carry them through
                # untouched. Rebuilding Settings without them put the code
                # length back to six, and a household with eight-digit codes
                # then had a keypad that submitted after six and a lockout
                # waiting at the fifth try.
                security=_security_from(settings.get("security"), current.security),
                # Not in the list above, and that was the whole bug (found in
                # review): this block builds a fresh Settings rather than
                # replacing fields on the stored one, so a field nobody
                # enumerated fell back to its dataclass default — `False`.
                # Page 12's switch could therefore never be turned on, and
                # any unrelated save turned it off again. §9.4 point 2 is a
                # decision the household makes; it is not one a settings save
                # gets to unmake.
                allow_auto_disarm=bool(
                    settings.get("allow_auto_disarm", current.allow_auto_disarm)
                ),
            ),
        )
    except (KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "settings"))
    if any(kind not in SILENCEABLE for kind in new.settings.silent_suppresses):
        return _fail(
            Problem("unknown_action_kind", "settings", None, "silent_suppresses")
        )
    log = new.settings.log
    if any(
        not MIN_RETENTION_DAYS <= log.retention(c.value) <= MAX_RETENTION_DAYS
        for c in LogCategory
    ):
        return _fail(Problem("retention_out_of_range", "settings", None, "log"))
    if log.pseudonymise_after is not None and not (
        MIN_PSEUDONYMISE_DAYS <= log.pseudonymise_after <= MAX_PSEUDONYMISE_DAYS
    ):
        return _fail(
            Problem("retention_out_of_range", "settings", None, "pseudonymise_after")
        )
    return _check(config, new, state, None)


def _policy_from(data: Any, current: CodePolicy) -> CodePolicy:
    """The code policy the caller sent, on top of the one already stored."""
    if not isinstance(data, dict):
        return current
    known = {f.name for f in fields(CodePolicy)}
    return replace(current, **{k: bool(v) for k, v in data.items() if k in known})


def _security_from(data: Any, current: SecuritySettings) -> SecuritySettings:
    """The code and lockout numbers, or the ones already stored."""
    if not isinstance(data, dict):
        return current
    return security_from_dict(data)


def _mqtt_from(data: Any, current: MqttSettings) -> MqttSettings:
    """The MQTT block, or the current one when the caller leaves it out.

    Parsed by the same function that reads the stored document, so what page 8
    sends and what is on disk can never mean two different things.
    """
    if not isinstance(data, dict):
        return current
    return mqtt_from_dict(data)


def _log_from(data: Any, current: LogSettings) -> LogSettings:
    """The log block, or the current one when the caller leaves it out.

    Parsed by the same function that reads the stored document, so what the
    panel sends and what is on disk can never mean two different things.

    The two settings of §10.4 are kept when the caller does not mention them.
    ``enabled`` and ``retention_days`` round-trip to their documented defaults
    when they are missing, which is harmless; these two carry a deliberate
    answer — "replace names after N days", "take the log with you" — and a
    save that moved a retention slider and silently switched both off would
    be a privacy setting nobody could keep (found in review).
    """
    if not isinstance(data, dict):
        return current
    # Merged category by category, not map by map: a payload naming the
    # retention of one category would otherwise put every other one back to
    # thirty days, which the next purge acts on (second review).
    categories = [c.value for c in LogCategory]
    merged = dict(data)
    if isinstance(data.get("enabled"), dict):
        merged["enabled"] = {
            **{c: current.is_enabled(c) for c in categories},
            **data["enabled"],
        }
    if isinstance(data.get("retention_days"), dict):
        merged["retention_days"] = {
            **{c: current.retention(c) for c in categories},
            **data["retention_days"],
        }
    parsed = log_from_dict(merged)
    return replace(
        parsed,
        # Every part of the block keeps what the caller did not mention, not
        # only the two settings of §10.4 (found in review). `log_from_dict`
        # is sparse by design — it keeps only what differs from the
        # documented default — so a payload naming one field would otherwise
        # switch every category back on and every retention back to thirty
        # days, which on the next purge deletes rows the household had asked
        # to keep longer.
        enabled=parsed.enabled if "enabled" in data else current.enabled,
        retention_days=(
            parsed.retention_days
            if "retention_days" in data
            else current.retention_days
        ),
        pseudonymise_after=(
            parsed.pseudonymise_after
            if "pseudonymise_after" in data
            else current.pseudonymise_after
        ),
        delete_on_uninstall=(
            parsed.delete_on_uninstall
            if "delete_on_uninstall" in data
            else current.delete_on_uninstall
        ),
    )


# What one field's before-and-after may be worth printing in a log row. A
# number, a name, a flag and a short list are; a profile's whole action list is
# not, and the row would become the configuration itself.
_SIMPLE = (str, int, float, bool, type(None))
_MAX_LIST = 6


def _simple(value: Any) -> bool:
    if isinstance(value, _SIMPLE):
        return True
    if isinstance(value, (list, tuple)):
        return len(value) <= _MAX_LIST and all(isinstance(v, _SIMPLE) for v in value)
    return False


def _pair(before: Any, after: Any) -> list[Any]:
    """``[before, after]`` when both are worth reading, ``[]`` when they are
    not: the field still says it changed, without dragging its contents in."""
    if _simple(before) and _simple(after):
        return [before, after]
    return []


def _fields(was: dict[str, Any], now: dict[str, Any]) -> dict[str, list[Any]]:
    return {
        key: _pair(was.get(key), now.get(key))
        for key in sorted(was.keys() | now.keys())
        if was.get(key) != now.get(key)
    }


def set_device_token(
    config: FoyerConfig, state: RuntimeState, device_id: str, token_hash: str | None
) -> EditResult:
    """Store a keypad's new token hash, or none (§9.2.1).

    The one path a token reaches the configuration by. It is generated by
    the caller, shown once and never stored in the clear: what arrives here
    is its SHA-256. Only a keypad on the endpoint may hold one (decision 99);
    a new one replaces the old at once, which is what closes the old one's
    streams.
    """
    device = config.device(device_id)
    if device is None:
        return _fail(Problem("unknown_device", "device", device_id))
    if token_hash is not None and (
        device.kind is not DeviceKind.KEYPAD
        or device.transport is not DeviceTransport.HTTP
    ):
        return _fail(Problem("tag_has_no_token", "device", device_id, "transport"))
    new = replace(
        config,
        devices=_replace_in(config.devices, replace(device, token_hash=token_hash)),
    )
    return _check(config, new, state, device_id)


# The configuration holds three credentials, and a log row is a place none of
# them may appear (§9.2.1): whoever reads the `config` category would be
# reading the address of a URL that stops an alarm, the address that keeps a
# dead installation looking alive, or the hash of a keypad's token. The row
# still says each one changed.
_REDACTED = "***"

# Kinds whose row says which field changed and nothing more (review
# follow-up). A contact's channels carry the notify service, which is named
# after somebody's phone, and a rule's trigger carries the people it watches:
# before-and-after values there would put in a row, unswept, what the
# privacy sweeps of §10.4 take out of every other one.
_FIELDS_ONLY = frozenset({"contacts", "rules"})


def _without_credentials(document: dict[str, Any]) -> dict[str, Any]:
    for device in document.get("devices", []):
        if device.get("token_hash"):
            device["token_hash"] = _REDACTED
    for user in document.get("users", []):
        # A person's codes are hashes and never belong in a row; their
        # pseudonym is the identifier a swept row carries, and a row that
        # printed it beside the name would undo the sweep.
        for key in ("code_hash", "duress_code_hash"):
            if user.get(key):
                user[key] = _REDACTED
        user.pop("pseudonym", None)
        # Nor their name: a config row is written by whoever made the change
        # and is not one the sweep of §10.4 rewrites, so a name here would
        # outlive the pseudonymisation of everything the person did. The row
        # names them by id, which the erasure does reach.
        user.pop("name", None)
    for contact in document.get("contacts", []):
        # The same for somebody in the address book: a name, and the phone
        # numbers and chat ids in their channels, are not what a row about
        # who changed the configuration needs to carry.
        contact.pop("name", None)
        for channel in contact.get("channels") or ():
            channel.pop("target", None)
            channel.pop("data", None)
    settings = document.get("settings") or {}
    if settings.get("ack_webhook_id"):
        settings["ack_webhook_id"] = _REDACTED
    watchdog = (document.get("health") or {}).get("watchdog") or {}
    if watchdog.get("url"):
        watchdog["url"] = _REDACTED
    return document


def _labeller(*sides: dict[str, dict[str, Any]]):
    """How an item is named in the row: its name, and its id as well when two
    carry the same name — keyed by name alone, one overwrote the other's
    entry (second review)."""
    names = [item.get("name") for side in sides for item in side.values()]
    ids = {i: item.get("name") for side in sides for i, item in side.items()}
    shared = {
        n for n in names if n is not None and sum(v == n for v in ids.values()) > 1
    }

    def label(item: dict[str, Any]) -> str:
        name = item.get("name") or item["id"]
        return f"{name} ({item['id'][:8]})" if name in shared else name

    return label


def config_diff(old: FoyerConfig, new: FoyerConfig) -> dict[str, Any]:
    """What an edit changed, for the log (§10.2, category ``config``).

    "Who changed what" is the question this category exists to answer, and a
    field name alone does not answer it: the row carries the value before and
    the value after. What it does not carry is anything long — a profile's
    action list, a trigger's states — because a row that contains the
    configuration is a row nobody reads.
    """
    before = _without_credentials(config_to_dict(old))
    after = _without_credentials(config_to_dict(new))
    # A credential replaced by another is still a change: the redaction above
    # makes the two sides equal, so the fact is put back as the field alone.
    secrets_changed: dict[str, dict[str, set[str]]] = {
        "devices": {
            d.id: {"token_hash"}
            for d in new.devices
            if (o := old.device(d.id)) is not None and o.token_hash != d.token_hash
        },
        "users": {
            u.id: {
                key
                for key in ("code_hash", "duress_code_hash", "name")
                if getattr(o, key) != getattr(u, key)
            }
            for u in new.users
            if (o := old.user(u.id)) is not None
        },
        "contacts": {
            c.id: {
                key
                for key in ("name", "channels")
                if getattr(o, key) != getattr(c, key)
            }
            for c in new.contacts
            if (o := old.contact(c.id)) is not None
        },
    }
    changes: dict[str, Any] = {}
    # Every kind of thing a household configures, people, contacts and rules
    # included: which rule was changed to disarm, and who was given
    # `manage_users`, are the questions this category exists for (second
    # review).
    for kind in (
        "areas",
        "zones",
        "scenarios",
        "groups",
        "profiles",
        "devices",
        "users",
        "contacts",
        "rules",
    ):
        was = {item["id"]: item for item in before.get(kind, [])}
        now = {item["id"]: item for item in after.get(kind, [])}
        label = _labeller(was, now)
        added = [label(now[i]) for i in now.keys() - was.keys()]
        removed = [label(was[i]) for i in was.keys() - now.keys()]
        edited = {
            # The name it has now: a rename shows as a change of "name", and
            # filing it under the old one would hide it from the object it
            # belongs to.
            label(now[i]): _fields(was[i], now[i])
            for i in was.keys() & now.keys()
            if was[i] != now[i]
        }
        if kind in _FIELDS_ONLY:
            edited = {
                name: {key: [] for key in fields} for name, fields in edited.items()
            }
        for i, keys in secrets_changed.get(kind, {}).items():
            if i in was and i in now:
                for key in keys:
                    edited.setdefault(label(now[i]), {})[key] = []
        entry = {
            k: v
            for k, v in (("added", added), ("removed", removed), ("changed", edited))
            if v
        }
        if entry:
            changes[kind] = entry
    for block in ("settings", "chime", "code_policy", "health"):
        was_block, now_block = before.get(block) or {}, after.get(block) or {}
        if was_block != now_block:
            changes[block] = _fields(was_block, now_block)
    # The same for the other two credentials: one real value replaced by
    # another redacts to the same "***" on both sides, and a watchdog pointed
    # somewhere else — the one address that keeps a dead house looking alive —
    # must not leave a row saying nothing changed.
    if old.settings.ack_webhook_id != new.settings.ack_webhook_id:
        changes.setdefault("settings", {})["ack_webhook_id"] = []
    if old.health.watchdog.url != new.health.watchdog.url:
        changes.setdefault("health", {})["watchdog.url"] = []
    return changes


def touches_people(old: FoyerConfig, new: FoyerConfig) -> bool:
    """Whether going from one configuration to the other adds, removes or
    changes a person or a tag (decision 111).

    What `manage_users` owns: who exists, what they may do, and which key
    opens the house as whom. The codes and the pseudonym are left out of the
    comparison because a restore keeps the installation's own — they would
    differ between the file and the house without anybody having changed a
    person.
    """

    def people(config: FoyerConfig) -> dict[str, dict[str, Any]]:
        return {
            user.id: {
                k: v
                for k, v in user_to_dict(user).items()
                if k not in ("code_hash", "duress_code_hash", "pseudonym")
            }
            for user in config.users
        }

    def tags(config: FoyerConfig) -> dict[str, dict[str, Any]]:
        return {
            d.id: device_to_dict(d) for d in config.devices if d.kind is DeviceKind.TAG
        }

    return people(old) != people(new) or tags(old) != tags(new)


def update_security(
    config: FoyerConfig, state: RuntimeState, data: dict[str, Any]
) -> EditResult:
    """The code policy and the code and lockout settings (§8.2, §8.4).

    Separate from the settings block because it is separate in the document:
    the policy is a property of the installation, not of its defaults, and
    every path in the system resolves it.
    """
    try:
        # Merged onto the stored policy, and unknown keys ignored (found in
        # review). Splatted straight into the constructor, a payload naming
        # one operation reset every other one to its default — an
        # installation that asks for a code to arm would lose that with
        # nothing reported — and a document from a newer minor version, which
        # is additive by contract, raised TypeError and failed the whole
        # save.
        policy = _policy_from(data.get("code_policy"), config.code_policy)
        security = security_from_dict(data["security"])
    except (ConfigError, KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "settings"))
    new = replace(
        config,
        code_policy=policy,
        settings=replace(config.settings, security=security),
    )
    return _check(config, new, state, None)


def update_chime(
    config: FoyerConfig, state: RuntimeState, chime: dict[str, Any]
) -> EditResult:
    """The global chime block (§6.6). Whether each zone chimes is on the zone."""
    try:
        new = replace(config, chime=chime_from_dict(chime))
    except (ConfigError, KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "chime"))
    return _check(config, new, state, None)


def update_health(
    config: FoyerConfig, state: RuntimeState, health: dict[str, Any]
) -> EditResult:
    """The system-health block (§12): the mains, the watchdog, the radios.

    One block rather than three editable objects, for the reason the chime
    is one block: it is a page of settings about the installation itself,
    not a list of things a household creates and deletes. The radios inside
    it are a list because there can be two, and a Zigbee outage says nothing
    about Z-Wave.
    """
    try:
        new = replace(config, health=health_from_dict(health))
    except (ConfigError, KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "health"))
    return _check(config, new, state, None)


def _replace_in(items: tuple, obj) -> tuple:
    if any(i.id == obj.id for i in items):
        return tuple(obj if i.id == obj.id else i for i in items)
    return (*items, obj)


def _check(
    old: FoyerConfig, new: FoyerConfig, state: RuntimeState, item_id: str | None
) -> EditResult:
    problems = validate(new) + edit_conflicts(old, new, state)
    if problems:
        return EditResult(config=None, problems=tuple(problems), id=item_id)
    return EditResult(config=new, id=item_id)
