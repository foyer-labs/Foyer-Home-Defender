"""Foyer Home Defender: an intruder alarm panel for Home Assistant.

Home Assistant modules are imported inside the setup functions rather than at
module level. Importing ``custom_components.foyer.core`` runs this file first,
and the core test suite must run on a machine where Home Assistant is not even
installed (INV-1).
"""

from __future__ import annotations

import logging
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

_LOGGER = logging.getLogger(__name__)
_WS_KEY = f"{DOMAIN}_websocket_registered"

PLATFORMS = (
    "alarm_control_panel",
    "select",
    "binary_sensor",
    "sensor",
    "switch",
    "button",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.exceptions import ConfigEntryError

    from .api import services, websocket
    from .panel import async_register_frontend
    from .runtime import acknowledge, mqtt
    from .runtime.system import FoyerSystem
    from .runtime.watcher import async_watch_zones
    from .store.config_store import ConfigStore
    from .store.log_store import LogStore
    from .store.schema import ConfigError
    from .store.seed import seed_config
    from .store.state_store import StateStore

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

    state_store = StateStore(hass)
    try:
        stored = await state_store.async_load(config)
    except ConfigError as err:
        # Refuse to start rather than start disarmed: a silent reset of an
        # armed house is exactly what INV-3 forbids. The file is left alone
        # for inspection.
        raise ConfigEntryError(
            f"Foyer cannot read its saved alarm state: {err}"
        ) from err

    log = LogStore(hass)
    try:
        await log.async_setup()
    except Exception:
        # The alarm runs without its log. It must never be the other way
        # round: an unreadable database file is a diagnostic problem, not a
        # reason to leave a house unprotected (SPEC §10, "a log failure must
        # never block the alarm path").
        _LOGGER.exception("Foyer could not open its event log; running without it")
        log = None

    system = FoyerSystem(hass, config, state_store, stored, log)
    system.entry_id = entry.entry_id
    entry.runtime_data = system
    hass.data[DOMAIN] = system

    if not hass.data.get(_WS_KEY):
        websocket.async_register(hass)
        hass.data[_WS_KEY] = True
    # Registered on every setup, and removed on unload: a service that
    # outlives the integration answers callers with a stale system.
    services.async_register(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_remove_stale_entities(hass, entry)
    entry.async_on_unload(async_watch_zones(system))
    system.async_start()
    # The broker, if this installation wants one (§9.2). Started beside this
    # setup and not inside it: a broker that does not answer must not keep the
    # alarm from loading. The install id keeps two houses on one broker apart;
    # it is the entry's, shortened, because a topic is something a person
    # types into a keypad's configuration.
    entry.async_on_unload(mqtt.async_start(hass, entry, system, entry.entry_id[:8]))
    # The two acknowledgement paths that arrive from outside (§7.2): the
    # button in an actionable push, and the DTMF webhook — which exists only
    # if this installation switched it on, because an unauthenticated URL
    # that stops an alarm is a decision the household makes knowingly.
    entry.async_on_unload(acknowledge.async_listen_push(hass, system))
    entry.async_on_unload(acknowledge.async_listen_cancel(hass, system))
    entry.async_on_unload(acknowledge.async_register_webhook(hass, system))
    await async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .api import services

    system = entry.runtime_data
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await system.async_stop()
        if system.log is not None:
            await system.log.async_close()
        # The sidebar panel is not removed here. Every configuration save
        # reloads the entry, a reload unloads it first, and a panel that
        # disappears from `hass.panels` for even a moment sends whoever is
        # looking at it back to the default dashboard. It goes when the
        # integration goes, in async_remove_entry.
        services.async_unregister(hass)
        hass.data.pop(DOMAIN, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Deleting the integration deletes its stored configuration and state.

    The event log database is deliberately left where it is. Whether to keep
    or delete it is a question the user must be asked, and asking it belongs
    to the clean uninstall of Phase 5 (SPEC §16); deleting thirty days of
    history without a word would be the wrong default to guess.
    """
    from .panel import async_unregister_panel
    from .store.config_store import ConfigStore
    from .store.state_store import StateStore

    async_unregister_panel(hass)
    await ConfigStore(hass).async_remove()
    await StateStore(hass).async_remove()


def _async_remove_stale_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop registry entries for areas and zones that no longer exist.

    Configuration changes reload the entry; without this, a deleted zone would
    leave a ghost entity behind, unavailable forever.
    """
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    from .entity.common import expected_unique_ids

    entities = er.async_get(hass)
    live = expected_unique_ids(entry.entry_id, entry.runtime_data.config)
    for registered in er.async_entries_for_config_entry(entities, entry.entry_id):
        if registered.unique_id not in live:
            _LOGGER.debug("Removing stale Foyer entity %s", registered.entity_id)
            entities.async_remove(registered.entity_id)

    devices = dr.async_get(hass)
    area_ids = {a.id for a in entry.runtime_data.config.areas}
    prefix = f"{entry.entry_id}_area_"
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        stale = any(
            domain == DOMAIN
            and identifier.startswith(prefix)
            and identifier.removeprefix(prefix) not in area_ids
            for domain, identifier in device.identifiers
        )
        if stale:
            devices.async_remove_device(device.id)
