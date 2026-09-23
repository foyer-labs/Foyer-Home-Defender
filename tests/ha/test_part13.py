"""What the second full review found in the Home Assistant layer (2026-09-23).

Each test is the sequence a reviewer used, asserted the right way round.
"""

from __future__ import annotations

from dataclasses import replace

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.components.persistent_notification import DOMAIN as NOTIFICATIONS
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import pytest

from custom_components.foyer.const import DOMAIN

from .conftest import PANEL_ENTITY
from .test_part2 import _advance, _state, _ws
from .test_part12 import endpoint  # noqa: F401 - the fixture
from .test_phase2 import CODE, _make_user
from .test_services import SCENARIO, _call


async def test_a_notification_that_fails_after_it_was_accepted_is_a_failure(
    hass, hass_ws_client, loaded
):
    """The service exists and accepts the call, then fails: counted as sent,
    the test button said a dead channel worked."""

    async def broken(call):
        raise HomeAssistantError("the provider refused it")

    hass.services.async_register("notify", "broken", broken)
    client = await hass_ws_client(hass)
    result = await _ws(
        client, {"type": "foyer/test_action", "service": "notify.broken"}
    )
    assert result["success"] is False


async def test_one_account_guessing_codes_does_not_lock_out_another(
    hass, hass_ws_client, hass_read_only_access_token, loaded
):
    admin = await hass_ws_client(hass)
    await _make_user(hass, admin, new_code=CODE)
    stranger = await hass_ws_client(hass, hass_read_only_access_token)
    for index in range(6):
        await stranger.send_json(
            {"id": 700 + index, "type": "foyer/disarm", "code": "000000"}
        )
        await stranger.receive_json()

    scenario_id = hass.data[DOMAIN].config.scenarios[0].id
    answer = await _ws(
        admin, {"type": "foyer/arm", "scenario_id": scenario_id, "code": CODE}
    )
    assert answer["success"], answer


async def test_a_refused_service_raises_when_nobody_reads_the_answer(
    hass, hass_ws_client, loaded, freezer
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE)
    await _call(hass, "arm", scenario_name=SCENARIO, code=CODE)
    await _advance(hass, freezer, 31)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "disarm", {"code": "000000"}, blocking=True
        )
    assert _state(hass, PANEL_ENTITY) == AlarmControlPanelState.ARMED_AWAY
    # And the caller who asks for the answer still gets it, refusal and all.
    answer = await _call(hass, "disarm", code="000000")
    assert answer["success"] is False and answer["reason"] == "bad_code"


async def test_a_bypass_cannot_last_for_ever(hass, loaded):
    zone_id = hass.data[DOMAIN].config.zones[0].id
    with pytest.raises(Exception):  # noqa: B017 - voluptuous refuses it
        await hass.services.async_call(
            DOMAIN,
            "bypass_zone",
            {"zone_id": zone_id, "seconds": 10**12},
            blocking=True,
            return_response=True,
        )


async def test_a_date_that_is_not_one_does_not_crash_the_log(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    result = await _ws(
        client, {"type": "foyer/log/query", "start": "2026-99-01T00:00:00"}
    )
    assert "rows" in result


async def test_invented_device_names_are_capped_and_shown_as_code(hass, loaded):
    for index in range(40):
        await hass.services.async_call(
            DOMAIN,
            "arm",
            {"scenario_name": SCENARIO, "device_id": f"[x{index}](https://evil)"},
            blocking=True,
            return_response=True,
        )
    await hass.async_block_till_done()
    shown = [
        n
        for n in hass.data[NOTIFICATIONS].values()
        if "foyer_device" in n["notification_id"]
    ]
    assert len(shown) == 1
    assert "`[x" in shown[0]["message"]


async def test_a_code_somebody_else_holds_spends_the_savers_lockout(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    await _make_user(hass, client, new_code=CODE, name="Luca")
    system = hass.data[DOMAIN]
    before = dict(system.state.lockouts)
    result = await _ws(
        client,
        {
            "type": "foyer/user/save",
            "user": {"name": "Guest", "permissions": ["arm"]},
            "new_code": CODE,
            "code": CODE,
        },
    )
    assert not result["success"]
    assert result["problems"][0]["code"] == "code_in_use"
    after = hass.data[DOMAIN].state.lockouts
    assert any(lock.failures for key, lock in after.items() if key.startswith("ha_ui:"))
    assert after != before


async def test_a_full_overflow_counter_never_refuses_the_right_token(
    hass,
    endpoint,  # noqa: F811 - the fixture imported above
):
    """Found in review: past sixty-four addresses every new one shared a
    counter, and once it locked, the real keypads were refused too."""
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    from custom_components.foyer.core.models import Lockout

    from .test_part12 import _post

    http, token, device_id, _client = endpoint
    system = hass.data[DOMAIN]
    until = dt_util.utcnow() + timedelta(hours=1)
    locks = {f"http:198.51.100.{i}": Lockout(until=None) for i in range(64)}
    locks["http:*"] = Lockout(until=until)
    system.state = replace(system.state, lockouts={**system.state.lockouts, **locks})

    response = await _post(http, token, {"action": "status"})
    assert response.status == 200

    # And its rows say nothing about a locked address (decision 135): only
    # the address's own counter can say that, and the test client has none.
    for body in (
        {"action": "arm", "scenario": SCENARIO, "code": CODE},
        {"action": "disarm", "code": CODE},
    ):
        answer = await (await _post(http, token, body)).json()
        assert answer["success"], answer
    await hass.async_block_till_done()
    await system.log.async_flush()
    rows = [
        r
        for r in (await system.log.async_query(limit=200))["rows"]
        if r.get("device_id") == device_id
    ]
    assert rows and not any("address_locked" in (r["detail"] or {}) for r in rows)


async def test_tokens_refused_on_the_locked_shared_counter_leave_one_row_a_minute(
    hass,
    endpoint,  # noqa: F811 - the fixture imported above
    freezer,
):
    """Review follow-up: once the shared counter locked, a flood of guesses
    from rotating addresses was answered without a trace. It is tallied in
    memory and written as one `security` row a minute."""
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    from custom_components.foyer.core.models import Lockout

    from .test_part12 import _post

    http, _token, _device_id, _client = endpoint
    system = hass.data[DOMAIN]
    until = dt_util.utcnow() + timedelta(hours=1)
    locks = {f"http:198.51.100.{i}": Lockout(until=None) for i in range(64)}
    locks["http:*"] = Lockout(until=until)
    system.state = replace(system.state, lockouts={**system.state.lockouts, **locks})

    for _ in range(3):
        response = await _post(http, "wrong", {"action": "status"})
        assert response.status == 401

    async def summaries():
        await hass.data[DOMAIN].log.async_flush()
        rows = (await hass.data[DOMAIN].log.async_query(limit=1000))["rows"]
        return [r for r in rows if r["event_type"] == "tokens_rejected"]

    assert await summaries() == []
    await _advance(hass, freezer, 61)
    (row,) = await summaries()
    assert row["category"] == "security"
    assert row["detail"]["count"] == "3"
    assert row["detail"]["addresses"] == "1"
