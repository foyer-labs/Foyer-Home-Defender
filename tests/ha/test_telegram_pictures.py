"""Camera pictures to a Telegram chat configured from the UI (decision 158).

Since the Telegram bot integration moved to the UI, a chat is a notify
*entity*, which carries a title and a message and nothing else, and the old
`notify.telegram` service that took a `photo` is deprecated. The text of an
alarm arrived and its pictures were dropped without a word. They now go
through the integration's own `telegram_bot.send_photo`, which takes that
same entity and a file; any other notify entity says in the log that it
received no picture.
"""

from __future__ import annotations

import logging

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from .conftest import ZONE
from .test_part3 import _allow_media
from .test_part12 import (  # noqa: F401 - `pictures` is a fixture
    DINING,
    KITCHEN,
    _arm,
    _config,
    _save,
    _settle,
    pictures,
)

CHAT = "notify.family_chat"


def _chat(hass, platform: str = "telegram_bot") -> None:
    """A notify entity, as the integration named by `platform` creates it."""
    er.async_get(hass).async_get_or_create(
        "notify", platform, "chat-1", suggested_object_id="family_chat"
    )
    hass.states.async_set(CHAT, "unknown")


async def _to_the_chat(hass, client, attachment: str = "telegram") -> None:
    profile = (await _config(client))["profiles"][0]
    params = profile["actions"][-1]["params"]
    params.update({"service": CHAT, "attachment": attachment, "data": {}})
    await _save(hass, client, "profile", profile)


async def test_a_telegram_chat_receives_one_photo_per_camera(
    hass,
    pictures,  # noqa: F811 - the fixture imported above
    freezer,
):
    _calls, client = pictures
    _chat(hass)
    _allow_media(hass)
    snapshots = async_mock_service(hass, "camera", "snapshot")
    texts = async_mock_service(hass, "notify", "send_message")
    photos = async_mock_service(hass, "telegram_bot", "send_photo")
    await _to_the_chat(hass, client)
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, photos, 1)

    assert [c.data["message"] for c in texts] == ["Alarm: Front door"]
    assert [c.data["entity_id"] for c in snapshots] == [KITCHEN, DINING]
    assert [c.data["caption"] for c in photos] == ["Kitchen", "Dining room"]
    for call, snapshot in zip(photos, snapshots, strict=True):
        assert call.data["entity_id"] == [CHAT]
        assert call.data["file"] == snapshot.data["filename"]


async def test_another_notify_entity_says_it_got_no_picture(
    hass,
    pictures,  # noqa: F811
    freezer,
    caplog,
):
    _calls, client = pictures
    _chat(hass, platform="mobile_app")
    texts = async_mock_service(hass, "notify", "send_message")
    photos = async_mock_service(hass, "telegram_bot", "send_photo")
    await _to_the_chat(hass, client, attachment="companion")
    await _arm(hass, freezer)

    with caplog.at_level(logging.WARNING):
        hass.states.async_set(ZONE, "on")
        await _settle(hass, texts, 1)

    assert [c.data["message"] for c in texts] == ["Alarm: Front door"]
    assert photos == []
    assert "carries no picture" in caplog.text


async def test_a_picture_that_fails_leaves_the_text_counted(
    hass,
    pictures,  # noqa: F811
    freezer,
):
    _calls, client = pictures
    _chat(hass)
    _allow_media(hass)
    async_mock_service(hass, "camera", "snapshot")
    texts = async_mock_service(hass, "notify", "send_message")
    attempts: list[str] = []

    async def refuse(call):
        attempts.append(call.data["caption"])
        raise RuntimeError("Telegram is down")

    hass.services.async_register("telegram_bot", "send_photo", refuse)
    await _to_the_chat(hass, client)
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, attempts, 1)

    assert [c.data["message"] for c in texts] == ["Alarm: Front door"]
    # The second camera is still tried after the first one failed.
    assert attempts == ["Kitchen", "Dining room"]


async def test_the_actions_own_camera_reaches_a_telegram_chat(
    hass,
    pictures,  # noqa: F811
    freezer,
):
    _calls, client = pictures
    _chat(hass)
    _allow_media(hass)
    snapshots = async_mock_service(hass, "camera", "snapshot")
    texts = async_mock_service(hass, "notify", "send_message")
    photos = async_mock_service(hass, "telegram_bot", "send_photo")
    profile = (await _config(client))["profiles"][0]
    profile["actions"][-1]["params"].update(
        {
            "service": CHAT,
            "attachment": "telegram",
            "data": {},
            "images": "fixed",
            "camera_entity_id": KITCHEN,
        }
    )
    await _save(hass, client, "profile", profile)
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, photos, 0)

    assert [c.data["message"] for c in texts] == ["Alarm: Front door"]
    assert len(photos) == 1
    assert photos[0].data["entity_id"] == [CHAT]
    assert photos[0].data["file"] == snapshots[0].data["filename"]
