"""API devices: what a device on the endpoint may read and do (SPEC §9.2.2).

The endpoint of §9.2.1 authenticates a device by its token. This module
decides what that device may then read and do, and builds what it reads:

* **scopes** are the device's own, every one off until switched on
  (decision 115);
* **without a code a device only reads** — every action needs a code, arming
  included, whatever the policy of §8.2 would ask (decision 116);
* each read scope is **free or after a code** (decision 117), and a code
  **unlocks** the device for as long as it says, within what the code's
  owner may read (decision 118);
* a scope beyond ``status`` is served **in the clear only if the owner has
  confirmed it** (decision 119);
* the state is streamed, and each **section** is a small request of its own,
  announced on the stream when it changes (decision 120).

The names in this module — actions, sections, reasons — are the contract of
``docs/api/openapi.yaml`` (decision 121); a test compares the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from ..core.journal import address_note, security_row
from ..core.models import (
    READ_SCOPES,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    Actor,
    AreaState,
    ArmAreaRequest,
    ArmingDevice,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    CodeAttempt,
    CodeResult,
    DeviceScope,
    DisarmRequest,
    FoyerConfig,
    Permission,
    Reason,
    RuntimeState,
    ZoneType,
)
from ..runtime.system import FoyerSystem

# The contract version of docs/api/openapi.yaml (decision 121).
CONTRACT_VERSION = "v1"

# Every action a device may send, and the scope each needs. `status` is a
# read: "tell me again", for a device that has just booted.
ACTION_SCOPES: dict[str, str] = {
    "status": DeviceScope.STATUS,
    "arm": DeviceScope.ARM,
    "disarm": DeviceScope.DISARM,
    "exclude": DeviceScope.EXCLUDE,
    "include": DeviceScope.EXCLUDE,
    "acknowledge": DeviceScope.ACKNOWLEDGE,
}
# Not commands to the house: a code offered to read, and the end of it.
SESSION_ACTIONS = ("unlock", "lock")
ACTIONS: tuple[str, ...] = (*ACTION_SCOPES, *SESSION_ACTIONS)

# The sections read with a request of their own, and the scope each needs.
SECTIONS: dict[str, str] = {
    "zones": DeviceScope.ZONES,
    "batteries": DeviceScope.BATTERIES,
    "health": DeviceScope.HEALTH,
    "log": DeviceScope.LOG,
}

# At most this many log rows a request: a microcontroller has little memory.
MAX_LOG_ROWS = 50
DEFAULT_LOG_ROWS = 20

# Who is unlocked, until when, and with whose code. In memory on purpose: a
# restart ends every unlock, which is the safe direction for it to fail.
_UNLOCKS = f"{DOMAIN}_device_unlocks"
# The last log row each device's reader could see, for the stream's notice.
_LOG_SEEN = f"{DOMAIN}_device_log_seen"


@dataclass(slots=True)
class Unlock:
    user_id: str
    until: datetime
    # The token it was opened under: a new token is a new device as far as
    # anybody reading it is concerned (review).
    token_hash: str | None


# --- the unlock (decision 118) --------------------------------------------------


def unlocked(
    hass: HomeAssistant,
    system: FoyerSystem,
    device: ArmingDevice,
    *,
    extend: bool = True,
) -> Unlock | None:
    """The device's unlock, if one is running and still stands.

    Checked again on every use, not only when it was opened (review): a
    person disabled, deleted or past their validity window reads nothing
    more, and neither does a device disabled or given a new token since.
    ``extend`` counts the use (decision 118: from its last use); the stream
    only looks, so being connected keeps nothing alive.
    """
    unlocks = hass.data.get(_UNLOCKS, {})
    unlock = unlocks.get(device.id)
    if unlock is None:
        return None
    now = dt_util.utcnow()
    user = system.config.user(unlock.user_id)
    if (
        unlock.until <= now
        or not device.enabled
        or unlock.token_hash != device.token_hash
        or user is None
        or not user.enabled
        or not user.in_window(now)
    ):
        unlocks.pop(device.id, None)
        return None
    if extend:
        unlock.until = now + timedelta(seconds=device.unlock_seconds)
    return unlock


def lock(hass: HomeAssistant, device_id: str) -> None:
    hass.data.get(_UNLOCKS, {}).pop(device_id, None)


async def async_unlock(
    hass: HomeAssistant,
    system: FoyerSystem,
    device: ArmingDevice,
    actor: Actor,
) -> tuple[Reason | None, datetime | None]:
    """A code offered to read. Counted like any other code (§8.4)."""
    if actor.code is CodeResult.NONE:
        return Reason.CODE_REQUIRED, None
    attempt = await system.async_handle(CodeAttempt(None, actor=actor))
    if attempt.reason is not None:
        return attempt.reason, None
    now = dt_util.utcnow()
    user = system.config.user(actor.user_id)
    if user is None or not user.enabled or not user.in_window(now):
        return Reason.USER_NOT_VALID, None
    until = now + timedelta(seconds=device.unlock_seconds)
    hass.data.setdefault(_UNLOCKS, {})[device.id] = Unlock(
        user.id, until, device.token_hash
    )
    # A display that shows the house after a code is a place where somebody
    # read it: which device, whose code, until when — and, like every row a
    # right token causes from a locked-out address, that address (decision
    # 135). Written here rather than by the engine, so noted here too.
    system.async_record(
        (
            security_row(
                now,
                event_type="device_unlocked",
                channel=device.channel,
                device_id=device.id,
                user_id=user.id,
                user_name=user.name,
                outcome="ok",
                detail={
                    "device": device.name,
                    "seconds": str(device.unlock_seconds),
                    **address_note(actor.locked_address),
                },
            ),
        )
    )
    return None, until


# --- what may be read (decisions 117, 119) --------------------------------------


def read_refusal(
    hass: HomeAssistant,
    system: FoyerSystem,
    device: ArmingDevice,
    scope: str,
    secure: bool,
    *,
    extend: bool = True,
) -> Reason | None:
    """Why this device may not read this scope now, or None.

    After a code, the unlock reads only what the code's owner may read
    (decision 118): the log is theirs to read with `view_log` or not at all.
    """
    if not device.may(scope):
        return Reason.SCOPE_NOT_GRANTED
    if scope != DeviceScope.STATUS and not secure and not device.clear_text_confirmed:
        return Reason.PLAIN_HTTP_NOT_CONFIRMED
    if scope in device.free_scopes:
        return None
    unlock = unlocked(hass, system, device, extend=extend)
    if unlock is None:
        return Reason.UNLOCK_REQUIRED
    if scope == DeviceScope.LOG:
        person = system.config.user(unlock.user_id)
        if person is None or not person.may(Permission.VIEW_LOG):
            return Reason.NOT_PERMITTED
    return None


def reader(hass: HomeAssistant, system: FoyerSystem, device: ArmingDevice) -> Any:
    """The person whose code unlocked the device, if any, for what they may read."""
    unlock = unlocked(hass, system, device, extend=False)
    return system.config.user(unlock.user_id) if unlock else None


def area_scope(person: Any) -> frozenset[str] | None:
    """The areas a reading is limited to: the unlocking person's (§8.3)."""
    if person is None or person.allowed_area_ids is None:
        return None
    return frozenset(person.allowed_area_ids)


