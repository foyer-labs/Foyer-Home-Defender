"""Serves the built frontend and registers the sidebar panel and the card."""

from __future__ import annotations

import hashlib
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    FRONTEND_MODULES,
    PANEL_ELEMENT,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL_PATH,
    STATIC_URL,
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
_VERSIONS_KEY = f"{DOMAIN}_frontend_versions"


def _hashes() -> dict[str, str]:
    """Content hashes, so a new release is never masked by a cached bundle."""
    return {
        name: hashlib.sha256((FRONTEND_DIR / name).read_bytes()).hexdigest()[:12]
        for name in FRONTEND_MODULES
    }


def _url(versions: dict[str, str], name: str) -> str:
    return f"{STATIC_URL}/{name}?v={versions[name]}"


async def async_register_frontend(hass: HomeAssistant) -> None:
    # Static paths and extra modules cannot be unregistered, so they are set up
    # once per Home Assistant run and survive config entry reloads.
    if (versions := hass.data.get(_VERSIONS_KEY)) is None:
        versions = await hass.async_add_executor_job(_hashes)
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=True)]
        )
        # Loaded on every frontend page: the card must be available on any
        # dashboard, and the sidebar icon must exist before the panel is opened.
        frontend.add_extra_js_url(hass, _url(versions, "foyer-icons.js"))
        frontend.add_extra_js_url(hass, _url(versions, "foyer-card.js"))
        hass.data[_VERSIONS_KEY] = versions

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_ELEMENT,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url=_url(versions, "foyer-panel.js"),
        require_admin=False,
        config={},
    )


def async_unregister_panel(hass: HomeAssistant) -> None:
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
