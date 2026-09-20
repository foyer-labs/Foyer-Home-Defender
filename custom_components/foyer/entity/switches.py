"""The three switches of §13: the chime, the walk test and automatic arming.

Neither holds state of its own: turning one goes through the engine like every
other command, so the choice survives a restart (INV-3) and is recorded.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..core.models import SetAutoArming, SetChime, WalkTestRequest
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, actor_of, hub_device, raise_if_rejected


async def async_setup_switches(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities(
        [
            FoyerChimeSwitch(system, entry.entry_id),
            FoyerWalkTestSwitch(system, entry.entry_id),
            FoyerAutoArmingSwitch(system, entry.entry_id),
        ]
    )


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

    async def _set(self, enabled: bool) -> None:
        actor = await actor_of(self.hass, self._system, self._context)
        await self._system.async_handle(SetChime(enabled, actor))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


class FoyerWalkTestSwitch(FoyerEntity, SwitchEntity):
    """``switch.foyer_walk_test`` (§13), reflecting the timeout.

    A switch cannot carry a code, and §8.2 asks for one to enter a walk
    test. That is not a reason to leave it out — §13 lists it, and a keypad
    or an automation is exactly the sort of place a walk test gets started
    from. It behaves the way ``button.foyer_acknowledge`` does with the same
    problem (decision 77): it honours the policy and refuses, visibly and in
    the log, rather than quietly doing nothing or quietly ignoring the rule.
    Whoever holds the per-user exemption of §8.2 on an identified channel can
    use it; everybody else uses the panel, which can ask.

    Off is not a decoration either: it ends the walk test at once, which is
    the one direction that is always safe.
    """

    _attr_translation_key = "walk_test"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_walk_test"
        self.entity_id = f"switch.{DOMAIN}_walk_test"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return self._system.state.walk_test is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """The timeout, because §13 asks the switch to reflect it.

        Two deadlines, because there are two: the window every detection
        pushes back, and the cap that never moves (part 2 decision 4). An
        automation or a dashboard that shows one number shows ``ends_at``.
        """
        walk = self._system.state.walk_test
        if walk is None:
            return None
        return {
            "started_at": walk.started_at.isoformat(),
            "ends_at": walk.deadline().isoformat(),
            "timeout_at": walk.until.isoformat(),
            "hard_timeout_at": walk.hard_until.isoformat(),
            "window": walk.window,
            "started_by": walk.user_name,
            "armed_areas": list(walk.armed_areas),
            "detected_zones": sorted(walk.detections),
        }

    async def _set(self, enable: bool) -> None:
        # Already there: a switch is idempotent, and an automation calling
        # turn_off on a house that is not in a walk test has not made a
        # mistake worth raising an error over. The engine would refuse it as
        # `invalid_state`, which is true and unhelpful.
        if enable == self.is_on:
            return
        actor = await actor_of(self.hass, self._system, self._context)
        decision = await self._system.async_handle(WalkTestRequest(enable, actor))
        raise_if_rejected(self._system, decision)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


class FoyerAutoArmingSwitch(FoyerEntity, SwitchEntity):
    """``switch.foyer_auto_arming`` (§9.4, §13): the global kill switch.

    It exists so the whole mechanism can be driven from a dashboard, an
    automation or a keypad — a fortnight away, a house full of guests, a
    weekend when the rules would be wrong. Off cancels whatever is counting
    down as well: a switch that let an announced arming happen anyway would
    not be doing what it says at the one moment somebody reaches for it.

    It holds no state of its own. Like the chime's, the decision goes through
    the engine, is recorded, and survives a restart (INV-3).
    """

    _attr_translation_key = "auto_arming"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_auto_arming"
        self.entity_id = f"switch.{DOMAIN}_auto_arming"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return self._system.state.auto_arming

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """How many rules are running behind it, and what is counting down.

        The detail belongs on ``sensor.foyer_next_auto_action``; what a
        switch owes its dashboard is whether switching it off would stop
        something that is about to happen.
        """
        state = self._system.state
        return {
            "rules": sum(1 for rule in self._system.config.rules if rule.enabled),
            "counting_down": [pending.rule_name for pending in state.pending_rules],
            "suspensions": len(state.suspensions),
        }

    async def _set(self, enabled: bool) -> None:
        if enabled == self.is_on:
            return
        actor = await actor_of(self.hass, self._system, self._context)
        await self._system.async_handle(SetAutoArming(enabled, actor))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
