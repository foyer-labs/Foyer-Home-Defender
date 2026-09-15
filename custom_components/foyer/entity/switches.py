"""``switch.foyer_chime`` (SPEC §6.6, §13): silence the chime, or let it sound.

The switch holds no state of its own: turning it goes through the engine like
every other command, so the choice survives a restart (INV-3) and is recorded.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..core.models import SetChime
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, channel_of, hub_device


async def async_setup_switches(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities([FoyerChimeSwitch(system, entry.entry_id)])


class FoyerChimeSwitch(FoyerEntity, SwitchEntity):
    _attr_translation_key = "chime"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_chime"
        self.entity_id = f"switch.{DOMAIN}_chime"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return self._system.state.chime_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._system.async_handle(SetChime(True, channel_of(self._context)))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._system.async_handle(SetChime(False, channel_of(self._context)))
