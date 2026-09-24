"""WebSocket commands under ``foyer/*`` used by the panel and the card.

Every command that changes state goes through the engine, and every command
that changes configuration is validated here, server-side, before anything is
stored (INV-2). The panel's own checks are a courtesy.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import partial
from pathlib import Path
from typing import Any
import uuid

from homeassistant.components import webhook, websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.network import NoURLAvailableError
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
from ..core.journal import LogRow, config_row, row_for, system_row
from ..core.models import (
    ARMED_HA_STATES,
    IDENTIFYING_CHANNELS,
    MAX_ARM_HOLD_TIMEOUT,
    MAX_BYPASS_SECONDS,
    MAX_CODE_LENGTH,
    MAX_CONDITIONS,
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_GRACE_SECONDS,
    MAX_LOCKOUT_FAILURES,
    MAX_LOCKOUT_SECONDS,
    MAX_LOW_BATTERY_THRESHOLD,
    MAX_RETENTION_DAYS,
    MAX_RF_CONFIRM,
    MAX_RF_WINDOW,
    MAX_RF_ZONES,
    MAX_RULE_MINUTES,
    MAX_SIREN_DURATION,
    MAX_SUPERVISION_TIMEOUT,
    MAX_TRIGGER_COUNT,
    MAX_VERIFICATION_WINDOW,
    MAX_WALK_TEST_TIMEOUT,
    MAX_WATCHDOG_FAILURES,
    MAX_WATCHDOG_INTERVAL,
    MAX_WATCHDOG_TIMEOUT,
    MIN_ARM_HOLD_TIMEOUT,
    MIN_CODE_LENGTH,
    MIN_LOCKOUT_FAILURES,
    MIN_LOCKOUT_SECONDS,
    MIN_LOW_BATTERY_THRESHOLD,
    MIN_RETENTION_DAYS,
    MIN_RF_CONFIRM,
    MIN_RF_WINDOW,
    MIN_RF_ZONES,
    MIN_SUPERVISION_TIMEOUT,
    MIN_VERIFICATION_WINDOW,
    MIN_WALK_TEST_TIMEOUT,
    MIN_WATCHDOG_FAILURES,
    MIN_WATCHDOG_INTERVAL,
    MIN_WATCHDOG_TIMEOUT,
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
    CodeAttempt,
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
    Purpose,
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
from ..core.privacy import (
    MAX_PSEUDONYMISE_DAYS,
    MIN_PSEUDONYMISE_DAYS,
    NAMED_CATEGORIES,
    SHORT_RETENTION_DAYS,
    PersonRef,
    person_ref,
)
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
from ..security.devices import new_token
from ..security.identity import async_actor
from ..store.editing import (
    KINDS,
    EditResult,
    delete,
    set_device_token,
    touches_people,
    update_chime,
    update_health,
    update_security,
    update_settings,
    upsert,
)
from ..store.log_store import LogUnavailable, export_csv, export_json
from ..store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    settings_to_dict,
)
from .alarmo import async_plan as async_alarmo_plan
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
    {Moment.ACTION_TESTED, Moment.ESCALATION_SKIPPED, Moment.ACCESS_RECOVERED}
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
    actor: Actor,
    operation: Operation,
    permission: Permission,
    *,
    need_code: bool = True,
) -> Reason | None:
    """The gate in front of every configuration and log command (§8.3).

    core/authz decides; see ``may_configure`` there. The panel is not open to
    an account nobody linked, even before the first code exists: that has
    been its rule since Phase 0 — a Home Assistant administrator, and nobody
    else.
    """
    return authz.may_configure(
        system.config,
        actor,
        operation,
        permission,
        dt_util.utcnow(),
        need_code=need_code,
    )


async def _gate(
    hass: HomeAssistant,
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    *,
    operation: Operation,
    permission: Permission,
    need_code: bool = True,
    purpose: Purpose | None = None,
    raised: list[LogRow] | None = None,
) -> Actor | None:
    """Check, answer the caller on refusal, and record the refusal.

    ``need_code`` is False for the commands that only read: §8.2 asks for a
    code to *edit* the configuration, and a panel that demanded one to open a
    page would teach the household to keep the code on a sticky note.

    ``purpose`` names the command where ``operation`` — the policy entry —
    does not: a duress code used to empty the log raises a `duress` that
    says so, and not "edit the configuration" (decision 134).

    ``raised``, when given, receives the `duress` row this request raised,
    if it raised one: the one command that empties the log has to write it
    again afterwards, or the clear it asked for erases it.
    """
    actor = await _actor(hass, system, connection, msg)
    # The lockout of §8.4, spent through the engine so that a wrong code here
    # counts exactly as one typed on a keypad does: the same counter, the same
    # `code_rejected` row, the same `lockout` moment a profile can answer.
    # These commands verify their own code and never reach `decide()`, so
    # before this they counted nothing at all — an unlimited, silent oracle
    # over the whole code space (found in review). A request carrying no
    # code offers nothing to count, and the engine is not woken for it: a
    # page opened is not an attempt (third review). A duress code raises
    # `duress` here, once for the command, whatever follows (§8.1).
    reason = None
    if actor.code is not CodeResult.NONE:
        attempt = await system.async_handle(
            CodeAttempt(operation=operation, actor=actor, purpose=purpose)
        )
        reason = attempt.reason
        if raised is not None:
            raised.extend(
                row_for(o, attempt.at)
                for o in attempt.occurrences
                if o.moment is Moment.DURESS
            )
    reason = reason or _may_configure(
        system, actor, operation, permission, need_code=need_code
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


def _me(
    system: FoyerSystem, connection: websocket_api.ActiveConnection
) -> tuple[str, str]:
    """Who to record for something done from the panel (§10.1).

    The Foyer person linked to this Home Assistant account when there is one,
    so every row in the log names people from one namespace and a question
    about a person can reach all of them.
    """
    me = system.config.user_of_ha(connection.user.id)
    return (me.id, me.name) if me else (connection.user.id, connection.user.name)


def _public_config(config) -> dict[str, Any]:
    """The configuration as the panel may see it: no hashes and no
    credentials, ever (§8.1, decision 128).

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
        ws_languages,
        ws_config,
        ws_config_save,
        ws_config_delete,
        ws_settings_save,
        ws_chime_save,
        ws_health,
        ws_health_save,
        ws_radio_candidates,
        ws_ack_webhook,
        ws_device_token,
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
        ws_privacy_preview,
        ws_privacy_export,
        ws_privacy_erase,
        ws_config_export,
        ws_config_import,
        ws_alarmo_preview,
        ws_alarmo_apply,
        ws_diagnostics,
        ws_simulate,
        ws_walk_test,
        ws_test_action,
        ws_auto_cancel,
        ws_auto_switch,
        ws_auto_suspend,
        ws_api_document,
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


