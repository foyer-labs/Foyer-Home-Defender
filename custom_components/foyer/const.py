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
# The disclaimer of SPEC §20.4, accepted in the config flow (decision 151) or,
# for an installation older than it, from a repair issue. The entry keeps
# which version of the text was accepted and when: Home Assistant does not
# tell an integration which account opened the flow, so "when" is all there
# is to keep. A new version of the text asks again.
CONF_DISCLAIMER: Final = "disclaimer"
DISCLAIMER_VERSION: Final = 1

# Frontend
PANEL_URL_PATH: Final = "foyer"
PANEL_ELEMENT: Final = "foyer-panel"
# The product's name, identical in every language: Foyer is the brand, Home
# Defender the product (decision 157).
PANEL_TITLE: Final = "Home Defender"
# An mdi icon, not the Foyer shield, and the reason is worth recording.
# A custom icon set is registered by a module; when the sidebar draws its
# icons before that module has run — which is what the companion app does
# when it starts from a cached page — Home Assistant falls back to a legacy
# element and never retries, so the panel shows an empty square for ever.
# The shield stays where our own modules are certainly loaded: the panel
# header. `foyer:shield` is still registered for anyone who
# wants it on a dashboard of their own.
PANEL_ICON: Final = "mdi:shield-home"
STATIC_URL: Final = "/foyer_static"
FRONTEND_MODULES: Final = ("foyer-panel.js", "foyer-card.js", "foyer-icons.js")

# Dispatcher signal: something visible changed. Survives entry reloads.
SIGNAL_UPDATE: Final = f"{DOMAIN}_update"

# Channels (SPEC §9.1)
CHANNEL_HA_UI: Final = "ha_ui"
CHANNEL_AUTOMATION: Final = "automation"
CHANNEL_API: Final = "api"
CHANNEL_MQTT: Final = "mqtt"
CHANNEL_KEYPAD: Final = "keypad"
# §9.4: what the engine calls itself when a rule acts. Never accepted from a
# caller — §9.1 lets a request claim only `api` or `automation`.
CHANNEL_AUTO_RULE: Final = "auto_rule"


# The action a button in an actionable notification sends back when somebody
# acknowledges the alarm from their phone (§7.2). One name, so the blueprint
# in docs/notification-channels.md and the listener agree on it.
ACK_ACTION = "FOYER_ACKNOWLEDGE"

# The action a Cancel button sends back when somebody stops an automatic
# rule's grace countdown (§9.4). The same mechanism as the acknowledgement
# above with a different id and a different handler — deliberately not a
# second one built beside it.
CANCEL_ACTION = "FOYER_CANCEL_AUTO"
# Where the countdown's id travels on that button, so pressing the button on
# last night's notification cannot stop tonight's arming.
CANCEL_PENDING_KEY = "foyer_pending"

# The four paths an acknowledgement arrives by (§7.2). Every one records who
# and through which channel; the word itself grants nothing.
ACK_VIA_COMMAND = "acknowledge"
ACK_VIA_DISARM = "disarm"
ACK_VIA_PUSH = "push"
ACK_VIA_DTMF = "dtmf"
# How a cancellation arrived, for the row §9.4 asks to carry the user.
CANCEL_VIA_PUSH = "push"
CANCEL_VIA_COMMAND = "command"
ACK_PATHS: Final = (ACK_VIA_COMMAND, ACK_VIA_DISARM, ACK_VIA_PUSH, ACK_VIA_DTMF)

# The event Home Assistant's own Companion app fires when a notification
# action is pressed. Foyer listens for it and calls the same acknowledgement
# everything else calls; it invents no fourth authorisation.
MOBILE_APP_ACTION_EVENT = "mobile_app_notification_action"
