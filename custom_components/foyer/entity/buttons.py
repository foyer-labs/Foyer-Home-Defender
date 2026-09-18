"""``button.foyer_acknowledge`` (SPEC §13): I have seen it.

Deferred out of Phase 1 by decision 59, for a reason that has now been
answered: a button cannot carry a code, so whether it could exist at all
depended on the code policy for acknowledging. It needs none by default
(decision 77) — §7.2 already acknowledges from a push notification, which
carries no code either — so here it is.

It honours the policy all the same. An installation that has raised
``acknowledge`` gets a button that refuses, visibly and in the log, which is
the honest behaviour: a button that quietly did nothing would be worse than no
button, and one that ignored the policy would not be a policy.

One press acknowledges whatever is pending: the intrusion incident and every
technical alarm at once (§5.6, §5.5, part 2 decision 11). They are different
channels with different acknowledgements, and the person pressing the button
has seen both.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..core.models import AcknowledgeIncident, AcknowledgeTechnical, Reason
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, actor_of, hub_device, raise_if_rejected

# Pressing with nothing to acknowledge is not an error worth raising: it is
# somebody checking. Everything else is reported.
_QUIET = (Reason.NOTHING_TO_ACKNOWLEDGE,)


async def async_setup_buttons(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities([FoyerAcknowledgeButton(system, entry.entry_id)])


class FoyerAcknowledgeButton(FoyerEntity, ButtonEntity):
    _attr_translation_key = "acknowledge"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_acknowledge"
        self.entity_id = f"button.{DOMAIN}_acknowledge"
        self._attr_device_info = hub_device(entry_id)

    async def async_press(self) -> None:
        actor = await actor_of(self.hass, self._system, self._context)
        refusal = None
        for event in (AcknowledgeIncident(actor), AcknowledgeTechnical(actor)):
            decision = await self._system.async_handle(event)
            if not decision.accepted and decision.reason not in _QUIET:
                refusal = decision
        if refusal is not None:
            raise_if_rejected(self._system, refusal)
