"""Phase 1 part 3 inside Home Assistant: profiles, actions, bypass.

The pure suite proves what the engine decides; this proves that a decision
becomes a real service call, that the migration keeps an installation's
notifications, and that a bypass round-trips over the WebSocket API.
"""

from __future__ import annotations

import os
from pathlib import Path

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY, ZONE
from .test_integration import _notifications
from .test_part2 import _advance, _set, _state, _ws

SIREN = "siren.outdoor"


async def _profile(client, actions: list[dict], name: str = "Full") -> dict:
    result = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "profile",
            "item": {"name": name, "severity": 3, "actions": actions},
        },
    )
    assert result["success"], result
    return result


def _allow_media(hass) -> None:
    """Let Foyer write under <config>/media, as a real installation must."""
    hass.config.allowlist_external_dirs = {
        str(Path(hass.config.path("media")).resolve())
    }


def _usable(folder: str) -> tuple[bool, str]:
    path = Path(folder)
    return (
        path.is_dir() and os.access(path, os.R_OK | os.W_OK | os.X_OK),
        oct(path.stat().st_mode) if path.exists() else "missing",
    )


def _siren_action(**params) -> dict:
    return {
        "kind": "siren",
        "moments": ["triggered"],
        "name": "Outdoor siren",
        "params": {"entity_ids": [SIREN], "duration": 60, **params},
        "conditions": [],
        "condition_mode": "all",
        "enabled": True,
    }


async def _use_profile(hass, client, profile_id: str) -> None:
    """Make the new profile the global default."""
    config = await _ws(client, {"type": "foyer/config"})
    settings = dict(config["config"]["settings"], default_profile_id=profile_id)
    result = await _ws(client, {"type": "foyer/config/settings", "settings": settings})
    assert result["success"], result
    await hass.async_block_till_done()


async def _arm_away(hass, freezer) -> None:
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    await _advance(hass, freezer, 31)  # the seeded area has a 30 s exit delay


async def test_a_profile_action_reaches_the_service_registry(
    hass, loaded, hass_ws_client, freezer
):
    """§6.2 end to end: the engine decides, the executor calls, nothing else."""
    calls = async_mock_service(hass, "siren", "turn_on")
    off = async_mock_service(hass, "siren", "turn_off")
    hass.states.async_set(SIREN, "off", {"supported_features": 0})
    client = await hass_ws_client(hass)
    await _profile(client, [_siren_action()])
    await hass.async_block_till_done()
    profile = hass.data[DOMAIN].config.profiles[-1]
    await _use_profile(hass, client, profile.id)

    await _arm_away(hass, freezer)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    await _set(hass, ZONE, "on", friendly_name="Front door")
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.TRIGGERED
    assert len(calls) == 1
    assert calls[0].data["entity_id"] == SIREN

    # Disarming stops the sounder it started (§5.2).
    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": PANEL_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(off) == 1
    assert off[0].data["entity_id"] == SIREN


async def test_a_delayed_action_runs_after_the_wait(
    hass, loaded, hass_ws_client, freezer
):
    """Part 3 decision 5: a held sequence is state, and the scheduler wakes."""
    calls = async_mock_service(hass, "siren", "turn_on")
    async_mock_service(hass, "siren", "turn_off")
    hass.states.async_set(SIREN, "off", {"supported_features": 0})
    client = await hass_ws_client(hass)
    delay = {
        "kind": "delay",
        "moments": ["triggered"],
        "name": "",
        "params": {"seconds": 30},
        "conditions": [],
        "condition_mode": "all",
        "enabled": True,
    }
    await _profile(client, [delay, _siren_action()])
    await hass.async_block_till_done()
    await _use_profile(hass, client, hass.data[DOMAIN].config.profiles[-1].id)

    await _arm_away(hass, freezer)
    await _set(hass, ZONE, "on", friendly_name="Front door")
    assert calls == []
    assert len(hass.data[DOMAIN].state.pending_runs) == 1

    await _advance(hass, freezer, 31)
    assert len(calls) == 1
    assert hass.data[DOMAIN].state.pending_runs == ()


