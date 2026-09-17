"""Constants shared by the Home Assistant-facing modules."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "foyer"

# Config entry data: the answers from the config flow. They seed the stored
# configuration on first setup; after that .storage/foyer.config is authoritative.
CONF_AREA_NAME: Final = "area_name"
CONF_SCENARIO_NAME: Final = "scenario_name"
CONF_ZONE_ENTITY: Final = "zone_entity"
CONF_TRIGGER_STATES: Final = "trigger_states"

# Frontend
PANEL_URL_PATH: Final = "foyer"
PANEL_ELEMENT: Final = "foyer-panel"
PANEL_TITLE: Final = "Foyer"  # brand name, identical in every language
# An mdi icon, not the Foyer shield, and the reason is worth recording.
# A custom icon set is registered by a module; when the sidebar draws its
# icons before that module has run — which is what the companion app does
# when it starts from a cached page — Home Assistant falls back to a legacy
# element and never retries, so the panel shows an empty square for ever.
# The shield stays where our own modules are certainly loaded: the panel
# header and the card. `foyer:shield` is still registered for anyone who
# wants it on a dashboard of their own.
PANEL_ICON: Final = "mdi:shield-home"
STATIC_URL: Final = "/foyer_static"
FRONTEND_MODULES: Final = ("foyer-panel.js", "foyer-card.js", "foyer-icons.js")

# Dispatcher signal: something visible changed. Survives entry reloads.
SIGNAL_UPDATE: Final = f"{DOMAIN}_update"

# Channels (SPEC §9.1)
CHANNEL_HA_UI: Final = "ha_ui"
CHANNEL_AUTOMATION: Final = "automation"
