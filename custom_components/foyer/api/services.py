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

**``walk_test`` and ``test_action`` are here now.** They were deliberately
absent until Phase 3 built them (decision 86), because a service that exists
and does nothing answers a caller with silence, and in an alarm system silence
is the answer that gets mistaken for success. Both are ``code required`` in
§8.2 and carry the permissions ``walk_test`` and ``test_actions`` of §8.3.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .. import i18n
from ..const import ACK_PATHS, CHANNEL_API, DOMAIN
from ..core.journal import security_row
from ..core.models import (
    ARMED_HA_STATES,
    MAX_BYPASS_SECONDS,
    MAX_WALK_TEST_TIMEOUT,
    MIN_WALK_TEST_TIMEOUT,
    AcknowledgeIncident,
    AcknowledgeTechnical,
    Actor,
    ArmAreaRequest,
    ArmModeRequest,
    ArmRequest,
    BypassZone,
    CodeAttempt,
    DisarmRequest,
    Operation,
    Permission,
    Purpose,
    Reason,
    WalkTestRequest,
)
from ..runtime import notices
from ..runtime.system import FoyerSystem
from ..security.devices import Requester, async_requester
from ..store.editing import touches_people
from .backup import async_write, backup_document, restore

SERVICE_ARM = "arm"
SERVICE_DISARM = "disarm"
SERVICE_BYPASS_ZONE = "bypass_zone"
SERVICE_UNBYPASS_ZONE = "unbypass_zone"
SERVICE_ACKNOWLEDGE = "acknowledge"
SERVICE_EXPORT_LOG = "export_log"
SERVICE_EXPORT_CONFIG = "export_config"
SERVICE_IMPORT_CONFIG = "import_config"
SERVICE_WALK_TEST = "walk_test"
SERVICE_TEST_ACTION = "test_action"

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
        vol.Optional("seconds"): vol.Any(
            vol.All(int, vol.Range(min=1, max=MAX_BYPASS_SECONDS)), None
        ),
        **_IDENTITY,
    }
)
UNBYPASS_SCHEMA = vol.Schema({vol.Required("zone_id"): cv.string, **_IDENTITY})
ACKNOWLEDGE_SCHEMA = vol.Schema(
    {
        vol.Optional("target", default="incident"): vol.In(["incident", "technical"]),
        # Which of the four paths of §7.2 this is, and who the notification
        # had gone to. Both are recorded, neither grants anything: a caller
        # that says "push" gets the authorisation of the channel it is
        # actually on, exactly as a claimed ``user_id`` does (decision 88).
        vol.Optional("via", default="acknowledge"): vol.In(ACK_PATHS),
        vol.Optional("contact_id"): vol.Any(cv.string, None),
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
WALK_TEST_SCHEMA = vol.Schema(
    {
        vol.Required("enable"): cv.boolean,
        # Shorter than the installation's maximum, never longer: §5.3 calls
        # the auto-exit mandatory and non-disableable (part 2 decision 5).
        vol.Optional("duration"): vol.Any(
            vol.All(
                int, vol.Range(min=MIN_WALK_TEST_TIMEOUT, max=MAX_WALK_TEST_TIMEOUT)
            ),
            None,
        ),
        **_IDENTITY,
    }
)
TEST_ACTION_SCHEMA = vol.Schema(
    {
        vol.Exclusive("action_id", "target"): cv.string,
        vol.Exclusive("service", "target"): cv.string,
        # The other half of §11.4: the button beside a contact's channel.
        vol.Exclusive("contact_id", "target"): cv.string,
        vol.Optional("channel_id"): cv.string,
        vol.Optional("profile_id"): cv.string,
        vol.Optional("message", default=""): cv.string,
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
        account=call.context.user_id,
    )


# How often one undeclared device may write a row. A person pressing keys
# produces a handful; an adapter stuck in a loop produces thousands, and a
# thousand identical rows bury the `security` category that somebody actually
# reads — the same reasoning §10.2 applies to zone activity.
_REPORT_EVERY = timedelta(minutes=1)
_REPORTED = f"{DOMAIN}_reported_devices"
_MAX_REPORTED = 20


def _plain(ref: str | None) -> str:
    """A name the sender chose, fit to sit in a notification's markdown.

    Shown as code, so `[Re-authenticate](https://…)` reads as the text it is
    and not as a link inside a Foyer security notice (second review).
    """
    text = " ".join((ref or "?").replace("`", "'").split())[:64]
    return f"`{text}`"


async def async_report_unknown_device(
    hass: HomeAssistant,
    system: FoyerSystem,
    *,
    channel: str,
    ref: str | None,
    wrong_transport: bool = False,
) -> None:
    """Record and show a device that tried to command and is not declared.

    One notification per device, not one per message: a keypad configured with
    the wrong name retries, and a hundred notifications are read exactly as
    carefully as none. The row underneath is rate-limited for the same reason
    and no further: it is written the first time, then at most once a minute
    per device, so a broken adapter leaves a legible trail instead of burying
    the category in which it sits.

    ``wrong_transport`` is a keypad of the device endpoint named on another
    path (decision 98). Whoever sent it was told exactly what an unknown
    device is told; the household is told the truth — somebody used the name
    of a keypad that only speaks with its token, and the token is the point.
    """
    seen: dict[str, datetime] = hass.data.setdefault(_REPORTED, {})
    key = f"{channel}:{ref or ''}"
    now = dt_util.utcnow()
    recently = seen.get(key)
    if recently is not None and now - recently < _REPORT_EVERY:
        # Not refreshed here: a sender retrying every fifty seconds must
        # leave a row a minute, not one row in total (found in review).
        return
    # The names are the sender's to choose, so the memory of them is kept
    # to what a minute of reports can need.
    for stale in [k for k, at in seen.items() if now - at >= _REPORT_EVERY]:
        del seen[stale]
    busy = sum(1 for k in seen if k.startswith(f"{channel}:"))
    if busy >= _MAX_REPORTED and not wrong_transport:
        # A sender rotating invented names would otherwise write a row and a
        # notification for each (second review). Past this many distinct
        # names in a minute on this channel the rest are not recorded one by
        # one — except the name of a keypad that speaks only with its token,
        # which is never lost in the noise somebody made first.
        return
    seen[key] = now
    system.async_record(
        (
            security_row(
                dt_util.utcnow(),
                event_type="device_rejected",
                channel=channel,
                device_id=ref,
                # The default, `blocked`: an outcome the log's filter and words
                # know. Why is the row's event type.
                detail={
                    "reason": Reason.DEVICE_NOT_REGISTERED.value,
                    "device": ref or "",
                    "channel": channel,
                    **({"wrong_transport": "true"} if wrong_transport else {}),
                },
            ),
        )
    )
    strings = await hass.async_add_executor_job(i18n.load_strings, system.language)
    key = "device_wrong_transport" if wrong_transport else "device_rejected"
    notices.async_create(
        hass,
        i18n.translate(strings, f"notification.{key}.message", device=_plain(ref)),
        title=i18n.translate(strings, f"notification.{key}.title"),
        # One per channel, replaced by the next: keyed by the name the sender
        # chose, a sender inventing names could add notifications without
        # end. The rows keep every name the log has room for.
        notification_id=f"foyer_device_{channel}_{key}",
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
        # Filed under the transport, never under the channel the message
        # claimed: a caller that may not choose its channel may not choose
        # which counter the refusal is recorded against either.
        await async_report_unknown_device(
            hass,
            system,
            channel=CHANNEL_API,
            ref=call.data.get("device_id"),
            wrong_transport=requester.wrong_transport,
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
        kind = (
            AcknowledgeIncident
            if call.data["target"] == "incident"
            else AcknowledgeTechnical
        )
        event: Any = kind(
            actor, via=call.data["via"], contact_id=call.data.get("contact_id")
        )
        return await _answer(hass, system, call, requester, event)

    async def walk_test(call: ServiceCall) -> ServiceResponse:
        """Enter or leave the walk test (§9.1, §11.3).

        A state-changing request, so it goes through the engine like arming:
        §8.2's "enter walk test" and §8.3's ``walk_test`` permission are
        resolved there and nowhere else (INV-2).
        """
        system = _system(hass)
        requester = await _requester(hass, system, call)
        event = WalkTestRequest(
            call.data["enable"],
            requester.actor or Actor(),
            duration=call.data.get("duration"),
        )
        return await _answer(hass, system, call, requester, event)

    async def test_action(call: ServiceCall) -> ServiceResponse:
        """Really execute one action, and record it as a test (§11.4).

        Gated here rather than by the engine because it changes no alarm
        state — the same place the configuration services are gated, and for
        the same reason. It really runs: that is the point.
        """
        system = _system(hass)
        requester = await _requester(hass, system, call)
        refused = await _refused(
            system, requester, Operation.TEST_ACTION, Permission.TEST_ACTIONS
        )
        if refused is not None:
            return refused
        return await system.async_test_action(
            profile_id=call.data.get("profile_id"),
            action_id=call.data.get("action_id"),
            service=call.data.get("service"),
            contact_id=call.data.get("contact_id"),
            channel_id=call.data.get("channel_id"),
            message=call.data["message"],
            actor=requester.actor,
        )

    async def export_log(call: ServiceCall) -> ServiceResponse:
        from ..store.log_store import export_csv, export_json

        system = _system(hass)
        requester = await _requester(hass, system, call)
        # A read, like the panel's own log page: the permission decides, the
        # code does not. §8.2 asks for a code to *edit* the configuration, and
        # the WebSocket command behind page 10 asks for none either — two
        # answers to one question is how one of them ends up being the wrong
        # one.
        refused = await _refused(
            system,
            requester,
            Operation.EDIT_CONFIG,
            Permission.VIEW_LOG,
            need_code=False,
            purpose=Purpose.EXPORT_LOG,
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
        refused = await _refused(
            system,
            requester,
            Operation.EDIT_CONFIG,
            Permission.EDIT_CONFIG,
            purpose=Purpose.EXPORT_CONFIG,
        )
        if refused is not None:
            return refused
        return {"success": True, "document": backup_document(system.config)}

    async def import_config(call: ServiceCall) -> ServiceResponse:
        system = _system(hass)
        requester = await _requester(hass, system, call)
        refused = await _refused(
            system,
            requester,
            Operation.EDIT_CONFIG,
            Permission.EDIT_CONFIG,
            purpose=Purpose.IMPORT_CONFIG,
        )
        if refused is not None:
            return refused
        assert requester.actor is not None
        result = restore(system, call.data["document"])
        if result.config is not None and touches_people(system.config, result.config):
            # People and tags are manage_users' (decision 111); the code was
            # checked above, and spent there: offered to the engine again, a
            # duress code would raise `duress` twice for one call (§8.1).
            refused = await _refused(
                system,
                requester,
                Operation.EDIT_CONFIG,
                Permission.MANAGE_USERS,
                need_code=False,
                attempt=False,
            )
            if refused is not None:
                return refused
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

    async def _refused(
        system: FoyerSystem,
        requester: Requester,
        operation: Operation,
        permission: Permission,
        *,
        need_code: bool = True,
        purpose: str | None = None,
        attempt: bool = True,
    ) -> ServiceResponse | None:
        """The gate for the services that read or write the configuration.

        The state-changing services are gated by the engine, which is the one
        place §8.2 and §8.3 are resolved for them (part 1). These three never
        reach the engine, so they ask core/authz the panel's question — with
        no administrator in it: a service call is not the admin path of §8.4,
        so the permission bites in full.

        ``purpose`` is the service's own name where §8.2's operation does not
        say what it is — a `duress` row names the log export, not "the
        configuration" (decision 134). ``attempt`` is False for a second
        question about a code already spent in the same call.
        """
        from ..core import authz

        if requester.actor is None:
            assert requester.reason is not None
            if requester.wrong_transport and requester.device is not None:
                # Decision 98 on every service, not only the ones that reach
                # the engine: an endpoint keypad's name is refused, recorded
                # and notified wherever it is used.
                await async_report_unknown_device(
                    hass,
                    system,
                    channel=CHANNEL_API,
                    ref=requester.device.ref,
                    wrong_transport=True,
                )
            return system.refusal(requester.reason)
        actor = requester.actor
        now = dt_util.utcnow()
        # Counted through the engine, like every other wrong code (§8.4,
        # found in review): these services verify their own and never reach
        # `decide()`, so a script could try codes here for ever without a
        # counter ever reaching its limit.
        if attempt:
            spent = await system.async_handle(
                CodeAttempt(operation=operation, actor=actor, purpose=purpose)
            )
            if spent.reason is not None:
                return {"success": False, "reason": spent.reason.value}
        # core/authz decides, as it does for the panel. A claimed `user_id`
        # grants nothing here (decision 102); before the first code exists
        # an automation may read and write the configuration (decision 78).
        reason = authz.may_configure(
            system.config,
            actor,
            operation,
            permission,
            now,
            need_code=need_code,
            open_while_inert=True,
        )
        if reason is not None:
            return {"success": False, "reason": reason.value}
        return None

    for name, handler, schema in (
        (SERVICE_ARM, arm, ARM_SCHEMA),
        (SERVICE_DISARM, disarm, DISARM_SCHEMA),
        (SERVICE_BYPASS_ZONE, bypass_zone, BYPASS_SCHEMA),
        (SERVICE_UNBYPASS_ZONE, unbypass_zone, UNBYPASS_SCHEMA),
        (SERVICE_ACKNOWLEDGE, acknowledge, ACKNOWLEDGE_SCHEMA),
        (SERVICE_WALK_TEST, walk_test, WALK_TEST_SCHEMA),
        (SERVICE_TEST_ACTION, test_action, TEST_ACTION_SCHEMA),
        (SERVICE_EXPORT_LOG, export_log, EXPORT_LOG_SCHEMA),
        (SERVICE_EXPORT_CONFIG, export_config, EXPORT_CONFIG_SCHEMA),
        (SERVICE_IMPORT_CONFIG, import_config, IMPORT_CONFIG_SCHEMA),
    ):
        hass.services.async_register(
            DOMAIN,
            name,
            _raising(hass, handler),
            schema=schema,
            supports_response=SupportsResponse.OPTIONAL,
        )


def _raising(hass: HomeAssistant, handler):
    """A refusal the caller will not read is raised, not returned.

    An automation that calls `foyer.disarm` without asking for the response
    would otherwise take a wrong code, a lockout or an open window for
    success, and carry on as if the house were disarmed (second review,
    decision 2). A caller that asks for the response gets the structured
    result of §9.1, refusal and all, exactly as before.
    """

    async def call(service: ServiceCall) -> ServiceResponse:
        result = await handler(service)
        if service.return_response or not isinstance(result, dict):
            return result
        if result.get("success") is False:
            reason = str(result.get("reason") or "")
            if not reason:
                # A configuration edit refused by validation answers with
                # problems and no reason; the first problem's code is the
                # reason, not "?" (third review).
                problems = result.get("problems") or ()
                first = next((p for p in problems if isinstance(p, dict)), None)
                reason = str((first or {}).get("code") or "")
            names = [
                str(z.get("name") or z.get("id"))
                for z in result.get("blocking_zones") or ()
                if isinstance(z, dict)
            ]
            if reason in _REASONS:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key=f"rejected_{reason}",
                    translation_placeholders={"zones": ", ".join(names)},
                )
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_refused",
                translation_placeholders={"reason": reason or "?"},
            )
        return None

    return call


_REASONS = frozenset(r.value for r in Reason)


def _log_filters(data: dict[str, Any]) -> dict[str, Any]:
    """The filters a caller sent, parsed. A date that cannot be read is
    dropped rather than guessed at: a wrong window hides rows silently."""
    out: dict[str, Any] = {}
    for key in ("start", "end"):
        if value := data.get(key):
            try:
                parsed = dt_util.parse_datetime(value)
            except ValueError:
                # "2026-99-01" is shaped like a date and is not one: Home
                # Assistant raises rather than answering None (second review).
                parsed = None
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
        SERVICE_WALK_TEST,
        SERVICE_TEST_ACTION,
        SERVICE_EXPORT_LOG,
        SERVICE_EXPORT_CONFIG,
        SERVICE_IMPORT_CONFIG,
    ):
        hass.services.async_remove(DOMAIN, name)
