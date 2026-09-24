"""Zone cameras and the device endpoint, through Home Assistant (§6.2.1, §9.2.1).

The two acceptance sentences, end to end. The kitchen window opens and the
phone receives the alarm, then one picture per camera, the text first; coming
home sends no picture. A keypad on the endpoint arms and disarms with its
token and a code, hears the countdown on its stream at once, is refused on
MQTT under its own name, and page 8 is told when it talks in the clear.
"""

from __future__ import annotations

import asyncio
import json

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.components.persistent_notification import DOMAIN as NOTIFICATIONS
import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.api.backup import backup_document
from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.dump import anonymised

from .conftest import PANEL_ENTITY, ZONE
from .test_part2 import _advance, _state, _ws
from .test_phase2 import CODE, _make_user
from .test_services import KEYPAD, SCENARIO, _call, _rows, _save

KITCHEN = "camera.kitchen"
DINING = "camera.dining"


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


async def _person(hass, client) -> None:
    await _make_user(
        hass,
        client,
        new_code=CODE,
        permissions=["arm", "disarm", "change_scenario", "edit_config"],
    )


# --- zone cameras -------------------------------------------------------------------


@pytest.fixture
async def pictures(hass, hass_ws_client, loaded):
    """The front door carries two cameras, and the default profile notifies the
    phone at `triggered` with the zone's cameras, and at `entry_started`."""
    for camera, name in ((KITCHEN, "Kitchen"), (DINING, "Dining room")):
        hass.states.async_set(camera, "idle", {"friendly_name": name})
    calls = async_mock_service(hass, "notify", "phone")
    client = await hass_ws_client(hass)
    config = await _config(client)
    zone = config["zones"][0]
    zone["camera_entity_ids"] = [KITCHEN, DINING]
    await _save(hass, client, "zone", zone)
    profile = (await _config(client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": ["triggered", "entry_started"],
            "name": "",
            "params": {
                "service": "notify.phone",
                "message": "Alarm: {{ incident_zones }}",
                "images": "zone",
                "attachment": "companion",
                "data": {"tag": "foyer", "push": {"sound": "alarm"}},
            },
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, client, "profile", profile)
    return calls, client


async def _settle(hass, calls, expected: int) -> None:
    """Wait for the pictures, which follow the text off the alarm path.

    They run detached, like the log writer — so waiting for every background
    task would wait for the log writer too, which never ends.
    """
    # No timed sleep: the clock is frozen in these tests, and a sleep would
    # never end. Yielding to the loop is enough — the snapshots are services
    # answered in this same loop.
    for _ in range(200):
        await hass.async_block_till_done()
        await asyncio.sleep(0)
        if len(calls) > expected:
            break


async def _arm(hass, freezer) -> None:
    await _call(hass, "arm", scenario_name=SCENARIO)
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY


async def test_the_text_goes_first_then_one_picture_per_camera(hass, pictures, freezer):
    calls, _client = pictures
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, calls, 3)

    assert [c.data["message"] for c in calls] == [
        "Alarm: Front door",
        "Kitchen",
        "Dining room",
    ]
    text, first, second = (c.data for c in calls)
    assert "image" not in text.get("data", {})
    assert first["data"]["image"] == f"/api/camera_proxy/{KITCHEN}"
    assert second["data"]["image"] == f"/api/camera_proxy/{DINING}"
    # The picture keeps what the channel needs, and never the `tag` under
    # which it would replace the text.
    assert first["data"]["push"] == {"sound": "alarm"}
    assert "tag" not in first["data"]


async def test_coming_home_sends_no_picture(hass, hass_ws_client, pictures, freezer):
    calls, _client = pictures
    config = await _config(_client)
    zone = config["zones"][0]
    zone.update({"type": "delayed", "entry_mode": "delayed"})
    await _save(hass, _client, "zone", zone)
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, calls, 3)

    assert [c.data["message"] for c in calls] == ["Alarm: "]
    assert "image" not in calls[0].data.get("data", {})


