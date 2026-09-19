"""The two acknowledgement paths that arrive from outside (SPEC §7.2).

Four paths acknowledge an alarm. Two were already here: an explicit
``foyer.acknowledge`` — the service, the WebSocket command and
``button.foyer_acknowledge`` — and disarming through any channel. These are
the other two:

- a **button in an actionable push notification**, which Home Assistant's own
  Companion app sends back as an event;
- a **DTMF keypress** captured by the voice-call provider and posted to a
  webhook.

Neither invents an authorisation. Both build the same
``AcknowledgeIncident`` / ``AcknowledgeTechnical`` the service builds and
hand it to the engine, where §8.2 is resolved as it is for everything else
(INV-2). What they add is the record of *which* path answered, and which
contact the notification had gone to (part 1 decision 7).

**The webhook is off until somebody switches it on**, and that is INV-6
rather than tidiness: a Home Assistant webhook is not authenticated, so
whoever holds the URL can stop an escalation on its way to the neighbour.
The threat is written next to the switch, in docs/notification-channels.md
and in the README's security model — stated, not implied.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp.web import Request, Response
from homeassistant.components import webhook
from homeassistant.core import Event as HassEvent, HomeAssistant, callback

from ..const import (
    ACK_ACTION,
    ACK_VIA_DTMF,
    ACK_VIA_PUSH,
    CHANNEL_API,
    DOMAIN,
    MOBILE_APP_ACTION_EVENT,
)
from ..core.models import AcknowledgeIncident, AcknowledgeTechnical, Actor

_LOGGER = logging.getLogger(__name__)

TECHNICAL = "technical"


def _event_for(kind: str, via: str, contact_id: str | None, channel: str) -> Any:
    actor = Actor(channel=channel)
    if kind == TECHNICAL:
        return AcknowledgeTechnical(actor, via=via, contact_id=contact_id)
    return AcknowledgeIncident(actor, via=via, contact_id=contact_id)


@callback
def async_listen_push(hass: HomeAssistant, system) -> Any:
    """Acknowledge from the button in an actionable notification (§7.2).

    The Companion app fires one event for every notification action; this
    listens for Foyer's own and ignores everybody else's, because the event
    belongs to Home Assistant and not to this integration.
    """

    async def _handle(event: HassEvent) -> None:
        data = event.data or {}
        if data.get("action") != ACK_ACTION:
            return
        await system.async_handle(
            _event_for(
                str(data.get("foyer_kind") or ""),
                ACK_VIA_PUSH,
                data.get("foyer_contact") or None,
                CHANNEL_API,
            )
        )

    return hass.bus.async_listen(MOBILE_APP_ACTION_EVENT, _handle)


@callback
def async_register_webhook(hass: HomeAssistant, system) -> Any:
    """Acknowledge from a DTMF keypress, when the installation asked for it.

    The provider — Twilio, a GSM gateway, anything — posts here after the
    person presses a key. Foyer reads nothing from the body but which alarm
    it is about: there is nothing else to trust in it.
    """
    webhook_id = system.config.settings.ack_webhook_id
    if not webhook_id:
        return lambda: None

    async def _handle(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> Response:
        payload: dict[str, Any] = {}
        try:
            if request.content_type == "application/json":
                payload = await request.json()
            else:
                payload = dict(await request.post())
        except Exception:  # a provider posting something unreadable still meant it
            _LOGGER.debug("Foyer could not read the acknowledgement webhook body")
        await system.async_handle(
            _event_for(
                str(payload.get("target") or ""),
                ACK_VIA_DTMF,
                str(payload.get("contact_id") or "") or None,
                CHANNEL_API,
            )
        )
        return Response(status=200)

    webhook.async_register(
        hass, DOMAIN, "Foyer acknowledgement", webhook_id, _handle
    )

    @callback
    def _remove() -> None:
        webhook.async_unregister(hass, webhook_id)

    return _remove
