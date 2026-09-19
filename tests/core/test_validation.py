"""Configuration validation and the edit guard (pure)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from custom_components.foyer.core.models import (
    ArmPolicy,
    Channel,
    EntryMode,
    EventTrigger,
    KeyAction,
    KeyCommand,
    NumericOperator,
    NumericTrigger,
    Settings,
    StateTrigger,
    ZoneType,
)
from custom_components.foyer.core.presets import PRESETS, preset
from custom_components.foyer.core.validation import edit_conflicts, validate

from .helpers import World, make_house


def with_zone(config, zone_id="window", **changes):
    return replace(
        config,
        zones=tuple(
            replace(z, **changes) if z.id == zone_id else z for z in config.zones
        ),
    )


def codes(config) -> set[str]:
    return {p.code for p in validate(config)}


def test_the_test_house_is_valid(config):
    assert validate(config) == []


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"entry_delay": 301}, "delay_out_of_range"),
        ({"entry_delay": -1}, "delay_out_of_range"),
        (
            {"trigger": StateTrigger(frozenset({"on", "unavailable"}))},
            "fault_state_as_trigger",
        ),
        ({"area_id": "nowhere"}, "unknown_area"),
        ({"channel": Channel.TECHNICAL}, "technical_always_on"),
        (
            {"channel": Channel.TECHNICAL, "always_on": True, "chime": True},
            "intrusion_only",
        ),
        ({"chime": True, "always_on": True}, "chime_always_on"),
        ({"trigger_count": 11}, "count_out_of_range"),
        ({"trigger_window": 0}, "window_out_of_range"),
        ({"cross_zone_id": "window"}, "cross_zone_invalid"),
        ({"cross_zone_id": "nope"}, "cross_zone_invalid"),
        (
            {"always_on": True, "entry_mode": EntryMode.DELAYED},
            "always_on_must_be_instant",
        ),
        (
            {"arm_policy": ArmPolicy.AUTO_BYPASS, "bypassable": False},
            "auto_bypass_needs_bypassable",
        ),
        ({"arm_hold_timeout": 120}, "hold_needs_arm_after_closing"),
        (
            {"arm_policy": ArmPolicy.ARM_AFTER_CLOSING, "arm_hold_timeout": 30},
            "hold_out_of_range",
        ),
        ({"supervision_timeout": 5}, "supervision_out_of_range"),
        ({"channel": Channel.KEY}, "key_action_required"),
        ({"key": KeyAction(KeyCommand.DISARM)}, "key_action_not_allowed"),
        ({"trigger": EventTrigger("press")}, "trigger_domain"),
        ({"entity_id": "light.kitchen"}, "unsupported_domain"),
        (
            {"trigger": NumericTrigger(NumericOperator.EQ, 1, hysteresis=1)},
            "eq_hysteresis",
        ),
        ({"name": "  "}, "name_required"),
    ],
)
def test_zone_problems(config, changes, code):
    assert code in codes(with_zone(config, **changes))


def test_key_arm_needs_a_real_scenario(config):
    bad = with_zone(
        config,
        channel=Channel.KEY,
        key=KeyAction(KeyCommand.ARM, "missing"),
    )
    assert "key_scenario_required" in codes(bad)


def test_event_trigger_rules(config):
    event_zone = with_zone(config, entity_id="event.button", trigger=EventTrigger())
    assert "event_type_required" in codes(event_zone)
    tag_zone = with_zone(config, entity_id="tag.front", trigger=EventTrigger("press"))
    assert "event_type_not_allowed" in codes(tag_zone)
    state_on_event = with_zone(config, entity_id="event.b")
    assert "trigger_domain" in codes(state_on_event)


def test_bounds_on_areas_scenarios_and_settings(config):
    bad = replace(
        config,
        areas=(replace(config.areas[0], default_exit_delay=301), *config.areas[1:]),
        scenarios=(
            replace(config.scenarios[0], siren_duration_override=901, areas=()),
            *config.scenarios[1:],
        ),
        settings=Settings(siren_duration=0, arm_hold_timeout=10),
    )
    assert {
        "delay_out_of_range",
        "siren_out_of_range",
        "scenario_without_areas",
        "hold_out_of_range",
    } <= codes(bad)


def test_duplicate_ids(config):
    bad = replace(config, zones=(*config.zones, config.zones[0]))
    assert "duplicate_id" in codes(bad)


# --- presets --------------------------------------------------------------------------


def test_every_preset_produces_a_zone_the_validator_accepts_or_names(config):
    for zone_type in ZoneType:
        props = PRESETS[zone_type]
        zone = replace(config.zones[2], type=zone_type, **props)
        if zone.channel is Channel.KEY:
            zone = replace(zone, key=KeyAction(KeyCommand.TOGGLE, "night"))
        found = codes(replace(config, zones=(zone,)))
        assert found == set(), zone_type


def test_presets_are_plain_json():
    assert preset(ZoneType.DELAYED)["entry_mode"] == "delayed"
    assert preset(ZoneType.TAMPER)["always_on"] is True


# --- editing while armed --------------------------------------------------------------


def test_zones_of_an_armed_area_cannot_be_edited():
    world = World()
    world.arm("night")
    new = with_zone(world.config, entry_delay=10)  # window: ground, armed
    assert [p.code for p in edit_conflicts(world.config, new, world.state)] == [
        "area_not_disarmed"
    ]


def test_disarmed_areas_can_be_programmed_while_others_are_armed():
    world = World()
    world.arm("night")
    new = with_zone(world.config, "garage_door", entry_delay=10)
    assert edit_conflicts(world.config, new, world.state) == []


def test_the_active_scenario_cannot_be_edited():
    world = World()
    world.arm("night")
    new = replace(
        world.config,
        scenarios=tuple(
            replace(s, exit_delay_override=10) if s.id == "night" else s
            for s in world.config.scenarios
        ),
    )
    assert [p.code for p in edit_conflicts(world.config, new, world.state)] == [
        "scenario_active"
    ]


def test_a_zone_cannot_be_moved_into_an_armed_area():
    world = World()
    world.arm("night")
    new = with_zone(world.config, "garage_door", area_id="ground")
    assert edit_conflicts(world.config, new, world.state)


def test_follows_rules(config):
    # Only a follower may follow, and only delayed intrusion zones.
    assert "follows_needs_follower" in codes(with_zone(config, follows=("door",)))
    assert "follows_not_delayed" in codes(
        with_zone(config, "hall", follows=("window",))
    )
    assert "follows_not_delayed" in codes(with_zone(config, "hall", follows=("nope",)))
    assert validate(with_zone(config, "landing", follows=("door", "garage_door"))) == []


# --- verification groups and cross-zone (§4.8) -------------------------------------


def with_group(config, **changes):
    from custom_components.foyer.core.models import Group

    group = Group("open", "Open plan", "ground", ("window", "patio"), 2, 60)
    return replace(config, groups=(replace(group, **changes),))


def test_a_valid_group_and_a_valid_pair(config):
    assert validate(with_group(config)) == []
    # Members in different areas are allowed (part 2 decision 9).
    assert validate(with_group(config, members=("window", "bath"))) == []
    assert validate(with_zone(config, cross_zone_id="bath")) == []


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"members": ("window",)}, "group_members"),
        ({"members": ("window", "window")}, "group_members"),
        ({"members": ("window", "nope")}, "group_member_invalid"),
        ({"n": 3}, "group_threshold"),
        ({"n": 1}, "group_threshold"),
        ({"window_seconds": 0}, "window_out_of_range"),
        ({"area_id": "nowhere"}, "unknown_area"),
        ({"name": ""}, "name_required"),
    ],
)
def test_group_problems(config, changes, code):
    assert code in codes(with_group(config, **changes))


def test_a_zone_belongs_to_one_group_at_most(config):
    # In a group and in a cross-zone pair: its activation would count twice.
    both = with_zone(with_group(config), "window", cross_zone_id="bath")
    assert "zone_in_two_groups" in codes(both)
    # Two pairs through the same zone.
    two_pairs = with_zone(
        with_zone(config, "window", cross_zone_id="bath"), "patio", cross_zone_id="bath"
    )
    assert "zone_in_two_groups" in codes(two_pairs)
    # A pair declared from both ends is one pair.
    mutual = with_zone(
        with_zone(config, "window", cross_zone_id="bath"),
        "bath",
        cross_zone_id="window",
    )
    assert validate(mutual) == []


def test_a_mutual_pair_has_one_window(config):
    mutual = with_zone(
        with_zone(config, "window", cross_zone_id="bath"),
        "bath",
        cross_zone_id="window",
        cross_zone_window=90,
    )
    assert "cross_zone_window_mismatch" in codes(mutual)


def test_chime_targets_must_be_players_sirens_or_notify(config):
    from custom_components.foyer.core.models import ChimeSettings, ChimeTarget

    bad = replace(config, chime=ChimeSettings(targets=(ChimeTarget("light.hall"),)))
    assert "chime_target_invalid" in codes(bad)
    sound = replace(
        config, chime=ChimeSettings(targets=(ChimeTarget("media_player.kitchen"),))
    )
    assert "chime_sound_required" in codes(sound)
    siren = replace(config, chime=ChimeSettings(targets=(ChimeTarget("siren.hall"),)))
    assert validate(siren) == []
    # The free channels the house already has (decision 60), with quiet hours
    # of their own (part 3 decision 8).
    phone = replace(
        config,
        chime=ChimeSettings(
            targets=(ChimeTarget("notify.mobile_app_luca", "22:00", "07:30"),)
        ),
    )
    assert validate(phone) == []
    half = replace(
        config,
        chime=ChimeSettings(targets=(ChimeTarget("notify.x", quiet_start="22:00"),)),
    )
    assert "quiet_hours_incomplete" in codes(half)


def test_editing_a_cross_zone_partner_in_an_armed_area_is_refused():
    world = World()
    world.arm("night")  # ground armed; bath is upstairs, disarmed
    paired = with_zone(world.config, "bath", cross_zone_id="window")
    assert [p.code for p in edit_conflicts(world.config, paired, world.state)] == [
        "area_not_disarmed"
    ]


def test_an_attachment_nobody_implements_is_refused(config):
    """§6.2: each transport reads its own key and ignores the rest in silence.

    A value Foyer does not turn into a payload is a picture that never
    arrives and never explains why — so it is refused where it is typed.
    """
    from custom_components.foyer.core.models import (
        ActionKind,
        Moment,
        ProfileAction,
        ResponseProfile,
    )

    def profile_with(attachment: str) -> object:
        return replace(
            config,
            profiles=(
                ResponseProfile(
                    id="p",
                    name="Tell",
                    actions=(
                        ProfileAction(
                            id="a",
                            kind=ActionKind.NOTIFY,
                            moments=frozenset({Moment.TRIGGERED}),
                            params={
                                "service": "notify.telegram",
                                "message": "x",
                                "camera_entity_id": "camera.front",
                                "attachment": attachment,
                            },
                        ),
                    ),
                ),
            ),
        )

    assert "unknown_attachment" in codes(profile_with("signal"))
    assert "unknown_attachment" not in codes(profile_with("telegram"))
    assert "unknown_attachment" not in codes(profile_with("companion"))


# --- contacts and escalation steps (SPEC §7) ---------------------------------------


def _house_with_contact(contact):
    return replace(make_house(), contacts=(contact,))


def test_a_contact_with_no_channel_is_refused():
    from custom_components.foyer.core.models import Contact

    problems = validate(_house_with_contact(Contact("c1", "Luca")))
    assert ("contact_without_channels", "contact") in {
        (p.code, p.kind) for p in problems
    }


def test_a_channel_must_name_a_notify_service():
    from custom_components.foyer.core.models import Contact, ContactChannel

    contact = Contact(
        "c1", "Luca", channels=(ContactChannel("ch", service="sms.send"),)
    )
    codes = {p.code for p in validate(_house_with_contact(contact))}
    assert "notify_service_required" in codes


def test_quiet_hours_need_both_ends():
    from custom_components.foyer.core.models import Contact, ContactChannel

    contact = Contact(
        "c1",
        "Luca",
        channels=(ContactChannel("ch", service="notify.app"),),
        quiet_start="22:00",
    )
    codes = {p.code for p in validate(_house_with_contact(contact))}
    assert "quiet_hours_incomplete" in codes


def test_a_notify_action_names_a_service_or_contacts_but_never_both():
    from custom_components.foyer.core.models import (
        ActionKind,
        Contact,
        ContactChannel,
        Moment,
        ProfileAction,
        ResponseProfile,
    )

    contact = Contact(
        "c1", "Luca", channels=(ContactChannel("ch", service="notify.app"),)
    )

    def with_params(params):
        profile = ResponseProfile(
            "p",
            "P",
            actions=(
                ProfileAction(
                    "a", ActionKind.NOTIFY, frozenset({Moment.TRIGGERED}), params=params
                ),
            ),
        )
        config = replace(
            _house_with_contact(contact),
            profiles=(profile,),
            settings=replace(make_house().settings, default_profile_id="p"),
        )
        return {p.code for p in validate(config)}

    assert "notify_target_required" in with_params({"message": "x"})
    assert "notify_target_ambiguous" in with_params(
        {"message": "x", "service": "notify.app", "contacts": [{"contact_id": "c1"}]}
    )
    assert "unknown_contact" in with_params(
        {"message": "x", "contacts": [{"contact_id": "nobody"}]}
    )
    assert not (
        {"notify_target_required", "notify_target_ambiguous", "unknown_contact"}
        & with_params({"message": "x", "contacts": [{"contact_id": "c1"}]})
    )


def test_an_escalation_step_is_a_notification_on_a_moment_that_can_be_acknowledged():
    from custom_components.foyer.core.models import (
        ActionKind,
        Moment,
        ProfileAction,
        ResponseProfile,
    )

    def codes(action):
        config = replace(
            make_house(), profiles=(ResponseProfile("p", "P", actions=(action,)),)
        )
        config = replace(
            config, settings=replace(config.settings, default_profile_id="p")
        )
        return {p.code for p in validate(config)}

    siren = ProfileAction(
        "a",
        ActionKind.SIREN,
        frozenset({Moment.TRIGGERED}),
        params={"entity_ids": ["siren.indoor"], "duration": 30},
        escalation_offset=60,
    )
    assert "escalation_kind_invalid" in codes(siren)

    armed = ProfileAction(
        "a",
        ActionKind.PERSISTENT_NOTIFICATION,
        frozenset({Moment.ARMED}),
        escalation_offset=60,
    )
    assert "escalation_moment_invalid" in codes(armed)

    too_far = ProfileAction(
        "a",
        ActionKind.PERSISTENT_NOTIFICATION,
        frozenset({Moment.TRIGGERED}),
        escalation_offset=999999,
    )
    assert "escalation_offset_out_of_range" in codes(too_far)
