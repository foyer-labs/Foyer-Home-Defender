"""WebSocket commands under ``foyer/*`` used by the panel and the card.

Every command that changes state goes through the engine, and every command
that changes configuration is validated here, server-side, before anything is
stored (INV-2). The panel's own checks are a courtesy.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .. import i18n
from ..const import CHANNEL_HA_UI, DOMAIN, SIGNAL_UPDATE
from ..core.journal import config_row
from ..core.models import (
    ARMED_HA_STATES,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_RETENTION_DAYS,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_RETENTION_DAYS,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    SILENCEABLE,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    ActionKind,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    Decision,
    DisarmRequest,
    LogCategory,
    LogSeverity,
    Moment,
    Outcome,
    ZoneType,
)
from ..core.presets import UNAVAILABLE_TYPES, preset
from ..core.proposals import propose_zone
from ..core.templates import TEMPLATE_VARIABLES
from ..core.validation import (
    ACTION_DOMAINS,
    CHIME_DOMAINS,
    MAX_ACTION_DELAY,
    MAX_SEVERITY,
    ZONE_DOMAINS,
    Problem,
    edit_conflicts,
    validate,
)
from ..runtime.system import FoyerSystem
from ..store.config_store import ConfigStore
from ..store.editing import (
    KINDS,
    EditResult,
    config_diff,
    delete,
    update_chime,
    update_settings,
    upsert,
)
from ..store.log_store import export_csv, export_json
from ..store.migrations import MigrationError, migrate
from ..store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    ConfigError,
    config_from_dict,
    config_to_dict,
)

PREFS_KEY = "foyer.prefs"

# Moments a profile can already be written against, though the phase that
# raises them has not landed (SPEC §6.1; part 3 appendix).
FUTURE_MOMENTS: tuple[Moment, ...] = (
    Moment.CODE_REJECTED,
    Moment.LOCKOUT,
    Moment.LOW_BATTERY,
    Moment.WALK_TEST_STARTED,
    Moment.WALK_TEST_ENDED,
    Moment.ESCALATION_EXHAUSTED,
)


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (
        ws_status,
        ws_subscribe,
        ws_translations,
        ws_config,
        ws_config_save,
        ws_config_delete,
        ws_settings_save,
        ws_chime_save,
        ws_propose_zone,
        ws_arm,
        ws_disarm,
        ws_acknowledge,
        ws_bypass,
        ws_prefs_get,
        ws_prefs_set,
        ws_log_query,
        ws_log_export,
        ws_log_clear,
        ws_config_export,
        ws_config_import,
    ):
        websocket_api.async_register_command(hass, command)


def _system(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg_id: int
) -> FoyerSystem | None:
    system = hass.data.get(DOMAIN)
    if system is None:
        connection.send_error(msg_id, "not_loaded", "Foyer is not loaded")
    return system


# --- live state ------------------------------------------------------------------


@websocket_api.websocket_command({vol.Required("type"): "foyer/status"})
@callback
def ws_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is not None:
        connection.send_result(msg["id"], system.status())


@websocket_api.websocket_command({vol.Required("type"): "foyer/subscribe"})
@callback
def ws_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Push the full status now and again after every change.

    Bound to a signal rather than to one FoyerSystem: a configuration change
    reloads the entry and replaces the system, and the panel that made the
    change must keep receiving updates without resubscribing.
    """
    if _system(hass, connection, msg["id"]) is None:
        return

    @callback
    def forward() -> None:
        if (system := hass.data.get(DOMAIN)) is not None:
            connection.send_message(
                websocket_api.event_message(msg["id"], system.status())
            )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_UPDATE, forward
    )
    connection.send_result(msg["id"])
    forward()


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/translations",
        vol.Optional("language"): str,
    }
)
@websocket_api.async_response
async def ws_translations(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    language = i18n.resolve_language(msg.get("language") or hass.config.language)
    strings = await hass.async_add_executor_job(i18n.load_strings, language)
    connection.send_result(msg["id"], {"language": language, "strings": strings})


# --- arming from the panel and the card -----------------------------------------------


def _result(system: FoyerSystem, decision: Decision) -> dict[str, Any]:
    """The structured result of SPEC §9.1, so the UI can name the zone."""
    names = {z.id: z.name for z in system.config.zones}
    return {
        "success": decision.accepted,
        "reason": decision.reason.value if decision.reason else None,
        "blocking_zones": [
            {"id": z, "name": names.get(z, z)} for z in decision.blocking_zones
        ],
        "bypassed_zones": [
            {"id": z, "name": names.get(z, z)} for z in decision.bypassed_zones
        ],
        "state": system.status(),
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/arm",
        vol.Exclusive("scenario_id", "target"): str,
        vol.Exclusive("area_id", "target"): str,
        vol.Exclusive("mode", "target"): vol.In(ARMED_HA_STATES),
        vol.Optional("force", default=False): bool,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_arm(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm a scenario, one area, or a master mode. The engine decides (INV-2)."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    code, force = msg.get("code"), msg["force"]
    if "scenario_id" in msg:
        event: Any = ArmRequest(msg["scenario_id"], code, CHANNEL_HA_UI, force)
    elif "area_id" in msg:
        event = ArmAreaRequest(msg["area_id"], code, CHANNEL_HA_UI, force)
    elif "mode" in msg:
        event = ArmModeRequest(msg["mode"], code, CHANNEL_HA_UI, force)
    else:
        connection.send_error(msg["id"], "invalid_format", "no target")
        return
    decision = await system.async_handle(event)
    connection.send_result(msg["id"], _result(system, decision))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/disarm",
        vol.Optional("area_ids"): [str],
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_disarm(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    area_ids = msg.get("area_ids")
    decision = await system.async_handle(
        DisarmRequest(
            tuple(area_ids) if area_ids else None, msg.get("code"), CHANNEL_HA_UI
        )
    )
    connection.send_result(msg["id"], _result(system, decision))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/acknowledge",
        # Two channels, two acknowledgements (§5.5): the caller says which.
        vol.Required("target"): vol.In(["incident", "technical"]),
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_acknowledge(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Acknowledge the incident or the technical alarm. The engine checks the
    code policy (INV-2): no code is needed before Phase 2, and the check runs
    already so that Phase 2 changes the policy, not this command."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    event: Any = (
        AcknowledgeIncident(msg.get("code"), CHANNEL_HA_UI)
        if msg["target"] == "incident"
        else AcknowledgeTechnical(msg.get("code"), CHANNEL_HA_UI)
    )
    decision = await system.async_handle(event)
    connection.send_result(msg["id"], _result(system, decision))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/bypass",
        vol.Required("zone_id"): str,
        vol.Optional("bypass", default=True): bool,
        # A timed temporary bypass: the zone rejoins on its own (SPEC §16).
        vol.Optional("seconds"): vol.Any(vol.All(int, vol.Range(min=1)), None),
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_bypass(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Exclude a zone by hand, or let it back in. The engine checks the code
    policy (INV-2): no code is needed before Phase 2, and the check runs
    already so that Phase 2 changes the policy, not this command."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    decision = await system.async_handle(
        BypassZone(
            zone_id=msg["zone_id"],
            bypass=msg["bypass"],
            seconds=msg.get("seconds"),
            code=msg.get("code"),
            channel=CHANNEL_HA_UI,
        )
    )
    connection.send_result(msg["id"], _result(system, decision))


# --- configuration (admin only) -------------------------------------------------------


def _meta() -> dict[str, Any]:
    """What the configuration pages need to know that is not configuration."""
    return {
        "zone_types": [
            {
                "type": t.value,
                "available": t not in UNAVAILABLE_TYPES,
                "preset": preset(t),
            }
            for t in ZoneType
        ],
        "zone_domains": list(ZONE_DOMAINS),
        "chime_domains": list(CHIME_DOMAINS),
        "ha_states": list(ARMED_HA_STATES),
        "bounds": {
            "exit_delay": [0, MAX_EXIT_DELAY],
            "entry_delay": [0, MAX_ENTRY_DELAY],
            "siren_duration": [1, MAX_SIREN_DURATION],
            "arm_hold_timeout": [MIN_ARM_HOLD_TIMEOUT, MAX_ARM_HOLD_TIMEOUT],
            "supervision_timeout": [MIN_SUPERVISION_TIMEOUT, MAX_SUPERVISION_TIMEOUT],
            "window": [MIN_VERIFICATION_WINDOW, MAX_VERIFICATION_WINDOW],
            "trigger_count": [1, MAX_TRIGGER_COUNT],
            "volume": [0, 100],
            "severity": [1, MAX_SEVERITY],
            "delay": [1, MAX_ACTION_DELAY],
        },
        # What page 5 needs to build an action editor without knowing the
        # engine: the catalogue, where each kind may point, and the moments.
        "action_kinds": [k.value for k in ActionKind],
        "action_domains": {k: list(v) for k, v in ACTION_DOMAINS.items()},
        "silenceable": sorted(SILENCEABLE),
        "moments": [m.value for m in Moment],
        # Moments no phase raises yet: selectable, and labelled as such.
        "future_moments": [m.value for m in FUTURE_MOMENTS],
        "template_variables": list(TEMPLATE_VARIABLES),
        "max_conditions": MAX_CONDITIONS,
        # What pages 10 and 11 need to build the filters and the retention
        # block without knowing the engine.
        "log_categories": [c.value for c in LogCategory],
        "log_severities": [s.value for s in LogSeverity],
        "outcomes": [o.value for o in Outcome],
        "retention_bounds": [MIN_RETENTION_DAYS, MAX_RETENTION_DAYS],
        "schema_version": [STORAGE_VERSION, STORAGE_MINOR_VERSION],
    }


@websocket_api.websocket_command({vol.Required("type"): "foyer/config"})
@websocket_api.require_admin
@callback
def ws_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is not None:
        connection.send_result(
            msg["id"], {"config": config_to_dict(system.config), "meta": _meta()}
        )


async def _apply(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg_id: int,
    system: FoyerSystem,
    result: EditResult,
    *,
    operation: str = "save",
    kind: str = "config",
) -> None:
    """Store a validated edit and reload, or return its problems untouched."""
    if result.config is None:
        connection.send_result(
            msg_id,
            {"success": False, "problems": [asdict(p) for p in result.problems]},
        )
        return
    # Who changed what, with a summary of what moved (§10.2, category
    # ``config``). Recorded before the reload, which replaces this system.
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation=operation,
                kind=kind,
                item_id=result.id,
                user_id=connection.user.id,
                user_name=connection.user.name,
                channel=CHANNEL_HA_UI,
                changes=config_diff(system.config, result.config),
            ),
        )
    )
    await ConfigStore(hass).async_save(result.config)
    # The entities follow the configuration: reload to rebuild them. The alarm
    # state is saved on unload and restored on setup (INV-3).
    entry = next(iter(hass.config_entries.async_entries(DOMAIN)), None)
    if entry is not None:
        hass.config_entries.async_schedule_reload(entry.entry_id)
    connection.send_result(msg_id, {"success": True, "id": result.id, "problems": []})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/save",
        vol.Required("kind"): vol.In(list(KINDS)),
        vol.Required("item"): dict,
        vol.Optional("trigger_confirmed", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_config_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    result = upsert(
        system.config,
        system.state,
        msg["kind"],
        msg["item"],
        trigger_confirmed=msg["trigger_confirmed"],
    )
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind=msg["kind"]
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/delete",
        vol.Required("kind"): vol.In(list(KINDS)),
        # Not "id": that is the WebSocket message id, and a clash makes Home
        # Assistant drop the command as invalid.
        vol.Required("item_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_config_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    result = delete(system.config, system.state, msg["kind"], msg["item_id"])
    await _apply(
        hass,
        connection,
        msg["id"],
        system,
        result,
        operation="delete",
        kind=msg["kind"],
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/settings",
        vol.Required("settings"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_settings_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    result = update_settings(system.config, system.state, msg["settings"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="settings"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/chime",
        vol.Required("chime"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_chime_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The global chime block (§6.6), validated like every configuration edit."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    result = update_chime(system.config, system.state, msg["chime"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="chime"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/zone/propose",
        vol.Required("entity_id"): str,
    }
)
@websocket_api.require_admin
@callback
def ws_propose_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The zone wizard's starting point (§4.4). The user must still confirm it."""
    state = hass.states.get(msg["entity_id"])
    attributes = dict(state.attributes) if state else {}
    proposal = propose_zone(
        msg["entity_id"], state.state if state else None, attributes
    )
    connection.send_result(
        msg["id"],
        {
            "entity_id": msg["entity_id"],
            "name": state.name if state else msg["entity_id"],
            "state": state.state if state else None,
            "device_class": attributes.get("device_class"),
            "trigger_kind": proposal.trigger_kind,
            "options": list(proposal.options),
            "proposed": list(proposal.proposed),
            "zone_type": proposal.zone_type.value if proposal.zone_type else None,
        },
    )


# --- per-user panel preferences (§15.2) -----------------------------------------------


def _prefs_store(hass: HomeAssistant) -> Store[dict[str, Any]]:
    key = f"{DOMAIN}_prefs_store"
    if key not in hass.data:
        hass.data[key] = Store(hass, 1, PREFS_KEY)
    return hass.data[key]


@websocket_api.websocket_command({vol.Required("type"): "foyer/prefs"})
@websocket_api.async_response
async def ws_prefs_get(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The help panels' state follows the Home Assistant user, not the browser."""
    data = await _prefs_store(hass).async_load() or {}
    connection.send_result(msg["id"], data.get(connection.user.id, {}))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/prefs/set",
        vol.Required("prefs"): {
            vol.Optional("help"): {str: bool},
            vol.Optional("help_hidden"): bool,
        },
    }
)
@websocket_api.async_response
async def ws_prefs_set(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    store = _prefs_store(hass)
    data = await store.async_load() or {}
    mine = data.get(connection.user.id, {})
    if "help" in msg["prefs"]:
        mine["help"] = {**mine.get("help", {}), **msg["prefs"]["help"]}
    if "help_hidden" in msg["prefs"]:
        mine["help_hidden"] = msg["prefs"]["help_hidden"]
    data[connection.user.id] = mine
    await store.async_save(data)
    connection.send_result(msg["id"], mine)


# --- the event log (SPEC §10) ------------------------------------------------------

# One export carries what a person can reasonably read, not the whole
# database: an export is a filtered view (§10.3), and a year of zone activity
# belongs in the file on disk rather than in one WebSocket message.
MAX_EXPORT_ROWS = 10000

_LOG_FILTERS = {
    vol.Optional("start"): vol.Any(str, None),
    vol.Optional("end"): vol.Any(str, None),
    vol.Optional("categories"): [str],
    vol.Optional("severity"): vol.Any(str, None),
    vol.Optional("area_id"): vol.Any(str, None),
    vol.Optional("zone_id"): vol.Any(str, None),
    vol.Optional("user_id"): vol.Any(str, None),
    vol.Optional("incident_id"): vol.Any(str, None),
    vol.Optional("outcome"): vol.Any(str, None),
}


def _filters(msg: dict[str, Any]) -> dict[str, Any]:
    """The filters the panel sent, parsed. A date that cannot be read is
    dropped rather than guessed at: a wrong window hides rows silently."""
    out: dict[str, Any] = {}
    for key in ("start", "end"):
        if value := msg.get(key):
            parsed = dt_util.parse_datetime(value)
            if parsed is not None:
                out[key] = dt_util.as_utc(parsed)
    for key in (
        "categories",
        "severity",
        "area_id",
        "zone_id",
        "user_id",
        "incident_id",
        "outcome",
    ):
        if msg.get(key):
            out[key] = msg[key]
    return out


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/log/query",
        vol.Optional("limit", default=200): vol.All(int, vol.Range(min=1, max=1000)),
        vol.Optional("offset", default=0): vol.All(int, vol.Range(min=0)),
        **_LOG_FILTERS,
    }
)
@websocket_api.async_response
async def ws_log_query(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 10, and the recent events on page 1."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    await system.log.async_flush()
    result = await system.log.async_query(
        limit=msg["limit"], offset=msg["offset"], **_filters(msg)
    )
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/log/export",
        vol.Required("format"): vol.In(["csv", "json"]),
        **_LOG_FILTERS,
    }
)
@websocket_api.async_response
async def ws_log_export(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Exactly the rows the current filters show, as CSV or JSON (§10.3)."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    await system.log.async_flush()
    result = await system.log.async_query(limit=MAX_EXPORT_ROWS, **_filters(msg))
    rows = result["rows"]
    content = export_csv(rows) if msg["format"] == "csv" else export_json(rows)
    stamp = dt_util.now().strftime("%Y%m%d-%H%M")
    fmt = msg["format"]
    connection.send_result(
        msg["id"],
        {
            "filename": f"foyer-log-{stamp}.{fmt}",
            "content": content,
            "rows": len(rows),
            # What the filters match in total, so the panel can say plainly
            # that an export was cut short rather than look complete.
            "total": result["total"],
            "truncated": result["total"] > len(rows),
        },
    )


@websocket_api.websocket_command({vol.Required("type"): "foyer/log/clear"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_log_clear(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Empty the log. An edit_config operation, and itself logged (§10.3).

    docs/security-model.md says plainly that an administrator with filesystem
    access can delete the database outright, so this row makes the log
    audit-useful, not tamper-proof.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    await system.log.async_flush()
    removed = await system.log.async_clear()
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="log_cleared",
                kind="log",
                user_id=connection.user.id,
                user_name=connection.user.name,
                channel=CHANNEL_HA_UI,
                changes={"removed": removed},
            ),
        )
    )
    connection.send_result(msg["id"], {"success": True, "removed": removed})


# --- configuration backup and restore (SPEC §15.1) ---------------------------------

# What an export is, so an import can tell a Foyer backup from any other JSON
# file dropped on it.
BACKUP_MAGIC = "foyer.config"


@websocket_api.websocket_command({vol.Required("type"): "foyer/config/export"})
@websocket_api.require_admin
@callback
def ws_config_export(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The stored document with its schema version (§15.1).

    Nobody who has configured forty zones will do it twice. The version
    travels with the document because an import must migrate it, not guess at
    it — and must refuse one written by a newer major version.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    stamp = dt_util.now().strftime("%Y%m%d-%H%M")
    document = {
        "foyer": BACKUP_MAGIC,
        "version": [STORAGE_VERSION, STORAGE_MINOR_VERSION],
        "created": dt_util.now().isoformat(),
        "config": config_to_dict(system.config),
    }
    connection.send_result(
        msg["id"],
        {"filename": f"foyer-config-{stamp}.json", "document": document},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/import",
        vol.Required("document"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_config_import(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Restore a backup: migrate, validate, then check what is armed.

    Never around those three. A document written by an older version is
    brought up to date by the same steps a real upgrade uses; one written by a
    newer major version is refused, because silently dropping fields it does
    not understand could drop an alarm setting; and a restore that would
    change an armed area is refused like any other edit.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    document = msg["document"]
    if document.get("foyer") != BACKUP_MAGIC or "config" not in document:
        connection.send_result(
            msg["id"],
            {
                "success": False,
                "problems": [asdict(Problem("not_a_foyer_backup", "config"))],
            },
        )
        return
    version = document.get("version") or [STORAGE_VERSION, STORAGE_MINOR_VERSION]
    try:
        data = migrate(
            (int(version[0]), int(version[1])),
            (STORAGE_VERSION, STORAGE_MINOR_VERSION),
            document["config"],
        )
        config = config_from_dict(data)
    except MigrationError:
        connection.send_result(
            msg["id"],
            {
                "success": False,
                "problems": [asdict(Problem("backup_version_unsupported", "config"))],
            },
        )
        return
    except (ConfigError, KeyError, TypeError, ValueError, IndexError):
        connection.send_result(
            msg["id"],
            {"success": False, "problems": [asdict(Problem("invalid", "config"))]},
        )
        return

    problems = validate(config) + edit_conflicts(system.config, config, system.state)
    result = EditResult(
        config=None if problems else config, problems=tuple(problems), id=None
    )
    await _apply(
        hass, connection, msg["id"], system, result, operation="restore", kind="config"
    )
