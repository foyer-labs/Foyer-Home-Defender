"""Runs the actions of a Decision. The only module that performs side effects.

It interprets nothing: if an intent is in the Decision it runs, and if it is
not, nothing happens. Conditions, inheritance, templates, suppression and
durations all belong to the engine, so that the simulator's trace and the
executor can never disagree.

Every call reports whether it worked, because "the notification channel was
misconfigured" must not be discovered during the emergency (§11.4). Part 4
turns those reports into the ``action`` log category.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import os
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.components.siren import SirenEntityFeature
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util, slugify

from .. import i18n
from ..core.models import ActionIntent, ActionKind, Decision

_LOGGER = logging.getLogger(__name__)

# How long a siren sounds as a chime: a blip, not an alarm.
CHIME_SIREN_SECONDS = 1


@dataclass(frozen=True, slots=True)
class ActionResult:
    """What one intent did, for the log (§10.2, category ``action``)."""

    action_id: str
    kind: str
    ok: bool
    error: str | None = None


class Executor:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_run(self, decision: Decision) -> list[ActionResult]:
        results: list[ActionResult] = []
        for intent in decision.actions:
            try:
                await self._async_run_one(intent)
                results.append(ActionResult(intent.action_id, intent.kind, True))
            except Exception as err:  # one failed action must not stop the others
                _LOGGER.exception("Foyer action %s failed", intent.action_id)
                results.append(
                    ActionResult(intent.action_id, intent.kind, False, str(err))
                )
        return results

    async def _async_run_one(self, intent: ActionIntent) -> None:
        runner: Callable[[ActionIntent], Any] | None = {
            "chime": self._async_chime,
            "revert": self._async_revert,
            ActionKind.PERSISTENT_NOTIFICATION.value: self._async_persistent,
            ActionKind.NOTIFY.value: self._async_notify,
            ActionKind.SIREN.value: self._async_siren,
            ActionKind.LIGHT.value: self._async_light,
            ActionKind.CAMERA.value: self._async_camera,
            ActionKind.SCENE.value: self._async_scene,
            ActionKind.SWITCH.value: self._async_switch,
            ActionKind.TTS.value: self._async_tts,
            ActionKind.CALL_SERVICE.value: self._async_call_service,
        }.get(intent.kind)
        if runner is None:
            _LOGGER.error("Foyer: no executor for action kind %r", intent.kind)
            return
        await runner(intent)

    # --- notifications --------------------------------------------------------

    async def _async_persistent(self, intent: ActionIntent) -> None:
        """A persistent notification. With no text of its own it uses the
        translated message for the moment, exactly as Phase 0 did."""
        title = str(intent.params.get("title") or "")
        message = str(intent.params.get("message") or "")
        if not message:
            strings = await self.hass.async_add_executor_job(
                i18n.load_strings, self.hass.config.language
            )
            base = f"notification.{intent.moment.value}"
            if intent.variant:
                base = f"{base}_{intent.variant}"
            message = i18n.translate(strings, f"{base}.message", **intent.placeholders)
            title = title or i18n.translate(
                strings, f"{base}.title", **intent.placeholders
            )
        persistent_notification.async_create(
            self.hass,
            message,
            title=title or None,
            # One notification per action and moment: a fault must not be
            # overwritten by the "armed" that follows it a second later.
            notification_id=f"foyer_{intent.action_id}_{intent.moment.value}",
        )

    async def _async_notify(self, intent: ActionIntent) -> None:
        """A `notify.*` service or notify entity, directly: no contact book and
        no escalation before Phase 4 (Phase 1 prompt)."""
        service = str(intent.params.get("service") or "")
        data: dict[str, Any] = {"message": intent.params.get("message", "")}
        if title := intent.params.get("title"):
            data["title"] = title
        extra = dict(intent.params.get("data") or {})
        if camera := intent.params.get("camera_entity_id"):
            # The live picture, through Home Assistant's authenticated proxy:
            # no file on disk, and nothing published to anyone who guesses a
            # URL (§6.2, part 3 decision 7).
            extra.setdefault("image", f"/api/camera_proxy/{camera}")
        if extra:
            data["data"] = extra
        await self._async_notify_call(service, data)

    async def _async_notify_call(self, service: str, data: dict[str, Any]) -> None:
        if self.hass.states.get(service) is not None:
            # A notify *entity*: one service for all of them (HA 2024.6+).
            await self._call(
                "notify",
                "send_message",
                {ATTR_ENTITY_ID: service, "message": data.get("message", "")},
            )
            return
        domain, _, name = service.partition(".")
        if not name:
            raise ValueError(f"not a notify service: {service!r}")
        await self._call(domain, name, data)

    # --- the world ------------------------------------------------------------

    async def _async_siren(self, intent: ActionIntent) -> None:
        entity_ids = _entities(intent)
        duration = intent.params.get("duration")
        for entity_id in entity_ids:
            if entity_id.startswith("switch."):
                await self._call("switch", "turn_on", {ATTR_ENTITY_ID: entity_id})
                continue
            data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id}
            features = self._features(entity_id)
            if duration and features & SirenEntityFeature.DURATION:
                data["duration"] = int(duration)
            if (
                tone := intent.params.get("tone")
            ) and features & SirenEntityFeature.TONES:
                data["tone"] = tone
            await self._call("siren", "turn_on", data)

    async def _async_light(self, intent: ActionIntent) -> None:
        data: dict[str, Any] = {ATTR_ENTITY_ID: _entities(intent)}
        if (brightness := intent.params.get("brightness")) is not None:
            data["brightness"] = int(brightness)
        if rgb := intent.params.get("rgb_color"):
            data["rgb_color"] = list(rgb)
        if flash := intent.params.get("flash"):
            data["flash"] = flash
        await self._call("light", "turn_on", data)

    async def _async_scene(self, intent: ActionIntent) -> None:
        await self._call(
            "scene", "turn_on", {ATTR_ENTITY_ID: intent.params.get("entity_id")}
        )

    async def _async_switch(self, intent: ActionIntent) -> None:
        state = str(intent.params.get("state", "on"))
        for entity_id in _entities(intent):
            domain = entity_id.split(".", 1)[0]
            await self._call(domain, f"turn_{state}", {ATTR_ENTITY_ID: entity_id})

    async def _async_revert(self, intent: ActionIntent) -> None:
        """Switch off what an action switched on: the siren cutoff, a disarm,
        or an auto-revert running out. The engine decided; this only calls."""
        state = str(intent.params.get("state", "off"))
        for entity_id in intent.params.get("entity_ids", ()):
            domain = entity_id.split(".", 1)[0]
            await self._call(domain, f"turn_{state}", {ATTR_ENTITY_ID: entity_id})

    async def _async_tts(self, intent: ActionIntent) -> None:
        await self._call(
            "tts",
            "speak",
            {
                ATTR_ENTITY_ID: intent.params.get("entity_id"),
                "media_player_entity_id": intent.params.get(
                    "media_player_entity_ids", []
                ),
                "message": intent.params.get("message", ""),
            },
        )

    async def _async_call_service(self, intent: ActionIntent) -> None:
        """The escape hatch of §6.2: anything Foyer does not model natively."""
        params = intent.params
        await self.hass.services.async_call(
            str(params["domain"]),
            str(params["service"]),
            dict(params.get("data") or {}),
            blocking=False,
            target=dict(params.get("target") or {}) or None,
        )

    async def _async_camera(self, intent: ActionIntent) -> None:
        """A snapshot or a recording, under the configured folder.

        Never under ``www``: Home Assistant serves that without authentication
        and the inside of a house is not something to publish. A notification
        that wants a picture attaches ``/api/camera_proxy/<entity>``, which is
        authenticated and needs no file at all.
        """
        entity_id = str(intent.params.get("entity_id") or "")
        directory = str(intent.params.get("directory") or "media/foyer")
        record = intent.params.get("mode") == "record"
        stamp = dt_util.now().strftime("%Y%m%d-%H%M%S")
        name = f"{slugify(entity_id)}-{stamp}.{'mp4' if record else 'jpg'}"
        path = self.hass.config.path(directory, name)
        await self.hass.async_add_executor_job(os.makedirs, os.path.dirname(path), True)
        if not self.hass.config.is_allowed_path(path):
            raise ValueError(
                f"{directory} is not an allowed path; add it to allowlist_external_dirs"
            )
        data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id, "filename": path}
        if record and (duration := intent.params.get("duration")):
            data["duration"] = int(duration)
        await self._call("camera", "record" if record else "snapshot", data)

    # --- chime (§6.6) ---------------------------------------------------------

    async def _async_chime(self, intent: ActionIntent) -> None:
        """Play the chime where the Decision says. Never blocks: a chime that
        waits for a slow speaker must not delay anything after it."""
        params = intent.params
        targets: tuple[str, ...] = tuple(params.get("targets") or ())
        zone = intent.placeholders.get("zone", "")
        players = [t for t in targets if t.startswith("media_player.")]
        sirens = [t for t in targets if t.startswith("siren.")]
        notifiers = [t for t in targets if t.startswith("notify.")]
        if players and params.get("volume") is not None:
            await self._call(
                "media_player",
                "volume_set",
                {ATTR_ENTITY_ID: players, "volume_level": params["volume"] / 100},
            )
        if players and params.get("mode") == "speech" and params.get("tts_entity"):
            await self._call(
                "tts",
                "speak",
                {
                    ATTR_ENTITY_ID: params["tts_entity"],
                    "media_player_entity_id": players,
                    "message": zone,
                },
            )
        elif players and params.get("sound"):
            await self._call(
                "media_player",
                "play_media",
                {
                    ATTR_ENTITY_ID: players,
                    "media_content_id": params["sound"],
                    "media_content_type": "music",
                },
            )
        for siren in sirens:
            if not self._features(siren) & SirenEntityFeature.DURATION:
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
                {ATTR_ENTITY_ID: siren, "duration": CHIME_SIREN_SECONDS},
            )
        for notifier in notifiers:
            # The free channels the house already has (decision 60), through
            # the same path the notify action uses.
            await self._async_notify_call(notifier, {"message": zone})

    # --- plumbing -------------------------------------------------------------

    def _features(self, entity_id: str) -> int:
        state = self.hass.states.get(entity_id)
        return int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) if state else 0

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        await self.hass.services.async_call(domain, service, data, blocking=False)


def _entities(intent: ActionIntent) -> list[str]:
    value = intent.params.get("entity_ids") or intent.params.get("entity_id") or []
    return [value] if isinstance(value, str) else [str(v) for v in value]
