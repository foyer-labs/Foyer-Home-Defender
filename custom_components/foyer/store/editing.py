"""Configuration edits from the panel, validated in the backend (pure).

The panel sends whole objects; this module turns them into a new FoyerConfig
or into a list of problems. Nothing is trusted from the client: every edit is
parsed, validated as a complete configuration, and checked against what is
armed right now. The panel's own checks are a courtesy (INV-2).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any
import uuid

from ..core.models import (
    MAX_RETENTION_DAYS,
    MIN_RETENTION_DAYS,
    SILENCEABLE,
    FoyerConfig,
    LogCategory,
    LogSettings,
    RuntimeState,
    Settings,
    ZoneType,
)
from ..core.presets import preset
from ..core.validation import Problem, edit_conflicts, validate
from .schema import (
    ConfigError,
    area_from_dict,
    chime_from_dict,
    config_to_dict,
    group_from_dict,
    log_from_dict,
    profile_from_dict,
    scenario_from_dict,
    zone_from_dict,
)

KINDS = ("area", "zone", "scenario", "group", "profile")

# What a new area is given when the panel does not say. The delays come from
# the global settings, so a household that wants 45 s sets it once (§15.1).
_AREA_DEFAULTS: dict[str, Any] = {
    "ha_state_when_armed": "armed_away",
    "response_profile_id": None,
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
}
_GROUP_DEFAULTS: dict[str, Any] = {
    "window_seconds": 60,
    "suppress_members": False,
    "response_profile_id": None,
}
_PROFILE_DEFAULTS: dict[str, Any] = {"severity": 1, "actions": []}


@dataclass(frozen=True, slots=True)
class EditResult:
    config: FoyerConfig | None
    problems: tuple[Problem, ...] = ()
    id: str | None = None


def _fail(*problems: Problem) -> EditResult:
    return EditResult(config=None, problems=tuple(problems))


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
    try:
        if kind == "area":
            obj = area_from_dict({**_area_defaults(config), **data})
            items = _replace_in(config.areas, obj)
            new = replace(config, areas=items)
        elif kind == "scenario":
            obj = scenario_from_dict(data)
            new = replace(config, scenarios=_replace_in(config.scenarios, obj))
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


def update_settings(
    config: FoyerConfig, state: RuntimeState, settings: dict[str, Any]
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
    return _check(config, new, state, None)


def _log_from(data: Any, current: LogSettings) -> LogSettings:
    """The log block, or the current one when the caller leaves it out.

    Parsed by the same function that reads the stored document, so what the
    panel sends and what is on disk can never mean two different things.
    """
    if not isinstance(data, dict):
        return current
    return log_from_dict(data)


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


def config_diff(old: FoyerConfig, new: FoyerConfig) -> dict[str, Any]:
    """What an edit changed, for the log (§10.2, category ``config``).

    "Who changed what" is the question this category exists to answer, and a
    field name alone does not answer it: the row carries the value before and
    the value after. What it does not carry is anything long — a profile's
    action list, a trigger's states — because a row that contains the
    configuration is a row nobody reads.
    """
    before, after = config_to_dict(old), config_to_dict(new)
    changes: dict[str, Any] = {}
    for kind in ("areas", "zones", "scenarios", "groups", "profiles"):
        was = {item["id"]: item for item in before.get(kind, [])}
        now = {item["id"]: item for item in after.get(kind, [])}
        added = [now[i].get("name", i) for i in now.keys() - was.keys()]
        removed = [was[i].get("name", i) for i in was.keys() - now.keys()]
        edited = {
            # The name it has now: a rename shows as a change of "name", and
            # filing it under the old one would hide it from the object it
            # belongs to.
            now[i].get("name", i): _fields(was[i], now[i])
            for i in was.keys() & now.keys()
            if was[i] != now[i]
        }
        entry = {
            k: v
            for k, v in (("added", added), ("removed", removed), ("changed", edited))
            if v
        }
        if entry:
            changes[kind] = entry
    for block in ("settings", "chime", "code_policy"):
        was_block, now_block = before.get(block) or {}, after.get(block) or {}
        if was_block != now_block:
            changes[block] = _fields(was_block, now_block)
    return changes


def update_chime(
    config: FoyerConfig, state: RuntimeState, chime: dict[str, Any]
) -> EditResult:
    """The global chime block (§6.6). Whether each zone chimes is on the zone."""
    try:
        new = replace(config, chime=chime_from_dict(chime))
    except (ConfigError, KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "chime"))
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
