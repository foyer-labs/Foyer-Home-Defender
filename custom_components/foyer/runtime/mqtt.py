"""The MQTT contract, in both directions (SPEC §9.2).

A keypad on a broker is the cheapest physical channel there is, and it is the
one that needs feedback most: somebody standing at a door in the dark has only
the beeps and the LED to tell them what happened. So the outbound message
carries enough to tell *arming was blocked by an open zone* from *that code is
wrong* — the distinction the whole contract exists for.

Three things here are decisions rather than plumbing.

**Topics are configurable** (§9.2). People run more than one site against one
broker, and people have a topic hierarchy they are not going to restructure
for a new integration. Empty means the default, ``foyer/<install_id>/…``,
resolved here rather than stored: the stored value would travel inside an
exported configuration and arrive somewhere else still naming this house.

**The outbound message says as little as it can** (part 2 decision 3). It is
retained, on a broker that is often shared, so everything in it is told to
whoever connects next — including "the house is armed and nobody is in". The
detail level opens that up on request, in two steps, and starts at the least.

**A device commands only if it is declared** (part 2 decision 1). Over MQTT
the ``device_id`` is not optional: anybody who can publish to a topic can
publish a command, so the name it gives is the only thing that distinguishes a
keypad from a stranger, and a name this installation does not carry is refused
before the code is even looked at — which is also what keeps the lockout of
§8.4 countable.

**The answer is two fields, not one** (decision 87). ``last_result`` is the
closed four-word vocabulary of §9.2 and does not grow, so a keypad written
today never meets a word it does not know; ``last_reason`` beside it carries
the precise reason, and an adapter that wants the difference between "a window
is open" and "I am not a registered device" reads that one.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from ..api.services import async_report_unknown_device
from ..const import CHANNEL_MQTT
from ..core.models import (
    AcknowledgeIncident,
    ArmModeRequest,
    ArmRequest,
    Decision,
    DisarmRequest,
    MqttDetail,
    Reason,
)
from ..security.devices import async_requester
from .system import FoyerSystem

_LOGGER = logging.getLogger(__name__)

# The four words of §9.2, and they stay four. A keypad maps them to its beeps
# and its LED once, and a value it has never seen would be a keypad that goes
# quiet exactly when something new happens — so the vocabulary does not grow
# (decision 87). What grows instead is `last_reason` beside it: the precise
# reason, from the same stable set the services return, for an adapter that
# wants to tell "I am not a registered device" from "a window is open". A
# simple keypad reads the first and never changes; an evolved one reads both.
RESULT_OK = "ok"
RESULT_BLOCKED = "blocked"
RESULT_BAD_CODE = "bad_code"
RESULT_LOCKED_OUT = "locked_out"

_RESULTS: dict[Reason, str] = {
    Reason.BAD_CODE: RESULT_BAD_CODE,
    Reason.CODE_REQUIRED: RESULT_BAD_CODE,
    Reason.LOCKED_OUT: RESULT_LOCKED_OUT,
}


def default_prefix(install_id: str) -> str:
    return f"foyer/{install_id}"


def topic_names(config: Any, install_id: str) -> tuple[str, str]:
    """(command, state), each configured or each defaulted (§9.2)."""
    settings = config.settings.mqtt
    prefix = default_prefix(install_id)
    return (
        settings.command_topic or f"{prefix}/command",
        settings.state_topic or f"{prefix}/state",
    )


def topics(system: FoyerSystem, install_id: str) -> tuple[str, str]:
    return topic_names(system.config, install_id)


async def async_clear_retained(
    hass: HomeAssistant, config: Any, install_id: str
) -> bool:
    """Empty the retained state topic, because leaving has to be leaving (§16).

    A retained message outlives the integration that published it. Unsubscribing
    takes Foyer off the broker and leaves behind a message telling whoever
    connects next what the house was doing when Foyer last spoke — which is
    decision 83's own reasoning applied to the moment Foyer is no longer there
    to correct it. An empty payload published retained is what removes one.

    Best effort, and deliberately so: the broker may be down, MQTT may have
    been removed first, and none of that may stop an integration from being
    removed. What it must not do is fail silently in the code — the caller
    logs when it did not work, because a message left on somebody's broker is
    something they would want to know to go and clear themselves.
    """
    settings = config.settings.mqtt
    if not settings.enabled:
        return False
    try:
        from homeassistant.components import mqtt
    except ImportError:  # pragma: no cover - MQTT is an optional dependency
        return False
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return False
    _, state_topic = topic_names(config, install_id)
    await mqtt.async_publish(hass, state_topic, "", qos=settings.qos, retain=True)
    return True


def result_of(decision: Decision) -> tuple[str, str | None]:
    """(result, reason): one word for the beeps, and the precise why (§9.2)."""
    if decision.accepted:
        return RESULT_OK, None
    if decision.reason is None:
        return RESULT_BLOCKED, None
    return _RESULTS.get(decision.reason, RESULT_BLOCKED), decision.reason.value


def state_payload(
    system: FoyerSystem,
    detail: MqttDetail,
    last: tuple[str, str | None] | None,
    now: datetime,
) -> dict[str, Any]:
    """What goes on the state topic, at the level this installation chose.

    ``minimal`` is what a keypad needs and nothing else: no scenario name, no
    area names, no list of open windows. ``standard`` adds the scenario and
    the areas; ``full`` is §9.2 as written, open zones by name included. The
    ladder exists because the message is retained on somebody else's broker.
    """
    status = system.status()
    areas = status["areas"]
    blocking = [
        zone
        for area in areas
        for zone in (*area["blocking"]["fault"], *area["blocking"]["open"])
    ]
    names = {z["id"]: z["name"] for z in status["zones"]}
    payload: dict[str, Any] = {
        "master": status["master"]["mode"] or status["master"]["state"],
        "countdown": _countdown(areas, now),
        "ready_to_arm": not blocking,
        # A count, not a list: "two zones are open" is enough to send somebody
        # to look, and it names nothing to whoever else reads this topic.
        "blocking_zones": len(set(blocking)),
        "fault": any(z["fault"] for z in status["zones"]),
        "last_result": last[0] if last else None,
        # A stable identifier, never a sentence and never a name: it belongs
        # at every detail level, including the one that says nothing about
        # the house.
        "last_reason": last[1] if last else None,
    }
    if detail is MqttDetail.MINIMAL:
        return payload
    scenario = next(
        (s for s in status["scenarios"] if s["id"] == status["active_scenario_id"]),
        None,
    )
    payload["scenario"] = scenario["name"] if scenario else None
    payload["areas"] = {area["name"]: area["state"] for area in areas}
    if detail is MqttDetail.FULL:
        payload["open_zones"] = [
            names.get(zone, zone) for zone in dict.fromkeys(blocking)
        ]
    return payload


def _countdown(areas: list[dict[str, Any]], now: datetime) -> dict[str, Any] | None:
    """The soonest exit or entry delay still running, in seconds.

    One countdown, not one per area: a keypad has one display, and the number
    that matters to whoever is standing at it is the one about to run out.
    """
    running = [area["timer"] for area in areas if area["timer"]]
    if not running:
        return None
    soonest = min(running, key=lambda timer: timer["due"])
    due = dt_util.parse_datetime(soonest["due"])
    if due is None:
        return None
    return {
        "kind": soonest["kind"],
        "remaining": max(0, int((due - now).total_seconds())),
    }


@callback
def async_start(
    hass: HomeAssistant, entry: Any, system: FoyerSystem, install_id: str
) -> CALLBACK_TYPE:
    """Begin, in the background, and never make the alarm wait for a broker.

    Connecting is somebody else's machine's business: it can be slow, it can
    be down, and Home Assistant waits while an MQTT entry is still setting
    up. An alarm that does not finish loading because a broker did not answer
    is exactly the failure this project exists to avoid, so the subscription
    is started beside the setup rather than inside it. Everything else —
    entities, the panel, the services, the engine — is up either way.
    """
    handles: list[CALLBACK_TYPE] = []

    async def begin() -> None:
        handle = await async_setup(hass, system, install_id)
        if handle is not None:
            handles.append(handle)

    task = entry.async_create_background_task(hass, begin(), name="foyer mqtt")

    @callback
    def stop() -> None:
        task.cancel()
        for handle in handles:
            handle()

    return stop


async def async_setup(
    hass: HomeAssistant, system: FoyerSystem, install_id: str
) -> CALLBACK_TYPE | None:
    """Subscribe to the command topic and publish state, if MQTT is wanted.

    Off unless the installation switched it on: an alarm that starts
    publishing its state on somebody else's broker the moment it is updated
    has made that choice for the household.
    """
    settings = system.config.settings.mqtt
    if not settings.enabled:
        return None
    try:
        from homeassistant.components import mqtt
    except ImportError:  # pragma: no cover - MQTT is an optional dependency
        _LOGGER.warning("Foyer: MQTT is configured but the integration is missing")
        return None
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.warning("Foyer: MQTT is configured but no broker is connected")
        return None

    command_topic, state_topic = topics(system, install_id)
    last: tuple[str, str | None] | None = None
    published: str | None = None

    async def publish(
        result: tuple[str, str | None] | None = None, *, force: bool = False
    ) -> None:
        """Publish the state, unless it would say exactly what it already says.

        Foyer notifies its listeners whenever anything visible moves, which
        includes every motion a living-room detector reports. At the default
        detail level almost none of that changes this message, and republishing
        an identical retained payload is traffic on somebody else's broker that
        tells nobody anything. A running countdown still publishes each time,
        because its remaining seconds genuinely differ.
        """
        nonlocal published
        payload = json.dumps(
            state_payload(system, settings.detail, result, dt_util.utcnow())
        )
        if payload == published and not force:
            return
        published = payload
        await mqtt.async_publish(
            hass,
            state_topic,
            payload,
            qos=settings.qos,
            retain=settings.retain,
        )

    async def on_message(message: Any) -> None:
        nonlocal last
        try:
            data = json.loads(message.payload)
            assert isinstance(data, dict)
        except (ValueError, AssertionError):
            _LOGGER.warning("Foyer: unreadable MQTT command on %s", command_topic)
            return
        last = await _async_command(hass, system, data)
        # A command is always answered, even when nothing about the house
        # moved: a keypad asking `status` after a reboot, or one refused twice
        # for the same reason, is waiting for this message.
        await publish(last, force=True)

    @callback
    def on_change() -> None:
        hass.async_create_task(publish(last), eager_start=True)

    unsubscribe = await mqtt.async_subscribe(
        hass, command_topic, on_message, qos=settings.qos
    )
    remove_listener = system.async_add_listener(on_change)
    await publish()

    @callback
    def stop() -> None:
        unsubscribe()
        if remove_listener is not None:
            remove_listener()

    return stop


async def _async_command(
    hass: HomeAssistant, system: FoyerSystem, data: dict[str, Any]
) -> tuple[str, str | None]:
    """One inbound message (§9.2). Returns what the keypad should be told."""
    action = str(data.get("action") or "")
    if action == "status":
        # Not a command: "tell me again", for a keypad that has just booted.
        return RESULT_OK, None
    ref = data.get("device_id")
    if not ref:
        # Over a broker the device is not optional. Anybody who can publish to
        # the topic can publish a command, so the name a message gives is the
        # only thing separating the hall keypad from a stranger — and the only
        # thing that makes the lockout of §8.4 countable.
        await async_report_unknown_device(hass, system, channel=CHANNEL_MQTT, ref=None)
        return RESULT_BLOCKED, Reason.DEVICE_NOT_REGISTERED.value
    requester = await async_requester(
        hass,
        system.config,
        transport=CHANNEL_MQTT,
        ref=str(ref),
        code=_as_code(data.get("code")),
    )
    if requester.actor is None:
        await async_report_unknown_device(
            hass, system, channel=CHANNEL_MQTT, ref=str(ref)
        )
        return RESULT_BLOCKED, Reason.DEVICE_NOT_REGISTERED.value
    actor = requester.actor
    scenario = data.get("scenario")
    force = bool(data.get("force", False))
    skip = bool(data.get("skip_exit_delay", False))
    if action == "arm":
        found = next((s for s in system.config.scenarios if s.name == scenario), None)
        if found is None and scenario in {
            s.ha_master_state for s in system.config.scenarios
        }:
            event: Any = ArmModeRequest(str(scenario), actor, force, skip)
        else:
            event = ArmRequest(
                found.id if found else str(scenario or ""), actor, force, skip
            )
    elif action == "disarm":
        areas = data.get("area_ids")
        event = DisarmRequest(tuple(str(a) for a in areas) if areas else None, actor)
    elif action == "acknowledge":
        event = AcknowledgeIncident(actor)
    else:
        _LOGGER.warning("Foyer: unknown MQTT action %r", action)
        return RESULT_BLOCKED, "unknown_action"
    decision = await system.async_handle(event)
    return result_of(decision)


def _as_code(value: Any) -> str | None:
    """A code arrives as a string. A keypad that sends 1234 as a number is
    not wrong about the code, only about JSON."""
    if value is None:
        return None
    return str(value)
