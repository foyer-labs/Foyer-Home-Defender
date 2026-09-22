"""The zone's cameras in a notification (SPEC §6.2.1). Pure: no Home Assistant.

The acceptance sentence is the first test: the kitchen window opens and the
notification carries the kitchen camera and the one next door; the hall PIR
joins and the next message carries all three. Coming home through the front
door carries no picture of anybody.
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import (
    ActionKind,
    Channel,
    Moment,
    NotifyImages,
    ProfileAction,
    ResponseProfile,
    ZoneType,
)
from custom_components.foyer.store.migrations import migrate

from .helpers import DOOR, HALL, WINDOW, World, make_house, zone

SMOKE = "binary_sensor.smoke"

CAMERAS = {
    "window": ("camera.kitchen", "camera.dining"),
    "hall": ("camera.hall", "camera.kitchen"),
    "door": ("camera.porch",),
}


def notify(
    action_id: str,
    moments: set[Moment],
    *,
    images: NotifyImages | None = NotifyImages.ZONE,
    offset: int | None = None,
    **params,
) -> ProfileAction:
    body = {"service": "notify.phone", "message": "{{ incident_zones }}", **params}
    if images is not None:
        body["images"] = images.value
    return ProfileAction(
        id=action_id,
        kind=ActionKind.NOTIFY,
        moments=frozenset(moments),
        params=body,
        escalation_offset=offset,
    )


def house(*actions: ProfileAction, cameras=CAMERAS):
    config = make_house()
    profile = ResponseProfile("pictures", "Pictures", actions=actions)
    return replace(
        config,
        zones=tuple(
            replace(z, camera_entity_ids=cameras.get(z.id, ())) for z in config.zones
        ),
        profiles=(*config.profiles, profile),
        areas=tuple(replace(a, response_profile_id="pictures") for a in config.areas),
    )


def armed(config) -> World:
    world = World(config)
    world.arm("away")
    world.advance(30)
    return world


def sent(decision, action_id: str):
    return [i for i in decision.actions if i.action_id == action_id]


def test_the_window_then_the_hall_shows_every_camera_in_joining_order():
    world = armed(
        house(
            notify("alarm", {Moment.TRIGGERED}),
            notify("joined", {Moment.INCIDENT_JOINED}),
        )
    )

    first = sent(world.set(WINDOW, "on"), "alarm")
    assert first[0].params["cameras"] == ["camera.kitchen", "camera.dining"]

    world.advance(20)
    joined = sent(world.set(HALL, "on"), "joined")
    # The window's cameras first, then the hall's, the kitchen once.
    assert joined[0].params["cameras"] == [
        "camera.kitchen",
        "camera.dining",
        "camera.hall",
    ]
    assert "cameras_omitted" not in joined[0].params


def test_coming_home_through_the_front_door_carries_no_picture():
    world = armed(house(notify("home", {Moment.ENTRY_STARTED, Moment.DISARMED})))

    entry = sent(world.set(DOOR, "on"), "home")
    assert entry and "cameras" not in entry[0].params
    disarmed = sent(world.disarm(), "home")
    assert disarmed and "cameras" not in disarmed[0].params


def test_at_most_four_and_the_rest_are_counted():
    cameras = {
        "window": ("camera.a", "camera.b", "camera.c"),
        "hall": ("camera.d", "camera.e", "camera.f"),
    }
    world = armed(
        house(
            notify("alarm", {Moment.TRIGGERED}),
            notify("joined", {Moment.INCIDENT_JOINED}),
            cameras=cameras,
        )
    )
    world.set(WINDOW, "on")
    joined = sent(world.set(HALL, "on"), "joined")[0]

    assert joined.params["cameras"] == ["camera.a", "camera.b", "camera.c", "camera.d"]
    assert joined.params["cameras_omitted"] == 2


def test_every_escalation_step_repeats_the_cameras_fresh():
    world = armed(
        house(
            notify("s0", {Moment.TRIGGERED}, offset=0),
            notify("s1", {Moment.TRIGGERED}, offset=60),
        )
    )
    step0 = sent(world.set(WINDOW, "on"), "s0")
    assert step0[0].params["cameras"] == ["camera.kitchen", "camera.dining"]

    world.advance(10)
    world.set(HALL, "on")
    step1 = sent(world.advance(50), "s1")
    # The step two minutes later carries what the house looks like now,
    # including the zone that joined after the first message.
    assert step1[0].params["cameras"] == [
        "camera.kitchen",
        "camera.dining",
        "camera.hall",
    ]


def test_a_fixed_action_is_untouched_and_none_carries_nothing():
    world = armed(
        house(
            notify(
                "fixed",
                {Moment.TRIGGERED},
                images=NotifyImages.FIXED,
                camera_entity_id="camera.garden",
            ),
            notify(
                "none",
                {Moment.TRIGGERED},
                images=NotifyImages.NONE,
                camera_entity_id="camera.left_behind",
            ),
        )
    )
    decision = world.set(WINDOW, "on")

    fixed = sent(decision, "fixed")[0].params
    assert fixed["camera_entity_id"] == "camera.garden"
    assert "cameras" not in fixed
    none = sent(decision, "none")[0].params
    assert "camera_entity_id" not in none
    assert "cameras" not in none


def test_an_action_that_does_not_say_is_read_as_the_migration_writes_it():
    world = armed(
        house(
            notify(
                "old",
                {Moment.TRIGGERED},
                images=None,
                camera_entity_id="camera.garden",
            ),
            notify("older", {Moment.TRIGGERED}, images=None),
        )
    )
    decision = world.set(WINDOW, "on")

    assert sent(decision, "old")[0].params["images"] == "fixed"
    assert sent(decision, "old")[0].params["camera_entity_id"] == "camera.garden"
    assert sent(decision, "older")[0].params["images"] == "none"
    assert "cameras" not in sent(decision, "older")[0].params


def test_a_zone_action_sends_its_text_alone_outside_an_alarm():
    world = World(house(notify("armed", {Moment.ARMED})))
    world.arm("away")
    decision = world.advance(30)

    armed_sent = sent(decision, "armed")
    assert armed_sent and "cameras" not in armed_sent[0].params


def test_the_technical_channel_shows_the_technical_zones_pending():
    config = house(notify("smoke", {Moment.TECHNICAL_RAISED}))
    config = replace(
        config,
        zones=(
            *config.zones,
            zone(
                "smoke",
                SMOKE,
                "ground",
                type=ZoneType.TECHNICAL,
                channel=Channel.TECHNICAL,
                always_on=True,
                bypassable=False,
                camera_entity_ids=("camera.kitchen",),
            ),
        ),
        settings=replace(config.settings, technical_profile_id="pictures"),
    )
    world = World(config)

    raised = sent(world.set(SMOKE, "on"), "smoke")
    assert raised[0].params["cameras"] == ["camera.kitchen"]


def test_the_migration_keeps_what_everybody_receives():
    document = {
        "zones": [{"id": "z"}],
        "profiles": [
            {
                "actions": [
                    {"kind": "notify", "params": {"camera_entity_id": "camera.x"}},
                    {"kind": "notify", "params": {"message": "hi"}},
                    {"kind": "siren", "params": {}},
                ]
            }
        ],
        "devices": [{"id": "k", "kind": "keypad"}],
    }
    out = migrate((7, 4), (8, 1), document)

    actions = out["profiles"][0]["actions"]
    assert actions[0]["params"]["images"] == "fixed"
    assert actions[1]["params"]["images"] == "none"
    assert "images" not in actions[2]["params"]
    assert out["zones"][0]["camera_entity_ids"] == []
    assert out["devices"][0]["transport"] == "mqtt"


def test_every_zone_joining_is_told_not_only_the_first():
    """§6.2.1: each zone joining repeats the cameras. The union of §5.6 keeps
    a siren from restarting; it does not swallow the second join's message."""
    from .helpers import PATIO

    cameras = {**CAMERAS, "patio": ("camera.garden",)}
    world = armed(
        house(
            notify("alarm", {Moment.TRIGGERED}),
            notify("joined", {Moment.INCIDENT_JOINED}),
            cameras=cameras,
        )
    )
    world.set(WINDOW, "on")
    assert sent(world.set(HALL, "on"), "joined")
    third = sent(world.set(PATIO, "on"), "joined")

    assert third[0].params["cameras"] == [
        "camera.kitchen",
        "camera.dining",
        "camera.hall",
        "camera.garden",
    ]


def test_the_simulator_lists_the_cameras_without_taking_a_picture():
    """INV-1: the trace names the cameras each notification would carry,
    read off the very intent the engine built — nothing is fetched."""
    from datetime import UTC, datetime

    from custom_components.foyer.core.simulate import (
        SimulationRequest,
        ZoneOverride,
        as_dict,
        run,
    )

    from .helpers import closed_entities

    start = datetime(2026, 9, 19, 19, 32, tzinfo=UTC)
    config = house(notify("alarm", {Moment.TRIGGERED}))
    sim = run(
        config,
        SimulationRequest(
            start=start,
            scenario_id="away",
            zones=(ZoneOverride("window", "on", at=60),),
        ),
        closed_entities(config, start),
    )
    traced = [
        action
        for step in as_dict(sim, config)["steps"]
        for batch in step["batches"]
        for action in batch["actions"]
        if action["action_id"] == "alarm" and action["ran"]
    ]
    assert traced[0]["cameras"] == ["camera.kitchen", "camera.dining"]
    assert traced[0]["cameras_omitted"] == 0