@websocket_api.websocket_command({vol.Required("type"): "foyer/languages"})
@websocket_api.async_response
async def ws_languages(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The languages Foyer can send its messages in, read from the files."""
    found = await hass.async_add_executor_job(i18n.languages)
    connection.send_result(msg["id"], {"languages": found})


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
        # Refused before the engine, after the code was read (decision 131).
        await system.async_refused_before_engine(
            actor, (Operation.FORCE_ARM if force else Operation.ARM).value
        )
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
        vol.Optional("seconds"): vol.Any(
            vol.All(int, vol.Range(min=1, max=MAX_BYPASS_SECONDS)), None
        ),
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
            # Refused before the engine, after the code was read (decision
            # 131).
            await system.async_refused_before_engine(actor, Purpose.SUSPEND_AUTO_ARMING)
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


def _lenient_datetime(value: str) -> Any:
    """A timestamp, or None when it cannot be read. Home Assistant raises for
    a string shaped like a date that is not one ("2026-99-01"), and a filter
    that crashed the handler answered nothing at all (second review)."""
    try:
        return dt_util.parse_datetime(value)
    except ValueError:
        return None


def _parse_time(value: str | None) -> Any:
    """An ISO timestamp from the panel, or None. A bad one is refused rather
    than guessed at: a suspension that ends at the wrong hour is a house
    armed at the wrong hour."""
    if not value:
        return None
    parsed = _lenient_datetime(value)
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
            # System health (§12). Here rather than written into the page,
            # so the panel cannot offer a value the backend then refuses.
            "watchdog_interval": [MIN_WATCHDOG_INTERVAL, MAX_WATCHDOG_INTERVAL],
            "watchdog_timeout": [MIN_WATCHDOG_TIMEOUT, MAX_WATCHDOG_TIMEOUT],
            "watchdog_failures": [MIN_WATCHDOG_FAILURES, MAX_WATCHDOG_FAILURES],
            "rf_zones": [MIN_RF_ZONES, MAX_RF_ZONES],
            "rf_window": [MIN_RF_WINDOW, MAX_RF_WINDOW],
            "rf_confirm": [MIN_RF_CONFIRM, MAX_RF_CONFIRM],
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
        # Timed pseudonymisation and the short preset §10.4 asks for, both
        # here rather than written into the page: the panel must not offer a
        # number the backend would refuse, or a preset that touches a
        # category this file does not agree names anybody.
        "pseudonymise_bounds": [MIN_PSEUDONYMISE_DAYS, MAX_PSEUDONYMISE_DAYS],
        "short_retention": SHORT_RETENTION_DAYS,
        "named_categories": list(NAMED_CATEGORIES),
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
    """The whole configuration, minus every hash and every credential in it
    (§8.1, decision 128).

    Reading needs the permission but no code: §8.2 asks for a code to change
    the configuration, and a panel that demanded one to open a page would
    teach the household to keep the code on a sticky note by the tablet.
    That is exactly why the webhook's address and the watchdog URL are not
    in it: the permission alone, with nobody asked for a code, would be
    enough to copy the URL that stops an alarm or the one that keeps a dead
    house looking alive. It says whether each is set, never what it is.
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
    # The Foyer person behind this Home Assistant account, when one is
    # linked. Written in preference to the Home Assistant id because every
    # other row in the log carries the Foyer one, and a `config` row in a
    # different namespace is a row no question about a person can reach —
    # including the erasure of §10.4 (found in review).
    me = system.config.user_of_ha(connection.user.id)
    answer = await async_write(
        hass,
        system,
        result,
        operation=operation,
        kind=kind,
        channel=CHANNEL_HA_UI,
        user_id=me.id if me else connection.user.id,
        user_name=me.name if me else connection.user.name,
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
    # A tag is not a setting, it is a credential belonging to a person: it
    # carries no code, and possession of it arms and disarms as whoever it
    # names (§9.3). Saving one with `edit_config` alone would let somebody
    # who may not disarm mint a token that disarms — so it asks for the
    # permission that owns people, as deleting a user does.
    permission = (
        Permission.MANAGE_USERS
        if msg["kind"] == "device" and (msg["item"] or {}).get("kind") == "tag"
        else Permission.EDIT_CONFIG
    )
    if (
        actor := await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=permission,
        )
    ) is None:
        return
    result = upsert(
        system.config,
        system.state,
        msg["kind"],
        msg["item"],
        trigger_confirmed=msg["trigger_confirmed"],
        now=dt_util.utcnow(),
    )
    # A key switch given to somebody, a name added to a scenario's list:
    # manage_users', whichever page it was saved from (decision 112).
    if (
        result.config is not None
        and touches_people(system.config, result.config)
        and _refuse_people(system, connection, msg["id"], actor)
    ):
        return
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
        actor := await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=permission,
        )
    ) is None:
        return
    result = delete(
        system.config,
        system.state,
        msg["kind"],
        msg["item_id"],
        now=dt_util.utcnow(),
    )
    if (
        result.config is not None
        and touches_people(system.config, result.config)
        and _refuse_people(system, connection, msg["id"], actor)
    ):
        return
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
    result = update_settings(
        system.config, system.state, msg["settings"], now=dt_util.utcnow()
    )
    _record_pseudonymisation(system, connection, result)
    await _apply(
        hass, connection, msg["id"], system, result, operation="save", kind="settings"
    )


