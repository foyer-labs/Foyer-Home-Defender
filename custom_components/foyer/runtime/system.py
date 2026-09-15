"""The runtime owner of alarm state: builds snapshots, calls decide(), applies.

This is the only place where a Decision becomes new state. The engine chooses;
this module records the choice, persists it (INV-3), re-arms the scheduler and
hands the actions to the executor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import (
    CALLBACK_TYPE,
    Event as HassEvent,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from ..const import SIGNAL_UPDATE
from ..core.engine import arm_blockers, decide, master_state, next_wakeup
from ..core.models import (
    AreaState,
    Decision,
    EntityState,
    Event,
    FoyerConfig,
    RuntimeState,
    Startup,
    SystemSnapshot,
    Tick,
    ZoneStateChanged,
)
from ..core.triggers import fault_cause
from ..store.state_store import StateStore, StoredState
from .executor import Executor

_LOGGER = logging.getLogger(__name__)

# How often "still alive" is written, bounding how much a crash can overstate
# the restart gap. Never understate: see store/state_store.py.
ALIVE_INTERVAL = timedelta(minutes=5)


def entity_state(state: State | None) -> EntityState:
    if state is None:
        return EntityState(state=None)
    return EntityState(
        state=state.state,
        attributes=dict(state.attributes),
        last_reported=state.last_reported,
    )


class FoyerSystem:
    """Holds the configuration and the runtime state of one config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: FoyerConfig,
        state_store: StateStore,
        stored: StoredState | None,
    ) -> None:
        self.hass = hass
        self.config = config
        self.state = stored.state if stored else RuntimeState()
        self._down_since = stored.alive_at if stored else None
        self._state_store = state_store
        # Until Home Assistant has started, entities are still appearing:
        # faults are not announced yet (see SystemSnapshot.settling).
        self.settling = not hass.is_running
        self.area_entity_ids: dict[str, str] = {}
        self._executor = Executor(hass)
        self._listeners: list[Callable[[], None]] = []
        self._unsub_wakeup: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._started = False

    # --- lifecycle -----------------------------------------------------------

    @callback
    def async_start(self) -> None:
        """Begin: restore timers, then hand over to the engine once HA runs."""
        if self.hass.is_running:
            # A reload (a configuration change) or the integration being
            # enabled: Home Assistant itself did not restart.
            self.hass.async_create_task(self._async_started("reload"), eager_start=True)
        else:
            self._unsubs.append(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, self._on_ha_started
                )
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_alive, ALIVE_INTERVAL)
        )
        self._unsubs.append(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_ha_stop)
        )
        self._reschedule()

    async def async_stop(self) -> None:
        """Unload: timers stop here, their state is on disk for the next start."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._unsub_wakeup:
            self._unsub_wakeup()
            self._unsub_wakeup = None
        await self._async_save()

    @callback
    def _on_ha_started(self, _event: HassEvent) -> None:
        self.hass.async_create_task(self._async_started("ha_start"), eager_start=True)

    async def _async_started(self, cause: str) -> None:
        if self._started:
            return
        self._started = True
        self.settling = False
        await self.async_handle(Startup(down_since=self._down_since, cause=cause))

    @callback
    def _on_alive(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_save(), eager_start=True)

    @callback
    def _on_ha_stop(self, _event: HassEvent) -> None:
        self.hass.async_create_task(self._async_save(), eager_start=True)

    # --- events --------------------------------------------------------------

    async def async_handle(
        self, event: Event, overrides: Mapping[str, EntityState] | None = None
    ) -> Decision:
        """Decide, store, persist, execute. Returns the Decision for reporting."""
        # No await between snapshot and store: on the event loop this block is
        # atomic, so two events can never interleave their decisions.
        decision = decide(
            self._snapshot(overrides), event, self.config, dt_util.utcnow()
        )
        self.state = decision.state
        _LOGGER.debug("%s -> %s", event, decision)
        self._reschedule()
        self._notify()
        await self._async_save()
        await self._executor.async_run(decision)
        return decision

    async def async_zone_changed(
        self, entity_id: str, old: State | None, new: State | None
    ) -> Decision:
        # Home Assistant has already stored the new state; the engine must see
        # the world as it was *before* the change to detect transitions.
        return await self.async_handle(
            ZoneStateChanged(entity_id=entity_id, new=entity_state(new)),
            overrides={entity_id: entity_state(old)},
        )

    @callback
    def async_heartbeat(self, entity_id: str) -> None:
        """An entity reported without changing: supervision moves on (decision 11)."""
        zones = [z for z in self.config.zones if z.entity_id == entity_id]
        if any(z.id in self.state.faults for z in zones):
            # It may have been in supervision fault: let the engine clear it.
            self.hass.async_create_task(self.async_handle(Tick()), eager_start=True)
        else:
            self._reschedule()

    # --- scheduler -----------------------------------------------------------

    @callback
    def _reschedule(self) -> None:
        """The scheduler owns the clock: one wake-up, at the next due time."""
        if self._unsub_wakeup:
            self._unsub_wakeup()
            self._unsub_wakeup = None
        now = dt_util.utcnow()
        due = next_wakeup(self._snapshot(), self.config, now)
        if due is None:
            return
        self._unsub_wakeup = async_track_point_in_utc_time(
            self.hass, self._on_wakeup, max(due, now)
        )

    @callback
    def _on_wakeup(self, _now: datetime) -> None:
        self._unsub_wakeup = None
        self.hass.async_create_task(self.async_handle(Tick()), eager_start=True)

    # --- persistence ---------------------------------------------------------

    async def _async_save(self) -> None:
        try:
            await self._state_store.async_save(self.state, dt_util.utcnow())
        except Exception:
            # Keep running: an alarm that stops because the disk is full is
            # worse than one that cannot remember. Say so loudly.
            _LOGGER.exception("Foyer could not persist its state")

    # --- snapshot ------------------------------------------------------------

    def zone_entity_ids(self) -> list[str]:
        return sorted({z.entity_id for z in self.config.zones})

    def _snapshot(
        self, overrides: Mapping[str, EntityState] | None = None
    ) -> SystemSnapshot:
        entities = {
            entity_id: entity_state(self.hass.states.get(entity_id))
            for entity_id in self.zone_entity_ids()
        }
        entities.update(overrides or {})
        return SystemSnapshot(
            self.state, entities, self.settling, dt_util.get_default_time_zone()
        )

    # --- listeners -----------------------------------------------------------

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            self._listeners.remove(listener)

        return remove

    @callback
    def async_notify(self) -> None:
        """Tell subscribers something visible changed (e.g. a zone state)."""
        self._notify()

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    # --- read model ----------------------------------------------------------

    def blockers(self, area_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
        return arm_blockers(self._snapshot(), self.config, area_ids, dt_util.utcnow())

    def master(self) -> tuple[AreaState, str | None]:
        return master_state(self.state, self.config)

    def status(self) -> dict[str, Any]:
        """The live state as sent to the panel and the card. Contains no secrets."""
        now = dt_util.utcnow()
        snapshot = self._snapshot()
        master, mode = master_state(self.state, self.config)
        areas = []
        for area in self.config.areas:
            rt = self.state.area(area.id)
            faulted, open_ = arm_blockers(snapshot, self.config, (area.id,), now)
            areas.append(
                {
                    "id": area.id,
                    "name": area.name,
                    "state": rt.state.value,
                    "entity_id": self.area_entity_ids.get(area.id),
                    "scenario_id": rt.scenario_id,
                    "memory": rt.memory,
                    "causes": list(rt.causes),
                    "timer": None
                    if rt.timer is None
                    else {"kind": rt.timer.kind.value, "due": rt.timer.due.isoformat()},
                    "ready": not faulted and not open_,
                    "blocking": {"fault": list(faulted), "open": list(open_)},
                }
            )
        zones = []
        for zone in self.config.zones:
            entity = snapshot.entity(zone.entity_id)
            zones.append(
                {
                    "id": zone.id,
                    "name": zone.name,
                    "area_id": zone.area_id,
                    "entity_id": zone.entity_id,
                    "type": zone.type.value,
                    "channel": zone.channel.value,
                    "enabled": zone.enabled,
                    "state": entity.state,
                    "fault": fault_cause(zone, entity, now) if zone.enabled else None,
                    "open": zone.id in self.state.active_zones,
                    "bypassed": (
                        self.state.bypassed[zone.id].value
                        if zone.id in self.state.bypassed
                        else None
                    ),
                }
            )
        return {
            "now": now.isoformat(),
            "active_scenario_id": self.state.active_scenario_id,
            "master": {"state": master.value, "mode": mode},
            "areas": areas,
            "scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "icon": s.icon,
                    "areas": list(s.areas),
                    "ha_master_state": s.ha_master_state,
                }
                for s in self.config.scenarios
            ],
            "zones": zones,
            "technical": self.technical_status(),
            "incident": self.incident_status(),
            "chime_enabled": self.state.chime_enabled,
        }

    def technical_status(self) -> list[dict[str, Any]]:
        """The technical channel (§5.5): every zone in alarm or in memory."""
        names = {z.id: z for z in self.config.zones}
        out = []
        for zone_id, alarm in self.state.technical.items():
            zone = names.get(zone_id)
            out.append(
                {
                    "zone_id": zone_id,
                    "name": zone.name if zone else zone_id,
                    "area_id": zone.area_id if zone else None,
                    "since": alarm.since.isoformat(),
                    "active": zone_id in self.state.active_zones,
                    "acknowledged": alarm.acknowledged,
                }
            )
        return out

    def incident_status(self) -> dict[str, Any] | None:
        incident = self.state.incident
        if incident is None:
            return None
        return {
            "id": incident.id,
            "opened_at": incident.opened_at.isoformat(),
            "zone_ids": list(incident.zone_ids),
            "area_ids": list(incident.area_ids),
            "acknowledged": incident.acknowledged,
        }