async def test_a_camera_that_fails_costs_only_its_own_picture(hass, pictures, freezer):
    calls, client = pictures
    profile = (await _config(client))["profiles"][0]
    profile["actions"][-1]["params"]["attachment"] = "telegram"
    await _save(hass, client, "profile", profile)
    hass.config.allowlist_external_dirs = {hass.config.path("media")}

    async def snapshot(call):
        if call.data["entity_id"] == KITCHEN:
            raise TimeoutError("the kitchen camera is not answering")
        # The file is never read here: what is checked is that the picture
        # that did answer is sent, and the one that did not costs only itself.

    hass.services.async_register("camera", "snapshot", snapshot)
    await _arm(hass, freezer)

    hass.states.async_set(ZONE, "on")
    await _settle(hass, calls, 2)

    messages = [c.data["message"] for c in calls]
    assert messages == ["Alarm: Front door", "Dining room"]
    assert calls[1].data["data"]["photo"][0]["caption"] == "Dining room"


async def test_the_cameras_travel_redacted_in_the_diagnostics(hass, pictures):
    system = hass.data[DOMAIN]
    dump = json.dumps(anonymised(system.config, system.state))
    assert KITCHEN not in dump and DINING not in dump
    assert "camera.zone_1_camera_1" in dump


# --- the device endpoint --------------------------------------------------------------


@pytest.fixture
async def endpoint(hass, hass_ws_client, hass_client_no_auth, loaded):
    """One person with a code, and one keypad on the endpoint with its token."""
    client = await hass_ws_client(hass)
    await _person(hass, client)
    await _save(
        hass,
        client,
        "device",
        {
            "name": "Hall keypad",
            "kind": "keypad",
            "ref": KEYPAD,
            "transport": "http",
            # What a keypad does (§9.2.2): every scope is off until switched on.
            "scopes": ["status", "arm", "disarm"],
        },
        code=CODE,
    )
    device_id = (await _config(client))["devices"][0]["id"]
    answer = await _ws(
        client, {"type": "foyer/device/token", "device_id": device_id, "code": CODE}
    )
    await hass.async_block_till_done()
    assert answer["success"] and answer["token"]
    http = await hass_client_no_auth()
    return http, answer["token"], device_id, client


async def _post(http, token: str | None, body: dict):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return await http.post("/api/foyer/device", json=body, headers=headers)


async def test_a_keypad_arms_and_disarms_with_its_token_and_a_code(
    hass, endpoint, freezer
):
    http, token, _device_id, _client = endpoint
    response = await _post(
        http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE}
    )
    answer = await response.json()
    assert response.status == 200
    assert answer["success"] and answer["last_result"] == "ok"
    # The state message of §9.2 at `minimal`, never the panel's status.
    assert set(answer["state"]) >= {"master", "countdown", "ready_to_arm"}
    assert "zones" not in answer["state"] and "areas" not in answer["state"]

    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    response = await _post(http, token, {"action": "disarm", "code": "000000"})
    assert (await response.json())["last_result"] == "bad_code"
    response = await _post(
        http, token, {"action": "disarm", "code": CODE, "device_id": "whatever"}
    )
    assert (await response.json())["success"]
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED


async def test_the_code_is_still_required(hass, endpoint, freezer):
    http, token, _device_id, _client = endpoint
    await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    await _advance(hass, freezer, 31)

    answer = await (await _post(http, token, {"action": "disarm"})).json()
    assert not answer["success"]
    assert answer["reason"] == "code_required"


async def _lock_out(hass, http) -> str:
    """Five wrong or missing tokens from the test client: its address locks."""
    for token in (None, "not-the-token", "still-not", "nope", "no"):
        response = await _post(http, token, {"action": "status"})
        assert response.status == 401
        assert await response.text() == ""
    (key,) = [k for k in hass.data[DOMAIN].state.lockouts if k.startswith("http:")]
    assert hass.data[DOMAIN].state.lockouts[key].until is not None
    return key


async def test_a_wrong_or_missing_token_is_401_and_counted_per_address(hass, endpoint):
    http, token, _device_id, _client = endpoint
    key = await _lock_out(hass, http)
    counter = hass.data[DOMAIN].state.lockouts[key]
    # Notified once, naming the address: the shared counter has words of its
    # own (tests/ha/test_part13.py).
    await hass.async_block_till_done()
    (shown,) = [
        n
        for n in hass.data[NOTIFICATIONS].values()
        if n["notification_id"] == "foyer_token_lockout"
    ]
    assert "127.0.0.1" in shown["message"]
    # Past the threshold a wrong token from the address is refused, and not
    # counted again: the lockout is a brake on the log.
    response = await _post(http, "still-guessing", {"action": "status"})
    assert response.status == 401
    assert hass.data[DOMAIN].state.lockouts[key] == counter
    # The right token is not (decision 135): a keypad behind the same NAT as
    # somebody guessing keeps working.
    response = await _post(http, token, {"action": "status"})
    assert response.status == 200
    assert hass.data[DOMAIN].state.lockouts[key] == counter


