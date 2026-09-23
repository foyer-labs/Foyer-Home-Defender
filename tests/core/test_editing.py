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
    item = {
        "id": "window",
        **ZONE_ITEM,
        "entity_id": config.zone("window").entity_id,
        "area_id": "ground",
        "name": "Kitchen",
    }
    item["trigger"] = {"kind": "state", "states": ["on"]}
    result = upsert(config, RuntimeState(), "zone", item)
    assert result.config is not None
    assert result.config.zone("window").name == "Kitchen"


def test_swapping_the_entity_needs_the_trigger_confirmed_again(config):
    """INV-5 (third review): the same trigger on another entity is a trigger
    nobody read against that entity's states — a lock's `locked/unlocked`
    never matches `on`, and the alarm never fires."""
    item = {"id": "window", **ZONE_ITEM, "area_id": "ground"}
    item["entity_id"] = "lock.front"
    item["trigger"] = {"kind": "state", "states": ["on"]}
    assert upsert(config, RuntimeState(), "zone", item).problems[0].code == (
        "trigger_not_confirmed"
    )
    confirmed = upsert(config, RuntimeState(), "zone", item, trigger_confirmed=True)
    assert confirmed.config is not None
    assert confirmed.config.zone("window").entity_id == "lock.front"


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
    item = {
        "id": "window",
        **ZONE_ITEM,
        "entity_id": config.zone("window").entity_id,
        "area_id": "ground",
        "cross_zone_id": "patio",
    }
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
        "targets": [{"entity_id": "media_player.kitchen"}],
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
    assert [t.entity_id for t in good.config.chime.targets] == ["media_player.kitchen"]


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


def test_saving_settings_leaves_the_code_and_lockout_numbers_alone(config):
    """Page 11 does not own them; page 7 does (§8.1, §8.4).

    Rebuilding the settings block without them put the code length back to
    six. A household with eight-digit codes then had a keypad that submitted
    after six digits and a lockout waiting at the fifth try — which is the
    "cannot disarm the house" class of failure.
    """
    from dataclasses import replace

    from custom_components.foyer.core.models import SecuritySettings

    hardened = replace(
        config,
        settings=replace(
            config.settings,
            security=SecuritySettings(
                code_length=8,
                lockout_failures=3,
                lockout_window=600,
                lockout_duration=900,
            ),
        ),
    )

    saved = update_settings(
        hardened, RuntimeState(), {"siren_duration": 120, "arm_hold_timeout": 600}
    )

    assert saved.config is not None
    assert saved.config.settings.security.code_length == 8
    assert saved.config.settings.security.lockout_failures == 3
    assert saved.config.settings.security.lockout_window == 600
    assert saved.config.settings.security.lockout_duration == 900


def test_saving_settings_leaves_the_mqtt_contract_alone(config):
    """The same rule, for the block page 8 owns (§9.2)."""
    from dataclasses import replace

    from custom_components.foyer.core.models import MqttDetail, MqttSettings

    with_mqtt = replace(
        config,
        settings=replace(
            config.settings,
            mqtt=MqttSettings(
                enabled=True,
                command_topic="house/alarm/cmd",
                detail=MqttDetail.FULL,
            ),
        ),
    )

    saved = update_settings(
        with_mqtt, RuntimeState(), {"siren_duration": 120, "arm_hold_timeout": 600}
    )

    assert saved.config is not None
    assert saved.config.settings.mqtt.enabled is True
    assert saved.config.settings.mqtt.command_topic == "house/alarm/cmd"
    assert saved.config.settings.mqtt.detail is MqttDetail.FULL


def test_a_configuration_change_records_the_value_before_and_after(config):
    """A field name on its own does not answer "who changed what" (§10.2)."""
    from dataclasses import replace

    from custom_components.foyer.store.editing import config_diff

    area = config.areas[0]
    renamed = replace(area, name="Windows and doors", default_exit_delay=45)
    new = replace(config, areas=(renamed, *config.areas[1:]))

    changes = config_diff(config, new)
    fields = changes["areas"]["changed"]["Windows and doors"]
    assert fields["default_exit_delay"] == [area.default_exit_delay, 45]
    assert fields["name"] == [area.name, "Windows and doors"]


def test_a_long_value_says_it_changed_without_dragging_itself_in(config):
    """A row that contains the configuration is a row nobody reads."""
    from dataclasses import replace

    from custom_components.foyer.core.models import ActionKind, Moment, ProfileAction
    from custom_components.foyer.store.editing import config_diff

    profile = config.profiles[0]
    action = ProfileAction(
        id="new", kind=ActionKind.SIREN, moments=frozenset({Moment.TRIGGERED})
    )
    new = replace(
        config,
        profiles=(replace(profile, actions=(*profile.actions, action)),),
    )

    fields = config_diff(config, new)["profiles"]["changed"][profile.name]
    assert fields["actions"] == []


def _unconfirmed(config):
    """A zone as the Alarmo importer leaves it: off, its trigger a proposal."""
    from dataclasses import replace

    window = config.zone("window")
    return replace(
        config,
        zones=tuple(
            replace(z, enabled=False, trigger_confirmed=False) if z is window else z
            for z in config.zones
        ),
    )


