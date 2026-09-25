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
from homeassistant.helpers import entity_registry as er
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

# The Telegram bot integration. Since Home Assistant moved it to the UI, a
# chat is a notify *entity*, which carries a title and a message and nothing
# else; the old `notify.telegram` service that took a `photo` is deprecated.
# The integration's own `send_photo` takes that same entity and a file, so a
# Telegram picture goes through it (decision 158).
TELEGRAM_BOT = "telegram_bot"

# How long a notification may take to be accepted before it counts as
# failed. Long enough for a slow provider, short enough that the retry still
# means something.
NOTIFY_TIMEOUT = 20

# How long to wait before the one retry a failed send gets (part 1 decision
# 4). Short, because an escalation step is worth seconds and not minutes: it
# exists for the transport that is not ready a second after a restart, not
# for the channel that has been dead for a week.
NOTIFY_RETRY_SECONDS = 3


def _worded(strings: dict[str, Any], placeholders: Mapping[str, str]) -> dict[str, str]:
    """The placeholders as one of Foyer's own sentences wants them.

    ``operation`` is an identifier (§6.4) — the engine cannot translate and
    must not — and a message of Foyer's own says it in the house's words.
    One the translation files do not name stays as it came, rather than
    being dropped: a message that says `export_log` has still said what the
    person was made to do (decision 134).
    """
    values = dict(placeholders)
    if operation := values.get("operation"):
        key = f"operation.{operation}"
        worded = i18n.translate(strings, key)
        values["operation"] = operation if worded == key else worded
    return values


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
        self._cache: dict[str, dict[str, Any]] = {}

    async def _strings(self) -> dict[str, Any]:
        """The words of the house's language, read from disk once.

        Asked for per recipient on the alarm path — every button needs its
        label — and each ask was a hop to the executor for a file already in
        memory (second review).
        """
        language = self.language
        if language not in self._cache:
            self._cache[language] = await self.hass.async_add_executor_job(
                i18n.load_strings, language
            )
        return self._cache[language]

    @property
    def language(self) -> str:
        # Read now, not at setup: left empty, the setting means "whatever
        # Home Assistant is speaking", and Home Assistant may have changed
        # language since Foyer was loaded.
        return self._language or self.hass.config.language

    async def async_run(self, decision: Decision) -> list[ActionResult]:
        """Run every intent, and say how each went, in the Decision's order.

        A notification waits for its transport's answer — that answer is the
        only honest test of a channel (§11.4, §12.2) — so notifications run
        beside the rest rather than in front of it: a Telegram server taking
        ten seconds must not hold back the siren that comes after the
        notification in the same list (second review). Everything else runs
        in order, as the profile lists it.
        """
        pending: dict[int, asyncio.Task[ActionResult]] = {}
        results: dict[int, ActionResult] = {}
        for index, intent in enumerate(decision.actions):
            if intent.kind == ActionKind.NOTIFY.value:
                pending[index] = self.hass.async_create_task(
                    self._async_result(intent), eager_start=True
                )
            else:
                results[index] = await self._async_result(intent)
        for index, task in pending.items():
            results[index] = await task
        return [results[i] for i in range(len(decision.actions))]

    async def _async_result(self, intent: ActionIntent) -> ActionResult:
        # A local, not a field on this object: two decisions interleave here
        # the moment either awaits a service call, and a shared accumulator
        # would give one decision's send outcomes to the other — losing a
        # dead channel, or counting one failure twice and breaking a working
        # channel at half the threshold.
        #
        # It is read back whether the action raised or not: a notification
        # to three contacts that failed for one of them has still told the
        # other two something true about their channels.
        sends: dict[str, bool] = {}
        try:
            await self._async_run_one(intent, sends)
        except Exception as err:  # one failed action must not stop the others
            _LOGGER.exception("Foyer action %s failed", intent.action_id)
            return ActionResult(
                intent.action_id, intent.kind, False, str(err), sends=sends
            )
        return ActionResult(intent.action_id, intent.kind, True, sends=sends)

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
            strings = await self._strings()
            base = f"notification.{intent.moment.value}"
            if intent.variant:
                base = f"{base}_{intent.variant}"
            values = _worded(strings, intent.placeholders)
            message = i18n.translate(strings, f"{base}.message", **values)
            title = title or i18n.translate(strings, f"{base}.title", **values)
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
        strings = await self._strings()
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
        values = _worded(strings, intent.placeholders)
        return (
            i18n.translate(strings, f"{base}.title", **values),
            i18n.translate(strings, f"{base}.message", **values),
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
            strings = await self._strings()
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

        async def reach(recipient: Mapping[str, Any]) -> None:
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

        # Everybody at once. Each send now waits for its transport's answer,
        # and one after the other a gateway that hangs would have made the
        # next person twenty seconds late, and the one after forty (second
        # review).
        await asyncio.gather(*(reach(r) for r in recipients))
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
        # messages saying nothing. A Telegram chat is the exception, sent
        # through its integration's own service (decision 158); any other
        # entity is told in the log rather than skipped in silence, because
        # "the text came and the picture did not" is otherwise a mystery.
        telegram = intent.params.get("attachment") == ATTACH_TELEGRAM
        kept: list[Mapping[str, Any]] = []
        for recipient in recipients:
            service = str(recipient.get("service") or "")
            if self.hass.states.get(service) is None or (
                telegram and self._is_telegram(service)
            ):
                kept.append(recipient)
            else:
                _LOGGER.warning(
                    "Foyer: %s is a notify entity, which carries no picture; "
                    "the cameras were not sent to it. %s",
                    service,
                    "Choose the Telegram attachment for a Telegram chat"
                    if self._is_telegram(service)
                    else "Use the notify service behind it to receive them",
                )
        recipients = tuple(kept)
        if not recipients:
            return
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
                if self.hass.states.get(service) is not None:
                    # A Telegram chat, the only entity kept above.
                    await self._async_send_photo(service, str(files[camera]), name)
                    continue
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
            strings = await self._strings()
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
            strings = await self._strings()
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
            # discovery §11.4 exists to move earlier. The one exception is a
            # Telegram chat's photo, which its integration sends on its own.
            extra = dict(data.get("data") or {})
            photos = extra.pop("photo", None) if self._is_telegram(service) else None
            lost = [
                key
                for key, value in (("data", extra), ("target", data.get("target")))
                if value
            ]
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
            await self._call_and_wait("notify", "send_message", payload)
            if photos and not isinstance(photos, list):
                photos = [photos]
            for photo in photos or ():
                # After the text, and never counted against it: the message
                # is what the acknowledgement and channel health rest on.
                await self._async_send_photo(
                    service, str(photo.get("file")), str(photo.get("caption") or "")
                )
            return
        domain, _, name = service.partition(".")
        if not name:
            raise ValueError(f"not a notify service: {service!r}")
        await self._call_and_wait(domain, name, data)

    def _is_telegram(self, service: str) -> bool:
        """Whether a notify entity is a chat of the Telegram bot integration."""
        entry = er.async_get(self.hass).async_get(service)
        return entry is not None and entry.platform == TELEGRAM_BOT

    async def _async_send_photo(self, entity_id: str, file: str, caption: str) -> None:
        """A snapshot to a Telegram chat, through the bot's own service.

        A picture that does not go is logged and costs nothing else: the text
        has already gone, and it is the one that matters (§6.2.1).
        """
        try:
            await self._call_and_wait(
                TELEGRAM_BOT,
                "send_photo",
                {ATTR_ENTITY_ID: [entity_id], "file": file, "caption": caption},
            )
        except Exception:
            _LOGGER.warning(
                "Foyer: %s did not accept the picture %s",
                entity_id,
                file,
                exc_info=True,
            )

    async def _call_and_wait(
        self, domain: str, service: str, data: dict[str, Any]
    ) -> None:
        """A notification, waited for, within a bound.

        Not fire-and-forget: a transport that accepts the call and then fails
        — a revoked Telegram token, a push the provider refused — only logs
        in Home Assistant, and Foyer counted it as sent. The test button said
        a dead channel worked, channel health never saw it fail, and the one
        retry never ran (second review). Bounded, because a transport that
        never answers is a failure too.
        """
        async with asyncio.timeout(NOTIFY_TIMEOUT):
            await self.hass.services.async_call(domain, service, data, blocking=True)

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
        folder = self._camera_folder(directory)
        path = os.path.join(folder, name)

        def _prepare() -> bool:
            # Both of these touch the filesystem, and `is_allowed_path` needs
            # the parent to exist to resolve it — so they belong together, off
            # the event loop.
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return self.hass.config.is_allowed_path(path)

        if not await self.hass.async_add_executor_job(_prepare):
            raise ValueError(
                f"{folder} is not an allowed path; add it to allowlist_external_dirs"
            )
        return path

    def _camera_folder(self, directory: str) -> str:
        """The camera folder as a path on this machine.

        A folder that starts with `media` — the default, `media/foyer`, among
        them — means Home Assistant's own media folder, wherever this
        installation keeps it: `<config>/media` on a plain install, but
        `/media` on Home Assistant OS, where `<config>/media` is not an
        allowed path and every snapshot was refused (decision 159). Home
        Assistant allows its media folders by default, and shows them under
        *Media*. Anything else is relative to the configuration folder, or
        absolute as written.
        """
        head, _, rest = directory.replace("\\", "/").partition("/")
        media = self.hass.config.media_dirs
        if head == "media" and media:
            base = media.get("local") or next(iter(media.values()))
            return os.path.join(base, *filter(None, rest.split("/")))
        return self.hass.config.path(directory)

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
            # the same path the notify action uses — off the path of what
            # comes after the chime, since a notification now waits for its
            # transport's answer.
            self.hass.async_create_background_task(
                self._async_chime_notify(notifier, zone),
                f"foyer_chime_{slugify(notifier)}",
            )

    async def _async_chime_notify(self, notifier: str, zone: str) -> None:
        try:
            await self._async_notify_call(notifier, {"message": zone})
        except Exception:
            _LOGGER.warning(
                "Foyer: %s did not accept the chime", notifier, exc_info=True
            )

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
