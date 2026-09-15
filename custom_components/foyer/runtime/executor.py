"""Runs the actions of a Decision. The only module that performs side effects.

It interprets nothing: if an intent is in the Decision it runs, and if it is
not, nothing happens. Conditions, inheritance and suppression all belong to the
engine, so that the simulator's trace and the executor can never disagree.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.components.siren import SirenEntityFeature
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant

from .. import i18n
from ..core.models import ActionIntent, Decision

_LOGGER = logging.getLogger(__name__)

# How long a siren sounds as a chime: a blip, not an alarm.
CHIME_SIREN_SECONDS = 1


class Executor:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_run(self, decision: Decision) -> None:
        for intent in decision.actions:
            try:
                if intent.kind == "chime":
                    await self._async_chime(intent)
                else:
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
        if intent.variant:
            base = f"{base}_{intent.variant}"
        persistent_notification.async_create(
            self.hass,
            i18n.translate(strings, f"{base}.message", **intent.placeholders),
            title=i18n.translate(strings, f"{base}.title", **intent.placeholders),
            # One notification per moment: a fault must not be overwritten by
            # the "armed" that follows it a second later.
            notification_id=f"foyer_{intent.action_id}_{intent.moment.value}",
        )

    async def _async_chime(self, intent: ActionIntent) -> None:
        """Play the chime where the Decision says (§6.6). Never blocks: a chime
        that waits for a slow speaker must not delay anything after it."""
        params = intent.params
        targets: tuple[str, ...] = tuple(params.get("targets") or ())
        players = [t for t in targets if t.startswith("media_player.")]
        sirens = [t for t in targets if t.startswith("siren.")]
        if players and params.get("volume") is not None:
            await self._call(
                "media_player",
                "volume_set",
                {"entity_id": players, "volume_level": params["volume"] / 100},
            )
        if players and params.get("mode") == "speech" and params.get("tts_entity"):
            await self._call(
                "tts",
                "speak",
                {
                    "entity_id": params["tts_entity"],
                    "media_player_entity_id": players,
                    "message": intent.placeholders.get("zone", ""),
                },
            )
        elif players and params.get("sound"):
            await self._call(
                "media_player",
                "play_media",
                {
                    "entity_id": players,
                    "media_content_id": params["sound"],
                    "media_content_type": "music",
                },
            )
        for siren in sirens:
            state = self.hass.states.get(siren)
            features = (
                int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) if state else 0
            )
            if not features & SirenEntityFeature.DURATION:
                # Without a duration the siren would sound until someone
                # stopped it: that is an alarm, not a chime. Say so instead.
                _LOGGER.warning(
                    "Foyer: %s cannot sound for a set duration; skipped as chime",
                    siren,
                )
                continue
            await self._call(
                "siren",
                "turn_on",
                {"entity_id": siren, "duration": CHIME_SIREN_SECONDS},
            )

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        await self.hass.services.async_call(domain, service, data, blocking=False)