# --- the sections (decision 120) ------------------------------------------------


def _zones(system: FoyerSystem, areas: frozenset[str] | None) -> list[dict[str, Any]]:
    return [
        z for z in system.status()["zones"] if areas is None or z["area_id"] in areas
    ]


def zones_section(
    system: FoyerSystem, areas: frozenset[str] | None = None
) -> dict[str, Any]:
    return {
        "zones": [
            {
                "id": z["id"],
                "name": z["name"],
                "area_id": z["area_id"],
                "type": z["type"],
                "enabled": z["enabled"],
                "open": z["open"],
                "fault": z["fault"],
                "excluded": z["bypassed"] is not None,
            }
            for z in _zones(system, areas)
        ]
    }


def batteries_section(
    system: FoyerSystem, areas: frozenset[str] | None = None
) -> dict[str, Any]:
    return {
        "zones": [
            {
                "id": z["id"],
                "name": z["name"],
                "battery": z["battery"],
                "low": bool(z["low_battery"]),
                # A tamper switch is a zone of its own (§4.2): open is tampered.
                "tamper": z["open"] if z["type"] == ZoneType.TAMPER.value else None,
            }
            for z in _zones(system, areas)
            if z["battery"] is not None
            or z["low_battery"]
            or z["type"] == ZoneType.TAMPER.value
        ]
    }


