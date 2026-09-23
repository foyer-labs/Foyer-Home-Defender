"""API devices through Home Assistant (SPEC §9.2.2, decisions 115-120).

A relay that only reads the state, a display that shows the house after a
code, a module that may arm only what it was given: each is the endpoint of
§9.2.1 with scopes of its own. These are the sentences of §9.2.2, end to end.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from custom_components.foyer.const import DOMAIN

from .conftest import ZONE
from .test_part12 import _post, endpoint  # noqa: F401 - the fixture
from .test_phase2 import CODE
from .test_services import SCENARIO, _rows


def _with(hass, device_id: str, **changes) -> None:
    """Give the endpoint's device other scopes, as page 8 would save them."""
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        devices=tuple(
            replace(d, **changes) if d.id == device_id else d
            for d in system.config.devices
        ),
    )


async def _get(http, token: str, section: str, **query):
    return await http.get(
        f"/api/foyer/device/{section}",
        headers={"Authorization": f"Bearer {token}"},
        params=query,
    )


async def test_a_relay_reads_the_state_and_nothing_else(
    hass,
    endpoint,  # noqa: F811 - the fixture imported above
):
    """Decision 115: a scope the device was not given is refused, by name."""
    http, token, device_id, _client = endpoint
    _with(hass, device_id, scopes=frozenset({"status"}))
    answer = await (await _post(http, token, {"action": "status"})).json()
    assert answer["success"]
    response = await _get(http, token, "zones")
    assert response.status == 403
    assert (await response.json())["reason"] == "scope_not_granted"
    refused = await (
        await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    ).json()
    assert refused["success"] is False and refused["reason"] == "scope_not_granted"


async def test_every_action_needs_a_code_even_to_arm(
    hass,
    endpoint,  # noqa: F811
):
    """Decision 116: the policy asks no code to arm; a device still does."""
    http, token, _device_id, _client = endpoint
    answer = await (
        await _post(http, token, {"action": "arm", "scenario": SCENARIO})
    ).json()
    assert answer["success"] is False
    assert answer["reason"] == "code_required"
    assert answer["last_result"] == "bad_code"


async def test_a_display_shows_the_zones_only_after_a_code(
    hass,
    endpoint,  # noqa: F811
):
    """Decisions 117-119: after a code, confirmed for the clear, and ended by a
    lock. The test client talks plain HTTP."""
    http, token, device_id, _client = endpoint
    _with(hass, device_id, scopes=frozenset({"status", "zones"}))
    response = await _get(http, token, "zones")
    assert (await response.json())["reason"] == "plain_http_not_confirmed"

    _with(hass, device_id, clear_text_confirmed=True)
    response = await _get(http, token, "zones")
    assert response.status == 403
    assert (await response.json())["reason"] == "unlock_required"

    wrong = await (
        await _post(http, token, {"action": "unlock", "code": "000000"})
    ).json()
    assert wrong["success"] is False and wrong["reason"] == "bad_code"
    right = await (await _post(http, token, {"action": "unlock", "code": CODE})).json()
    assert right["success"] and right["until"]
    response = await _get(http, token, "zones")
    body = await response.json()
    assert response.status == 200
    assert body["zones"] and {"id", "name", "open", "fault", "excluded"} <= set(
        body["zones"][0]
    )
    rows = await _rows(hass, category="security")
    assert any(r["event_type"] == "device_unlocked" for r in rows)

    await _post(http, token, {"action": "lock"})
    response = await _get(http, token, "zones")
    assert (await response.json())["reason"] == "unlock_required"


async def test_a_free_scope_needs_no_code(
    hass,
    endpoint,  # noqa: F811
):
    http, token, device_id, _client = endpoint
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "zones"}),
        free_scopes=frozenset({"status", "zones"}),
        clear_text_confirmed=True,
    )
    response = await _get(http, token, "zones")
    assert response.status == 200


async def test_arming_ends_the_unlock(
    hass,
    endpoint,  # noqa: F811
):
    """Decision 118: what the display showed was for before."""
    http, token, device_id, _client = endpoint
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "zones", "arm"}),
        clear_text_confirmed=True,
    )
    await _post(http, token, {"action": "unlock", "code": CODE})
    assert (await _get(http, token, "zones")).status == 200
    armed = await (
        await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    ).json()
    assert armed["success"], armed
    assert (await (await _get(http, token, "zones")).json())["reason"] == (
        "unlock_required"
    )


async def test_arming_reaches_only_where_the_device_may(
    hass,
    endpoint,  # noqa: F811
):
    http, token, device_id, _client = endpoint
    _with(hass, device_id, arm_scenario_ids=())
    refused = await (
        await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    ).json()
    assert refused["reason"] == "scope_not_granted"


