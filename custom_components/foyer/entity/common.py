"""Shared pieces of the Foyer entities: devices, channels, refusals."""

from __future__ import annotations

from homeassistant.core import Context, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from ..const import CHANNEL_AUTOMATION, CHANNEL_HA_UI, DOMAIN
from ..core.models import Area, Decision, FoyerConfig
from ..runtime.system import FoyerSystem

MANUFACTURER = "Foyer Home Defender"


def hub_device(entry_id: str) -> DeviceInfo:
    """The device that carries system-wide entities (master, scenario, …)."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=MANUFACTURER,
        manufacturer=MANUFACTURER,
    )


def area_device(entry_id: str, area: Area) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_area_{area.id}")},
        name=area.name,
        manufacturer=MANUFACTURER,
        via_device=(DOMAIN, entry_id),
    )


def expected_unique_ids(entry_id: str, config: FoyerConfig) -> set[str]:
    """Every entity this configuration creates. Anything else is stale."""
    ids = {
        f"{entry_id}_{suffix}"
        for suffix in ("master", "scenario", "ready_to_arm", "fault", "open_zones")
    }
    for area in config.areas:
        for prefix in ("area", "ready_to_arm", "countdown"):
            ids.add(f"{entry_id}_{prefix}_{area.id}")
    ids.update(f"{entry_id}_zone_{zone.id}" for zone in config.zones)
    return ids


def channel_of(context: Context | None) -> str:
    """A person in the UI, or an automation: the log will say which."""
    return (
        CHANNEL_HA_UI if context is not None and context.user_id else CHANNEL_AUTOMATION
    )


def raise_if_rejected(system: FoyerSystem, decision: Decision) -> None:
    """Turn a refusal into a translated error naming the zones (§5.4)."""
    if decision.accepted or decision.reason is None:
        return
    names = {z.id: z.name for z in system.config.zones}
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key=f"rejected_{decision.reason.value}",
        translation_placeholders={
            "zones": ", ".join(names.get(z, z) for z in decision.blocking_zones)
        },
    )


class FoyerEntity(Entity):
    """Pushes its state whenever the system changes; never polls."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, system: FoyerSystem) -> None:
        self._system = system

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._system.async_add_listener(self._on_change))

    @callback
    def _on_change(self) -> None:
        self.async_write_ha_state()
