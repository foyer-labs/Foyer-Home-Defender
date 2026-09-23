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

    from .runtime.system import FoyerSystem

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
    from .runtime.system import FoyerSystem
    from .runtime.watcher import async_watch_zones
    from .store.config_store import ConfigStore
    from .store.log_store import LogStore
    from .store.schema import ConfigError
    from .store.seed import seed_config
    from .store.state_store import StateStore

    store = ConfigStore(hass)
    # Deliberately not guarded. `config is None` below means "first run" and
    # seeds a fresh configuration over the file, so swallowing a read failure
    # here would answer a corrupt or newer-major document by destroying every
    # area, zone, user and code hash in it. A document this version cannot
    # read must stop the setup, exactly as the alarm state does below.
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
        # Against the entry, so the writer goes when the entry goes even if
        # something below this line never gets the chance to close it.
        await log.async_setup(
            lambda coro, name: entry.async_create_background_task(hass, coro, name)
        )
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

    # The log is closed last of all, after the system and every listener
    # registered below have stopped: rows they write while stopping belong
    # in it, and a close that ran before them dropped what came after
    # (third review). `async_on_unload` callbacks run in reverse order.
    if log is not None:
        entry.async_on_unload(log.async_close)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_remove_stale_entities(hass, entry)
    entry.async_on_unload(async_watch_zones(system))
    system.async_start()
    try:
        await _async_setup_transports(hass, entry, system)
    except Exception:
        # A transport that fails to start must not leave a system running
        # with its timers and listeners behind a failed setup, which Home
        # Assistant will not unload (third review).
        await system.async_stop()
        raise
    return True


async def _async_setup_transports(
    hass: HomeAssistant, entry: ConfigEntry, system: FoyerSystem
) -> None:
    """Everything that talks to the outside once the system runs."""
    from .api import endpoint
    from .panel import async_register_frontend
    from .runtime import acknowledge, mqtt

    # The broker, if this installation wants one (§9.2). Started beside this
    # setup and not inside it: a broker that does not answer must not keep the
    # alarm from loading. The install id keeps two houses on one broker apart;
    # it is the entry's, shortened, because a topic is something a person
    # types into a keypad's configuration.
    entry.async_on_unload(mqtt.async_start(hass, entry, system, entry.entry_id[:8]))
    # The device endpoint (§9.2.1): the second transport a keypad may use,
    # with a token of its own. Its views are registered once and outlive a
    # reload; its streams follow whichever system is running.
    entry.async_on_unload(endpoint.async_start(hass, system))
    # The two acknowledgement paths that arrive from outside (§7.2): the
    # button in an actionable push, and the DTMF webhook — which exists only
    # if this installation switched it on, because an unauthenticated URL
    # that stops an alarm is a decision the household makes knowingly.
    entry.async_on_unload(acknowledge.async_listen_push(hass, system))
    entry.async_on_unload(acknowledge.async_listen_cancel(hass, system))
    entry.async_on_unload(acknowledge.async_register_webhook(hass, system))
    await async_register_frontend(hass)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .api import services

    system = entry.runtime_data
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await system.async_stop()
        # The sidebar panel is not removed here. Every configuration save
        # reloads the entry, a reload unloads it first, and a panel that
        # disappears from `hass.panels` for even a moment sends whoever is
        # looking at it back to the default dashboard. It goes when the
        # integration goes, in async_remove_entry.
        services.async_unregister(hass)
        hass.data.pop(DOMAIN, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Leaving, and leaving nothing behind (SPEC §16).

    Entities and devices out of both registries, the sidebar panel gone, the
    repair issues forgotten, the notifications Foyer put up taken down, the
    retained MQTT message cleared — a message that outlives the integration
    keeps telling whoever connects next what the house was doing — and the
    stored configuration and alarm state deleted.

    The log database is the one thing that is a question rather than an
    answer, and the question was asked before this ran: Home Assistant's own
    confirmation is the last dialogue there is, so what decides here is the
    switch on page 11 (part 2 decision 9). It is off unless somebody turned it
    on, because §16 says to ask rather than guess and keeping is the only
    answer that destroys nothing. An installation that never answered keeps
    its thirty days, and `docs/privacy.md` says where the file is.

    What Foyer does *not* delete is the camera folder. The snapshots under
    `media/foyer` are pictures of the inside of a house and are the one item
    nobody would think to look for — but the folder is configurable, may point
    anywhere and may hold files that are not Foyer's, so it is named in the
    documentation and beside the switch instead of being removed.
    """
    from .panel import async_unregister_panel
    from .repairs import async_forget_all
    from .runtime import mqtt, notices
    from .store.config_store import ConfigStore
    from .store.log_store import async_delete_database
    from .store.state_store import StateStore

    # Read before anything is deleted: the answer to "keep or delete the log"
    # lives in the configuration this function is about to remove. Guarded,
    # because a document this version cannot read must not stop the removal —
    # Home Assistant drops the entry whatever this raises, and everything
    # below would simply never run, leaving the panel in the sidebar and the
    # stored configuration, hashes and all, on disk with nothing left to
    # remove it. What is lost is the answer to the log question, and the
    # answer it falls back to is the one that destroys nothing.
    store = ConfigStore(hass)
    try:
        config = await store.async_load()
    except Exception:
        _LOGGER.exception("Foyer could not read its configuration while removing")
        config = None

    async_unregister_panel(hass)
    # Repair issues are registered against the domain rather than the entry,
    # so Home Assistant does not take them away with it: without this,
    # removing Foyer leaves a card in Settings for ever, pointing at an
    # integration that is not there to fix it (§12.4).
    async_forget_all(hass)
    notices.async_dismiss_all(hass)
    _async_remove_registrations(hass, entry)

    asked = config is not None and config.settings.log.delete_on_uninstall
    if asked and not await async_delete_database(hass):
        # A file left behind when somebody asked for it to go is worth a line:
        # it is thirty days of history, and the `-wal` beside it is the last
        # rows of it.
        _LOGGER.warning(
            "Foyer could not delete its event log database; it is still in "
            "the configuration directory"
        )

    await store.async_remove()
    await StateStore(hass).async_remove()

    # The broker last, and deliberately. `async_wait_for_mqtt_client` waits up
    # to fifty seconds for an MQTT entry that is retrying against a broker
    # nobody can reach, and every deletion above would sit behind it — a
    # removal the household abandons halfway is a removal that did nothing.
    if config is not None and config.settings.mqtt.enabled:
        try:
            cleared = await mqtt.async_clear_retained(hass, config, entry.entry_id[:8])
        except Exception:
            cleared = False
            _LOGGER.exception("Foyer could not clear its retained MQTT message")
        if not cleared:
            # Said out loud rather than shrugged off: what is left behind is a
            # message on somebody else's broker describing this house, and the
            # household can go and clear it by hand if they know.
            _LOGGER.warning(
                "Foyer left its retained MQTT message on the broker: it could not "
                "be reached while the integration was being removed"
            )


def _async_remove_registrations(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Every entity and device this entry created, out of both registries.

    Home Assistant does this itself when an entry is removed. It is done here
    as well because §16 asks for it by name and because the failure it is
    guarding against — an entity left behind, unavailable for ever, in
    somebody's dashboard — is silent, and a second removal of something
    already removed costs nothing.
    """
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    entities = er.async_get(hass)
    for registered in list(er.async_entries_for_config_entry(entities, entry.entry_id)):
        entities.async_remove(registered.entity_id)
    devices = dr.async_get(hass)
    for device in list(dr.async_entries_for_config_entry(devices, entry.entry_id)):
        devices.async_remove_device(device.id)


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
