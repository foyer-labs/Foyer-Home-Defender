"""``alarm_control_panel.foyer_<area>`` and ``alarm_control_panel.foyer_master``.

The entities decide nothing. Commands become engine events; the entities report
whatever state the runtime holds afterwards.

* An area's panel arms **only that area**, outside any scenario (decision 5),
  in the one mode it reports when armed. Its disarm disarms only that area.
* The master is derived from the areas (SPEC §13). Its arm services arm the one
  scenario reporting that mode, and are refused when two scenarios share it
  (decision 8); its disarm disarms everything.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from ..const import DOMAIN
from ..core.models import (
    Area,
    AreaState,
    ArmAreaRequest,
    ArmModeRequest,
    DisarmRequest,
)
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, area_device, channel_of, hub_device, raise_if_rejected

_ARM_FEATURES: dict[str, AlarmControlPanelEntityFeature] = {
    "armed_home": AlarmControlPanelEntityFeature.ARM_HOME,
    "armed_away": AlarmControlPanelEntityFeature.ARM_AWAY,
    "armed_night": AlarmControlPanelEntityFeature.ARM_NIGHT,
    "armed_vacation": AlarmControlPanelEntityFeature.ARM_VACATION,
    "armed_custom_bypass": AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
}

_NOT_ARMED: dict[AreaState, AlarmControlPanelState] = {
    AreaState.DISARMED: AlarmControlPanelState.DISARMED,
    AreaState.ARMING: AlarmControlPanelState.ARMING,
    AreaState.ENTRY: AlarmControlPanelState.PENDING,  # §5.1: entry maps to pending
    AreaState.TRIGGERED: AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities(
        [
            FoyerMasterPanel(system, entry.entry_id),
            *(FoyerAreaPanel(system, entry.entry_id, a) for a in system.config.areas),
        ]
    )


class _Panel(FoyerEntity, AlarmControlPanelEntity):
    # No codes before Phase 2. The engine still applies the code policy and
    # would refuse a request that needs one (INV-2); see CodePolicy.
    _attr_code_format = None
    _attr_code_arm_required = False

    async def _run(self, event: Any) -> None:
        decision = await self._system.async_handle(event)
        raise_if_rejected(self._system, decision)


class FoyerAreaPanel(_Panel):
    _attr_name = None  # the entity is the area's device: named after the area

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area) -> None:
        super().__init__(system)
        self._area = area
        self._attr_unique_id = f"{entry_id}_area_{area.id}"
        self.entity_id = f"alarm_control_panel.{DOMAIN}_{slugify(area.name)}"
        self._attr_device_info = area_device(entry_id, area)
        self._attr_supported_features = _ARM_FEATURES.get(
            area.ha_state_when_armed, AlarmControlPanelEntityFeature(0)
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._system.area_entity_ids[self._area.id] = self.entity_id
        self._system.async_notify()

    async def async_will_remove_from_hass(self) -> None:
        self._system.area_entity_ids.pop(self._area.id, None)

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        state = self._system.state.area(self._area.id).state
        if state is AreaState.ARMED:
            return AlarmControlPanelState(self._area.ha_state_when_armed)
        return _NOT_ARMED[state]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        rt = self._system.state.area(self._area.id)
        return {
            "scenario_id": rt.scenario_id,
            "alarm_memory": rt.memory,
            "timer": rt.timer.kind.value if rt.timer else None,
            "timer_due": rt.timer.due.isoformat() if rt.timer else None,
        }

    async def _arm(self, code: str | None) -> None:
        await self._run(
            ArmAreaRequest(self._area.id, code=code, channel=channel_of(self._context))
        )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm(code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._arm(code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm(code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._arm(code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._arm(code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._run(
            DisarmRequest(
                (self._area.id,), code=code, channel=channel_of(self._context)
            )
        )


class FoyerMasterPanel(_Panel):
    _attr_translation_key = "master"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_master"
        self.entity_id = f"alarm_control_panel.{DOMAIN}_master"
        self._attr_device_info = hub_device(entry_id)
        modes = [s.ha_master_state for s in system.config.scenarios]
        features = AlarmControlPanelEntityFeature(0)
        for mode in set(modes):
            # Only unambiguous modes are offered: a shared mode would be
            # refused anyway, and voice assistants should not suggest it.
            if modes.count(mode) == 1:
                features |= _ARM_FEATURES.get(mode, AlarmControlPanelEntityFeature(0))
        self._attr_supported_features = features

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        state, mode = self._system.master()
        if state is AreaState.ARMED and mode:
            return AlarmControlPanelState(mode)
        return _NOT_ARMED.get(state, AlarmControlPanelState.DISARMED)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        scenario = self._system.config.scenario(self._system.state.active_scenario_id)
        return {
            "scenario_id": scenario.id if scenario else None,
            "scenario": scenario.name if scenario else None,
        }

    async def _arm(self, mode: str, code: str | None) -> None:
        await self._run(
            ArmModeRequest(mode, code=code, channel=channel_of(self._context))
        )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm("armed_away", code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._arm("armed_home", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm("armed_night", code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._arm("armed_vacation", code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._arm("armed_custom_bypass", code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._run(
            DisarmRequest(None, code=code, channel=channel_of(self._context))
        )