@callback
def _record_pseudonymisation(
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    result: EditResult,
) -> None:
    """A row of its own when timed pseudonymisation is switched on or off.

    The ordinary settings row says that the log block changed, which is not
    enough here (part 2 decision 5). This is the one configuration change that
    destroys the past, and switching it *off* is as much worth recording as
    switching it on — "who turned the protection off, and when" is a question
    somebody will ask, and its absence from the record would be the most
    convenient absence in the file.
    """
    if result.config is None:
        return
    was = system.config.settings.log.pseudonymise_after
    now = result.config.settings.log.pseudonymise_after
    if was == now:
        return
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="pseudonymisation",
                kind="log",
                user_id=(me := _me(system, connection))[0],
                user_name=me[1],
                channel=CHANNEL_HA_UI,
                changes={"from": was, "to": now},
            ),
        )
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

    Switching it on always mints a new id, so it is also how a lost address
    is replaced: the answer to it is the one place the address is ever
    shown, as the keypad token's is (decisions 128, 129). Nothing reads it
    back afterwards; to see it again, generate a new one.

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
        now=dt_util.utcnow(),
    )
    me = system.config.user_of_ha(connection.user.id)
    answer = await async_write(
        hass,
        system,
        result,
        operation="new_webhook" if webhook_id else "forget_webhook",
        kind="settings",
        channel=CHANNEL_HA_UI,
        user_id=me.id if me else connection.user.id,
        user_name=me.name if me else connection.user.name,
    )
    if answer.get("success") and webhook_id:
        answer = {**answer, **_webhook_address(hass, webhook_id)}
    connection.send_result(msg["id"], answer)


