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
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util, slugify

from ..const import DOMAIN
from ..core import authz
from ..core.models import (
    Actor,
    Area,
    AreaState,
    ArmAreaRequest,
    ArmModeRequest,
    DisarmRequest,
    Operation,
    Reason,
    Scenario,
)
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, actor_of, area_device, hub_device, raise_if_rejected

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

# One request as §8.2 resolves it: the areas it acts on, and its scenario.
_Target = tuple[tuple[Area, ...], Scenario | None]


def _armable(scenarios: tuple[Scenario, ...]) -> list[Scenario]:
    """The scenarios the master can arm: one per mode, and only an unshared
    mode, because a shared one is refused (decision 8)."""
    modes = [s.ha_master_state for s in scenarios]
    return [
        s
        for s in scenarios
        if s.ha_master_state in _ARM_FEATURES and modes.count(s.ha_master_state) == 1
    ]


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
    """What Home Assistant's alarm card, dialog, tiles and voice assistants
    talk to.

    ``code_format`` and ``code_arm_required`` are read from the policy, for
    nobody in particular, because an entity is not a connection and does not
    know who is looking. Whether this particular person needs to type anything
    is decided when the request arrives (INV-2): a right code typed where none
    was needed names who typed it, and a wrong one is refused as anywhere else.

    The two say different things (§13, decision 136). ``code_format`` says a
    code *may* be asked, so the alarm panel card draws its field wherever one
    could be. ``code_arm_required`` is acted on: while it is true, Home
    Assistant refuses a codeless arming itself, for everybody, before Foyer
    sees who is asking. So it is true only where that refuses nobody Foyer
    would let through.
    """

    @property
    def code_format(self) -> CodeFormat | None:
        wants = any(
            self._asks(operation, target)
            for operation in (Operation.ARM, Operation.DISARM)
            for target in self._readings()
        )
        return CodeFormat.NUMBER if wants else None

    @property
    def code_arm_required(self) -> bool:
        config = self._system.config
        if any(u.enabled and u.code_exempt_when_identified for u in config.users):
            # Somebody may arm from Home Assistant with no code, and Home
            # Assistant cannot tell them from anybody else.
            return False
        targets = self._arms()
        return bool(targets) and all(
            self._asks(Operation.ARM, target) for target in targets
        )

    def _asks(self, operation: Operation, target: _Target) -> bool:
        areas, scenario = target
        return authz.code_required(
            self._system.config,
            operation,
            now=dt_util.utcnow(),
            areas=areas,
            scenario=scenario,
        )

    def _arms(self) -> list[_Target]:
        """What this entity's arm actions arm, one request each."""
        raise NotImplementedError

    def _readings(self) -> list[_Target]:
        """Every request of this entity that the policy may ask a code for."""
        raise NotImplementedError

    async def _actor(self, code: str | None) -> Actor:
        return await actor_of(self.hass, self._system, self._context, code)

    async def _run(self, event: Any, *, arming: bool = False) -> None:
        decision = await self._system.async_handle(event)
        if arming and not decision.accepted and decision.reason is Reason.CODE_REQUIRED:
            # Home Assistant's dialog and tiles ask for a code to arm only
            # while code_arm_required is true, and it is false once anybody
            # is exempt: without this the person is told a code is needed
            # and not where it can be typed (§13).
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="panel_arm_code_required",
            )
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
        # One round of updates once the areas have all arrived, not one per
        # area: each was every entity, the broker and every open panel.
        self._system.async_notify_soon()

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

    def _arms(self) -> list[_Target]:
        return [((self._area,), None)]

    def _readings(self) -> list[_Target]:
        return self._arms()

    async def _arm(self, code: str | None) -> None:
        await self._run(
            ArmAreaRequest(self._area.id, await self._actor(code)),
            arming=True,
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
        await self._run(DisarmRequest((self._area.id,), await self._actor(code)))


class FoyerMasterPanel(_Panel):
    _attr_translation_key = "master"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_master"
        self.entity_id = f"alarm_control_panel.{DOMAIN}_master"
        self._attr_device_info = hub_device(entry_id)
        features = AlarmControlPanelEntityFeature(0)
        # Only unambiguous modes are offered: a shared mode would be refused
        # anyway, and voice assistants should not suggest it.
        for scenario in _armable(system.config.scenarios):
            features |= _ARM_FEATURES[scenario.ha_master_state]
        self._attr_supported_features = features

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Whatever the household renamed it to: the card recognises the
        # master by this, not by the id it was created with.
        self._system.master_entity_id = self.entity_id
        self._system.async_notify_soon()

    async def async_will_remove_from_hass(self) -> None:
        self._system.master_entity_id = None
        self._system.async_notify_soon()

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

    def _arms(self) -> list[_Target]:
        # Every scenario it can arm, each with its own areas. All of them
        # must ask for a code before Home Assistant is told arming needs
        # one: a mode whose scenario asks none would otherwise be refused by
        # Home Assistant, an automation arming it included, where Foyer
        # would have armed it.
        config = self._system.config
        return [
            (self._areas_of(scenario), scenario)
            for scenario in _armable(config.scenarios)
        ]

    def _readings(self) -> list[_Target]:
        # Every area and every scenario as well as the installation's
        # policy: read from the policy alone, a house where only an area or
        # a scenario asks for a code had no field on the master's card, and
        # nowhere there to type the code it was then refused for.
        config = self._system.config
        return [
            ((), None),
            *(((area,), None) for area in config.areas),
            *((self._areas_of(s), s) for s in config.scenarios),
        ]

    def _areas_of(self, scenario: Scenario) -> tuple[Area, ...]:
        config = self._system.config
        return tuple(
            area
            for area in (config.area(a) for a in scenario.areas)
            if area is not None
        )

    async def _arm(self, mode: str, code: str | None) -> None:
        await self._run(ArmModeRequest(mode, await self._actor(code)), arming=True)

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
        await self._run(DisarmRequest(None, await self._actor(code)))
