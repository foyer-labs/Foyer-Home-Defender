"""The ``foyer.*`` services (SPEC §9.1, §14.1).

The channel an adapter reaches Foyer through when it has no WebSocket and no
broker: a Home Assistant automation, a blueprint, a shell command, anything
that can call a service. Every state-changing service takes ``code``,
``user_id``, ``channel`` and ``device_id`` and answers with the structured
result of §9.1 — the same object the WebSocket commands return, built by the
same function, because a keypad adapter that got two different shapes from two
paths would have to guess which one it was holding.

Three rules this module keeps and never bends.

**Nothing decides here.** A service builds an Actor and hands an event to the
engine, exactly as the panel does (INV-2). The code is compared in
``security/``; the permission, the policy and the lockout are resolved in
``core/authz``; this file does neither.

**A device commands only if it is declared** (part 2 decision 1). An unknown
``device_id`` is refused before the code is even looked at, recorded under
``security``, and raised as a Home Assistant notification so that a keypad
somebody set up with the wrong name is a visible problem rather than a silent
one.

**``walk_test`` and ``test_action`` are not here.** §14.1 lists them and Phase
3 builds them. A service that exists and does nothing answers a caller with
silence, and in an alarm system silence is the answer that gets mistaken for
success.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .. import i18n
from ..const import CHANNEL_API, DOMAIN
from ..core.journal import security_row
from ..core.models import (
    ARMED_HA_STATES,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    Actor,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    CodeResult,
    DisarmRequest,
    Operation,
    Permission,
    Reason,
)
from ..runtime.system import FoyerSystem
from ..security.devices import Requester, async_requester
from .backup import async_write, backup_document, restore

SERVICE_ARM = "arm"
SERVICE_DISARM = "disarm"
SERVICE_BYPASS_ZONE = "bypass_zone"
SERVICE_UNBYPASS_ZONE = "unbypass_zone"
SERVICE_ACKNOWLEDGE = "acknowledge"
SERVICE_EXPORT_LOG = "export_log"
SERVICE_EXPORT_CONFIG = "export_config"
SERVICE_IMPORT_CONFIG = "import_config"

# One export carries what a caller can reasonably hold in one response.
MAX_EXPORT_ROWS = 10000

# What every state-changing service accepts (§9.1). ``channel`` is honoured
# only for the channels a caller may claim without a device behind it; the
# rest come from the device register, or the request is refused.
_IDENTITY = {
    vol.Optional("code"): vol.Any(cv.string, None),
    vol.Optional("user_id"): vol.Any(cv.string, None),
    vol.Optional("channel"): vol.Any(cv.string, None),
    vol.Optional("device_id"): vol.Any(cv.string, None),
}

ARM_SCHEMA = vol.Schema(
    {
        vol.Exclusive("scenario_id", "target"): cv.string,
        vol.Exclusive("scenario_name", "target"): cv.string,
        vol.Exclusive("area_id", "target"): cv.string,
        vol.Exclusive("mode", "target"): vol.In(ARMED_HA_STATES),
        vol.Optional("force", default=False): cv.boolean,
        vol.Optional("skip_exit_delay", default=False): cv.boolean,
        **_IDENTITY,
    }
)
DISARM_SCHEMA = vol.Schema(
    {vol.Optional("area_ids"): vol.All(cv.ensure_list, [cv.string]), **_IDENTITY}
)
BYPASS_SCHEMA = vol.Schema(
    {
        vol.Required("zone_id"): cv.string,
        vol.Optional("seconds"): vol.Any(vol.All(int, vol.Range(min=1)), None),
        **_IDENTITY,
    }
)
UNBYPASS_SCHEMA = vol.Schema({vol.Required("zone_id"): cv.string, **_IDENTITY})
ACKNOWLEDGE_SCHEMA = vol.Schema(
    {
        vol.Optional("target", default="incident"): vol.In(["incident", "technical"]),
        **_IDENTITY,
    }
)
# `user_id` is missing from the filters on purpose: it is already one of the
# identity fields of §9.1, and one name meaning "who is calling" in one place
# and "whose rows to return" in another is how an export quietly comes back
# filtered. Filtering the log by person is the panel's, and page 10 does it.
EXPORT_LOG_SCHEMA = vol.Schema(
    {
        vol.Optional("format", default="json"): vol.In(["csv", "json"]),
        vol.Optional("start"): vol.Any(cv.string, None),
        vol.Optional("end"): vol.Any(cv.string, None),
        vol.Optional("categories"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("severity"): vol.Any(cv.string, None),
        vol.Optional("area_id"): vol.Any(cv.string, None),
        vol.Optional("zone_id"): vol.Any(cv.string, None),
        vol.Optional("incident_id"): vol.Any(cv.string, None),
        vol.Optional("outcome"): vol.Any(cv.string, None),
        **_IDENTITY,
    }
)
EXPORT_CONFIG_SCHEMA = vol.Schema(_IDENTITY)
IMPORT_CONFIG_SCHEMA = vol.Schema({vol.Required("document"): dict, **_IDENTITY})


def _system(hass: HomeAssistant) -> FoyerSystem:
    system = hass.data.get(DOMAIN)
    if system is None:
        raise HomeAssistantError("Foyer is not loaded")
    return system


async def _requester(hass: HomeAssistant, system: FoyerSystem, call: ServiceCall):
    """Who is calling, or why they are refused before anything happens."""
    return await async_requester(
        hass,
        system.config,
        transport=CHANNEL_API,
        ref=call.data.get("device_id"),
        code=call.data.get("code"),
        channel=call.data.get("channel"),
        user_id=call.data.get("user_id"),
    )


async def async_report_unknown_device(
    hass: HomeAssistant, system: FoyerSystem, *, channel: str, ref: str | None
) -> None:
    """Record and show a device that tried to command and is not declared.

    One notification per device, not one per message: a keypad configured with
    the wrong name retries every few seconds, and a hundred notifications are
    read exactly as carefully as none. The row underneath is written every
    time, because the log is where the count belongs.
    """
    system.async_record(
        (
            security_row(
                dt_util.utcnow(),
                event_type="device_rejected",
                channel=channel,
                device_id=ref,
                outcome=Reason.DEVICE_NOT_REGISTERED.value,
                detail={"device": ref or "", "channel": channel},
            ),
        )
    )
    strings = await hass.async_add_executor_job(i18n.load_strings, system.language)
    persistent_notification.async_create(
        hass,
        i18n.translate(
            strings, "notification.device_rejected.message", device=ref or "?"
        ),
        title=i18n.translate(strings, "notification.device_rejected.title"),
        # Keyed by the device, so the same one retrying replaces its own
        # notification instead of adding a hundred nobody reads.
        notification_id=f"foyer_device_{channel}_{ref}",
    )


async def _answer(
    hass: HomeAssistant,
    system: FoyerSystem,
    call: ServiceCall,
    requester: Requester,
    event: Any,
) -> ServiceResponse:
    """Hand the event to the engine, or answer the refusal in the same shape."""
    if requester.actor is None:
        assert requester.reason is not None
        await async_report_unknown_device(
            hass,
            system,
            channel=call.data.get("channel") or CHANNEL_API,
            ref=call.data.get("device_id"),
        )
        return system.refusal(requester.reason)
    decision = await system.async_handle(event)
    return system.result(decision)


def async_register(hass: HomeAssistant) -> None:
    """Register every service of §14.1 this phase owns."""

    async def arm(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        actor = requester.actor or Actor()
        force = call.data["force"]
        skip = call.data["skip_exit_delay"]
        scenario_id = call.data.get("scenario_id")
        if (name := call.data.get("scenario_name")) is not None:
            found = next(
                (s for s in system.config.scenarios if s.name == name),
                None,
            )
            # An unknown name is not silently an unknown id: the engine
            # answers `unknown_scenario` either way, and says so.
            scenario_id = found.id if found else name
        if "area_id" in call.data:
            event: Any = ArmAreaRequest(call.data["area_id"], actor, force, skip)
        elif "mode" in call.data:
            event = ArmModeRequest(call.data["mode"], actor, force, skip)
        else:
            event = ArmRequest(scenario_id or "", actor, force, skip)
        return await _answer(hass, system, call, requester, event)

    async def disarm(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        area_ids = call.data.get("area_ids")
        event = DisarmRequest(
            tuple(area_ids) if area_ids else None, requester.actor or Actor()
        )
        return await _answer(hass, system, call, requester, event)

    async def bypass_zone(call: ServiceCall) -> ServiceResponse:
        return await _bypass(call, bypass=True)

    async def unbypass_zone(call: ServiceCall) -> ServiceResponse:
        return await _bypass(call, bypass=False)

    async def _bypass(call: ServiceCall, *, bypass: bool) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        event = BypassZone(
            zone_id=call.data["zone_id"],
            bypass=bypass,
            seconds=call.data.get("seconds"),
            actor=requester.actor or Actor(),
        )
        return await _answer(hass, system, call, requester, event)

    async def acknowledge(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        actor = requester.actor or Actor()
        event: Any = (
            AcknowledgeIncident(actor)
            if call.data["target"] == "incident"
            else AcknowledgeTechnical(actor)
        )
        return await _answer(hass, system, call, requester, event)

    async def export_log(call: ServiceCall) -> ServiceResponse:
        from ..store.log_store import export_csv, export_json

        system = _system(hass)
        requester = await _requester(hass, system, call)
        refused = _refused(
            system, requester, Operation.EDIT_CONFIG, Permission.VIEW_LOG
        )
        if refused is not None:
            return refused
        if system.log is None:
            return {"success": False, "reason": "no_log"}
        await system.log.async_flush()
        result = await system.log.async_query(
            limit=MAX_EXPORT_ROWS, **_log_filters(call.data)
        )
        rows = result["rows"]
        fmt = call.data["format"]
        return {
            "success": True,
            "rows": len(rows),
            "total": result["total"],
            "truncated": result["total"] > len(rows),
            "content": export_csv(rows) if fmt == "csv" else export_json(rows),
        }

    async def export_config(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        refused = _refused(
            system, requester, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
        if refused is not None:
            return refused
        return {"success": True, "document": backup_document(system.config)}

    async def import_config(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        refused = _refused(
            system, requester, Operation.EDIT_CONFIG, Permission.EDIT_CONFIG
        )
        if refused is not None:
            return refused
        assert requester.actor is not None
        result = restore(system, call.data["document"])
        named = system.config.user(requester.actor.user_id)
        return await async_write(
            hass,
            system,
            result,
            operation="restore",
            kind="config",
            channel=requester.actor.channel,
            user_id=requester.actor.user_id,
            user_name=named.name if named else None,
        )

    def _refused(
        system: FoyerSystem,
        requester: Requester,
        operation: Operation,
        permission: Permission,
    ) -> ServiceResponse | None:
        """The gate for the services that read or write the configuration.

        The state-changing services are gated by the engine, which is the one
        place §8.2 and §8.3 are resolved for them (part 1). These three never
        reach the engine, so they ask the same questions here — and, unlike
        the panel, an administrator is not part of the question: a service
        call carries no Home Assistant account to be an administrator of, so
        the permission bites in full.
        """
        from ..core import authz

        if requester.actor is None:
            assert requester.reason is not None
            return system.refusal(requester.reason)
        actor = requester.actor
        now = dt_util.utcnow()
        if actor.code is CodeResult.INVALID:
            return {"success": False, "reason": Reason.BAD_CODE.value}
        user = system.config.user(actor.user_id)
        if user is None:
            # Nobody is behind this call. Before the first code exists that is
            # every call, and the policy is inert (decision 78); once codes
            # are in force, a caller who cannot be named may not read or
            # rewrite the configuration.
            if authz.enforced(system.config, now):
                return {"success": False, "reason": Reason.NOT_PERMITTED.value}
            return None
        if not user.enabled or not user.in_window(now):
            return {"success": False, "reason": Reason.USER_NOT_VALID.value}
        if not user.may(permission):
            return {"success": False, "reason": Reason.NOT_PERMITTED.value}
        if (
            authz.code_required(
                system.config,
                operation,
                now=now,
                user=user,
                identified=actor.identified,
                channel=actor.channel,
            )
            and not actor.code_verified
        ):
            return {"success": False, "reason": Reason.CODE_REQUIRED.value}
        return None

    for name, handler, schema in (
        (SERVICE_ARM, arm, ARM_SCHEMA),
        (SERVICE_DISARM, disarm, DISARM_SCHEMA),
        (SERVICE_BYPASS_ZONE, bypass_zone, BYPASS_SCHEMA),
        (SERVICE_UNBYPASS_ZONE, unbypass_zone, UNBYPASS_SCHEMA),
        (SERVICE_ACKNOWLEDGE, acknowledge, ACKNOWLEDGE_SCHEMA),
        (SERVICE_EXPORT_LOG, export_log, EXPORT_LOG_SCHEMA),
        (SERVICE_EXPORT_CONFIG, export_config, EXPORT_CONFIG_SCHEMA),
        (SERVICE_IMPORT_CONFIG, import_config, IMPORT_CONFIG_SCHEMA),
    ):
        hass.services.async_register(
            DOMAIN,
            name,
            handler,
            schema=schema,
            supports_response=SupportsResponse.OPTIONAL,
        )


def _log_filters(data: dict[str, Any]) -> dict[str, Any]:
    """The filters a caller sent, parsed. A date that cannot be read is
    dropped rather than guessed at: a wrong window hides rows silently."""
    out: dict[str, Any] = {}
    for key in ("start", "end"):
        if value := data.get(key):
            parsed = dt_util.parse_datetime(value)
            if parsed is not None:
                out[key] = dt_util.as_utc(parsed)
    for key in (
        "categories",
        "severity",
        "area_id",
        "zone_id",
        "incident_id",
        "outcome",
    ):
        if data.get(key):
            out[key] = data[key]
    return out


@callback
def async_unregister(hass: HomeAssistant) -> None:
    for name in (
        SERVICE_ARM,
        SERVICE_DISARM,
        SERVICE_BYPASS_ZONE,
        SERVICE_UNBYPASS_ZONE,
        SERVICE_ACKNOWLEDGE,
        SERVICE_EXPORT_LOG,
        SERVICE_EXPORT_CONFIG,
        SERVICE_IMPORT_CONFIG,
    ):
        hass.services.async_remove(DOMAIN, name)