def _webhook_address(hass: HomeAssistant, webhook_id: str) -> dict[str, Any]:
    """Where the voice provider has to post, as something it can be given.

    The path always; the full URL too when Home Assistant knows its own
    external address (decision 129). Never the internal one: a voice
    provider calls from the internet, and an address on the household's
    network pasted into it would acknowledge nothing the night it was
    needed. With no external address the panel shows the path and says to
    put the household's own address in front of it.
    """
    try:
        url: str | None = webhook.async_generate_url(
            hass, webhook_id, allow_internal=False, prefer_external=True
        )
    except NoURLAvailableError:
        url = None
    return {"path": webhook.async_generate_path(webhook_id), "url": url}


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/device/token",
        vol.Required("device_id"): str,
        # False generates a new token; True revokes the one there is.
        vol.Optional("revoke", default=False): bool,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_device_token(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Generate or revoke an endpoint keypad's token (§9.2.1).

    An `edit_config` operation with a code, as saving the keypad is: the
    token alone disarms nothing, but it is the keypad's identity. Generated
    here and never accepted from the caller, like the webhook id above. The
    answer to a generation is the one place the token is ever shown — it is
    stored as its hash and nothing can read it back — and the reload the save
    performs is what closes every stream the old token had open.
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
    token, hashed = (None, None) if msg["revoke"] else new_token()
    result = set_device_token(
        system.config, system.state, msg["device_id"], hashed, now=dt_util.utcnow()
    )
    me = system.config.user_of_ha(connection.user.id)
    answer = await async_write(
        hass,
        system,
        result,
        operation="revoke_token" if msg["revoke"] else "new_token",
        kind="device",
        channel=CHANNEL_HA_UI,
        user_id=me.id if me else connection.user.id,
        user_name=me.name if me else connection.user.name,
    )
    if answer.get("success") and token is not None:
        answer = {**answer, "token": token}
    connection.send_result(msg["id"], answer)


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
    result = update_chime(
        system.config, system.state, msg["chime"], now=dt_util.utcnow()
    )
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

    The watchdog URL is written and never read back (§12.3, decision 130):
    nothing returns it, so a block without one — the panel's, unless
    somebody typed a new URL — keeps the one stored.
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
    result = update_health(
        system.config, system.state, msg["health"], now=dt_util.utcnow()
    )
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
    actor = await _gate(
        hass,
        system,
        connection,
        msg,
        operation=Operation.EDIT_CONFIG,
        permission=Permission.MANAGE_USERS,
    )
    if actor is None:
        return

    item = dict(msg["user"])
    # Whatever the client sent, hashes come from here and nowhere else.
    item.pop("code_hash", None)
    item.pop("duress_code_hash", None)
    existing = system.config.user(item.get("id"))
    length = system.config.settings.security.code_length
    problems: list[Problem] = []
    new_codes: dict[str, str] = {}
    # A person is linked to somebody's account, never to one Home Assistant
    # runs itself — Home Assistant Cloud's, the supervisor's. Their requests
    # come from no person, and an exemption linked to them would reach every
    # voice assistant behind the Cloud (fix phase). The Users page never
    # offered them; the backend now refuses them too.
    if ha_user_id := item.get("ha_user_id"):
        linked = await hass.auth.async_get_user(ha_user_id)
        if linked is None or linked.system_generated:
            problems.append(
                Problem("unknown_ha_user", "user", item.get("id"), "ha_user_id")
            )
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
        new_codes[field] = code
        item[stored] = getattr(existing, stored) if existing else None
    if problems:
        connection.send_result(
            msg["id"],
            {"success": False, "problems": [asdict(p) for p in problems]},
        )
        return
    # The rest of the person first. Checked after it, the uniqueness check is
    # reached only by a save that would otherwise be stored: before it, a
    # save built to fail validation made every probe free, and the check an
    # unlimited way of testing codes against the household (second review).
    trial = upsert(system.config, system.state, "user", item, now=dt_util.utcnow())
    if trial.config is None:
        connection.send_result(
            msg["id"],
            {"success": False, "problems": [asdict(p) for p in trial.problems]},
        )
        return
    # Only a person who already exists keeps their own code out of the check,
    # and only as the stored record says — never an id the client chose.
    own = existing.id if existing is not None else None
    collided = False
    for field, code in new_codes.items():
        if await hass.async_add_executor_job(
            partial(codes.collides, system.config.users, code, ignore_user_id=own)
        ):
            collided = True
            problems.append(Problem("code_in_use", "user", item.get("id"), field))
    # A person's two codes must differ as well, and this cannot be left to the
    # uniqueness check above: that one skips the user being edited, precisely
    # so they can keep their own code. Setting a duress code equal to one's own
    # ordinary code would be accepted by it — and the duress code would then
    # never be reached, because the ordinary hash matches first. A silent alarm
    # that can never fire is the worst thing in this file.
    ordinary = new_codes.get("new_code")
    duress = new_codes.get("new_duress_code")
    if ordinary and duress and ordinary == duress:
        problems.append(
            Problem("code_in_use", "user", item.get("id"), "new_duress_code")
        )
    for field, other in (
        ("new_code", "duress_code_hash"),
        ("new_duress_code", "code_hash"),
    ):
        code = new_codes.get(field)
        stored = item.get(other)
        if not code or not stored or (field == "new_code" and duress):
            continue
        if field == "new_duress_code" and ordinary:
            continue
        if await hass.async_add_executor_job(codes.matches, code, stored):
            # This person's other code: counted like a collision, or it
            # could be probed without limit by whoever edits them.
            collided = True
            problems.append(Problem("code_in_use", "user", item.get("id"), field))
    if collided:
        # A code that is somebody else's is spent like a wrong code (second
        # review, decision 5): the same counter, the same row, the same
        # lockout. The accidental collision of a household choosing codes is
        # one attempt; a series of them is somebody testing codes.
        #
        # Offering one's own duress code as a new code is this and nothing
        # else: a collision, not a use of it, so it raises no `duress` (§8.1).
        await system.async_handle(
            CodeAttempt(
                operation=Operation.EDIT_CONFIG,
                actor=replace(actor, code=CodeResult.INVALID, duress=False),
            )
        )
    if problems:
        connection.send_result(
            msg["id"],
            {"success": False, "problems": [asdict(p) for p in problems]},
        )
        return
    for field, stored in (
        ("new_code", "code_hash"),
        ("new_duress_code", "duress_code_hash"),
    ):
        if field in new_codes:
            item[stored] = await hass.async_add_executor_job(
                codes.hash_code, new_codes[field]
            )

    result = upsert(system.config, system.state, "user", item, now=dt_util.utcnow())
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
        now=dt_util.utcnow(),
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
@websocket_api.async_response
async def ws_propose_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The zone wizard's starting point (§4.4). The user must still confirm it.

    Open to whoever may edit the configuration (§8.3), like the save it
    prepares: gated on the administrator alone, a person holding edit_config
    could open the Zones page and never add a zone (third review).
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
        is None
    ):
        return
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