def _noted(row: dict) -> bool:
    return (
        row["detail"].get("address") == "127.0.0.1"
        and row["detail"].get("address_locked") == "true"
    )


async def test_a_right_token_from_a_locked_address_is_served_and_said(
    hass, endpoint, freezer
):
    """Decision 135: every row the keypad's request causes says the address
    was locked; the request neither spends nor clears the address's counter,
    and a wrong code counts against the keypad, as it always has."""
    http, token, device_id, _client = endpoint
    key = await _lock_out(hass, http)
    counter = hass.data[DOMAIN].state.lockouts[key]

    answer = await (
        await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    ).json()
    assert answer["success"], answer
    await _advance(hass, freezer, 31)
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY

    answer = await (
        await _post(http, token, {"action": "disarm", "code": "000000"})
    ).json()
    assert answer["last_result"] == "bad_code"
    lockouts = hass.data[DOMAIN].state.lockouts
    assert lockouts[f"keypad:{device_id}"].failures
    assert lockouts[key] == counter
    answer = await (await _post(http, token, {"action": "disarm", "code": CODE})).json()
    assert answer["success"]
    await hass.async_block_till_done()

    rows = [r for r in await _rows(hass) if r.get("device_id") == device_id]
    kinds = {r["event_type"] for r in rows}
    assert {"armed", "code_rejected", "disarmed"} <= kinds
    assert all(_noted(r) for r in rows)
    # The rows of the actions those requests set off say it too (fix phase):
    # the default profile answers a disarm with a Home Assistant notification.
    acted = [
        r
        for r in await _rows(hass)
        if r["category"] == "action" and r["detail"].get("moment") == "disarmed"
    ]
    assert acted and all(_noted(r) for r in acted)
    assert hass.data[DOMAIN].state.lockouts[key] == counter


async def test_a_right_token_from_a_locked_address_opens_its_stream(hass, endpoint):
    http, token, _device_id, _client = endpoint
    key = await _lock_out(hass, http)
    counter = hass.data[DOMAIN].state.lockouts[key]
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status == 200
    assert response.headers["Content-Type"].startswith("text/event-stream")
    first = json.loads((await response.content.readline()).decode()[len("data: ") :])
    assert "master" in first
    response.close()
    # A wrong token from it is still refused, and not counted again.
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": "Bearer nope"}
    )
    assert response.status == 401
    assert hass.data[DOMAIN].state.lockouts[key] == counter


async def test_the_stream_says_the_countdown_at_once(hass, endpoint):
    http, token, _device_id, _client = endpoint
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status == 200
    assert response.headers["Content-Type"].startswith("text/event-stream")
    first = json.loads((await response.content.readline()).decode()[len("data: ") :])
    await response.content.readline()
    assert first["countdown"] is None

    await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    line = await asyncio.wait_for(response.content.readline(), 5)
    update = json.loads(line.decode()[len("data: ") :])
    assert update["countdown"]["kind"] == "exit"
    assert update["last_result"] == "ok"
    response.close()


async def test_a_new_token_invalidates_the_old_one_and_its_stream(hass, endpoint):
    http, token, device_id, client = endpoint
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": f"Bearer {token}"}
    )
    await response.content.readline()
    await response.content.readline()

    answer = await _ws(
        client, {"type": "foyer/device/token", "device_id": device_id, "code": CODE}
    )
    await hass.async_block_till_done()
    assert answer["token"] != token
    # The old stream ends.
    assert await asyncio.wait_for(response.content.read(), 5) == b""
    assert (await _post(http, token, {"action": "status"})).status == 401
    assert (await _post(http, answer["token"], {"action": "status"})).status == 200