async def test_a_free_log_says_what_happened_and_never_who(
    hass,
    endpoint,  # noqa: F811
):
    http, token, device_id, _client = endpoint
    await _post(http, token, {"action": "arm", "scenario": SCENARIO, "code": CODE})
    await hass.async_block_till_done()
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "log"}),
        free_scopes=frozenset({"status", "log"}),
        clear_text_confirmed=True,
    )
    await hass.data[DOMAIN].log.async_flush()
    body = await (await _get(http, token, "log", limit="5")).json()
    assert body["rows"]
    assert all("person" not in row for row in body["rows"])
    assert len(body["rows"]) <= 5

    # After a code that may not read the log, still nobody's name.
    await _post(http, token, {"action": "unlock", "code": CODE})
    body = await (await _get(http, token, "log", limit="50")).json()
    assert all("person" not in row for row in body["rows"])

    # After a code that may read the log, the names come back.
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        users=tuple(
            replace(u, permissions=frozenset({*u.permissions, "view_log"}))
            for u in system.config.users
        ),
    )
    body = await (await _get(http, token, "log", limit="50")).json()
    assert any(row.get("person") for row in body["rows"])


async def test_the_stream_says_which_section_changed(
    hass,
    endpoint,  # noqa: F811
):
    """Decision 120: a one-line notice, and the device reads it if it cares."""
    http, token, device_id, _client = endpoint
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "zones"}),
        free_scopes=frozenset({"status", "zones"}),
        clear_text_confirmed=True,
    )
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": f"Bearer {token}"}
    )
    await response.content.readline()
    await response.content.readline()

    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()
    lines: list[str] = []
    while "event: changed" not in lines:
        line = await asyncio.wait_for(response.content.readline(), 5)
        lines.append(line.decode().strip())
    notice = await asyncio.wait_for(response.content.readline(), 5)
    assert notice.decode().strip() == "data: zones"
    response.close()


# --- what the security review found ------------------------------------------------


async def test_switching_scenario_disarms_only_with_the_disarm_scope(
    hass,
    endpoint,  # noqa: F811
    freezer,
):
    """Arming a scenario while another is armed disarms what the new one
    leaves out: that is a disarm, and needs the device's `disarm` scope."""
    from custom_components.foyer.core.models import Scenario

    http, token, device_id, _client = endpoint
    system = hass.data[DOMAIN]
    first = system.config.scenarios[0]
    # A second scenario with no area at all: switching to it drops them all.
    system.config = replace(
        system.config,
        scenarios=(
            *system.config.scenarios,
            Scenario(id="empty", name="Empty", areas=(), ha_master_state="armed_night"),
        ),
    )
    armed = await (
        await _post(
            http, token, {"action": "arm", "scenario": first.name, "code": CODE}
        )
    ).json()
    assert armed["success"], armed
    _with(hass, device_id, scopes=frozenset({"status", "arm"}))
    refused = await (
        await _post(http, token, {"action": "arm", "scenario": "Empty", "code": CODE})
    ).json()
    assert refused["success"] is False
    assert refused["reason"] == "scope_not_granted"


async def test_an_unlock_ends_when_its_owner_is_disabled(
    hass,
    endpoint,  # noqa: F811
):
    http, token, device_id, _client = endpoint
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "zones"}),
        clear_text_confirmed=True,
    )
    await _post(http, token, {"action": "unlock", "code": CODE})
    assert (await _get(http, token, "zones")).status == 200
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        users=tuple(replace(u, enabled=False) for u in system.config.users),
    )
    response = await _get(http, token, "zones")
    assert (await response.json())["reason"] == "unlock_required"


async def test_the_log_after_a_code_needs_view_log(
    hass,
    endpoint,  # noqa: F811
):
    http, token, device_id, _client = endpoint
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "log"}),
        clear_text_confirmed=True,
    )
    await _post(http, token, {"action": "unlock", "code": CODE})
    response = await _get(http, token, "log")
    assert response.status == 403
    assert (await response.json())["reason"] == "not_permitted"


async def test_no_notice_before_the_code_or_in_the_clear(
    hass,
    endpoint,  # noqa: F811
):
    """A notice that the zones moved is news about the house."""
    http, token, device_id, _client = endpoint
    _with(hass, device_id, scopes=frozenset({"status", "zones"}))
    response = await http.get(
        "/api/foyer/device/state", headers={"Authorization": f"Bearer {token}"}
    )
    await response.content.readline()
    await response.content.readline()
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()
    lines = []
    try:
        while True:
            line = await asyncio.wait_for(response.content.readline(), 1)
            lines.append(line.decode().strip())
    except TimeoutError:
        pass
    assert "event: changed" not in lines
    response.close()


async def test_health_names_nobody(
    hass,
    endpoint,  # noqa: F811
):
    from custom_components.foyer.core.models import (
        Contact,
        ContactChannel,
        ContactChannelKind,
    )

    http, token, device_id, _client = endpoint
    system = hass.data[DOMAIN]
    system.config = replace(
        system.config,
        contacts=(
            Contact(
                "anna",
                "Anna Rossi",
                channels=(
                    ContactChannel(
                        "push", ContactChannelKind.PUSH, "notify.mobile_app_anna"
                    ),
                ),
            ),
        ),
    )
    _with(
        hass,
        device_id,
        scopes=frozenset({"status", "health"}),
        free_scopes=frozenset({"status", "health"}),
        clear_text_confirmed=True,
    )
    body = await (await _get(http, token, "health")).text()
    assert "Anna" not in body and "mobile_app_anna" not in body
    assert '"channels"' in body