# --- the API contract (§9.2.2, decision 122) ----------------------------------------

# The copy that travels with the integration: docs/ is not installed by HACS.
# A test keeps it identical to docs/api/openapi.yaml.
API_DOCUMENT = Path(__file__).parent / "openapi.yaml"


@websocket_api.websocket_command({vol.Required("type"): "foyer/api/document"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_api_document(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The OpenAPI document, for the administrators' API page.

    Over the authenticated WebSocket and nowhere else: a documentation page
    served to anybody would tell a scanner that an alarm lives here.
    """
    text = await hass.async_add_executor_job(API_DOCUMENT.read_text, "utf-8")
    connection.send_result(msg["id"], {"document": text})


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
            # One flag per help page: bounded, because this is written to
            # a store file by whoever holds any account (third review).
            vol.Optional("help"): vol.All(
                {vol.All(str, vol.Length(max=64)): bool}, vol.Length(max=64)
            ),
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
    # Only the rows a glance may find (§8.1, decision 133): what the
    # Overview's recent events ask for, on the tablet a duress code may have
    # been typed at. The log page and an export never ask.
    vol.Optional("glance"): bool,
}


def _filters(msg: dict[str, Any]) -> dict[str, Any]:
    """The filters the panel sent, parsed. A date that cannot be read is
    dropped rather than guessed at: a wrong window hides rows silently."""
    out: dict[str, Any] = {}
    for key in ("start", "end"):
        if value := msg.get(key):
            parsed = _lenient_datetime(value)
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
        "glance",
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
    # A duress code used to empty the log raised its `duress` at the gate,
    # and that row was queued before the clear it came with. Written again
    # after the clear, beside "log cleared", or the request would erase the
    # one record that the person asking was not free to refuse (§8.1).
    raised: list[LogRow] = []
    if (
        await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
            purpose=Purpose.CLEAR_LOG,
            raised=raised,
        )
    ) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    await system.log.async_flush()
    removed = await system.log.async_clear(
        keep=raised, settings=system.config.settings.log
    )
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="log_cleared",
                kind="log",
                user_id=(me := _me(system, connection))[0],
                user_name=me[1],
                channel=CHANNEL_HA_UI,
                changes={"removed": removed},
            ),
        )
    )
    connection.send_result(msg["id"], {"success": True, "removed": removed})


# --- personal data in the log (SPEC §10.4) -----------------------------------

# The three commands of §10.4, and they are not equally weighted (part 2
# decision 3). Export is a read of the log and asks for `view_log`; erasing a
# person's history is an operation on people and asks for `manage_users` and a
# code; switching timed pseudonymisation on is a change to the installation and
# goes through the settings, with `edit_config` and a code, like every other.
#
# What follows from that, and what `docs/privacy.md` says in as many words: a
# subject access request made by somebody who is not an administrator of this
# installation goes through whoever is. In a household that is the person who
# set it up; in a B&B or a small office it is an arrangement somebody has to
# make, and the documentation is where that is said rather than left to be
# discovered.


def _person(
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> PersonRef | None:
    ref = person_ref(system.config, msg["user_id"])
    if ref is None:
        connection.send_error(msg["id"], "unknown_user", "no such person")
        return None
    return ref


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/privacy/preview",
        vol.Required("user_id"): str,
    }
)
@websocket_api.async_response
async def ws_privacy_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """How many rows an erasure would touch, and which key found them.

    Shown before anybody presses the button (part 2 decision 12): a row
    written before this person was a Foyer user, or under a name they have
    since changed, is found by the name and not by the id, and whoever is
    about to erase somebody should see that rather than trust it.
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
            need_code=False,
        )
    ) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    if (ref := _person(system, connection, msg)) is None:
        return
    counts = await system.log.async_person_count(ref)
    connection.send_result(msg["id"], counts)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/privacy/export",
        vol.Required("user_id"): str,
        vol.Required("format"): vol.In(["csv", "json"]),
    }
)
@websocket_api.async_response
async def ws_privacy_export(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """One person's rows, in a readable format, for a subject access request.

    A second caller of the export of §10.3, not a second export: the same two
    formats, the same columns, the same "this came back cut short" answer. What
    differs is the selection, which is wide on purpose (part 2 decision 7) —
    the rows where this person is the subject rather than the actor are their
    personal data too.
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
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    if (ref := _person(system, connection, msg)) is None:
        return
    result = await system.log.async_person_rows(ref)
    rows = result["rows"]
    content = export_csv(rows) if msg["format"] == "csv" else export_json(rows)
    stamp = dt_util.now().strftime("%Y%m%d-%H%M")
    connection.send_result(
        msg["id"],
        {
            # Named after the person, because the file is handed to them and a
            # folder of "foyer-log-20260920" files is a file nobody can give
            # to anybody.
            "filename": f"foyer-{_slug(system.config.user(ref.user_id))}-{stamp}"
            f".{msg['format']}",
            "content": content,
            "rows": len(rows),
            "total": result["total"],
            "truncated": result["total"] > len(rows),
        },
    )


def _slug(user: User | None) -> str:
    name = (user.name if user else "") or "person"
    kept = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return kept or "person"


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/privacy/erase",
        vol.Required("user_id"): str,
        # Erasing is erasing unless whoever performs it asks for the other
        # thing (part 2 decision 1): a stable identifier keeps "the same
        # person on both nights" and is therefore not forgetting them.
        vol.Optional("pseudonymise", default=False): bool,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_privacy_erase(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Take a person out of the log, leaving every event where it is.

    The operation §10.4 exists for, and the one it insists is *not* deleting a
    user: ``user_name`` is denormalised precisely so that deleting a user does
    not erase the history of what they did, which is right for audit and wrong
    for erasure.

    It is itself recorded, and the row does not name the person (part 2
    decision 2). Deleting the whole log is an ``edit_config`` operation and is
    logged (§10.3), and the same rule here would produce a row that names the
    person who was just erased — an erasure that leaves the name it removed
    has not happened.
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
            permission=Permission.MANAGE_USERS,
            purpose=Purpose.ERASE_PERSON,
        )
    ) is None:
        return
    if system.log is None:
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    if (ref := _person(system, connection, msg)) is None:
        return
    pseudonym = ref.pseudonym if msg["pseudonymise"] else None
    try:
        removed = await system.log.async_erase_person(ref, pseudonym=pseudonym)
    except LogUnavailable:
        # A configuration save reloads the entry and closes the database. Say
        # so, rather than answer success and record an erasure that did not
        # happen.
        connection.send_error(msg["id"], "no_log", "the event log is not available")
        return
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="history_erased",
                kind="log",
                # No item_id and no name: both would point straight back at
                # the person this row exists because of.
                user_id=actor.user_id,
                user_name=(
                    named.name if (named := system.config.user(actor.user_id)) else None
                ),
                channel=CHANNEL_HA_UI,
                changes={"rows": removed, "pseudonymised": bool(pseudonym)},
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
            purpose=Purpose.EXPORT_CONFIG,
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
        actor := await _gate(
            hass,
            system,
            connection,
            msg,
            operation=Operation.EDIT_CONFIG,
            permission=Permission.EDIT_CONFIG,
            purpose=Purpose.IMPORT_CONFIG,
        )
    ) is None:
        return
    result = restore(system, msg["document"])
    if (
        result.config is not None
        and touches_people(system.config, result.config)
        and _refuse_people(system, connection, msg["id"], actor)
    ):
        return
    await _apply(
        hass, connection, msg["id"], system, result, operation="restore", kind="config"
    )


def _refuse_people(
    system: FoyerSystem,
    connection: websocket_api.ActiveConnection,
    msg_id: int,
    actor: Actor,
) -> bool:
    """Refuse, and say so, a bulk write that brings people or tags with it
    to somebody without `manage_users` (decision 111). The code has already
    been checked by the gate in front of the command. True when refused."""
    reason = _may_configure(
        system,
        actor,
        Operation.EDIT_CONFIG,
        Permission.MANAGE_USERS,
        need_code=False,
    )
    if reason is None:
        return False
    # A refusal is a row of its own (§10.2), as _gate writes one.
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation="refused",
                kind=Operation.EDIT_CONFIG.value,
                user_id=actor.user_id,
                user_name=(
                    named.name if (named := system.config.user(actor.user_id)) else None
                ),
                channel=CHANNEL_HA_UI,
                changes={"reason": reason.value},
            ),
        )
    )
    connection.send_result(
        msg_id,
        {
            "success": False,
            "reason": reason.value,
            "problems": [asdict(Problem(reason.value, "code", None, "code"))],
        },
    )
    return True


# --- bringing an Alarmo configuration across (SPEC §20.2) -------------------------
#
# A preview, then an apply, the shape the erasure of §10.4 already uses: what
# would be created and what could not be brought across are on the screen
# before anything is written, and the apply is refused if anything the
# preview was computed from has changed since (part 3 decision 2).


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/alarmo/preview",
        # The words new areas and scenarios are named with, from the panel's
        # translations; checked field by field, and never more than names.
        vol.Optional("labels"): dict,
    }
)
@websocket_api.async_response
async def ws_alarmo_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """What an import would do. Reads, writes nothing, so asks no code."""
    if (system := _system(hass, connection, msg["id"])) is None:
        return
    if (
        actor := await _gate(
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
    result, answer = await async_alarmo_plan(hass, system, msg.get("labels"))
    # The preview names the people it would bring in, and people are
    # manage_users' (decision 111): whoever may not apply them may not read
    # them either (fix phase).
    if (
        result is not None
        and result.counts["people"]
        and _refuse_people(system, connection, msg["id"], actor)
    ):
        return
    connection.send_result(msg["id"], answer)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "foyer/alarmo/apply",
        vol.Required("fingerprint"): str,
        vol.Optional("labels"): dict,
        vol.Optional("code"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_alarmo_apply(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Store what the preview showed, and nothing it did not.

    A configuration change like any other: ``edit_config`` with a code, the
    same validation, the same refusal while an area it would change is armed,
    the same row in the log. It creates people too, so it also needs the
    permission that owns people — as saving a tag does.
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
            permission=Permission.EDIT_CONFIG,
            purpose=Purpose.IMPORT_ALARMO,
        )
    ) is None:
        return
    result, answer = await async_alarmo_plan(hass, system, msg.get("labels"))
    if result is None:
        connection.send_result(msg["id"], answer)
        return
    # A save from another tab reloads the entry while the file is read; the
    # plan would then be computed against a configuration and an alarm state
    # that are no longer the installation's, and would overwrite that save.
    if answer["fingerprint"] != msg["fingerprint"] or hass.data.get(DOMAIN) is not (
        system
    ):
        connection.send_result(
            msg["id"],
            {"success": False, "refused": {"code": "changed", "params": {}}},
        )
        return
    if result.counts["people"] and _refuse_people(system, connection, msg["id"], actor):
        return
    if answer["problems"]:
        connection.send_result(
            msg["id"], {"success": False, "problems": answer["problems"]}
        )
        return
    await _apply(
        hass,
        connection,
        msg["id"],
        system,
        EditResult(result.config),
        operation="import",
        kind="alarmo",
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
            purpose=Purpose.SIMULATE,
            need_code=False,
        )
    ) is None:
        return
    start = _lenient_datetime(msg.get("start") or "") or dt_util.utcnow()
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