def health_section(
    system: FoyerSystem, areas: frozenset[str] | None = None
) -> dict[str, Any]:
    """System health as a device may read it: how each part is doing, and
    nobody's name, phone or service (review). The page keeps the rest. The
    zones it names are only those of the reader's areas."""
    health = system.health_status()
    zone_areas = {z.id: z.area_id for z in system.config.zones}
    mains = health.get("mains") or {}
    watchdog = health.get("watchdog") or {}
    return {
        "causes": list(health.get("causes", [])),
        "mains": {"lost": mains.get("lost"), "since": mains.get("since")},
        "watchdog": {
            "enabled": watchdog.get("enabled"),
            "failures": watchdog.get("failures"),
            "down_since": watchdog.get("down_since"),
            "last_ok": watchdog.get("last_ok"),
            "ever_ok": watchdog.get("ever_ok"),
        },
        "channels": [
            {
                "kind": channel.get("kind"),
                "fault": channel.get("fault"),
                "since": channel.get("since"),
                "failures": channel.get("failures"),
                "last_ok": channel.get("last_ok"),
                "checked": channel.get("checked"),
            }
            for channel in health.get("channels", [])
        ],
        "radios": [
            {
                "name": radio.get("name"),
                "enabled": radio.get("enabled"),
                "zones": radio.get("zones"),
                "quiet": radio.get("quiet"),
                "suspected_since": radio.get("suspected_since"),
                "confirmed": radio.get("confirmed"),
                "coordinator_down_since": radio.get("coordinator_down_since"),
            }
            for radio in health.get("radios", [])
        ],
        "unreachable_zones": [
            {
                "id": zone.get("id"),
                "name": zone.get("name"),
                "since": zone.get("since"),
                "days": zone.get("days"),
            }
            for zone in health.get("unreachable_zones", [])
            if areas is None or zone_areas.get(zone.get("id") or "") in areas
        ],
    }


