"""The mains from devices outside the UPS, through Home Assistant (decision 162).

Saved as page 14 saves it, watched without anybody subscribing by hand, and
reported by the system health sensor once every device has been silent for
the delay.
"""

from __future__ import annotations

from .test_part2 import _advance, _set, _ws
from .test_part9 import HEALTH_SENSOR, _save_health, _system

PLUG = "switch.fridge_plug"
METER = "sensor.shelly_em_power"


async def test_every_device_outside_the_ups_silent_is_a_power_cut(
    hass, loaded, hass_ws_client, freezer
):
    await _set(hass, PLUG, "on")
    await _set(hass, METER, "230")
    client = await hass_ws_client(hass)
    await _save_health(
        hass,
        client,
        mains_mode="outside_ups",
        mains_outside_entity_ids=[PLUG, METER],
        mains_outside_delay=60,
    )
    assert _system(hass).config.health.mains_outside_entity_ids == (PLUG, METER)

    await _set(hass, PLUG, "unavailable")
    await _set(hass, METER, "unavailable")
    await hass.async_block_till_done()
    assert _system(hass).state.health.mains_lost_since is None

    await _advance(hass, freezer, 61)
    assert _system(hass).state.health.mains_lost_since is not None
    assert "mains_lost" in hass.states.get(HEALTH_SENSOR).attributes["causes"]

    status = await _ws(client, {"type": "foyer/health"})
    mains = status["mains"]
    assert mains["mode"] == "outside_ups"
    assert mains["lost"] is True

    await _set(hass, METER, "231")
    await hass.async_block_till_done()
    assert _system(hass).state.health.mains_lost_since is None


async def test_a_delay_outside_its_range_is_refused(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    result = await _ws(
        client,
        {
            "type": "foyer/config/health",
            "health": {
                "mains_mode": "outside_ups",
                "mains_outside_entity_ids": [PLUG],
                "mains_outside_delay": 5,
            },
        },
    )
    assert any(p["field"] == "mains_outside_delay" for p in result["problems"]), result
