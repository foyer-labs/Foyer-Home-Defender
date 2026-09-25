"""The template variables a person reads, said in words (decision 160).

`{{ reason }}` held `zone_open`, `{{ state }}` held `armed`, `{{ channel }}`
held `automation`, and nothing said which moment a notification was for. The
engine still hands them over as identifiers, because it reads no translation
file (INV-1); the executor says them in the language of outgoing messages.
"""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import async_mock_service

from .conftest import ZONE
from .test_part2 import _advance
from .test_part12 import _config
from .test_services import SCENARIO, _call, _save

TEMPLATE = (
    "{{ event }} | {{ scenario }} | {{ user }} | {{ channel }} | {{ state }} "
    "| {{ reason }}"
)


async def _notify_on(hass, client, *moments: str) -> list:
    calls = async_mock_service(hass, "notify", "phone")
    profile = (await _config(client))["profiles"][0]
    profile["actions"].append(
        {
            "kind": "notify",
            "moments": list(moments),
            "name": "",
            "params": {"service": "notify.phone", "message": TEMPLATE},
            "conditions": [],
            "condition_mode": "all",
            "enabled": True,
            "escalation_offset": None,
        }
    )
    await _save(hass, client, "profile", profile)
    return calls


async def test_an_arming_by_an_automation_is_said_in_words(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    calls = await _notify_on(hass, client, "armed")

    await _call(hass, "arm", scenario_name=SCENARIO, channel="automation")
    await _advance(hass, freezer, 31)
    await hass.async_block_till_done()

    # Nobody acted in person, so {{ user }} says what did.
    assert [c.data["message"] for c in calls] == [
        f"Armed | {SCENARIO} | Automation | Automation | Armed | "
    ]


async def test_a_fault_says_its_cause_in_words(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    calls = await _notify_on(hass, client, "zone_fault")

    hass.states.async_set(ZONE, "unavailable")
    await hass.async_block_till_done()

    assert [c.data["message"] for c in calls] == [
        "Zone fault |  |  |  | Disarmed | not responding"
    ]