async def test_bypassing_a_zone_over_the_websocket_lets_it_arm(
    hass, loaded, hass_ws_client
):
    """SPEC §16: the panel and the card send this; the engine decides."""
    client = await hass_ws_client(hass)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    blocked = await _ws(
        client, {"type": "foyer/arm", "area_id": hass.data[DOMAIN].config.areas[0].id}
    )
    assert not blocked["success"]
    assert blocked["reason"] == "zone_open"

    zone_id = hass.data[DOMAIN].config.zones[0].id
    result = await _ws(
        client, {"type": "foyer/bypass", "zone_id": zone_id, "seconds": 3600}
    )
    assert result["success"], result
    [zone] = [z for z in result["state"]["zones"] if z["id"] == zone_id]
    assert zone["bypassed"] == "manual"
    assert zone["bypass_until"] is not None

    armed = await _ws(
        client, {"type": "foyer/arm", "area_id": hass.data[DOMAIN].config.areas[0].id}
    )
    assert armed["success"], armed


async def test_a_timed_bypass_returns_on_its_own(hass, loaded, hass_ws_client, freezer):
    client = await hass_ws_client(hass)
    zone_id = hass.data[DOMAIN].config.zones[0].id
    await _ws(client, {"type": "foyer/bypass", "zone_id": zone_id, "seconds": 60})
    assert hass.data[DOMAIN].state.bypassed

    await _advance(hass, freezer, 61)
    assert hass.data[DOMAIN].state.bypassed == {}


async def test_a_phase_0_installation_keeps_its_notifications(
    hass, entry, hass_storage
):
    """The 3.1 -> 4.1 migration moves the Phase 0 action into the default
    profile: an installation that updates hears what it heard yesterday."""
    from custom_components.foyer.core.models import ActionKind
    from custom_components.foyer.store.config_store import STORAGE_KEY
    from custom_components.foyer.store.migrations import migrate
    from custom_components.foyer.store.schema import (
        STORAGE_MINOR_VERSION,
        STORAGE_VERSION,
    )

    from .test_integration import PHASE_0_DOCUMENT

    alpha_4 = migrate((1, 1), (3, 1), PHASE_0_DOCUMENT["data"])
    hass_storage[STORAGE_KEY] = {
        "version": 3,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": alpha_4,
    }
    hass.states.async_set(ZONE, "off")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (STORAGE_VERSION, STORAGE_MINOR_VERSION) == (7, 1)
    config = hass.data[DOMAIN].config
    [profile] = config.profiles
    assert config.settings.default_profile_id == profile.id
    [action] = profile.actions
    assert action.kind is ActionKind.PERSISTENT_NOTIFICATION
    assert "armed" in {m.value for m in action.moments}


async def test_a_persistent_notification_still_reaches_home_assistant(
    hass, loaded, freezer
):
    """The Phase 0 behaviour, now produced by the default profile."""
    await _arm_away(hass, freezer)

    assert any(
        "Foyer" in str(notification.get("title", ""))
        for notification in _notifications(hass)
    ), _notifications(hass)


async def test_a_notification_can_carry_the_camera_picture(
    hass, loaded, hass_ws_client, freezer
):
    """§6.2: the attachment is the authenticated camera proxy, not a file
    under www, which is served to anyone who guesses the URL."""
    calls = async_mock_service(hass, "notify", "mobile_app_luca")
    client = await hass_ws_client(hass)
    await _profile(
        client,
        [
            {
                "kind": "notify",
                "moments": ["triggered"],
                "name": "Tell Luca",
                "params": {
                    "service": "notify.mobile_app_luca",
                    "message": "{{ zone }} in {{ area }}",
                    "camera_entity_id": "camera.front",
                },
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
            }
        ],
        name="Notify",
    )
    await hass.async_block_till_done()
    await _use_profile(hass, client, hass.data[DOMAIN].config.profiles[-1].id)

    await _arm_away(hass, freezer)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    assert len(calls) == 1
    assert calls[0].data["message"] == "Front door in Casa"
    assert calls[0].data["data"]["image"] == "/api/camera_proxy/camera.front"


