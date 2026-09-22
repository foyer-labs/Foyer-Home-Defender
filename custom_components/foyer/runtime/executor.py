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

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import logging
import os
import secrets
from typing import Any

from homeassistant.components.siren import SirenEntityFeature
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util, slugify

from .. import i18n
from ..const import ACK_ACTION, CANCEL_ACTION, CANCEL_PENDING_KEY
from ..core.models import (
    ATTACH_TELEGRAM,
    DEFAULT_CAMERA_DIR,
    ActionIntent,
    ActionKind,
    Decision,
    Moment,
)
from . import notices

_LOGGER = logging.getLogger(__name__)

# How long a siren sounds as a chime: a blip, not an alarm.
CHIME_SIREN_SECONDS = 1

# How long a snapshot may take before the notification leaves without it.
SNAPSHOT_TIMEOUT = 10

# The channel kinds that show a picture (§6.2.1, decision 94 applied to an
# address book). A push and a chat do; an SMS, a voice call or a channel the
# household called "other" would turn each camera into another text or
# another call.
PICTURE_KINDS: frozenset[str] = frozenset({"push", "chat"})

# What the notification of a picture does not take from its channel: the
# buttons, which belong to the text, and the `tag` of the Companion app, under
# which a second notification replaces the first. The picture would take the
# place of the message that carries the acknowledgement.
PICTURE_DROPPED_KEYS: frozenset[str] = frozenset({"actions", "tag"})

# How long to wait before the one retry a failed send gets (part 1 decision
# 4). Short, because an escalation step is worth seconds and not minutes: it
# exists for the transport that is not ready a second after a restart, not
# for the channel that has been dead for a week.
NOTIFY_RETRY_SECONDS = 3


@dataclass(frozen=True, slots=True)
class ActionResult:
    """What one intent did, for the log (§10.2, category ``action``)."""

    action_id: str
    kind: str
    ok: bool
    error: str | None = None
    # What each contact channel this action used actually did (§12.2). The
    # send is the only honest test of a channel there is — a service that is
    # in the registry can still fail every time it is called — so the
    # outcome is carried back and the engine counts it. Keyed
    # "<contact_id>:<channel_id>", empty for everything that is not a
    # notification to the address book.
    sends: Mapping[str, bool] = field(default_factory=dict)


