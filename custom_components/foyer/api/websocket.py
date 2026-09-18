"""WebSocket commands under ``foyer/*`` used by the panel and the card.

Every command that changes state goes through the engine, and every command
that changes configuration is validated here, server-side, before anything is
stored (INV-2). The panel's own checks are a courtesy.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import partial
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .. import i18n
from ..const import CHANNEL_HA_UI, DOMAIN, SIGNAL_UPDATE
from ..core import authz
from ..core.journal import config_row
from ..core.models import (
    ARMED_HA_STATES,
    IDENTIFYING_CHANNELS,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_CODE_LENGTH,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_LOCKOUT_FAILURES,
    MAX_LOCKOUT_SECONDS,
    MAX_RETENTION_DAYS,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_CODE_LENGTH,
    MIN_LOCKOUT_FAILURES,
    MIN_LOCKOUT_SECONDS,
    MIN_RETENTION_DAYS,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    SILENCEABLE,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    ActionKind,
    Actor,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    CodeResult,
    Decision,
    DisarmRequest,
    LogCategory,
    LogSeverity,
    Moment,
    Operation,
    Outcome,
    Permission,
    Reason,
    User,
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
from ..security import codes
from ..security.identity import async_actor
from ..store.config_store import ConfigStore
from ..store.editing import (
    KINDS,
    EditResult,
    config_diff,
    delete,
    update_chime,
    update_security,
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


# Commands the panel sends that change nothing and reveal nothing: reading the
# live state is open to any signed-in Home Assistant user, as the entities are.


async def _actor(
    hass: HomeAssistant,
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> Actor:
    """Who is asking over this connection, with whatever code came with it."""
    return await async_actor(
        hass,
        system.config,
        ha_user_id=connection.user.id,
        code=msg.get("code"),
        channel=CHANNEL_HA_UI,
        is_admin=connection.user.is_admin,
    )


def _may_configure(
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    actor: Actor,
    operation: Operation,
    permission: Permission,
    *,
    need_code: bool = True,
) -> Reason | None:
    """The gate in front of every configuration and log command (§8.3).

    Foyer knows this person, or it does not. If a Foyer user is linked to
    their Home Assistant account, Foyer's own rules apply in full: the
    permission, and the code the policy asks for. If none is, the rule is the
    one this integration has used since Phase 0 — a Home Assistant
    administrator, and nobody else.

    That second half is deliberate and belongs in the open: an administrator
    who is not a Foyer user configures without a code. INV-6 says as much
    already — an administrator can read .storage, call any service and
    disable the integration — and the alternative is an installation whose
    owner has locked themselves out of their own configuration.
    """
    user = system.config.user(actor.user_id)
    if actor.code is CodeResult.INVALID:
        return Reason.BAD_CODE
    if user is None:
        return None if connection.user.is_admin else Reason.NOT_PERMITTED
    if not user.enabled or not user.in_window(dt_util.utcnow()):
        return Reason.USER_NOT_VALID
    if not user.may(permission):
        return Reason.NOT_PERMITTED
    if (
        need_code
        and authz.code_required(
            system.config,
            operation,
            now=dt_util.utcnow(),
            user=user,
            identified=actor.identified,
            channel=actor.channel,
        )
        and not actor.code_verified
    ):
        return Reason.CODE_REQUIRED
    return None


async def _gate(
    hass: HomeAssistant,
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    operation: Operation,
    permission: Permission,
    *,
    need_code: bool = True,
) -> Actor | None:
    """Check, answer the caller on refusal, and record the refusal.

    ``need_code`` is False for the commands that only read: §8.2 asks for a
    code to *edit* the configuration, and a panel that demanded one to open a
    page would teach the household to keep the code on a sticky note.
    """
    actor = await _actor(hass, system, connection, msg)
    reason = _may_configure(
        system, connection, actor, operation, permission, need_code=need_code
    )
    if reason is None:
        return actor
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="refused",
                kind=operation.value,
                user_id=actor.user_id,
                user_name=(
                    named.name if (named := system.config.user(actor.user_id)) else None
                ),
                channel=CHANNEL_HA_UI,
                changes={"reason": reason.value},
            ),
        )
    )
    if need_code:
        # A refused write answers like any other refused edit, so the page
        # shows it where it shows every other problem — and, for a missing or
        # wrong code, so the panel knows to ask for one.
        connection.send_result(
            msg["id"],
            {
                "success": False,
                "reason": reason.value,
                "problems": [asdict(Problem(reason.value, "code", None, "code"))],
            },
        )
    else:
        # A refused read fails the request outright: there is no half-read
        # configuration to show, and a page that got an empty one would look
        # like an installation with nothing in it.
        connection.send_error(msg["id"], reason.value, reason.value)
    return None


def _public_config(config) -> dict[str, Any]:
    """The configuration as the panel may see it: no hashes, ever (§8.1).

    A hash never leaves the backend — not here, not in an export, not in a
    diagnostic. What the panel needs is whether a code exists, which is a
    boolean, and that is what it gets.
    """
    document = config_to_dict(config)
    document["users"] = [_public_user(u) for u in config.users]
    return document


def _public_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "has_code": bool(user.code_hash),
        "has_duress_code": bool(user.duress_code_hash),
        "ha_user_id": user.ha_user_id,
        "permissions": sorted(user.permissions),
        "allowed_area_ids": (
            None if user.allowed_area_ids is None else list(user.allowed_area_ids)
        ),
        "allowed_scenario_ids": (
            None
            if user.allowed_scenario_ids is None
            else list(user.allowed_scenario_ids)
        ),
        "valid_from": user.valid_from.isoformat() if user.valid_from else None,
        "valid_until": user.valid_until.isoformat() if user.valid_until else None,
        "code_exempt_when_identified": user.code_exempt_when_identified,
        "enabled": user.enabled,
    }


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
        ws_security_save,
        ws_user_save,
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
        connection.send_result(msg["id"], system.status(connection.user))


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
                websocket_api.event_message(msg["id"], system.status(connection.user))
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


def _result(
    system: FoyerSystem, decision: Decision, ha_user: Any = None
) -> dict[str, Any]:
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
        "state": system.status(ha_user),
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
    force = msg["force"]
    actor = await _actor(hass, system, connection, msg)
    if "scenario_id" in msg:
        event: Any = ArmRequest(msg["scenario_id"], actor, force)
    elif "area_id" in msg:
        event = ArmAreaRequest(msg["area_id"], actor, force)
    elif "mode" in msg:
        event = ArmModeRequest(msg["mode"], actor, force)
    else:
        connection.send_error(msg["id"], "invalid_format", "no target")
        return
    decision = await system.async_handle(event)
    connection.send_result(msg["id"], _result(system, decision, connection.user))


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
    actor = await _actor(hass, system, connection, msg)
    decision = await system.async_handle(
        DisarmRequest(tuple(area_ids) if area_ids else None, actor)
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


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
    """Acknowledge the incident or the technical alarm.

    No code by default (decision 77): §7.2 already acknowledges from a push
    notification that carries none. An installation that has raised the policy
    is refused here by the engine, like any other request (INV-2).
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    actor = await _actor(hass, system, connection, msg)
    event: Any = (
        AcknowledgeIncident(actor)
        if msg["target"] == "incident"
        else AcknowledgeTechnical(actor)
    )
    decision = await system.async_handle(event)
    connection.send_result(msg["id"], _result(system, decision, connection.user))


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
    """Exclude a zone by hand, or let it back in. The engine decides (INV-2)."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    decision = await system.async_handle(
        BypassZone(
            zone_id=msg["zone_id"],
            bypass=msg["bypass"],
            seconds=msg.get("seconds"),
            actor=await _actor(hass, system, connection, msg),
        )
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


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
            "code_length": [MIN_CODE_LENGTH, MAX_CODE_LENGTH],
            "lockout_failures": [MIN_LOCKOUT_FAILURES, MAX_LOCKOUT_FAILURES],
            "lockout_seconds": [MIN_LOCKOUT_SECONDS, MAX_LOCKOUT_SECONDS],
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
        # What page 7 needs to build the permission list and the policy table
        # without knowing §8.2 and §8.3 by heart.
        "permissions": [p.value for p in Permission],
        "operations": [o.value for o in Operation],
        # The operations no phase raises yet: the policy is complete, the
        # features are not, and the page says which is which.
        "future_operations": [Operation.WALK_TEST.value, Operation.TEST_ACTION.value],
        "identifying_channels": sorted(IDENTIFYING_CHANNELS),
        "schema_version": [STORAGE_VERSION, STORAGE_MINOR_VERSION],
    }


@websocket_api.websocket_command({vol.Required("type"): "foyer/config"})
@websocket_api.async_response
async def ws_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The whole configuration, minus every hash in it (§8.1).

    Reading needs the permission but no code: §8.2 asks for a code to change
    the configuration, and a panel that demanded one to open a page would
    teach the household to keep the code on a sticky note by the tablet.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            Operation.EDIT_CONFIG,
            Permission.EDIT_CONFIG,
            need_code=False,
        )
    ) is None:
        return
    connection.send_result(
        msg["id"], {"config": _public_config(system.config), "meta": _meta()}
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
@websocket_api.async_response
async def ws_config_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    # A user is saved through its own command, which has to hash a code and
    # check it against every other one first.
    if msg["kind"] == "user":
        connection.send_error(msg["id"], "invalid_format", "use foyer/user/save")
        return
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
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
@websocket_api.async_response
async def ws_config_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    # Deleting a person is managing users, not editing the configuration.
    permission = (
        Permission.MANAGE_USERS if msg["kind"] == "user" else Permission.EDIT_CONFIG
    )
    if (
        await _gate(hass, system, connection, msg, Operation.EDIT_CONFIG, permission)
    ) is None:
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
@websocket_api.async_response
async def ws_settings_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
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
@websocket_api.async_response
async def ws_chime_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The global chime block (§6.6), validated like every configuration edit."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
        return
    result = update_chime(system.config, system.state, msg["chime"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="chime"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/user/save",
        vol.Required("user"): dict,
        # The new code for this person, and their duress code. Absent means
        # "leave it as it is"; null means "remove it".
        vol.Optional("new_code"): vol.Any(str, None),
        vol.Optional("new_duress_code"): vol.Any(str, None),
        # The code of whoever is doing the saving, for the policy (§8.2).
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_user_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Create or change a person, and hash whatever code came with them.

    Codes travel one way. What arrives is hashed here and stored; what is
    stored is never sent back, so changing a person's name cannot round-trip
    their code through a browser (§8.1, INV-2).

    A code already belonging to somebody else is refused, and the refusal does
    not say whose it was — that would turn this command into a way of testing
    codes against the household.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            Operation.EDIT_CONFIG,
            Permission.MANAGE_USERS,
        )
    ) is None:
        return

    item = dict(msg["user"])
    # Whatever the client sent, hashes come from here and nowhere else.
    item.pop("code_hash", None)
    item.pop("duress_code_hash", None)
    existing = system.config.user(item.get("id"))
    length = system.config.settings.security.code_length
    problems: list[Problem] = []
    for field, stored in (
        ("new_code", "code_hash"),
        ("new_duress_code", "duress_code_hash"),
    ):
        if field not in msg:
            item[stored] = getattr(existing, stored) if existing else None
            continue
        code = msg[field]
        if not code:
            item[stored] = None
            continue
        try:
            codes.validate(code, length)
        except codes.CodeError:
            problems.append(Problem("code_length", "user", item.get("id"), field))
            continue
        if await hass.async_add_executor_job(
            partial(
                codes.collides,
                system.config.users,
                code,
                ignore_user_id=item.get("id"),
            )
        ):
            problems.append(Problem("code_in_use", "user", item.get("id"), field))
            continue
        item[stored] = await hass.async_add_executor_job(codes.hash_code, code)
    # The two codes of one person must differ too, or the duress code would
    # never be reached: the ordinary one matches first.
    if (
        item.get("code_hash")
        and item.get("duress_code_hash")
        and msg.get("new_code")
        and msg.get("new_code") == msg.get("new_duress_code")
    ):
        problems.append(
            Problem("code_in_use", "user", item.get("id"), "new_duress_code")
        )
    if problems:
        connection.send_result(
            msg["id"],
            {"success": False, "problems": [asdict(p) for p in problems]},
        )
        return

    result = upsert(system.config, system.state, "user", item)
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="user"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/security",
        vol.Required("code_policy"): dict,
        vol.Required("security"): dict,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_security_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The code policy and the lockout settings (§8.2, §8.4)."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            Operation.EDIT_CONFIG,
            Permission.MANAGE_USERS,
        )
    ) is None:
        return
    result = update_security(
        system.config,
        system.state,
        {"code_policy": msg["code_policy"], "security": msg["security"]},
    )
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="security"
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
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            Operation.EDIT_CONFIG,
            Permission.VIEW_LOG,
            need_code=False,
        )
    ) is None:
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
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            Operation.EDIT_CONFIG,
            Permission.VIEW_LOG,
            need_code=False,
        )
    ) is None:
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/log/clear",
        vol.Optional("code"): vol.Any(str, None),
    }
)
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
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/export",
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_config_export(
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
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
        return
    stamp = dt_util.now().strftime("%Y%m%d-%H%M")
    document = {
        "foyer": BACKUP_MAGIC,
        "version": [STORAGE_VERSION, STORAGE_MINOR_VERSION],
        "created": dt_util.now().isoformat(),
        # Without the hashes: a backup is a file that leaves the machine, and
        # a code hash in it is an offline guessing exercise waiting to happen.
        # A restore keeps the codes of the people it recognises (§8.1).
        "config": _public_config(system.config),
    }
    connection.send_result(
        msg["id"],
        {"filename": f"foyer-config-{stamp}.json", "document": document},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/import",
        vol.Required("document"): dict,
        vol.Optional("code"): vol.Any(str, None),
    }
)
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
    if (
        await _gate(
            hass, system, connection, msg, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
    ) is None:
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

    # A backup carries no hashes, so the people in it come back without their
    # codes — except those already here under the same id, whose codes are
    # kept. Nothing in a file can set a hash: that way lies a backup that
    # hands somebody a code of their choosing.
    config = replace(
        config,
        users=tuple(
            replace(
                user,
                code_hash=(k.code_hash if (k := system.config.user(user.id)) else None),
                duress_code_hash=(k.duress_code_hash if k else None),
            )
            for user in config.users
        ),
    )
    problems = validate(config) + edit_conflicts(system.config, config, system.state)
    result = EditResult(
        config=None if problems else config, problems=tuple(problems), id=None
    )
    await _apply(
        hass, connection, msg["id"], system, result, operation="restore", kind="config"
    )