async def test_telegram_gets_a_photo_file_and_not_the_proxy_link(
    hass, loaded, hass_ws_client, freezer
):
    """The same field, the other transport (§6.2).

    Telegram's server fetches the picture itself, from outside the house and
    with no Home Assistant session, so `/api/camera_proxy/...` is unreachable
    to it by construction — and telegram_bot reads `photo`, never `image`. A
    key it does not know is dropped without a word, which is what "I attached
    a camera and nothing arrived" looks like from the outside.
    """
    _allow_media(hass)
    snapshots = async_mock_service(hass, "camera", "snapshot")
    calls = async_mock_service(hass, "notify", "telegram")
    client = await hass_ws_client(hass)
    await _profile(
        client,
        [
            {
                "kind": "notify",
                "moments": ["triggered"],
                "name": "Tell the group",
                "params": {
                    "service": "notify.telegram",
                    "message": "{{ zone }} in {{ area }}",
                    "camera_entity_id": "camera.front",
                    "attachment": "telegram",
                },
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
            }
        ],
        name="Telegram",
    )
    await hass.async_block_till_done()
    await _use_profile(hass, client, hass.data[DOMAIN].config.profiles[-1].id)

    await _arm_away(hass, freezer)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    # The still is written first, under the configured camera folder.
    assert len(snapshots) == 1
    filename = snapshots[0].data["filename"]
    assert snapshots[0].data["entity_id"] == "camera.front"
    assert "media/foyer" in filename.replace("\\", "/")

    assert len(calls) == 1
    photo = calls[0].data["data"]["photo"]
    assert photo == [{"file": filename, "caption": "Front door in Casa"}]
    # And never the Companion app's key, which Telegram would discard.
    assert "image" not in calls[0].data["data"]


async def test_the_camera_action_makes_a_folder_that_can_be_written_to(
    hass, loaded, hass_ws_client, freezer
):
    """The folder was created with mode 1 — `--------x`.

    `os.makedirs(name, mode, exist_ok)` takes exist_ok third, and it was being
    passed True as the *mode*, which is 0o001. The directory came out with no
    read and no write for anybody, so every snapshot after the first run of a
    new installation failed at the moment of the alarm. Nothing caught it
    because nothing ever ran this action kind.
    """
    _allow_media(hass)
    snapshots = async_mock_service(hass, "camera", "snapshot")
    client = await hass_ws_client(hass)
    await _profile(
        client,
        [
            {
                "kind": "camera",
                "moments": ["triggered"],
                "name": "Front door still",
                "params": {"entity_id": "camera.front", "mode": "snapshot"},
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
            }
        ],
        name="Camera",
    )
    await hass.async_block_till_done()
    await _use_profile(hass, client, hass.data[DOMAIN].config.profiles[-1].id)

    await _arm_away(hass, freezer)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    assert len(snapshots) == 1
    usable, mode = _usable(os.path.dirname(snapshots[0].data["filename"]))
    assert usable, mode


async def test_a_camera_that_does_not_answer_still_lets_the_alarm_speak(
    hass, loaded, hass_ws_client, freezer
):
    """Losing the picture is a disappointment; losing the message is not
    something a camera gets to decide."""
    # No allowlisted folder, so the snapshot cannot be written at all.
    hass.config.allowlist_external_dirs = set()
    calls = async_mock_service(hass, "notify", "telegram")
    client = await hass_ws_client(hass)
    await _profile(
        client,
        [
            {
                "kind": "notify",
                "moments": ["triggered"],
                "name": "Tell the group",
                "params": {
                    "service": "notify.telegram",
                    "message": "{{ zone }}",
                    "camera_entity_id": "camera.front",
                    "attachment": "telegram",
                },
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
            }
        ],
        name="Telegram",
    )
    await hass.async_block_till_done()
    await _use_profile(hass, client, hass.data[DOMAIN].config.profiles[-1].id)

    await _arm_away(hass, freezer)
    await _set(hass, ZONE, "on", friendly_name="Front door")

    assert len(calls) == 1
    assert calls[0].data["message"] == "Front door"
    assert "photo" not in (calls[0].data.get("data") or {})
