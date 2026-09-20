"""WebSocket commands under ``foyer/*`` used by the panel and the card.

Every command that changes state goes through the engine, and every command
that changes configuration is validated here, server-side, before anything is
stored (INV-2). The panel's own checks are a courtesy.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import partial
from typing import Any
import uuid

from homeassistant.components import webhook, websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .. import i18n
from ..const import (
    ACK_PATHS,
    CANCEL_VIA_COMMAND,
    CHANNEL_HA_UI,
    DOMAIN,
    SIGNAL_UPDATE,
)
from ..core import authz
from ..core.journal import config_row, system_row
from ..core.models import (
    ARMED_HA_STATES,
    IDENTIFYING_CHANNELS,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_CODE_LENGTH,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_GRACE_SECONDS,
    MAX_LOCKOUT_FAILURES,
    MAX_LOCKOUT_SECONDS,
    MAX_LOW_BATTERY_THRESHOLD,
    MAX_RETENTION_DAYS,
    MAX_RULE_MINUTES,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MAX_WALK_TEST_TIMEOUT,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_CODE_LENGTH,
    MIN_LOCKOUT_FAILURES,
    MIN_LOCKOUT_SECONDS,
    MIN_LOW_BATTERY_THRESHOLD,
    MIN_RETENTION_DAYS,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    MIN_WALK_TEST_TIMEOUT,
    SILENCEABLE,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    ActionKind,
    Actor,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    CancelAutoAction,
    CodeResult,
    ContactChannelKind,
    Decision,
    DisarmRequest,
    LogCategory,
    LogSeverity,
    Moment,
    Operation,
    Outcome,
    Permission,
    Reason,
    RuleActionKind,
    RuleTriggerKind,
    SetAutoArming,
    SetSuspension,
    Suspension,
    SuspensionKind,
    User,
    WalkTestRequest,
    ZoneType,
)
from ..core.presets import UNAVAILABLE_TYPES, preset
from ..core.proposals import propose_zone
from ..core.simulate import (
    DEFAULT_HORIZON,
    MAX_HORIZON,
    SimulationRequest,
    ZoneOverride,
    inputs as simulation_inputs,
)
from ..core.templates import TEMPLATE_VARIABLES
from ..core.validation import (
    ACTION_DOMAINS,
    CHIME_DOMAINS,
    ESCALATION_KINDS,
    ESCALATION_MOMENTS,
    MAX_ACTION_DELAY,
    MAX_ESCALATION_OFFSET,
    MAX_SEVERITY,
    PRESENCE_DOMAINS,
    ZONE_DOMAINS,
    Problem,
)
from ..runtime.system import FoyerSystem
from ..security import codes
from ..security.identity import async_actor
from ..store.editing import (
    KINDS,
    EditResult,
    delete,
    update_chime,
    update_health,
    update_security,
    update_settings,
    upsert,
)
from ..store.log_store import export_csv, export_json
from ..store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    settings_to_dict,
)
from .backup import (
    async_write,
    backup_document,
    backup_filename,
    public_config,
    public_user,
    restore,
)

PREFS_KEY = "foyer.prefs"

# Moments a profile can already be written against, though the phase that
# raises them has not landed (SPEC §6.1; part 3 appendix).
# Empty, and that is the point: escalation_exhausted was the last entry, and
# part 4 raises it. Every moment the editor offers is a moment something
# produces, and a label still saying "nothing raises this yet" after
# something does is a label that teaches people to skip a working setting.
FUTURE_MOMENTS: tuple[Moment, ...] = ()

# Moments nothing can answer, so nothing is offered them (see _meta).
UNANSWERABLE_MOMENTS: frozenset[Moment] = frozenset(
    {Moment.ACTION_TESTED, Moment.ESCALATION_SKIPPED}
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

    Foyer knows this person, or it does not. A Foyer user linked to their
    Home Assistant account is subject to Foyer's rules; with none linked, the
    rule is the one this integration has used since Phase 0 — a Home
    Assistant administrator, and nobody else.

    With one exception, deliberate and stated where it is implemented: a Home
    Assistant **administrator** is never refused the configuration for want of
    a permission. INV-6 already says they can read .storage, call any service
    and disable the integration, so refusing them here buys no security — and
    it would buy a real failure: the owner who links their own account, leaves
    manage_users unticked and can never tick it again.

    The code is a different matter and still applies to them: it is what
    protects the configuration from somebody using their unlocked tablet,
    which is exactly the threat INV-6 says codes are for.
    """
    user = system.config.user(actor.user_id)
    if actor.code is CodeResult.INVALID:
        return Reason.BAD_CODE
    if user is None:
        return None if connection.user.is_admin else Reason.NOT_PERMITTED
    if not user.enabled or not user.in_window(dt_util.utcnow()):
        return Reason.USER_NOT_VALID
    if not user.may(permission) and not connection.user.is_admin:
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
    *,
    operation: Operation,
    permission: Permission,
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

    Built where every other caller builds it (api/backup), so what the panel
    is shown and what a backup contains can never drift apart.
    """
    return public_config(config)


def _public_user(user: User) -> dict[str, Any]:
    return public_user(user)


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
        ws_health,
        ws_health_save,
        ws_radio_candidates,
        ws_ack_webhook,
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
        ws_diagnostics,
        ws_simulate,
        ws_walk_test,
        ws_test_action,
        ws_auto_cancel,
        ws_auto_switch,
        ws_auto_suspend,
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
    """The structured result of SPEC §9.1, built where everything builds it."""
    return system.result(decision, ha_user)


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
        vol.Optional("via", default="acknowledge"): vol.In(list(ACK_PATHS)),
        vol.Optional("contact_id"): vol.Any(str, None),
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
    kind = AcknowledgeIncident if msg["target"] == "incident" else AcknowledgeTechnical
    event: Any = kind(actor, via=msg["via"], contact_id=msg.get("contact_id"))
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


# --- automatic arming (§9.4) ------------------------------------------------------


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/auto/cancel",
        # Which countdown. Omitted, it stops whatever is counting down, which
        # is what the panel's single button means when only one is.
        vol.Optional("pending_id"): vol.Any(str, None),
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_auto_cancel(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Stop an automatic rule before it acts (§9.4).

    Its own operation in the code policy, without a code by default (part 2
    decision 3). The engine decides, here as everywhere (INV-2): an
    installation that raised the policy gets a refusal the panel can show.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    decision = await system.async_handle(
        CancelAutoAction(
            pending_id=msg.get("pending_id"),
            actor=await _actor(hass, system, connection, msg),
            via=CANCEL_VIA_COMMAND,
        )
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/auto/switch",
        vol.Required("enabled"): bool,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_auto_switch(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The global kill switch (§9.4), from the panel rather than the entity."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    decision = await system.async_handle(
        SetAutoArming(msg["enabled"], await _actor(hass, system, connection, msg))
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/auto/suspend",
        # One command for the three forms §9.4 says are mechanically one:
        # until a date and time, skip the next occurrence, or a named
        # expected-visitor window. With only `suspension_id`, it lifts one.
        vol.Optional("kind"): vol.In([k.value for k in SuspensionKind]),
        vol.Optional("suspension_id"): vol.Any(str, None),
        vol.Optional("rule_ids", default=[]): [str],
        vol.Optional("name"): vol.Any(str, None),
        vol.Optional("start"): vol.Any(str, None),
        vol.Optional("until"): vol.Any(str, None),
        vol.Optional("reduced_scenario_id"): vol.Any(str, None),
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_auto_suspend(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Suspend automatic arming, or lift a suspension (§9.4).

    Runtime state, not configuration (part 2 decision 7), so this is not an
    ``edit_config`` operation: §9.4 asks for three clicks from the panel or
    the card the evening before the boiler engineer comes.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    actor = await _actor(hass, system, connection, msg)
    user = system.config.user(actor.user_id)
    suspension: Suspension | None = None
    if msg.get("kind"):
        try:
            start = _parse_time(msg.get("start"))
            until = _parse_time(msg.get("until"))
        except ValueError:
            connection.send_error(msg["id"], "invalid_format", "invalid timestamp")
            return
        suspension = Suspension(
            id=uuid.uuid4().hex,
            kind=SuspensionKind(msg["kind"]),
            rule_ids=tuple(msg["rule_ids"]),
            name=msg.get("name") or None,
            start=start,
            until=until,
            reduced_scenario_id=msg.get("reduced_scenario_id") or None,
            created_at=dt_util.utcnow(),
            user_id=actor.user_id,
            # Denormalised for the same reason the log denormalises it: the
            # row this writes has to still name somebody in six months.
            user_name=user.name if user else None,
        )
    decision = await system.async_handle(
        SetSuspension(suspension, msg.get("suspension_id"), actor)
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


def _parse_time(value: str | None) -> Any:
    """An ISO timestamp from the panel, or None. A bad one is refused rather
    than guessed at: a suspension that ends at the wrong hour is a house
    armed at the wrong hour."""
    if not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        raise ValueError(value)
    return dt_util.as_utc(parsed)


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
            "low_battery_threshold": [
                MIN_LOW_BATTERY_THRESHOLD,
                MAX_LOW_BATTERY_THRESHOLD,
            ],
            "walk_test_timeout": [MIN_WALK_TEST_TIMEOUT, MAX_WALK_TEST_TIMEOUT],
            "escalation_offset": [0, MAX_ESCALATION_OFFSET],
        },
        # What page 5 needs to build an action editor without knowing the
        # engine: the catalogue, where each kind may point, and the moments.
        "action_kinds": [k.value for k in ActionKind],
        "action_domains": {k: list(v) for k, v in ACTION_DOMAINS.items()},
        "silenceable": sorted(SILENCEABLE),
        # Every moment a profile may answer. Two are not: ACTION_TESTED is
        # somebody pressing the test button of §11.4, and a profile that
        # answered a test by sounding the siren would be a loop; and
        # ESCALATION_SKIPPED is a row saying a notification did not go out
        # while Home Assistant was down, which is a record rather than
        # something the house can answer.
        "moments": [m.value for m in Moment if m not in UNANSWERABLE_MOMENTS],
        # Moments no phase raises yet: selectable, and labelled as such.
        # Part 4 raises the last of them.
        "future_moments": [m.value for m in FUTURE_MOMENTS],
        # Which moments an escalation step may answer (§7.2): an incident and
        # the technical channel, the only two things with an acknowledgement.
        "escalation_moments": sorted(m.value for m in ESCALATION_MOMENTS),
        "escalation_kinds": sorted(k.value for k in ESCALATION_KINDS),
        "contact_channel_kinds": [k.value for k in ContactChannelKind],
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
        # Every operation of §8.2 has a caller now: part 2 built the last two.
        "future_operations": [],
        "identifying_channels": sorted(IDENTIFYING_CHANNELS),
        # What page 12 needs to build a rule without knowing §9.4 by heart:
        # the closed sets, the bounds, and which entities a rule may watch.
        "rule_triggers": [k.value for k in RuleTriggerKind],
        "rule_actions": [k.value for k in RuleActionKind],
        "suspension_kinds": [k.value for k in SuspensionKind],
        "presence_domains": sorted(PRESENCE_DOMAINS),
        "max_grace_seconds": MAX_GRACE_SECONDS,
        "max_rule_minutes": MAX_RULE_MINUTES,
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
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
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
    answer = await async_write(
        hass,
        system,
        result,
        operation=operation,
        kind=kind,
        channel=CHANNEL_HA_UI,
        user_id=connection.user.id,
        user_name=connection.user.name,
    )
    connection.send_result(msg_id, answer)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/save",
        vol.Required("kind"): vol.In(list(KINDS)),
        vol.Required("item"): dict,
        vol.Optional("trigger_confirmed", default=False): bool,
        vol.Optional("code"): vol.Any(str, None),
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
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
        vol.Optional("code"): vol.Any(str, None),
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
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=permission,
        )
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
        vol.Optional("code"): vol.Any(str, None),
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    result = update_settings(system.config, system.state, msg["settings"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="settings"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/ack_webhook",
        vol.Required("enabled"): bool,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_ack_webhook(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Switch the DTMF acknowledgement webhook on or off (§7.2).

    The id is generated here and never accepted from the caller: an
    unauthenticated URL is protected by nothing except the fact that nobody
    can guess it, and a client that chose its own would eventually choose
    "foyer". Switching it off forgets the id, so switching it on again hands
    out a new one rather than reviving a URL somebody may still hold.

    An ordinary configuration edit, with the permission and the code §8.2
    asks for — and the panel says, beside the switch, what the URL can do.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    webhook_id = webhook.async_generate_id() if msg["enabled"] else None
    # The whole settings block, unchanged, plus the one field this command
    # owns. It is passed beside the block rather than inside it: the store
    # refuses to read this id out of anything a client sent, so that the
    # address of an unauthenticated URL can only ever be generated here.
    result = update_settings(
        system.config,
        system.state,
        settings_to_dict(system.config.settings),
        webhook_id=webhook_id,
    )
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="settings"
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/chime",
        vol.Required("chime"): dict,
        vol.Optional("code"): vol.Any(str, None),
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    result = update_chime(system.config, system.state, msg["chime"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="chime"
    )


@websocket_api.websocket_command({vol.Required("type"): "foyer/health"})
@websocket_api.async_response
async def ws_health(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 14 (§12, §15.1), gated on ``view_log`` (part 1 decision 12).

    The same threshold as the Log page, and for the same reason: this page
    says what has been wrong with the house and for how long, which is the
    history of the installation read from a different angle. Reading it
    changes nothing, so it asks for no code.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.VIEW_LOG,
            need_code=False,
        )
    ) is None:
        return
    connection.send_result(msg["id"], system.health_status())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/config/health",
        vol.Required("health"): dict,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_health_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The system-health block (§12), validated like every other edit.

    Configuration, so ``edit_config`` and its code policy — the page itself
    is open to anyone who may read the log, and changing the watchdog's URL
    or which entity is the mains is not reading.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    result = update_health(system.config, system.state, msg["health"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="health"
    )


@websocket_api.websocket_command({vol.Required("type"): "foyer/health/radios"})
@websocket_api.async_response
async def ws_radio_candidates(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Which config entries the zones of this installation actually come from.

    A radio is a config entry (part 1 decision 7), so this is the honest
    menu: the integrations that back at least one zone, with how many. An
    installation whose sensors are all on Wi-Fi sees an empty list, which is
    the true answer rather than a list of integrations that are not radios.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
            need_code=False,
        )
    ) is None:
        return
    connection.send_result(msg["id"], {"radios": system.radio_candidates()})


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
            operation=Operation.EDIT_CONFIG,
            permission=Permission.MANAGE_USERS,
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
        # Absent, or empty, means "leave it as it is": the editor sends the
        # field as soon as somebody types in it, so a code typed and then
        # cleared must not silently remove the code they already had. Only an
        # explicit null removes one.
        code = msg.get(field) if field in msg else ""
        if code == "":
            item[stored] = getattr(existing, stored) if existing else None
            continue
        if code is None:
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
    # A person's two codes must differ as well, and this cannot be left to the
    # uniqueness check above: that one skips the user being edited, precisely
    # so they can keep their own code. Setting a duress code equal to one's own
    # ordinary code would be accepted by it — and the duress code would then
    # never be reached, because the ordinary hash matches first. A silent alarm
    # that can never fire is the worst thing in this file.
    for field, other in (
        ("new_code", "duress_code_hash"),
        ("new_duress_code", "code_hash"),
    ):
        code = msg.get(field)
        if not code or not item.get(other):
            continue
        if await hass.async_add_executor_job(codes.matches, code, item[other]):
            problems.append(Problem("code_in_use", "user", item.get("id"), field))
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
            operation=Operation.EDIT_CONFIG,
            permission=Permission.MANAGE_USERS,
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
            operation=Operation.EDIT_CONFIG,
            permission=Permission.VIEW_LOG,
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
            operation=Operation.EDIT_CONFIG,
            permission=Permission.VIEW_LOG,
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    connection.send_result(
        msg["id"],
        {
            "filename": backup_filename("config"),
            "document": backup_document(system.config),
        },
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
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
        )
    ) is None:
        return
    result = restore(system, msg["document"])
    await _apply(
        hass, connection, msg["id"], system, result, operation="restore", kind="config"
    )


# --- page 9: diagnostics and the simulator (SPEC §11.1, §11.2) --------------------

# Both of these **read**, and they are gated as reads: view_log, no code.
#
# Decided explicitly rather than copied from whatever was nearby, because the
# same mistake was made once already and had to be undone. Neither command
# changes state and neither changes configuration, so edit_config is the wrong
# permission on both counts: it would refuse the diagnostics table to somebody
# trusted to read the log of what actually happened, which is strictly more
# than the table shows. And §8.2 asks for a code to *edit* the configuration —
# demanding one to open a page teaches a household to keep the code on a
# sticky note beside the tablet.
#
# view_log is the right shape for a second reason: what these two reveal is
# what the log reveals. The table says which zones exist and which are open;
# the trace says what the house would do about them. Somebody who may read
# "disarmed at 03:14 by Luca" may certainly read "the kitchen window is a
# delayed zone with a 30 s entry delay".


@websocket_api.websocket_command({vol.Required("type"): "foyer/diagnostics"})
@websocket_api.async_response
async def ws_diagnostics(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 9, tab 1: every mapped zone, live (§11.1)."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.VIEW_LOG,
            need_code=False,
        )
    ) is None:
        return
    connection.send_result(msg["id"], system.diagnostics())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/simulate",
        # The hypothetical scenario, or the areas armed on their own. Neither
        # is a question too: a 24h zone answers on a disarmed house.
        vol.Exclusive("scenario_id", "target"): vol.Any(str, None),
        vol.Exclusive("area_ids", "target"): [str],
        # The hypothetical clock. Absent means now, which is the common case.
        vol.Optional("start"): vol.Any(str, None),
        vol.Optional("zones", default=[]): [
            {
                vol.Required("zone_id"): str,
                vol.Required("state"): str,
                vol.Optional("at", default=0): vol.All(
                    int, vol.Range(min=0, max=MAX_HORIZON)
                ),
            }
        ],
        vol.Optional("entities", default={}): {str: str},
        vol.Optional("horizon", default=DEFAULT_HORIZON): vol.All(
            int, vol.Range(min=1, max=MAX_HORIZON)
        ),
        # Not for the command, which only reads: for the arming the run uses
        # as its premise. An installation that asks for a code to arm asks
        # for one here too, and the trace says so rather than pretending.
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_simulate(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 9, tab 2: rehearse the configuration (§11.2).

    Nothing here is executed, and that is guaranteed structurally rather than
    by this handler being careful: core.simulate calls the same decide() the
    runtime calls and never hands the Decision to the executor (INV-1).
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        actor := await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.VIEW_LOG,
            need_code=False,
        )
    ) is None:
        return
    start = dt_util.parse_datetime(msg.get("start") or "") or dt_util.utcnow()
    request = SimulationRequest(
        start=dt_util.as_utc(start),
        timezone=dt_util.get_default_time_zone(),
        scenario_id=msg.get("scenario_id") or None,
        area_ids=tuple(msg.get("area_ids") or ()),
        zones=tuple(
            ZoneOverride(z["zone_id"], z["state"], z["at"]) for z in msg["zones"]
        ),
        entities=dict(msg["entities"]),
        horizon=msg["horizon"],
        actor=actor,
    )
    # §11.2: every run is logged with its inputs, so a configuration change
    # can be justified after the fact — which only works if the row carries
    # enough to run it again.
    system.async_record(
        (
            system_row(
                dt_util.utcnow(),
                event_type="simulation_run",
                user_id=actor.user_id,
                user_name=(
                    named.name if (named := system.config.user(actor.user_id)) else None
                ),
                channel=CHANNEL_HA_UI,
                detail=simulation_inputs(request),
            ),
        )
    )
    connection.send_result(msg["id"], system.simulate(request))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/walk_test",
        vol.Required("enable"): bool,
        # Shorter than the installation's maximum, never longer (§5.3).
        vol.Optional("duration"): vol.Any(
            vol.All(
                int, vol.Range(min=MIN_WALK_TEST_TIMEOUT, max=MAX_WALK_TEST_TIMEOUT)
            ),
            None,
        ),
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_walk_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 9, tab 3: enter or leave the walk test (§11.3).

    A state-changing request like any other, so it goes to the engine and the
    engine resolves §8.2 and §8.3 — "enter walk test" is code required by
    default, and a rehearsal buys no exemption (INV-2).
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    decision = await system.async_handle(
        WalkTestRequest(
            msg["enable"],
            await _actor(hass, system, connection, msg),
            duration=msg.get("duration"),
        )
    )
    connection.send_result(msg["id"], _result(system, decision, connection.user))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/test_action",
        # One configured action of one profile (page 5), a contact's channel
        # (page 6) — the other half of §11.4's "a test button next to every
        # action and every contact channel" — or a bare notification service,
        # which is what the first-run wizard tests.
        vol.Exclusive("action_id", "target"): str,
        vol.Exclusive("service", "target"): str,
        vol.Exclusive("contact_id", "target"): str,
        vol.Optional("channel_id"): str,
        vol.Optional("profile_id"): str,
        vol.Optional("message"): str,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_test_action(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Page 9, tab 4: really execute one action (§11.4).

    Gated like a configuration command rather than through the engine,
    because it changes no alarm state: it presses a button an administrator
    could press from Developer Tools anyway, which is exactly the case INV-6
    describes. The `test_actions` permission and the code of §8.2 both
    apply; what does not is refusing an administrator for a permission they
    can grant themselves in two clicks.
    """
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        actor := await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.TEST_ACTION,
            permission=Permission.TEST_ACTIONS,
        )
    ) is None:
        return
    result = await system.async_test_action(
        profile_id=msg.get("profile_id"),
        action_id=msg.get("action_id"),
        service=msg.get("service"),
        contact_id=msg.get("contact_id"),
        channel_id=msg.get("channel_id"),
        message=msg.get("message", ""),
        actor=actor,
    )
    connection.send_result(msg["id"], result)
