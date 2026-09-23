"""The anonymised diagnostics dump (SPEC §12.4, §19).

§19 asks for one of these by name: "a test asserting diagnostics output
contains no code hashes and no personal names". It is written as a sweep
over the whole document rather than as a list of fields, because the failure
this guards against is a field somebody adds later — and a test that checks
the fields it knows about would pass happily while the new one leaked.
"""

from __future__ import annotations

from dataclasses import replace
import json

from custom_components.foyer.core.dump import Placeholders, anonymised
from custom_components.foyer.core.models import (
    ActionKind,
    Area,
    Contact,
    ContactChannel,
    ContactChannelKind,
    HealthSettings,
    Moment,
    ProfileAction,
    Radio,
    ResponseProfile,
    Scenario,
    Settings,
    WatchdogSettings,
)

from .helpers import World, make_house, user

# Everything a real installation carries that must not leave the house.
SECRETS = (
    "Luca",
    "Partner",
    "$2b$12$placeholder",
    "https://hc-ping.example/9f8c-secret-token",
    "+393331234567",
    "notify.mobile_app_lucas_iphone",
    "Front door",
    "Ground floor",
    "binary_sensor.front_door",
    "Night",
)


def furnished() -> World:
    """A house with everything in it: people, codes, contacts, a watchdog."""
    config = make_house()
    config = replace(
        config,
        areas=(
            Area("ground", "Ground floor", "armed_away", 30, 30),
            *config.areas[1:],
        ),
        scenarios=(
            Scenario("away", "Away", ("ground", "upstairs", "garage"), "armed_away"),
            Scenario("night", "Night", ("ground",), "armed_night"),
        ),
        users=(
            user("luca", "Luca"),
            user("partner", "Partner", duress_code_hash="$2b$12$placeholder"),
        ),
        contacts=(
            Contact(
                "c1",
                "Luca",
                channels=(
                    ContactChannel(
                        "push",
                        ContactChannelKind.PUSH,
                        "notify.mobile_app_lucas_iphone",
                        actionable=True,
                    ),
                    ContactChannel(
                        "sms",
                        ContactChannelKind.SMS,
                        "notify.gsm",
                        target="+393331234567",
                    ),
                ),
            ),
        ),
        profiles=(
            ResponseProfile(
                "full",
                "Full",
                severity=5,
                actions=(
                    ProfileAction(
                        "siren",
                        ActionKind.SIREN,
                        frozenset({Moment.TRIGGERED}),
                        params={"entity_ids": ["siren.hall"], "duration": 120},
                    ),
                    ProfileAction(
                        "tell",
                        ActionKind.NOTIFY,
                        frozenset({Moment.TRIGGERED}),
                        params={
                            "contacts": [{"contact_id": "c1", "channel_id": "push"}],
                            "message": "Alarm at Luca's house",
                        },
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="full"),
        health=HealthSettings(
            mains_entity_id="binary_sensor.ups_on_battery",
            watchdog=WatchdogSettings(
                enabled=True, url="https://hc-ping.example/9f8c-secret-token"
            ),
            radios=(Radio("r1", "Zigbee", "entry1", "sensor.zha_coordinator"),),
        ),
    )
    return World(config)


def dumped(world: World) -> str:
    return json.dumps(anonymised(world.config, world.state, world.snapshot()))


def test_the_dump_carries_no_code_hash_and_no_personal_name():
    text = dumped(furnished())
    for secret in SECRETS:
        assert secret not in text, secret
    assert "$2b$" not in text


def test_the_watchdog_url_never_travels():
    """A healthchecks.io ping URL is the credential: whoever holds it can
    keep the check green for ever, which is to say silence the one thing
    that reports Foyer's own death."""
    document = anonymised(furnished().config, furnished().state, furnished().snapshot())
    assert document["health"]["watchdog"]["url_set"] is True
    assert "url" not in document["health"]["watchdog"]


def test_a_free_text_message_never_travels_only_the_shape_of_it():
    document = anonymised(furnished().config, furnished().state, furnished().snapshot())
    action = document["profiles"][0]["actions"][1]
    assert action["params"] == ["contacts", "message"]
    assert "Alarm at Luca's house" not in json.dumps(action)


def test_people_are_counted_and_never_listed():
    document = anonymised(furnished().config, furnished().state, furnished().snapshot())
    assert document["users"] == {
        "count": 2,
        "enabled": 2,
        "with_code": 2,
        "with_duress_code": 1,
        "linked_to_ha": 0,
    }


def test_placeholders_are_stable_across_two_downloads():
    """An issue thread has to be able to say binary_sensor.zone_3 twice and
    mean the same zone (part 1 decision 11)."""
    world = furnished()
    assert dumped(world) == dumped(world)
    first = Placeholders(world.config)
    second = Placeholders(world.config)
    assert first.ids == second.ids


def test_a_placeholder_keeps_the_domain_because_that_is_what_helps():
    world = furnished()
    names = Placeholders(world.config)
    garage = world.config.zone("garage_door")
    assert names.entity(garage.entity_id) == "cover.zone_8"


def test_the_dump_still_says_what_is_wrong():
    """Anonymised is not the same as useless: the whole point is an issue
    somebody can answer."""
    world = furnished()
    world.set("binary_sensor.front_door", "unavailable")
    document = anonymised(world.config, world.state, world.snapshot())
    faulted = [z for z in document["zones"] if z["in_fault"]]
    assert faulted and faulted[0]["entity"].startswith("binary_sensor.zone_")
    assert document["health"]["watchdog"]["enabled"] is True
    assert document["health"]["radios"][0]["coordinator_set"] is True


def test_the_webhook_id_never_travels():
    """The other configuration credential (decision 128): an unauthenticated
    URL that stops an alarm. The dump says whether it is on, never where."""
    world = furnished()
    webhook_id = "5f0c1d2e3b4a69788796a5b4c3d2e1f0"
    config = replace(
        world.config, settings=replace(world.config.settings, ack_webhook_id=webhook_id)
    )
    document = anonymised(config, world.state, world.snapshot())
    assert document["settings"]["ack_webhook_enabled"] is True
    assert webhook_id not in json.dumps(document)
