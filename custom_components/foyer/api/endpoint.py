"""The device endpoint: a keypad that proves who it is (SPEC §9.2.1).

On the broker a keypad is only the name it gives (decision 81). Here it is a
token of its own, and that is the whole of what the token buys: **it
authenticates the device; it does not encrypt anything.** Over plain HTTP the
token and the code typed on the keypad cross the network as readable as over
plain MQTT, so a request in the clear is served and *said* — on every row it
causes, and on page 8 until a request from that keypad arrives encrypted.

Two routes:

``POST /api/foyer/device``
    ``{action, scenario, code}`` with ``Authorization: Bearer <token>``. The
    token names the device; a ``device_id`` in the body is ignored. The answer
    is the structured result of §9.1 with ``last_result`` / ``last_reason``,
    its ``state`` the message of §9.2 at the installation's detail level
    (decision 83) rather than the panel's whole status.

``GET /api/foyer/device/state``
    Server-Sent Events: that same message on connect and on every change, and
    a comment line every thirty seconds so a proxy does not close a quiet
    connection. A stream belongs to its token: a new token, a revoked one, a
    keypad removed, disabled or moved off the endpoint closes it at once.

What stays exactly as it is everywhere else: the request becomes an Actor in
``security/devices.async_requester``, the code is still the identity and
still required by the policy (§8.2), the channel is ``keypad`` (nothing about
the transport identifies a person), and the lockout of §8.4 counts per
device. A wrong or missing token has no device to count against, so it
counts against its source address, through the engine like every other
wrong credential, and is answered 401 with no detail.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
import ipaddress
import json
import logging
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.util import dt as dt_util

from .. import i18n
from ..const import DOMAIN
from ..core import authz
from ..core.models import (
    Actor,
    ArmingDevice,
    CodeAttempt,
    CodeResult,
    Decision,
    DeviceContact,
    DeviceTransport,
    Moment,
    MqttDetail,
    Reason,
)
from ..runtime import notices
from ..runtime.mqtt import (
    RESULT_BLOCKED,
    RESULT_OK,
    UNKNOWN_ACTION,
    as_code,
    command_event,
    result_of,
    state_payload,
)
from ..runtime.system import FoyerSystem
from ..security.devices import TRANSPORT_HTTP, async_requester, device_by_token

_LOGGER = logging.getLogger(__name__)

URL = "/api/foyer/device"
STATE_URL = "/api/foyer/device/state"

# How often a quiet stream says it is still there (§9.2.1). Under the idle
# timeout of every common reverse proxy, which is the only reason it exists.
KEEPALIVE_SECONDS = 30

# Fired whenever something a keypad's stream might show has moved: the
# alarm's state, a keypad's own last answer, a token. Streams listen on the
# bus rather than on the system, because every configuration save replaces
# the system, and a keypad must not be disconnected because somebody renamed
# a zone.
SIGNAL = f"{DOMAIN}_device_endpoint"

# Each keypad's own last answer, for its stream (decision 87). Per keypad,
# not the broker's one retained answer: the hall keypad must never hear that
# the garden keypad's code was wrong.
_LAST = f"{DOMAIN}_device_last"
_REGISTERED = f"{DOMAIN}_device_views"

# At most this much body is read. A keypad's command is a few dozen bytes.
MAX_BODY = 4096

# How many source addresses may hold a bad-token counter of their own. Past
# it, every new address shares one counter: an attacker rotating addresses —
# an IPv6 host has a /64 to rotate through — must not grow the persisted
# state, the log and the notifications without bound (found in review).
MAX_ADDRESS_COUNTERS = 64
OVERFLOW_ADDRESS = "*"

# How long a stream waits for a system that has gone before it closes: long
# enough for the reload every configuration save performs, short enough that
# a token revoked by a reload that then failed is not kept open for ever.
STREAM_ORPHAN_SECONDS = 60

# One bad token at a time goes through the engine, so a burst of concurrent
# requests from one address cannot all pass the lockout check before the
# first of them has been counted.
_BAD_TOKEN_LOCK = f"{DOMAIN}_bad_token_lock"


def _system(hass: HomeAssistant) -> FoyerSystem | None:
    system = hass.data.get(DOMAIN)
    return system if isinstance(system, FoyerSystem) else None


def _bearer(request: web.Request) -> str | None:
    header = request.headers.get("Authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def _address(request: web.Request) -> str:
    """Where the request came from, as Home Assistant established it.

    ``request.remote`` is the peer, rewritten by Home Assistant's own
    forwarded middleware to the client behind a reverse proxy only when that
    proxy is one it trusts — the same judgement it makes for its own login
    bans. A header is never read here: a header is what an attacker writes.

    An IPv6 address counts by its /64: one host holds the whole prefix and
    can pick a new address for every guess.
    """
    remote = request.remote or "unknown"
    try:
        address = ipaddress.ip_address(remote)
    except ValueError:
        return remote
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return str(address.ipv4_mapped)
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return str(address)


def _counted_as(system: FoyerSystem, address: str) -> str:
    """The counter a bad token from this address spends (§9.2.1)."""
    lockouts = system.state.lockouts
    if f"http:{address}" in lockouts:
        return address
    known = sum(1 for key in lockouts if key.startswith("http:"))
    return address if known < MAX_ADDRESS_COUNTERS else OVERFLOW_ADDRESS


def _endpoint_in_use(system: FoyerSystem) -> bool:
    """Whether any enabled keypad speaks on the endpoint at all.

    Where none does, the routes answer 404 as if they did not exist: an
    installation that never chose the endpoint must neither advertise an
    alarm to a scanner nor count strangers' guesses.
    """
    return any(
        d.enabled and d.transport is DeviceTransport.HTTP for d in system.config.devices
    )


def _unauthorised() -> web.Response:
    # No detail at all: whether the token was missing, wrong, revoked or the
    # address is locked out is the one thing a guesser wants to learn.
    return web.Response(status=HTTPStatus.UNAUTHORIZED)


def detail_of(system: FoyerSystem) -> MqttDetail:
    """The one detail level the broker and the endpoint share (decision 83)."""
    return system.config.settings.mqtt.detail


def device_result(
    system: FoyerSystem,
    decision: Decision | None,
    reason: Reason | None,
    last: tuple[str, str | None],
) -> dict[str, Any]:
    """§9.1's structured result, at the detail level of §9.2 (§9.2.1).

    The shape of §9.1 — success, reason, the zones that blocked and the zones
    that were bypassed — with ``last_result`` / ``last_reason`` beside it and
    the §9.2 message as its state. A zone is named only at ``full``, as the
    broker names open zones only at ``full``: below it a keypad is told which
    zones by their opaque id and how many, and nothing that says where the
    house is open to whoever else is listening on a network in the clear.
    """
    detail = detail_of(system)
    names = {z.id: z.name for z in system.config.zones}

    def zones(ids: tuple[str, ...]) -> list[dict[str, str]]:
        if detail is MqttDetail.FULL:
            return [{"id": z, "name": names.get(z, z)} for z in ids]
        return [{"id": z} for z in ids]

    if decision is not None:
        success = decision.accepted
        why = decision.reason.value if decision.reason else None
    else:
        success = last[0] == RESULT_OK
        why = reason.value if reason else last[1]
    return {
        "success": success,
        "reason": None if success else why,
        "blocking_zones": zones(decision.blocking_zones if decision else ()),
        "bypassed_zones": zones(decision.bypassed_zones if decision else ()),
        "low_battery_zones": zones(decision.low_battery_zones if decision else ()),
        "last_result": last[0],
        "last_reason": last[1],
        "state": state_payload(system, detail, last, dt_util.utcnow()),
    }


async def _async_bad_token(
    hass: HomeAssistant, system: FoyerSystem, request: web.Request
) -> None:
    """Count one wrong or missing token against its address (§9.2.1).

    Through the engine, like every wrong credential: the same counter, the
    same `security` rows, the same `lockout` moment a profile can answer —
    a token-guessing loop is a tamper signal like a keypad's. Notified once
    per lockout, not once per request.
    """
    lock = hass.data.setdefault(_BAD_TOKEN_LOCK, asyncio.Lock())
    async with lock:
        address = _counted_as(system, _address(request))
        if authz.address_locked_until(system.state.lockouts, address, dt_util.utcnow()):
            # Locked while this request waited its turn: answered, not
            # counted again.
            return
        decision = await system.async_handle(
            CodeAttempt(
                None,
                actor=Actor(
                    channel="keypad",
                    code=CodeResult.INVALID,
                    address=address,
                    encrypted=request.secure,
                ),
            )
        )
    if Moment.LOCKOUT not in decision.moments:
        return
    strings = await hass.async_add_executor_job(i18n.load_strings, system.language)
    notices.async_create(
        hass,
        i18n.translate(strings, "notification.token_lockout.message", address=address),
        title=i18n.translate(strings, "notification.token_lockout.title"),
        # One notification, replaced by the next lockout rather than added
        # to: a guesser rotating addresses must not be able to bury the
        # notifications that matter under a pile of these.
        notification_id="foyer_token_lockout",
    )


async def _async_authenticate(
    hass: HomeAssistant, request: web.Request
) -> tuple[FoyerSystem | None, ArmingDevice | None, web.Response | None]:
    """The keypad behind this request, or the answer to give instead."""
    system = _system(hass)
    if system is None or system.superseded:
        # A reload, which every configuration save performs. The keypad tries
        # again in a moment, and must not be told its token is wrong; and a
        # system that has already stored a newer configuration — a revoked
        # token, say — must not keep answering from the old one.
        return None, None, web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE)
    if not _endpoint_in_use(system):
        return system, None, web.Response(status=HTTPStatus.NOT_FOUND)
    # The address's own counter, never the shared overflow one: that one
    # stops strangers' guesses from being counted one by one, and must never
    # refuse a keypad whose token is right. Refusing on it let anybody who
    # had filled the sixty-four counters lock every keypad in the house out
    # (second review).
    address = _address(request)
    if authz.address_locked_until(system.state.lockouts, address, dt_util.utcnow()):
        # Answered here, before the engine: a locked address hammering the
        # endpoint must not write a row per request.
        return system, None, _unauthorised()
    device = device_by_token(system.config, _bearer(request))
    if device is None:
        await _async_bad_token(hass, system, request)
        return system, None, _unauthorised()
    if (device.id in system.state.in_clear) == request.secure:
        # Whether this keypad talks in the clear has changed (or was never
        # known): recorded, so page 8's warning is right after a restart.
        await system.async_handle(
            DeviceContact(
                Actor(
                    channel=device.channel,
                    device_id=device.id,
                    encrypted=request.secure,
                )
            )
        )
    return system, device, None


def _remember(
    hass: HomeAssistant, device_id: str, last: tuple[str, str | None]
) -> None:
    hass.data.setdefault(_LAST, {})[device_id] = last
    async_dispatcher_send(hass, SIGNAL)


class DeviceCommandView(HomeAssistantView):
    """``POST /api/foyer/device`` (§9.2.1)."""

    url = URL
    name = "api:foyer:device"
    # Home Assistant's own authentication is not this endpoint's: a keypad
    # holds a token of Foyer's, not an account on the house.
    requires_auth = False
    cors_allowed = False

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        system, device, refusal = await _async_authenticate(hass, request)
        if refusal is not None:
            return refusal
        assert system is not None and device is not None
        data: Any = None
        try:
            raw = b""
            # Read to the end, bounded: one `read(n)` may return only the
            # first segment of a slow keypad's body.
            while len(raw) <= MAX_BODY and (chunk := await request.content.read(1024)):
                raw += chunk
            if len(raw) <= MAX_BODY:
                data = json.loads(raw)
        except (ValueError, RecursionError):
            # RecursionError: a few hundred nested brackets, well inside the
            # size limit, which is not a ValueError.
            data = None
        if not isinstance(data, dict):
            return web.Response(status=HTTPStatus.BAD_REQUEST)
        if str(data.get("action") or "") == "status":
            # Not a command: "tell me again", for a keypad that has just
            # booted — answered with what it was last told.
            last = hass.data.get(_LAST, {}).get(device.id, (RESULT_OK, None))
            answer = device_result(system, None, None, last)
            return self.json({**answer, "success": True, "reason": None})
        requester = await async_requester(
            hass,
            system.config,
            transport=TRANSPORT_HTTP,
            device=device,
            code=as_code(data.get("code")),
            encrypted=request.secure,
        )
        assert requester.actor is not None
        event = command_event(system.config, data, requester.actor)
        if event is None:
            last = (RESULT_BLOCKED, UNKNOWN_ACTION)
            _remember(hass, device.id, last)
            return self.json(device_result(system, None, None, last))
        decision = await system.async_handle(event)
        last = result_of(decision)
        _remember(hass, device.id, last)
        return self.json(device_result(system, decision, None, last))


class DeviceStateView(HomeAssistantView):
    """``GET /api/foyer/device/state``: the §9.2 message as a stream."""

    url = STATE_URL
    name = "api:foyer:device:state"
    requires_auth = False
    cors_allowed = False

    async def get(self, request: web.Request) -> web.StreamResponse:
        hass: HomeAssistant = request.app["hass"]
        system, device, refusal = await _async_authenticate(hass, request)
        if refusal is not None:
            return refusal
        assert system is not None and device is not None
        response = web.StreamResponse(
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                # nginx buffers a response unless told not to, which would
                # hold the countdown back until the buffer filled.
                "X-Accel-Buffering": "no",
            }
        )
        await response.prepare(request)
        await _async_stream(hass, response, device.id, device.token_hash)
        return response


def _still_valid(system: FoyerSystem, device_id: str, token_hash: str | None) -> bool:
    """Whether the keypad this stream was opened for still answers to its token."""
    device = system.config.device(device_id)
    return (
        device is not None
        and device.enabled
        and device.transport is DeviceTransport.HTTP
        and bool(token_hash)
        and device.token_hash == token_hash
    )


async def _async_stream(
    hass: HomeAssistant,
    response: web.StreamResponse,
    device_id: str,
    token_hash: str | None,
) -> None:
    """Write the state on connect, on every change, and a comment when quiet."""
    changed = asyncio.Event()

    @callback
    def wake() -> None:
        changed.set()

    remove = async_dispatcher_connect(hass, SIGNAL, wake)
    sent: str | None = None
    orphaned: float | None = None
    loop = asyncio.get_running_loop()
    try:
        while True:
            system = _system(hass)
            if system is None or system.superseded:
                # Reloading: wait, but not for ever. A reload that failed,
                # or an entry switched off, would otherwise keep a revoked
                # token's connection open until Home Assistant restarts.
                orphaned = orphaned if orphaned is not None else loop.time()
                if loop.time() - orphaned > STREAM_ORPHAN_SECONDS:
                    return
            elif not _still_valid(system, device_id, token_hash):
                # A new token invalidates the old one at once and closes its
                # streams (§9.2.1), and so does a keypad taken away.
                return
            else:
                orphaned = None
                last = hass.data.get(_LAST, {}).get(device_id)
                payload = json.dumps(
                    state_payload(system, detail_of(system), last, dt_util.utcnow())
                )
                if payload != sent:
                    await response.write(f"data: {payload}\n\n".encode())
                    sent = payload
            if hass.is_stopping:
                return
            changed.clear()
            try:
                await asyncio.wait_for(changed.wait(), KEEPALIVE_SECONDS)
            except TimeoutError:
                await response.write(b": keepalive\n\n")
    except (ConnectionResetError, asyncio.CancelledError):
        # The keypad went away, or Home Assistant is closing the server.
        return
    finally:
        remove()


@callback
def async_start(hass: HomeAssistant, system: FoyerSystem) -> Any:
    """Register the views once, and tell the streams whenever the house moves.

    The views outlive a reload (Home Assistant cannot unregister a view), so
    they look the running system up on every request; the listener is this
    system's and goes with it.
    """
    if not hass.data.get(_REGISTERED):
        hass.http.register_view(DeviceCommandView())
        hass.http.register_view(DeviceStateView())
        hass.data[_REGISTERED] = True

    @callback
    def changed() -> None:
        async_dispatcher_send(hass, SIGNAL)

    remove = system.async_add_listener(changed)
    # A system that has just replaced another — a reload, which is what a
    # token being generated or revoked causes — may have closed a stream.
    async_dispatcher_send(hass, SIGNAL)

    @callback
    def stop() -> None:
        if remove is not None:
            remove()
        async_dispatcher_send(hass, SIGNAL)

    return stop
