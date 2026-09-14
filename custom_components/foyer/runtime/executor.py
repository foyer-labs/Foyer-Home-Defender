"""Runs the actions of a Decision. The only module that performs side effects.

It interprets nothing: if an intent is in the Decision it runs, and if it is
not, nothing happens. Conditions, inheritance and suppression all belong to the
engine, so that the simulator's trace and the executor can never disagree.
"""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant

from .. import i18n
from ..core.models import ActionIntent, Decision

_LOGGER = logging.getLogger(__name__)


class Executor:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_run(self, decision: Decision) -> None:
        for intent in decision.actions:
            try:
                await self._async_run_one(intent)
            except Exception:  # one failed action must not stop the others
                _LOGGER.exception("Foyer action %s failed", intent.action_id)

    async def _async_run_one(self, intent: ActionIntent) -> None:
        if intent.kind != "notification":
            _LOGGER.error("Foyer: no executor for action kind %r", intent.kind)
            return

        strings = await self.hass.async_add_executor_job(
            i18n.load_strings, self.hass.config.language
        )
        base = f"notification.{intent.moment.value}"
        persistent_notification.async_create(
            self.hass,
            i18n.translate(strings, f"{base}.message", **intent.placeholders),
            title=i18n.translate(strings, f"{base}.title", **intent.placeholders),
            notification_id=f"foyer_{intent.action_id}",
        )
