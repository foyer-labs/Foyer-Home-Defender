"""Arming devices: tags, keypads, and the white list in front of both.

SPEC §9.3 and part 2 decisions 1, 2 and 4. Nothing here speaks MQTT or calls a
service — those are the runtime's, and they arrive at this same engine through
the same Actor.
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import (
    ArmingDevice,
    CodeResult,
    DeviceKind,
    EntityState,
    KeyCommand,
    Moment,
    Reason,
)
from custom_components.foyer.core.validation import validate
from custom_components.foyer.store.schema import (
    config_from_dict,
    config_to_dict,
    state_from_dict,
    state_to_dict,
)

from .helpers import NOW, World, make_house, user

TAG = "tag.luca"


def tag(**changes) -> ArmingDevice:
    device = ArmingDevice(
        id="luca_tag",
        name="Luca's tag",
        kind=DeviceKind.TAG,
        entity_id=TAG,
        user_id="luca",
        command=KeyCommand.TOGGLE,
        scenario_id="away",
    )
    return replace(device, **changes)


def keypad(**changes) -> ArmingDevice:
    device = ArmingDevice(
        id="hall_keypad", name="Hall keypad", kind=DeviceKind.KEYPAD, ref="keypad_hall"
    )
    return replace(device, **changes)


def house(*devices: ArmingDevice, **changes) -> World:
    changes.setdefault("users", (user(),))
    entities = changes.pop("entities", None)
    config = replace(make_house(), devices=devices or (tag(),), **changes)
    world = World(config, entities)
    # The tag entity exists and has been read once: its first readable value is
    # a baseline, never a scan.
    world.entities[TAG] = EntityState("2026-09-14T10:00:00+00:00", last_reported=NOW)
    world.advance(0)
    return world


def scan(world: World, at: str = "2026-09-14T19:40:00+00:00", **attributes):
    return world.set(TAG, at, **attributes)


# --- a tag commands (§9.3) -------------------------------------------------------


def test_a_tag_arms_and_disarms_as_the_person_it_names():
    world = house()
    scan(world)
    assert world.states()["ground"] == "arming"
    world.advance(30)
    assert world.states()["ground"] == "armed"

    scan(world, "2026-09-14T19:50:00+00:00")
    assert set(world.states().values()) == {"disarmed"}


def test_a_scan_is_attributed_to_its_owner_and_its_device():
    world = house()
    scan(world)
    # Arming starts an exit delay, so the `armed` row comes when it ends.
    world.advance(30)
    armed = [o for o in world.last.occurrences if o.moment is Moment.ARMED]
    assert armed and armed[0].user_id == "luca"
    assert armed[0].channel == "nfc"
    assert armed[0].device_id == "luca_tag"


def test_a_tag_needs_no_code_even_when_the_policy_demands_one():
    """Possession is the credential: there is nowhere to type a code (§9.3)."""
    world = house()
    world.config = replace(
        world.config,
        areas=tuple(
            replace(a, require_code_to_arm=True, require_code_to_disarm=True)
            for a in world.config.areas
        ),
    )
    scan(world)
    assert world.states()["ground"] == "arming"


def test_a_tag_still_obeys_its_owners_permissions():
    """The code cannot apply; everything else about the person still does."""
    world = house(users=(user(permissions=frozenset()),))
    decision = scan(world)
    assert world.states()["ground"] == "disarmed"
    assert any(
        o.moment is Moment.CODE_REJECTED
        and o.detail.get("reason") == Reason.NOT_PERMITTED.value
        for o in decision.occurrences
    )


def test_a_disabled_tag_does_nothing():
    world = house(tag(enabled=False))
    scan(world)
    assert world.states()["ground"] == "disarmed"


def test_the_first_reading_of_a_tag_is_a_baseline_not_a_scan():
    """A tag entity carrying last week's timestamp is not somebody at the door."""
    config = replace(make_house(), users=(user(),), devices=(tag(),))
    world = World(config)
    world.entities[TAG] = EntityState("2026-09-01T08:00:00+00:00", last_reported=NOW)
    world.advance(0)
    assert world.states()["ground"] == "disarmed"


def test_a_tag_returning_from_unavailable_is_not_a_scan():
    world = house()
    world.set(TAG, "unavailable")
    world.set(TAG, "2026-09-14T19:40:00+00:00")
    assert world.states()["ground"] == "disarmed"