async def test_the_keypad_is_refused_on_mqtt_and_services_under_its_own_name(
    hass, endpoint, freezer
):
    _http, _token, _device_id, _client = endpoint
    answer = await _call(
        hass,
        "arm",
        scenario_name=SCENARIO,
        code=CODE,
        device_id=KEYPAD,
    )
    # Exactly what an unknown device is told: nothing about which names exist.
    assert answer["reason"] == "device_not_registered"
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.DISARMED
    await hass.async_block_till_done()

    rows = await _rows(hass, category="security")
    rejected = [r for r in rows if r["event_type"] == "device_rejected"]
    assert rejected and rejected[0]["detail"]["wrong_transport"] == "true"
    shown = hass.data[NOTIFICATIONS]
    assert any(
        KEYPAD in n["message"] and "token" in n["message"] for n in shown.values()
    )


async def test_a_plain_http_keypad_is_said_everywhere(hass, endpoint, hass_ws_client):
    http, token, device_id, client = endpoint
    await _post(http, token, {"action": "status"})
    status = await _ws(client, {"type": "foyer/status"})
    assert status["devices_in_clear"] == [device_id]


async def test_the_token_never_leaves(hass, endpoint):
    _http, token, _device_id, client = endpoint
    system = hass.data[DOMAIN]
    config = await _config(client)
    assert config["devices"][0]["has_token"] is True
    assert "token_hash" not in config["devices"][0]
    for document in (
        json.dumps(config),
        json.dumps(backup_document(system.config)),
        json.dumps(anonymised(system.config, system.state)),
    ):
        assert token not in document
        assert system.config.devices[0].token_hash not in document


async def test_a_restore_keeps_the_token_and_can_never_set_one(hass, endpoint):
    from custom_components.foyer.api.backup import restore

    _http, _token, device_id, _client = endpoint
    system = hass.data[DOMAIN]
    held = system.config.device(device_id).token_hash
    document = backup_document(system.config)
    document["config"]["devices"][0]["token_hash"] = "ff" * 32
    result = restore(system, document)
    assert result.config is not None
    assert result.config.device(device_id).token_hash == held


async def test_a_tag_cannot_be_given_a_token(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await _person(hass, client)
    hass.states.async_set("tag.luca", "2026-09-22T10:00:00")
    config = await _config(client)
    scenario_id = config["scenarios"][0]["id"]
    user_id = (await _ws(client, {"type": "foyer/config"}))["config"]["users"][0]["id"]
    await _save(
        hass,
        client,
        "device",
        {
            "name": "Tag",
            "kind": "tag",
            "entity_id": "tag.luca",
            "user_id": user_id,
            "command": "arm",
            "scenario_id": scenario_id,
        },
        code=CODE,
    )
    device_id = (await _config(client))["devices"][0]["id"]
    answer = await _ws(
        client, {"type": "foyer/device/token", "device_id": device_id, "code": CODE}
    )
    assert not answer["success"]
    assert answer["problems"][0]["code"] == "tag_has_no_token"


async def test_the_endpoint_is_not_there_where_no_keypad_uses_it(
    hass, loaded, hass_client_no_auth
):
    """An installation that never chose the endpoint advertises nothing and
    counts nobody's guesses."""
    http = await hass_client_no_auth()
    response = await _post(http, "anything", {"action": "status"})
    assert response.status == 404
    assert not [k for k in hass.data[DOMAIN].state.lockouts if k.startswith("http:")]


async def test_an_edit_racing_a_revocation_cannot_bring_the_token_back(hass, endpoint):
    """Found in review: an edit built from the configuration the running
    system still held, between a save and the reload it schedules, wrote the
    revoked token back over the new document. The superseded system refuses
    it, and the endpoint stops answering from the old configuration at once."""
    http, token, _device_id, client = endpoint
    system = hass.data[DOMAIN]
    zone = (await _config(client))["zones"][0]
    system.superseded = True  # a save has been written; the reload is pending

    await client.send_json(
        {
            "id": 90002,
            "type": "foyer/config/save",
            "kind": "zone",
            "item": zone,
            "code": CODE,
        }
    )
    answer = (await client.receive_json())["result"]
    assert not answer["success"]
    assert answer["problems"][0]["code"] == "config_reloading"
    assert (await _post(http, token, {"action": "status"})).status == 503
    system.superseded = False


async def test_a_body_nested_too_deep_is_a_bad_request(hass, endpoint):
    http, token, _device_id, _client = endpoint
    response = await http.post(
        "/api/foyer/device",
        data="[" * 2000,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status == 400
