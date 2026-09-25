"""The ready-made notifications profile (decision 161).

The panel builds it from the translations and opens it unsaved; this builds
the same profile, from the same files, and checks that the backend accepts it
and that each kind of moment reaches the contact with its own words.
"""

from __future__ import annotations

import json
from pathlib import Path

from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.foyer.const import DOMAIN

from .conftest import ZONE
from .test_part2 import _advance, _ws
from .test_part3 import _use_profile
from .test_services import SCENARIO, _call

PANEL_STRINGS = (
    Path(__file__).parents[2]
    / "custom_components"
    / "foyer"
    / "translations"
    / "panel"
    / "en.json"
)

# Mirrors TEMPLATE_ACTIONS in frontend/src/panel/pages/profiles.ts.
TEMPLATE = (
    ("alarm", ["triggered", "incident_joined"], "zone"),
    ("technical", ["technical_raised"], "zone"),
    ("armed", ["armed"], "none"),
    ("disarmed", ["disarmed"], "none"),
    ("warning", ["arm_failed", "forced_arm", "zone_fault", "low_battery"], "none"),
)


def _template(contact_id: str) -> dict:
    words = json.loads(PANEL_STRINGS.read_text(encoding="utf-8"))["profiles"][
        "template"
    ]
    return {
        "name": words["profile_name"],
        "severity": 1,
        "actions": [
            {
                "kind": "notify",
                "moments": moments,
                "name": words[key]["name"],
                "params": {
                    "title": words[key]["title"],
                    "message": words[key]["message"],
                    "attachment": "companion",
                    "images": images,
                    "contacts": [{"contact_id": contact_id, "channel_id": None}],
                },
                "conditions": [],
                "condition_mode": "all",
                "enabled": True,
                "escalation_offset": None,
            }
            for key, moments, images in TEMPLATE
        ],
    }


async def test_the_template_is_accepted_and_tells_each_moment_apart(
    hass, loaded, hass_ws_client, freezer
):
    client = await hass_ws_client(hass)
    phone = async_mock_service(hass, "notify", "mobile_app_luca")
    saved = await _ws(
        client,
        {
            "type": "foyer/config/save",
            "kind": "contact",
            "item": {
                "name": "Luca",
                "channels": [
                    {"id": "push", "kind": "push", "service": "notify.mobile_app_luca"}
                ],
            },
        },
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    contact = hass.data[DOMAIN].config.contacts[0]

    saved = await _ws(
        client,
        {"type": "foyer/config/save", "kind": "profile", "item": _template(contact.id)},
    )
    assert saved["success"], saved
    await hass.async_block_till_done()
    system = hass.data[DOMAIN]
    profile = next(p for p in system.config.profiles if p.name == "Notifications")
    await _use_profile(hass, client, profile.id)

    await _call(hass, "arm", scenario_name=SCENARIO, channel="automation")
    await _advance(hass, freezer, 31)
    hass.states.async_set(ZONE, "on")
    await hass.async_block_till_done()

    titles = [c.data["title"] for c in phone]
    assert titles[0] == "🔒 Armed — Casa"
    assert phone[0].data["message"].startswith("Automation, ")
    assert titles[1] == "🚨 ALARM — Casa"
    assert phone[1].data["message"].startswith("Intrusion: Front door at ")