def test_a_remote_fires_only_on_the_button_it_names():
    world = house(tag(event_type="arm_away"))
    scan(world, event_type="press_other")
    assert world.states()["ground"] == "disarmed"
    scan(world, "2026-09-14T19:41:00+00:00", event_type="arm_away")
    assert world.states()["ground"] == "arming"


def test_a_refused_arming_from_a_tag_is_never_silent():
    world = house(entities={"binary_sensor.kitchen_window": "on"})
    decision = scan(world)
    assert world.states()["ground"] == "disarmed"
    failed = [o for o in decision.occurrences if o.moment is Moment.ARM_FAILED]
    assert failed and failed[0].channel == "nfc"
    assert "window" in failed[0].zone_ids


def test_what_a_device_was_seen_as_survives_a_restart():
    world = house()
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.seen_devices == {"luca_tag"}


# --- attribution (decision 88) ---------------------------------------------------


def test_a_name_nothing_established_is_marked_as_claimed():
    """A service call may name somebody; nothing verified it (§9.1)."""
    world = house()
    world.arm("away", user_id="luca", channel="api", claimed=True)
    world.advance(30)
    armed = [o for o in world.last.occurrences if o.moment is Moment.ARMED]
    assert armed and armed[0].user_name == "Luca"
    assert armed[0].detail["attributed"] == "claimed"


def test_a_name_a_code_established_carries_no_marker():
    world = house()
    world.arm("away", user_id="luca", channel="ha_ui", code=CodeResult.VALID)
    world.advance(30)
    armed = [o for o in world.last.occurrences if o.moment is Moment.ARMED]
    assert armed and "attributed" not in armed[0].detail


def test_a_tag_is_not_a_claim_either():
    """Possession established it, even though no code did (§9.3)."""
    world = house()
    scan(world)
    world.advance(30)
    armed = [o for o in world.last.occurrences if o.moment is Moment.ARMED]
    assert armed and "attributed" not in armed[0].detail


def test_what_a_claim_was_survives_a_restart():
    world = house()
    world.arm("away", user_id="luca", channel="api", claimed=True)
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.area("ground").claimed is True


# --- the white list (part 2 decision 1) ------------------------------------------


def test_a_device_answers_only_to_the_name_it_was_given():
    config = replace(make_house(), devices=(keypad(),))
    assert config.device_by_ref("keypad_hall") is not None
    assert config.device_by_ref("keypad_garden") is None
    assert config.device_by_ref(None) is None


def test_a_disabled_device_is_not_found_by_its_name():
    """Switching a device off must stop it commanding, not merely hide it."""
    config = replace(make_house(), devices=(keypad(enabled=False),))
    assert config.device_by_ref("keypad_hall") is None


def test_a_keypad_speaks_on_the_keypad_channel_and_a_tag_on_nfc():
    assert keypad().channel == "keypad" and not keypad().token
    assert tag().channel == "nfc" and tag().token


# --- validation ------------------------------------------------------------------


def codes(config) -> set[str]:
    return {p.code for p in validate(config)}


def with_devices(*devices: ArmingDevice):
    return replace(make_house(), users=(user(),), devices=devices)


def test_a_keypad_needs_the_name_it_calls_itself_by():
    assert "ref_required" in codes(with_devices(keypad(ref=None)))


def test_two_devices_cannot_share_one_name():
    assert "duplicate_ref" in codes(
        with_devices(keypad(), keypad(id="other", name="Garden"))
    )


def test_a_tag_may_not_carry_a_name_anybody_could_type():
    """A ref is typed into a message; a tag has no code to protect it."""
    assert "tag_has_no_ref" in codes(with_devices(tag(ref="luca_tag")))


def test_a_tag_needs_an_entity_and_an_owner():
    problems = codes(with_devices(tag(entity_id=None, user_id=None)))
    assert {"tag_entity_required", "tag_needs_a_user"} <= problems


def test_a_tag_that_arms_needs_a_scenario_that_exists():
    assert "scenario_required" in codes(with_devices(tag(scenario_id=None)))
    assert "unknown_scenario" in codes(with_devices(tag(scenario_id="ghost")))
    # Disarming needs none: it acts on every area, as the master does.
    assert not codes(with_devices(tag(command=KeyCommand.DISARM, scenario_id=None)))


def test_a_keypad_has_no_entity_and_no_owner():
    assert "keypad_has_no_entity" in codes(with_devices(keypad(user_id="luca")))


def test_devices_survive_the_round_trip_through_the_document():
    config = with_devices(tag(), keypad())
    assert config_from_dict(config_to_dict(config)).devices == config.devices
