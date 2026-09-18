"""``select.foyer_scenario``: the running scenario, by name (SPEC §13).

Choosing an option arms that scenario, or switches to it while armed
(decisions 7 and 9). Several scenarios may report the same master mode; this
entity is where the exact one is always visible.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..core.models import ArmRequest
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, actor_of, hub_device, raise_if_rejected


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities([FoyerScenarioSelect(system, entry.entry_id)])


class FoyerScenarioSelect(FoyerEntity, SelectEntity):
    _attr_translation_key = "scenario"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_scenario"
        self.entity_id = f"select.{DOMAIN}_scenario"
        self._attr_device_info = hub_device(entry_id)
        self._attr_options = [s.name for s in system.config.scenarios]

    @property
    def current_option(self) -> str | None:
        scenario = self._system.config.scenario(self._system.state.active_scenario_id)
        return scenario.name if scenario else None

    async def async_select_option(self, option: str) -> None:
        scenario = next(
            (s for s in self._system.config.scenarios if s.name == option), None
        )
        if scenario is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="rejected_unknown_scenario"
            )
        # A select carries no code, like a button (§13): a scenario whose
        # arming needs one is refused here and says so, rather than arming.
        actor = await actor_of(self.hass, self._system, self._context)
        decision = await self._system.async_handle(ArmRequest(scenario.id, actor))
        raise_if_rejected(self._system, decision)
