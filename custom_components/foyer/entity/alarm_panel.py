"""``alarm_control_panel.foyer_<area>``: one entity per area (SPEC §13).

The entity decides nothing. Arm and disarm become engine events; the entity
reports whatever state the runtime holds afterwards.
"""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from ..const import CHANNEL_AUTOMATION, CHANNEL_HA_UI, DOMAIN
from ..core.models import Area, AreaState, ArmRequest, Decision, DisarmRequest
from ..runtime.system import FoyerSystem

_ARM_FEATURES: dict[str, AlarmControlPanelEntityFeature] = {
    "armed_home": AlarmControlPanelEntityFeature.ARM_HOME,
    "armed_away": AlarmControlPanelEntityFeature.ARM_AWAY,
    "armed_night": AlarmControlPanelEntityFeature.ARM_NIGHT,
    "armed_vacation": AlarmControlPanelEntityFeature.ARM_VACATION,
    "armed_custom_bypass": AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities(
        FoyerAreaPanel(system, entry.entry_id, area) for area in system.config.areas
    )


class FoyerAreaPanel(AlarmControlPanelEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None  # the entity is the device: named after the area
    # Phase 0 has no codes. The engine still applies the code policy and would
    # refuse a request that needs one (INV-2); see CodePolicy.
    _attr_code_format = None
    _attr_code_arm_required = False

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area) -> None:
        self._system = system
        self._area = area
        self._attr_unique_id = f"{entry_id}_area_{area.id}"
        self.entity_id = f"alarm_control_panel.{DOMAIN}_{slugify(area.name)}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_area_{area.id}")},
            name=area.name,
            manufacturer="Foyer Home Defender",
        )
        features = AlarmControlPanelEntityFeature(0)
        for scenario in system.config.scenarios:
            if area.id in scenario.areas:
                features |= _ARM_FEATURES.get(
                    scenario.ha_master_state, AlarmControlPanelEntityFeature(0)
                )
        self._attr_supported_features = features

    async def async_added_to_hass(self) -> None:
        self._system.area_entity_ids[self._area.id] = self.entity_id
        self.async_on_remove(self._system.async_add_listener(self._on_change))
        self._system.async_notify()

    async def async_will_remove_from_hass(self) -> None:
        self._system.area_entity_ids.pop(self._area.id, None)

    @callback
    def _on_change(self) -> None:
        self.async_write_ha_state()

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        state = self._system.area_states[self._area.id]
        if state is AreaState.ARMED:
            return AlarmControlPanelState(self._area.ha_state_when_armed)
        if state is AreaState.TRIGGERED:
            return AlarmControlPanelState.TRIGGERED
        return AlarmControlPanelState.DISARMED

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {"scenario_id": self._system.active_scenario_id}

    # --- commands ------------------------------------------------------------

    def _channel(self) -> str:
        user_id = self._context.user_id if self._context else None
        return CHANNEL_HA_UI if user_id else CHANNEL_AUTOMATION

    async def _async_arm(self, ha_state: str, code: str | None) -> None:
        scenario = next(
            (
                s
                for s in self._system.config.scenarios
                if self._area.id in s.areas and s.ha_master_state == ha_state
            ),
            None,
        )
        if scenario is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="no_scenario"
            )
        decision = await self._system.async_handle(
            ArmRequest(scenario_id=scenario.id, code=code, channel=self._channel())
        )
        self._raise_if_rejected(decision)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._async_arm("armed_away", code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._async_arm("armed_home", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._async_arm("armed_night", code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._async_arm("armed_vacation", code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._async_arm("armed_custom_bypass", code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        decision = await self._system.async_handle(
            DisarmRequest(code=code, channel=self._channel())
        )
        self._raise_if_rejected(decision)

    def _raise_if_rejected(self, decision: Decision) -> None:
        if decision.accepted or decision.reason is None:
            return
        names = {z.id: z.name for z in self._system.config.zones}
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key=f"rejected_{decision.reason.value}",
            translation_placeholders={
                "zones": ", ".join(names.get(z, z) for z in decision.blocking_zones)
            },
        )
