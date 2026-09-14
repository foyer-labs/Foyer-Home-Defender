"""WebSocket commands under ``foyer/*`` used by the panel and the card.

Phase 0 exposes read-only commands. State changes go through the
alarm_control_panel services, which route through the engine.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
import voluptuous as vol

from .. import i18n
from ..const import DOMAIN
from ..runtime.system import FoyerSystem


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_status)
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_translations)


def _system(hass: HomeAssistant) -> FoyerSystem | None:
    return hass.data.get(DOMAIN)


@websocket_api.websocket_command({vol.Required("type"): "foyer/status"})
@callback
def ws_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if (system := _system(hass)) is None:
        connection.send_error(msg["id"], "not_loaded", "Foyer is not loaded")
        return
    connection.send_result(msg["id"], system.status())


@websocket_api.websocket_command({vol.Required("type"): "foyer/subscribe"})
@callback
def ws_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Push the full status now and again after every change."""
    if (system := _system(hass)) is None:
        connection.send_error(msg["id"], "not_loaded", "Foyer is not loaded")
        return

    @callback
    def forward() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], system.status()))

    connection.subscriptions[msg["id"]] = system.async_add_listener(forward)
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
