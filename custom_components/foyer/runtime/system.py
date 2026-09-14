"""The runtime owner of alarm state: builds snapshots, calls decide(), applies.

This is the only place where a Decision is turned into new state. The engine
chooses; this module records the choice and hands the actions to the executor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from ..core.engine import decide, is_fault, is_triggered
from ..core.models import (
    AreaState,
    Decision,
    Event,
    FoyerConfig,
    SystemSnapshot,
    ZoneStateChanged,
)
from .executor import Executor

_LOGGER = logging.getLogger(__name__)


class FoyerSystem:
    """Holds area states and the active scenario for one config entry.

    Phase 0 keeps state in memory only: after a restart every area starts
    disarmed. Persisting it (INV-3) is Phase 1 work, agreed for this phase.
    """

    def __init__(self, hass: HomeAssistant, config: FoyerConfig) -> None:
        self.hass = hass
        self.config = config
        self.area_states: dict[str, AreaState] = {
            a.id: AreaState.DISARMED for a in config.areas
        }
        self.active_scenario_id: str | None = None
        self.area_entity_ids: dict[str, str] = {}
        self._executor = Executor(hass)
        self._listeners: list[Callable[[], None]] = []

    # --- events --------------------------------------------------------------

    async def async_handle(self, event: Event) -> Decision:
        """Decide, apply, execute. Returns the Decision so callers can report it."""
        decision = self._decide_and_apply(event, self._snapshot())
        await self._executor.async_run(decision)
        return decision

    async def async_zone_changed(
        self, entity_id: str, old_state: str | None, new_state: str | None
    ) -> Decision:
        # The state machine has already stored new_state; the engine must see
        # the world as it was *before* the change to detect transitions.
        snapshot = self._snapshot(overrides={entity_id: old_state})
        decision = self._decide_and_apply(
            ZoneStateChanged(entity_id=entity_id, new_state=new_state), snapshot
        )
        await self._executor.async_run(decision)
        return decision

    def _decide_and_apply(self, event: Event, snapshot: SystemSnapshot) -> Decision:
        # No await between snapshot and apply: on the event loop this block is
        # atomic, so two requests can never interleave their decisions.
        decision = decide(snapshot, event, self.config, dt_util.utcnow())
        if decision.accepted:
            self.area_states.update(decision.area_states)
            self.active_scenario_id = decision.active_scenario_id
        _LOGGER.debug("%s -> %s", event, decision)
        self._notify()
        return decision

    def _snapshot(
        self, overrides: Mapping[str, str | None] | None = None
    ) -> SystemSnapshot:
        entity_states: dict[str, str | None] = {}
        for zone in self.config.zones:
            state = self.hass.states.get(zone.entity_id)
            entity_states[zone.entity_id] = state.state if state else None
        entity_states.update(overrides or {})
        return SystemSnapshot(
            area_states=self.area_states,
            active_scenario_id=self.active_scenario_id,
            entity_states=entity_states,
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

    # --- read model ----------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """The live state as sent to the panel. Contains no secrets."""
        states = self._snapshot().entity_states
        return {
            "active_scenario_id": self.active_scenario_id,
            "areas": [
                {
                    "id": area.id,
                    "name": area.name,
                    "state": self.area_states[area.id].value,
                    "entity_id": self.area_entity_ids.get(area.id),
                }
                for area in self.config.areas
            ],
            "scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "areas": list(s.areas),
                    "ha_master_state": s.ha_master_state,
                }
                for s in self.config.scenarios
            ],
            "zones": [
                {
                    "id": zone.id,
                    "name": zone.name,
                    "area_id": zone.area_id,
                    "entity_id": zone.entity_id,
                    "state": states.get(zone.entity_id),
                    "fault": is_fault(states.get(zone.entity_id)),
                    "open": is_triggered(zone, states.get(zone.entity_id)),
                }
                for zone in self.config.zones
            ],
        }
