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

from ..core.models import FoyerConfig, RuntimeState, Settings, ZoneType
from ..core.presets import preset
from ..core.validation import Problem, edit_conflicts, validate
from .schema import (
    ConfigError,
    area_from_dict,
    chime_from_dict,
    group_from_dict,
    scenario_from_dict,
    zone_from_dict,
)

KINDS = ("area", "zone", "scenario", "group")

_AREA_DEFAULTS: dict[str, Any] = {
    "default_entry_delay": 30,
    "default_exit_delay": 30,
    "ha_state_when_armed": "armed_away",
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
}
_GROUP_DEFAULTS: dict[str, Any] = {
    "window_seconds": 60,
    "suppress_members": False,
}


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
            obj = area_from_dict({**_AREA_DEFAULTS, **data})
            items = _replace_in(config.areas, obj)
            new = replace(config, areas=items)
        elif kind == "scenario":
            obj = scenario_from_dict(data)
            new = replace(config, scenarios=_replace_in(config.scenarios, obj))
        elif kind == "group":
            obj = group_from_dict({**_GROUP_DEFAULTS, **data})
            new = replace(config, groups=_replace_in(config.groups, obj))
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


def update_settings(
    config: FoyerConfig, state: RuntimeState, settings: dict[str, Any]
) -> EditResult:
    try:
        new = replace(
            config,
            settings=Settings(
                siren_duration=int(settings["siren_duration"]),
                arm_hold_timeout=int(settings["arm_hold_timeout"]),
            ),
        )
    except (KeyError, TypeError, ValueError):
        return _fail(Problem("invalid", "settings"))
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
