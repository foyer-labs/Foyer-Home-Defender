"""Configuration edits from the panel, validated in the backend (pure)."""

from __future__ import annotations

import itertools

from custom_components.foyer.core.models import (
    Channel,
    EntryMode,
    RuntimeState,
    StateTrigger,
    ZoneType,
)
from custom_components.foyer.store.editing import delete, update_settings, upsert

from .helpers import World

IDS = (f"new{n}" for n in itertools.count())


def new_id() -> str:
    return next(IDS)


ZONE_ITEM = {
    "name": "Study window",
    "entity_id": "binary_sensor.study_window",
    "area_id": "upstairs",
    "type": "delayed",
    "trigger": {"kind": "state", "states": ["on"]},
}


def test_new_zone_takes_its_preset_and_needs_a_confirmed_trigger(config):
    refused = upsert(config, RuntimeState(), "zone", ZONE_ITEM, new_id=new_id)
    assert refused.config is None
    assert refused.problems[0].code == "trigger_not_confirmed"

    result = upsert(
        config,
        RuntimeState(),
        "zone",
        ZONE_ITEM,
        trigger_confirmed=True,
        new_id=new_id,
    )
    zone = result.config.zone(result.id)
    assert zone.entry_mode is EntryMode.DELAYED  # from the "delayed" preset
    assert zone.channel is Channel.INTRUSION
    assert zone.trigger == StateTrigger(frozenset({"on"}))


def test_editing_a_zone_without_touching_its_trigger_needs_no_confirmation(config):
    item = {"id": "window", **ZONE_ITEM, "area_id": "ground", "name": "Kitchen"}
    item["trigger"] = {"kind": "state", "states": ["on"]}
    result = upsert(config, RuntimeState(), "zone", item)
    assert result.config is not None
    assert result.config.zone("window").name == "Kitchen"


def test_changing_a_trigger_needs_confirmation_again(config):
    item = {**ZONE_ITEM, "id": "window", "area_id": "ground"}
    item["trigger"] = {"kind": "state", "states": ["off"]}
    assert upsert(config, RuntimeState(), "zone", item).problems[0].code == (
        "trigger_not_confirmed"
    )


def test_explicit_properties_override_the_preset(config):
    item = {**ZONE_ITEM, "entry_mode": "instant"}
    result = upsert(
        config, RuntimeState(), "zone", item, trigger_confirmed=True, new_id=new_id
    )
    assert result.config.zone(result.id).entry_mode is EntryMode.INSTANT


def test_technical_zones_are_accepted_now_their_channel_exists(config):
    """Part 1 refused them; the technical channel (§5.5) lifts the refusal."""
    item = {**ZONE_ITEM, "type": ZoneType.TECHNICAL.value}
    result = upsert(
        config, RuntimeState(), "zone", item, trigger_confirmed=True, new_id=new_id
    )
    assert result.problems == ()
    zone = result.config.zone(result.id)
    assert (zone.channel, zone.always_on, zone.bypassable) == (
        Channel.TECHNICAL,
        True,
        False,
    )


GROUP_ITEM = {
    "name": "Open plan",
    "area_id": "ground",
    "members": ["window", "patio"],
    "n": 2,
    "window_seconds": 60,
}


def test_groups_are_created_edited_and_deleted(config):
    created = upsert(config, RuntimeState(), "group", GROUP_ITEM, new_id=new_id)
    assert created.problems == ()
    group = created.config.group(created.id)
    assert (group.members, group.n, group.suppress_members) == (
        ("window", "patio"),
        2,
        False,
    )
    removed = delete(created.config, RuntimeState(), "group", created.id)
    assert removed.config.groups == ()


def test_a_zone_in_a_group_cannot_be_deleted_first(config):
    created = upsert(config, RuntimeState(), "group", GROUP_ITEM, new_id=new_id)
    refused = delete(created.config, RuntimeState(), "zone", "window")
    assert [p.code for p in refused.problems] == ["zone_in_group"]


def test_a_cross_zone_partner_cannot_be_deleted_first(config):
    item = {"id": "window", **ZONE_ITEM, "area_id": "ground", "cross_zone_id": "patio"}
    item["trigger"] = {"kind": "state", "states": ["on"]}
    paired = upsert(config, RuntimeState(), "zone", item)
    assert paired.problems == ()
    refused = delete(paired.config, RuntimeState(), "zone", "patio")
    assert [p.code for p in refused.problems] == ["zone_is_cross_partner"]


def test_group_edits_are_refused_while_a_member_area_is_armed():
    world = World()
    world.arm("night")  # arms the ground floor only
    item = {**GROUP_ITEM, "area_id": "upstairs", "members": ["bath", "window"]}
    result = upsert(world.config, world.state, "group", item, new_id=new_id)
    assert [p.code for p in result.problems] == ["area_not_disarmed"]


def test_chime_settings_are_validated(config):
    from custom_components.foyer.store.editing import update_chime

    chime = {
        "targets": ["media_player.kitchen"],
        "mode": "speech",
        "tts_entity": None,
        "volume": 140,
        "quiet_start": "23:00",
        "quiet_end": None,
        "during_exit": False,
    }
    bad = update_chime(config, RuntimeState(), chime)
    assert sorted(p.code for p in bad.problems) == [
        "chime_tts_required",
        "quiet_hours_incomplete",
        "volume_out_of_range",
    ]
    good = update_chime(
        config,
        RuntimeState(),
        {**chime, "tts_entity": "tts.piper", "volume": 40, "quiet_end": "07:00"},
    )
    assert good.config.chime.targets == ("media_player.kitchen",)


def test_garbage_is_a_problem_not_an_exception(config):
    result = upsert(config, RuntimeState(), "zone", {"name": "x", "type": "nope"})
    assert result.problems[0].code == "invalid"


def test_area_with_defaults(config):
    result = upsert(config, RuntimeState(), "area", {"name": "Cellar"}, new_id=new_id)
    area = result.config.area(result.id)
    assert (area.default_exit_delay, area.default_entry_delay) == (30, 30)


def test_duplicate_names_are_refused(config):
    result = upsert(config, RuntimeState(), "area", {"name": "garage"}, new_id=new_id)
    assert [p.code for p in result.problems] == ["duplicate_name"]


def test_deleting_what_is_still_used_is_refused(config):
    assert delete(config, RuntimeState(), "area", "ground").problems[0].code == (
        "area_has_zones"
    )
    assert (
        delete(config, RuntimeState(), "zone", "nope").problems[0].code == "not_found"
    )
    assert delete(config, RuntimeState(), "zone", "window").config is not None


def test_edits_are_refused_while_the_area_is_armed():
    world = World()
    world.arm("night")
    item = {**ZONE_ITEM, "area_id": "ground"}
    result = upsert(
        world.config, world.state, "zone", item, trigger_confirmed=True, new_id=new_id
    )
    assert [p.code for p in result.problems] == ["area_not_disarmed"]


def test_settings_are_validated(config):
    bad = update_settings(
        config, RuntimeState(), {"siren_duration": 901, "arm_hold_timeout": 300}
    )
    assert [p.code for p in bad.problems] == ["siren_out_of_range"]
    good = update_settings(
        config, RuntimeState(), {"siren_duration": 120, "arm_hold_timeout": 600}
    )
    assert good.config.settings.arm_hold_timeout == 600
