"""Foyer Home Defender: an intruder alarm panel for Home Assistant.

Home Assistant modules are imported inside the setup functions rather than at
module level. Importing ``custom_components.foyer.core`` runs this file first,
and the core test suite must run on a machine where Home Assistant is not even
installed (INV-1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import (
    CONF_AREA_NAME,
    CONF_SCENARIO_NAME,
    CONF_TRIGGER_STATES,
    CONF_ZONE_ENTITY,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_WS_KEY = f"{DOMAIN}_websocket_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.const import Platform

    from .api import websocket
    from .panel import async_register_frontend
    from .runtime.system import FoyerSystem
    from .runtime.watcher import async_watch_zones
    from .store.config_store import ConfigStore
    from .store.seed import seed_config

    store = ConfigStore(hass)
    config = await store.async_load()
    if config is None:
        # First run: the config flow's answers seed the stored configuration.
        # From here on .storage/foyer.config is the source of truth.
        zone_entity = entry.data[CONF_ZONE_ENTITY]
        state = hass.states.get(zone_entity)
        config = seed_config(
            area_name=entry.data[CONF_AREA_NAME],
            scenario_name=entry.data[CONF_SCENARIO_NAME],
            zone_entity_id=zone_entity,
            zone_name=state.name if state else zone_entity,
            trigger_states=entry.data[CONF_TRIGGER_STATES],
        )
        await store.async_save(config)

    system = FoyerSystem(hass, config)
    entry.runtime_data = system
    hass.data[DOMAIN] = system

    if not hass.data.get(_WS_KEY):
        websocket.async_register(hass)
        hass.data[_WS_KEY] = True

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.ALARM_CONTROL_PANEL]
    )
    entry.async_on_unload(async_watch_zones(system))
    await async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.const import Platform

    from .panel import async_unregister_panel

    unloaded = await hass.config_entries.async_unload_platforms(
        entry, [Platform.ALARM_CONTROL_PANEL]
    )
    if unloaded:
        async_unregister_panel(hass)
        hass.data.pop(DOMAIN, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Deleting the integration deletes its stored configuration too."""
    from .store.config_store import ConfigStore

    await ConfigStore(hass).async_remove()
