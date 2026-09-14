"""Binary sensors and sensors (SPEC §13): zones, readiness, faults, countdown."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from ..const import DOMAIN
from ..core.models import Area, TimerKind, Zone
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, area_device, hub_device

_COUNTDOWN_KINDS = (TimerKind.EXIT, TimerKind.HOLD, TimerKind.ENTRY)


async def async_setup_binary_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    entry_id = entry.entry_id
    areas = {a.id: a for a in system.config.areas}
    async_add_entities(
        [
            FoyerReadyToArm(system, entry_id, None),
            *(FoyerReadyToArm(system, entry_id, a) for a in system.config.areas),
            FoyerFault(system, entry_id),
            *(
                FoyerZoneSensor(system, entry_id, z, areas[z.area_id])
                for z in system.config.zones
                if z.area_id in areas
            ),
        ]
    )


async def async_setup_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities(
        [
            FoyerOpenZones(system, entry.entry_id),
            *(FoyerCountdown(system, entry.entry_id, a) for a in system.config.areas),
        ]
    )


# --- binary sensors -------------------------------------------------------------


class FoyerZoneSensor(FoyerEntity, BinarySensorEntity):
    """The zone as Foyer reads it: ``on`` means triggered, whatever the entity
    says "open" with (INV-5). A fault is an attribute, never "off" (INV-4)."""

    _attr_name = None

    def __init__(self, system: FoyerSystem, entry_id: str, zone: Zone, area: Area):
        super().__init__(system)
        self._zone = zone
        self._attr_unique_id = f"{entry_id}_zone_{zone.id}"
        self.entity_id = f"binary_sensor.{DOMAIN}_zone_{slugify(zone.name)}"
        self._attr_device_info = area_device(entry_id, area)
        self._attr_name = zone.name

    @property
    def is_on(self) -> bool:
        return self._zone.id in self._system.state.active_zones

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bypass = self._system.state.bypassed.get(self._zone.id)
        return {
            "zone_id": self._zone.id,
            "source_entity": self._zone.entity_id,
            "type": self._zone.type.value,
            "bypassed": bypass.value if bypass else None,
            "fault": self._zone.id in self._system.state.faults,
            "enabled": self._zone.enabled,
        }


class FoyerReadyToArm(FoyerEntity, BinarySensorEntity):
    """Whether arming would succeed right now, for one area or for all."""

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area | None):
        super().__init__(system)
        self._area = area
        if area is None:
            self._attr_translation_key = "ready_to_arm"
            self._attr_unique_id = f"{entry_id}_ready_to_arm"
            self.entity_id = f"binary_sensor.{DOMAIN}_ready_to_arm"
            self._attr_device_info = hub_device(entry_id)
        else:
            self._attr_translation_key = "ready_to_arm"
            self._attr_unique_id = f"{entry_id}_ready_to_arm_{area.id}"
            self.entity_id = f"binary_sensor.{DOMAIN}_ready_to_arm_{slugify(area.name)}"
            self._attr_device_info = area_device(entry_id, area)

    def _area_ids(self) -> tuple[str, ...]:
        if self._area is not None:
            return (self._area.id,)
        return tuple(a.id for a in self._system.config.areas)

    @property
    def is_on(self) -> bool:
        faulted, open_ = self._system.blockers(self._area_ids())
        return not faulted and not open_

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        faulted, open_ = self._system.blockers(self._area_ids())
        names = {z.id: z.name for z in self._system.config.zones}
        return {
            "faulted_zones": [names[z] for z in faulted],
            "open_zones": [names[z] for z in open_],
        }


class FoyerFault(FoyerEntity, BinarySensorEntity):
    """Any zone in fault (INV-4)."""

    _attr_translation_key = "fault"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_fault"
        self.entity_id = f"binary_sensor.{DOMAIN}_fault"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return bool(self._system.state.faults)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        names = {z.id: z.name for z in self._system.config.zones}
        return {"zones": sorted(names[z] for z in self._system.state.faults)}


# --- sensors ----------------------------------------------------------------------


class FoyerOpenZones(FoyerEntity, SensorEntity):
    _attr_translation_key = "open_zones"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_open_zones"
        self.entity_id = f"sensor.{DOMAIN}_open_zones"
        self._attr_device_info = hub_device(entry_id)

    def _open(self) -> list[str]:
        active = self._system.state.active_zones
        return [z.name for z in self._system.config.zones if z.id in active]

    @property
    def native_value(self) -> int:
        return len(self._open())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"zones": self._open()}


class FoyerCountdown(FoyerEntity, SensorEntity):
    """Seconds left on an exit, hold or entry timer; 0 when none is running.

    Ticks once a second only while a countdown runs, so the recorder does not
    hear from it the rest of the day.
    """

    _attr_translation_key = "countdown"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area) -> None:
        super().__init__(system)
        self._area = area
        self._attr_unique_id = f"{entry_id}_countdown_{area.id}"
        self.entity_id = f"sensor.{DOMAIN}_countdown_{slugify(area.name)}"
        self._attr_device_info = area_device(entry_id, area)
        self._unsub_tick: CALLBACK_TYPE | None = None

    def _timer(self):
        timer = self._system.state.area(self._area.id).timer
        return timer if timer is not None and timer.kind in _COUNTDOWN_KINDS else None

    @property
    def native_value(self) -> int:
        timer = self._timer()
        if timer is None:
            return 0
        return max(0, round((timer.due - dt_util.utcnow()).total_seconds()))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        timer = self._timer()
        return {
            "kind": timer.kind.value if timer else None,
            "due": timer.due.isoformat() if timer else None,
        }

    @callback
    def _on_change(self) -> None:
        running = self._timer() is not None
        if running and self._unsub_tick is None:
            self._unsub_tick = async_track_time_interval(
                self.hass, self._tick, timedelta(seconds=1)
            )
        elif not running and self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None
        super()._on_change()

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._on_change()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None