async def async_log_section(
    system: FoyerSystem,
    config: FoyerConfig,
    person: Any,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    """The log, newest first, paged by an opaque cursor.

    The same rows the log page shows (§10), after the sweeps of §10.4. A
    person's name appears only when the code that unlocked the device is
    somebody's who may read the log (decision 118); a free log scope shows
    what happened and never who.
    """
    if system.log is None:
        return {"rows": [], "next": None}
    offset = _offset(cursor)
    limit = max(1, min(limit, MAX_LOG_ROWS))
    # What the stream announced is written before it is read (review).
    await system.log.async_flush()
    answer = await system.log.async_query(limit=limit, offset=offset)
    names = person is not None and person.may(Permission.VIEW_LOG)
    scope = area_scope(person)
    areas = {a.id: a.name for a in config.areas}
    zones = {z.id: z.name for z in config.zones}
    zone_areas = {z.id: z.area_id for z in config.zones}
    rows = [
        {
            "ts": row["ts"],
            "category": row["category"],
            "event_type": row["event_type"],
            "severity": row["severity"],
            "outcome": row.get("outcome"),
            "area": areas.get(row.get("area_id") or "", row.get("area_id")),
            "zone": zones.get(row.get("zone_id") or "", row.get("zone_id")),
            **({"person": row.get("user_name")} if names else {}),
        }
        for row in answer["rows"]
        # Rows about an area the unlocking person may not reach are theirs
        # neither to read; rows about no area (the system's) are.
        if _row_visible(row, scope, zone_areas)
    ]
    more = offset + len(answer["rows"]) < int(answer["total"])
    following = offset + len(answer["rows"])
    return {"rows": rows, "next": f"o{following}" if more else None}


def _row_visible(
    row: Any, scope: frozenset[str] | None, zone_areas: dict[str, str]
) -> bool:
    """Whether a row is about an area the reader may reach.

    A row that names a zone and no area (a refused exclusion, say) is about
    the zone's area (review); one about neither is the system's, and shown.
    """
    if scope is None:
        return True
    area = _get(row, "area_id") or zone_areas.get(_get(row, "zone_id") or "")
    return area is None or area in scope


def _get(row: Any, key: str) -> Any:
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def _offset(cursor: str | None) -> int:
    if not cursor or not cursor.startswith("o"):
        return 0
    try:
        # Bounded: an offset past what SQLite holds raises rather than
        # answering nothing (review).
        return min(max(0, int(cursor[1:])), 10**9)
    except ValueError:
        return 0


def fingerprints(
    hass: HomeAssistant, system: FoyerSystem, device: ArmingDevice, secure: bool
) -> dict[str, str]:
    """What each section the device may read now looks like, for the stream
    to say which one changed (decision 120).

    Only a section the device could read at this moment is announced: a
    notice that the zones moved is itself news about the house, and one sent
    before the code, or in the clear without the owner's confirmation, would
    tell it to anybody on the network (review). Looking does not extend the
    unlock.
    """

    def may(scope: str) -> bool:
        return read_refusal(hass, system, device, scope, secure, extend=False) is None

    person = reader(hass, system, device)
    areas = area_scope(person)
    out: dict[str, str] = {}
    if may(DeviceScope.ZONES):
        out["zones"] = json.dumps(zones_section(system, areas), sort_keys=True)
    if may(DeviceScope.BATTERIES):
        out["batteries"] = json.dumps(batteries_section(system, areas), sort_keys=True)
    if may(DeviceScope.HEALTH):
        out["health"] = json.dumps(
            health_section(system, areas), sort_keys=True, default=str
        )
    if may(DeviceScope.LOG):
        # The last row this reader could see: a row about an area it may not
        # reach must not announce itself either (review).
        seen = hass.data.setdefault(_LOG_SEEN, {})
        row = system.last_row
        zone_areas = {z.id: z.area_id for z in system.config.zones}
        if row is not None and _row_visible(row, areas, zone_areas):
            seen[device.id] = f"{row.ts.isoformat()}:{row.event_type}"
        out["log"] = seen.get(device.id, "")
    return out


# --- what may be done (decisions 115, 116) --------------------------------------


def command(
    config: FoyerConfig,
    device: ArmingDevice,
    data: dict[str, Any],
    actor: Actor,
    state: RuntimeState | None = None,
) -> tuple[Any | None, Reason | None]:
    """The engine event an action asks for, or why it is refused before it.

    The scope comes first, then the code — every action needs one (decision
    116) — then where the device's own restrictions let it reach. What the
    code's owner may do is the engine's to decide, as for every other path.
    """
    action = str(data.get("action") or "")
    scope = ACTION_SCOPES.get(action)
    if scope is None or scope == DeviceScope.STATUS:
        return None, Reason.UNKNOWN_ACTION
    if not device.may(scope):
        return None, Reason.SCOPE_NOT_GRANTED
    if actor.code is CodeResult.NONE:
        return None, Reason.CODE_REQUIRED
    if action == "arm":
        return _arm(config, device, data, actor, state)
    if action == "disarm":
        return _disarm(config, device, data, actor)
    if action in ("exclude", "include"):
        zone = _find(config.zones, data.get("zone"))
        if zone is None:
            return None, Reason.UNKNOWN_ZONE
        return BypassZone(zone.id, bypass=action == "exclude", actor=actor), None
    if str(data.get("target") or "incident") == "technical":
        return AcknowledgeTechnical(actor), None
    return AcknowledgeIncident(actor), None


def _find(items: Any, ref: Any) -> Any:
    """By id or by name: a device's firmware holds whichever it was given."""
    if not isinstance(ref, str) or not ref:
        return None
    return next((i for i in items if ref in (i.id, i.name)), None)


def _drops(
    config: FoyerConfig,
    device: ArmingDevice,
    scenario: Any,
    state: RuntimeState | None,
) -> Reason | None:
    """Arming a scenario while another is armed disarms the areas the new one
    leaves out (§4.6). That is a disarm, and needs what a disarm needs from
    this device: its `disarm` scope, within its areas (review)."""
    if state is None:
        return None
    current = state.active_scenario_id
    if current is None or current == scenario.id:
        return None
    # Exactly what the engine drops (§4.6): the areas the current scenario
    # armed. An area armed on its own is left as it is, and needs nothing.
    dropped = [
        area_id
        for area_id, rt in state.areas.items()
        if rt.state is not AreaState.DISARMED
        and rt.scenario_id == current
        and area_id not in scenario.areas
    ]
    if not dropped:
        return None
    if not device.may(DeviceScope.DISARM):
        return Reason.SCOPE_NOT_GRANTED
    allowed = device.disarm_area_ids
    if allowed is not None and any(a not in allowed for a in dropped):
        return Reason.SCOPE_NOT_GRANTED
    return None


def _arm(
    config: FoyerConfig,
    device: ArmingDevice,
    data: dict[str, Any],
    actor: Actor,
    state: RuntimeState | None,
) -> tuple[Any | None, Reason | None]:
    force = bool(data.get("force", False))
    skip = bool(data.get("skip_exit_delay", False))
    if data.get("area") is not None:
        area = _find(config.areas, data.get("area"))
        if area is None:
            return None, Reason.UNKNOWN_AREA
        if device.arm_area_ids is not None and area.id not in device.arm_area_ids:
            return None, Reason.SCOPE_NOT_GRANTED
        return ArmAreaRequest(area.id, actor, force, skip), None
    scenario = _find(config.scenarios, data.get("scenario"))
    if scenario is None:
        mode = data.get("scenario")
        if isinstance(mode, str) and mode in {
            s.ha_master_state for s in config.scenarios
        }:
            # A Home Assistant mode, as the broker accepts one (§9.2). Only
            # when the device may arm every scenario: a mode names none.
            if device.arm_scenario_ids is not None:
                return None, Reason.SCOPE_NOT_GRANTED
            for moded in (s for s in config.scenarios if s.ha_master_state == mode):
                if (reason := _drops(config, device, moded, state)) is not None:
                    return None, reason
            return ArmModeRequest(mode, actor, force, skip), None
        return None, Reason.UNKNOWN_SCENARIO
    if (
        device.arm_scenario_ids is not None
        and scenario.id not in device.arm_scenario_ids
    ):
        return None, Reason.SCOPE_NOT_GRANTED
    if (reason := _drops(config, device, scenario, state)) is not None:
        return None, reason
    return ArmRequest(scenario.id, actor, force, skip), None


def _disarm(
    config: FoyerConfig, device: ArmingDevice, data: dict[str, Any], actor: Actor
) -> tuple[Any | None, Reason | None]:
    refs = data.get("areas", data.get("area_ids"))
    if refs is None:
        # Everything this device may disarm: the whole house, or its own list.
        allowed = device.disarm_area_ids
        return DisarmRequest(
            tuple(allowed) if allowed is not None else None, actor
        ), None
    if not isinstance(refs, list) or not refs:
        return None, Reason.UNKNOWN_AREA
    areas = [_find(config.areas, ref) for ref in refs]
    if any(a is None for a in areas):
        return None, Reason.UNKNOWN_AREA
    ids = tuple(a.id for a in areas)
    allowed = device.disarm_area_ids
    if allowed is not None and any(i not in allowed for i in ids):
        return None, Reason.SCOPE_NOT_GRANTED
    return DisarmRequest(ids, actor), None


def reads(device: ArmingDevice) -> list[str]:
    """The read scopes this device holds, for the page and the document."""
    return sorted(s for s in device.scopes if s in READ_SCOPES)