class Executor:
    """``language`` is the language Foyer speaks in what it sends out (§15.1):
    the notification text and anything else it writes for a person. None means
    the language Home Assistant itself runs in. It is given here rather than
    looked up because the configuration is not this layer's to read."""

    def __init__(self, hass: HomeAssistant, language: str | None = None) -> None:
        self.hass = hass
        self._language = language

    @property
    def language(self) -> str:
        # Read now, not at setup: left empty, the setting means "whatever
        # Home Assistant is speaking", and Home Assistant may have changed
        # language since Foyer was loaded.
        return self._language or self.hass.config.language

    async def async_run(self, decision: Decision) -> list[ActionResult]:
        results: list[ActionResult] = []
        for intent in decision.actions:
            # A local, not a field on this object: two decisions interleave
            # here the moment either awaits a service call, and a shared
            # accumulator would give one decision's send outcomes to the
            # other — losing a dead channel, or counting one failure twice
            # and breaking a working channel at half the threshold.
            #
            # It is read back whether the action raised or not: a
            # notification to three contacts that failed for one of them has
            # still told the other two something true about their channels.
            sends: dict[str, bool] = {}
            try:
                await self._async_run_one(intent, sends)
                results.append(
                    ActionResult(intent.action_id, intent.kind, True, sends=sends)
                )
            except Exception as err:  # one failed action must not stop the others
                _LOGGER.exception("Foyer action %s failed", intent.action_id)
                results.append(
                    ActionResult(
                        intent.action_id, intent.kind, False, str(err), sends=sends
                    )
                )
        return results

    async def _async_run_one(
        self, intent: ActionIntent, sends: dict[str, bool]
    ) -> None:
        if intent.kind == ActionKind.NOTIFY.value:
            # The one action that learns something about a channel, and the
            # only one handed the map to write it into.
            await self._async_notify(intent, sends)
            return
        runner: Callable[[ActionIntent], Any] | None = {
            "chime": self._async_chime,
            "revert": self._async_revert,
            ActionKind.PERSISTENT_NOTIFICATION.value: self._async_persistent,
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
                i18n.load_strings, self.language
            )
            base = f"notification.{intent.moment.value}"
            if intent.variant:
                base = f"{base}_{intent.variant}"
            message = i18n.translate(strings, f"{base}.message", **intent.placeholders)
            title = title or i18n.translate(
                strings, f"{base}.title", **intent.placeholders
            )
        notices.async_create(
            self.hass,
            message,
            title=title or None,
            # One notification per action and moment: a fault must not be
            # overwritten by the "armed" that follows it a second later.
            notification_id=f"foyer_{intent.action_id}_{intent.moment.value}",
        )

    async def _async_text(self, intent: ActionIntent) -> tuple[str, str]:
        """The title and message of a notification that carries none.

        A profile's action carries text the user wrote, rendered in ``core``.
        What Foyer sends of its own — an automatic rule's countdown (§9.4) —
        carries none, and the words then come from ``translations/panel``,
        in the language the house speaks (§15.1, decision 73). The backend
        writes no user-visible string anywhere else either: this is the same
        lookup ``_async_persistent`` does, for the same reason.
        """
        strings = await self.hass.async_add_executor_job(
            i18n.load_strings, self.language
        )
        base = f"notification.{intent.moment.value}"
        if intent.variant:
            variant = f"{base}_{intent.variant}"
            # A missing key comes back as the key itself, so this is how the
            # variant is asked for without demanding that every moment have
            # one: an `arm` countdown reads differently from a `disarm` one,
            # and a moment with no variants falls back to its own text.
            key = f"{variant}.message"
            if i18n.translate(strings, key) != key:
                base = variant
        return (
            i18n.translate(strings, f"{base}.title", **intent.placeholders),
            i18n.translate(strings, f"{base}.message", **intent.placeholders),
        )

    async def _async_notify(self, intent: ActionIntent, sends: dict[str, bool]) -> None:
        """A notification, to a `notify.*` service or to the address book.

        Both forms exist and both keep existing (part 1 decision 8): the
        service an action names directly, and the contacts §7.1 gives an
        order of priority to. Which contacts, through which channel and with
        what that channel needs was all decided in ``core`` and arrives in
        ``recipients`` — this layer looks nothing up (INV-1).
        """
        service = str(intent.params.get("service") or "")
        data: dict[str, Any] = {"message": intent.params.get("message", "")}
        title = intent.params.get("title")
        if not data["message"] and intent.profile_id is None:
            # Only for what Foyer sends of its own — the countdown of §9.4.
            # A profile's action with an empty rendered message ("{zone}"
            # with no zone) must not fall through to a moment key that may
            # not exist: `i18n.translate` answers a missing key with the key
            # itself, and "notification.triggered.message" is not a sentence
            # to send somebody at four in the morning.
            title, data["message"] = await self._async_text(intent)
        if title:
            data["title"] = title
        extra = dict(intent.params.get("data") or {})
        if camera := intent.params.get("camera_entity_id"):
            if intent.params.get("attachment") == ATTACH_TELEGRAM:
                # Telegram's server fetches the picture itself, from outside
                # the house and with no session, so the proxy path below is
                # unreachable to it. The snapshot is taken here, now, because
                # a picture of the alarm is worth only the moment it shows.
                try:
                    path = await self._async_snapshot(
                        camera,
                        str(intent.params.get("directory") or DEFAULT_CAMERA_DIR),
                    )
                except (TimeoutError, HomeAssistantError, ValueError, OSError):
                    # The message goes without the picture. Losing the
                    # attachment is a disappointment; losing the notification
                    # that the house was broken into is not something a
                    # camera gets to decide.
                    _LOGGER.warning(
                        "Foyer could not snapshot %s for the notification; "
                        "sending the message without it",
                        camera,
                        exc_info=True,
                    )
                else:
                    extra.setdefault(
                        "photo", [{"file": path, "caption": data.get("message", "")}]
                    )
            else:
                # The live picture, through Home Assistant's authenticated
                # proxy: no file on disk, and nothing published to anyone who
                # guesses a URL (§6.2, part 3 decision 7).
                extra.setdefault("image", f"/api/camera_proxy/{camera}")
        if extra:
            data["data"] = extra
        cameras = tuple(str(c) for c in intent.params.get("cameras") or ())
        if omitted := int(intent.params.get("cameras_omitted") or 0):
            # Past four, the message says how many were left out (decision
            # 95), in the words of the house (decision 73). On the text,
            # because the text is the one message that always arrives.
            strings = await self.hass.async_add_executor_job(
                i18n.load_strings, self.language
            )
            note = i18n.translate(
                strings, "notification.cameras_omitted", count=omitted
            )
            data["message"] = f"{data['message']}\n{note}".strip()
        recipients = intent.params.get("recipients")
        if not recipients:
            await self._async_notify_call(service, data)
            if cameras:
                self._pictures_later(intent, cameras, ({"service": service},))
            return
        errors: list[str] = []
        # Which alarm the button would acknowledge. The technical channel is
        # never the intrusion one (§5.5), so a button on a smoke alarm must
        # not close an incident.
        kind = "technical" if intent.moment is Moment.TECHNICAL_RAISED else "incident"
        for recipient in recipients:
            key = f"{recipient.get('contact_id')}:{recipient.get('channel_id')}"
            try:
                await self._async_reach(recipient, dict(data), kind)
            except Exception as err:  # one dead channel must not stop the rest
                _LOGGER.exception(
                    "Foyer could not reach %s through %s",
                    recipient.get("contact_name"),
                    recipient.get("service"),
                )
                sends[key] = False
                errors.append(f"{recipient.get('contact_name')}: {err}")
            else:
                sends[key] = True
        if cameras:
            # After the text, whatever happened to it: the pictures are for
            # whoever the text was for, and a channel that refused the text
            # may still take a picture. Only a channel that shows pictures
            # gets them: a push or a chat. An SMS or a voice call would be
            # four more texts, or four more calls, saying the name of a camera.
            self._pictures_later(
                intent,
                cameras,
                tuple(r for r in recipients if r.get("kind") in PICTURE_KINDS),
            )
        if errors:
            raise HomeAssistantError("; ".join(errors))

    def _pictures_later(
        self,
        intent: ActionIntent,
        cameras: tuple[str, ...],
        recipients: tuple[Mapping[str, Any], ...],
    ) -> None:
        """Send the cameras after the text, off the alarm path (§6.2.1).

        Detached, because a snapshot is bounded at ten seconds and four of
        them must not hold back the siren that comes after this action in
        the same sequence. The text has already gone, and it is the one the
        acknowledgement and channel health are counted on (§12.2): nothing
        that happens here is counted against a channel.
        """
        if not recipients:
            return
        self.hass.async_create_background_task(
            self._async_pictures(intent, cameras, recipients),
            f"foyer_pictures_{intent.action_id}",
        )

    async def _async_pictures(
        self,
        intent: ActionIntent,
        cameras: tuple[str, ...],
        recipients: tuple[Mapping[str, Any], ...],
    ) -> None:
        """One notification per camera: its picture and its name (decision 94).

        The Companion app shows one image per notification, so each camera is
        a notification of its own. The transport the action names decides
        how the picture travels (decision 90): a live link to the
        authenticated proxy for the app, a snapshot file for Telegram, whose
        own server does the fetching from outside the house. A camera that
        does not answer costs its own picture and nothing else.
        """
        # A notify entity carries a title and a message and nothing else,
        # so it would receive the name of a camera and no picture: four
        # messages saying nothing, and — for Telegram — four snapshots taken
        # for nobody.
        recipients = tuple(
            r
            for r in recipients
            if self.hass.states.get(str(r.get("service") or "")) is None
        )
        if not recipients:
            return
        telegram = intent.params.get("attachment") == ATTACH_TELEGRAM
        files: dict[str, str | None] = {}
        if telegram:
            directory = str(intent.params.get("directory") or DEFAULT_CAMERA_DIR)
            taken = await asyncio.gather(
                *(self._async_snapshot(camera, directory) for camera in cameras),
                return_exceptions=True,
            )
            for camera, result in zip(cameras, taken, strict=True):
                if isinstance(result, BaseException):
                    _LOGGER.warning(
                        "Foyer could not snapshot %s for the notification; "
                        "its picture was not sent",
                        camera,
                        exc_info=result,
                    )
                    files[camera] = None
                else:
                    files[camera] = result
        for camera in cameras:
            if telegram and files.get(camera) is None:
                continue
            name = self._camera_name(camera)
            picture: dict[str, Any] = (
                {"photo": [{"file": files[camera], "caption": name}]}
                if telegram
                else {"image": f"/api/camera_proxy/{camera}"}
            )
            for recipient in recipients:
                service = str(recipient.get("service") or "")
                # The data of the channel, so the picture arrives the way that
                # channel delivers anything; but no buttons, and no `tag`,
                # under which the Companion app would replace the text (and
                # its acknowledgement button) with the picture.
                extra = {
                    key: value
                    for key, value in {
                        # The action's own transport data, then the channel's,
                        # merged in the order the text merged them.
                        **dict(intent.params.get("data") or {}),
                        **dict(recipient.get("data") or {}),
                    }.items()
                    if key not in PICTURE_DROPPED_KEYS
                }
                payload: dict[str, Any] = {
                    "message": name,
                    "data": {**extra, **picture},
                }
                if target := recipient.get("target"):
                    payload["target"] = target
                try:
                    await self._async_notify_call(service, payload)
                except Exception:  # one picture must not stop the next
                    _LOGGER.warning(
                        "Foyer: %s did not accept the picture of %s",
                        service,
                        camera,
                        exc_info=True,
                    )

    def _camera_name(self, camera: str) -> str:
        state = self.hass.states.get(camera)
        name = state.attributes.get("friendly_name") if state else None
        return str(name or camera)

    async def _async_reach(
        self, recipient: Mapping[str, Any], data: dict[str, Any], kind: str = "incident"
    ) -> None:
        """One contact, through one channel, with one retry (part 1 decision 4).

        The retry is here and not in the engine because it is an I/O
        failure, not a decision: a transport that is not ready a second
        after a restart is the case it exists for. Beyond that the
        escalation carries on at its own times — a channel that is dead
        stays dead, and the next step is what reaches somebody.
        """
        payload = dict(data)
        extra = {**dict(payload.get("data") or {}), **dict(recipient.get("data") or {})}
        if cancel := recipient.get("cancel"):
            # The Cancel button of §9.4: the same mechanism as the
            # acknowledgement below, with a different action id and a
            # different handler. It carries which countdown it would stop,
            # so the button on last night's notification cannot stop
            # tonight's arming.
            strings = await self.hass.async_add_executor_job(
                i18n.load_strings, self.language
            )
            if "actions" in extra:
                # This channel configures its own actions, so the button
                # would be dropped. Said out loud rather than swallowed: a
                # countdown nobody can stop from the notification is the
                # whole feature missing, quietly (§11.4's reasoning).
                _LOGGER.warning(
                    "Foyer: %s carries its own notification actions, so the "
                    "Cancel button was not added; the countdown can still be "
                    "stopped from the panel",
                    recipient.get("service"),
                )
            extra.setdefault(
                "actions",
                [
                    {
                        "action": CANCEL_ACTION,
                        "title": i18n.translate(strings, "notification.cancel"),
                        CANCEL_PENDING_KEY: cancel,
                        "foyer_contact": recipient.get("contact_id", ""),
                    }
                ],
            )
        if recipient.get("ack"):
            # The button that stops the escalation (§7.2). Only a channel
            # declared actionable carries it: a transport discards a key it
            # does not know without a word, and a button nobody can press is
            # worse than none.
            strings = await self.hass.async_add_executor_job(
                i18n.load_strings, self.language
            )
            extra.setdefault(
                "actions",
                [
                    {
                        "action": ACK_ACTION,
                        "title": i18n.translate(strings, "notification.acknowledge"),
                        # Who the button was offered to, so the log can name
                        # the contact that answered even when that contact
                        # names no Foyer user (part 1 decision 7), and which
                        # of the two escalations it would stop.
                        "foyer_contact": recipient.get("contact_id", ""),
                        "foyer_kind": kind,
                    }
                ],
            )
        if extra:
            payload["data"] = extra
        if target := recipient.get("target"):
            payload["target"] = target
        service = str(recipient.get("service") or "")
        try:
            await self._async_notify_call(service, payload)
        except Exception:
            # The retry waits, and the alarm does not wait with it. It runs
            # detached on purpose: this is awaited inside the decision, and
            # a sleep here would hold back the siren that comes after this
            # action in the same sequence — seconds spent on a phone that is
            # already not answering.
            _LOGGER.warning(
                "Foyer: %s did not accept the notification; one retry in %s s",
                service,
                NOTIFY_RETRY_SECONDS,
            )
            self.hass.async_create_background_task(
                self._async_retry(service, payload),
                f"foyer_notify_retry_{slugify(service)}",
            )
            raise

    async def _async_retry(self, service: str, payload: dict[str, Any]) -> None:
        """The one retry of part 1 decision 4, off the alarm path.

        For the transport that is not ready a second after a restart. What
        it cannot do is make the row already written say it worked: the log
        records the attempt that failed, and this one records its own
        outcome beside it.
        """
        await asyncio.sleep(NOTIFY_RETRY_SECONDS)
        try:
            await self._async_notify_call(service, payload)
        except Exception:
            _LOGGER.error("Foyer: %s refused the notification twice", service)
        else:
            _LOGGER.warning("Foyer: %s accepted the notification on the retry", service)

    async def _async_notify_call(self, service: str, data: dict[str, Any]) -> None:
        if self.hass.states.get(service) is not None:
            # A notify *entity*: one service for all of them (HA 2024.6+).
            # It carries a message and a title and nothing else — no target,
            # no transport data, no action button. Whatever else was asked
            # for is said out loud rather than dropped in silence, because a
            # channel that reports success while losing the button is the
            # discovery §11.4 exists to move earlier.
            lost = [key for key in ("data", "target") if data.get(key)]
            if lost:
                _LOGGER.warning(
                    "Foyer: %s is a notify entity, which carries only a title "
                    "and a message; %s was not sent. Use the notify service "
                    "behind it if this channel needs it",
                    service,
                    " and ".join(lost),
                )
            payload = {ATTR_ENTITY_ID: service, "message": data.get("message", "")}
            if title := data.get("title"):
                payload["title"] = title
            await self._call("notify", "send_message", payload)
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
        directory = str(intent.params.get("directory") or DEFAULT_CAMERA_DIR)
        record = intent.params.get("mode") == "record"
        path = await self._async_camera_path(
            entity_id, directory, "mp4" if record else "jpg"
        )
        data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id, "filename": path}
        if record and (duration := intent.params.get("duration")):
            data["duration"] = int(duration)
        await self._call("camera", "record" if record else "snapshot", data)

    async def _async_camera_path(
        self, entity_id: str, directory: str, suffix: str
    ) -> str:
        """Where a camera file goes, with the folder made and checked.

        The check is not a formality: ``camera.snapshot`` and telegram_bot
        both refuse a path outside ``allowlist_external_dirs``, and they say
        so at the moment of the alarm. Failing here names the setting.
        """
        stamp = dt_util.now().strftime("%Y%m%d-%H%M%S")
        # A few random characters too: two notifications at one moment take
        # the same camera in the same second, and one file rewritten under
        # the other's send is a picture that arrives empty (found in review).
        name = f"{slugify(entity_id)}-{stamp}-{secrets.token_hex(3)}.{suffix}"
        path = self.hass.config.path(directory, name)

        def _prepare() -> bool:
            # Both of these touch the filesystem, and `is_allowed_path` needs
            # the parent to exist to resolve it — so they belong together, off
            # the event loop.
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return self.hass.config.is_allowed_path(path)

        if not await self.hass.async_add_executor_job(_prepare):
            raise ValueError(
                f"{directory} is not an allowed path; add it to allowlist_external_dirs"
            )
        return path

    async def _async_snapshot(self, entity_id: str, directory: str) -> str:
        """One still, written and waited for, so it exists before it is sent."""
        path = await self._async_camera_path(entity_id, directory, "jpg")
        # Blocking, and the only blocking call in this file: whoever sends the
        # picture opens the file straight afterwards, and a still that is not
        # written yet is an attachment that silently does not arrive. Bounded,
        # because a camera that has stopped answering must not hold up the
        # rest of the alarm while it decides.
        async with asyncio.timeout(SNAPSHOT_TIMEOUT):
            await self._call(
                "camera",
                "snapshot",
                {ATTR_ENTITY_ID: entity_id, "filename": path},
                blocking=True,
            )
        return path

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

    async def _call(
        self, domain: str, service: str, data: dict[str, Any], *, blocking: bool = False
    ) -> None:
        await self.hass.services.async_call(domain, service, data, blocking=blocking)


def _entities(intent: ActionIntent) -> list[str]:
    value = intent.params.get("entity_ids") or intent.params.get("entity_id") or []
    return [value] if isinstance(value, str) else [str(v) for v in value]