def test_an_unconfirmed_zone_may_not_be_switched_on_without_confirming(config):
    """INV-5: a proposal nobody checked may exist, but it may not watch."""
    from custom_components.foyer.store.schema import zone_to_dict

    config = _unconfirmed(config)
    item = {**zone_to_dict(config.zone("window")), "enabled": True}
    refused = upsert(config, RuntimeState(), "zone", item)
    assert refused.config is None
    assert [p.code for p in refused.problems] == ["trigger_not_confirmed"]

    accepted = upsert(config, RuntimeState(), "zone", item, trigger_confirmed=True)
    zone = accepted.config.zone("window")
    assert zone.enabled and zone.trigger_confirmed


def test_the_item_cannot_claim_its_own_confirmation(config):
    """The flag is this request's confirmation or the stored zone's, never a
    field a client writes into the body."""
    from custom_components.foyer.store.schema import zone_to_dict

    config = _unconfirmed(config)
    item = {
        **zone_to_dict(config.zone("window")),
        "enabled": True,
        "trigger_confirmed": True,
    }
    assert upsert(config, RuntimeState(), "zone", item).config is None


def test_an_unconfirmed_zone_stays_editable_while_it_is_off(config):
    """Renaming a zone nobody has confirmed yet does not confirm it."""
    from custom_components.foyer.store.schema import zone_to_dict

    config = _unconfirmed(config)
    item = {**zone_to_dict(config.zone("window")), "name": "Kitchen window"}
    result = upsert(config, RuntimeState(), "zone", item)
    zone = result.config.zone("window")
    assert zone.name == "Kitchen window"
    assert zone.trigger_confirmed is False and zone.enabled is False


def test_validation_refuses_an_enabled_unconfirmed_zone_on_every_path(config):
    """A restore or an import goes through validate() and not through
    upsert(), so the rule has to live there too."""
    from dataclasses import replace

    from custom_components.foyer.core.validation import validate

    window = config.zone("window")
    bad = replace(
        config,
        zones=tuple(
            replace(z, trigger_confirmed=False) if z is window else z
            for z in config.zones
        ),
    )
    assert ("trigger_not_confirmed", "window") in {
        (p.code, p.ref) for p in validate(bad)
    }


# --- the watchdog URL: written, never read back (§12.3, decision 130) --------------

PING = "https://hc-ping.example/9f8c-secret-token"


def _watched(config):
    """An installation whose watchdog is on and pings PING."""
    from dataclasses import replace

    from custom_components.foyer.core.models import WatchdogSettings

    return replace(
        config,
        health=replace(
            config.health, watchdog=WatchdogSettings(enabled=True, url=PING)
        ),
    )


def _panel_health(config, **watchdog):
    """The block as page 14 sends it: no URL, unless somebody typed one."""
    from custom_components.foyer.store.schema import health_to_dict

    health = health_to_dict(config.health)
    health["watchdog"].pop("url")
    health["watchdog"].update(watchdog)
    return health


def test_a_health_save_without_a_url_keeps_the_stored_one(config):
    """The panel has no URL to send back: nothing returns it. A save that
    cleared it would stop the heartbeat quietly."""
    from custom_components.foyer.store.editing import config_diff, update_health

    config = _watched(config)
    for sent in ({}, {"url": None}, {"url": ""}, {"url": "   "}):
        result = update_health(
            config, RuntimeState(), _panel_health(config, interval=600, **sent)
        )
        assert result.config is not None, (sent, result.problems)
        watchdog = result.config.health.watchdog
        # Null in particular: read as-is it became the string "None", a URL
        # that is set and pings nothing.
        assert watchdog.url == PING, sent
        assert watchdog.enabled and watchdog.interval == 600
        # Kept before anything compares the two: the log row does not say
        # the URL changed when it did not.
        assert "watchdog.url" not in config_diff(config, result.config).get(
            "health", {}
        )


def test_a_new_url_replaces_the_stored_one(config):
    from custom_components.foyer.store.editing import config_diff, update_health

    config = _watched(config)
    result = update_health(
        config,
        RuntimeState(),
        _panel_health(config, url="  https://uptime.example/api/push/other  "),
    )
    assert result.config.health.watchdog.url == "https://uptime.example/api/push/other"
    assert config_diff(config, result.config)["health"]["watchdog.url"] == []


def test_switching_the_watchdog_off_keeps_its_url(config):
    from custom_components.foyer.store.editing import update_health

    config = _watched(config)
    off = update_health(config, RuntimeState(), _panel_health(config, enabled=False))
    assert off.config.health.watchdog.enabled is False
    assert off.config.health.watchdog.url == PING
    # And back on without typing it again: the stored URL passes validation.
    on = update_health(
        off.config, RuntimeState(), _panel_health(off.config, enabled=True)
    )
    assert on.config is not None, on.problems
    assert on.config.health.watchdog.enabled is True


def test_a_watchdog_switched_on_with_no_url_anywhere_is_still_refused(config):
    """Keeping means keeping what there is: on a fresh installation there is
    nothing, and a watchdog with nowhere to ping is refused as before."""
    from custom_components.foyer.store.editing import update_health

    result = update_health(config, RuntimeState(), _panel_health(config, enabled=True))
    assert result.config is None
    assert result.problems[0].code == "watchdog_url_required"


def test_a_watchdog_block_that_is_not_a_map_is_refused_not_a_traceback(config):
    from custom_components.foyer.store.editing import update_health

    health = _panel_health(config)
    health["watchdog"] = "on"
    result = update_health(config, RuntimeState(), health)
    assert result.config is None
    assert result.problems[0].code == "invalid"
