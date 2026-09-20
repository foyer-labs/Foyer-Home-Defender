"""System health (SPEC §12): the mains, the channels, the watchdog, the radio.

Every one of these runs with no Home Assistant instance anywhere, which is
the point of putting the arithmetic in ``core/health.py``: "eight zones on
one radio went quiet and the coordinator is still answering" is a question
that can be asked of a pure function, and the night it matters is not the
night to find out what the answer would have been.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core import health
from custom_components.foyer.core.models import (
    ActionKind,
    AreaState,
    ChannelFault,
    CodeResult,
    Contact,
    ContactChannel,
    ContactChannelKind,
    EntityState,
    HealthCause,
    HealthSettings,
    Moment,
    ProfileAction,
    Radio,
    ResponseProfile,
    Settings,
    Startup,
    WatchdogSettings,
    channel_key,
)

from .helpers import NOW, World, make_house

MAINS = "binary_sensor.ups_on_battery"
COORDINATOR = "sensor.zha_coordinator"

# Four zones on one radio is the §12.5 default threshold.
RADIO_ZONES = ("window", "bath", "landing", "garage_door")


def house_with_health(**health_kwargs) -> object:
    config = make_house()
    return replace(config, health=HealthSettings(**health_kwargs))


def zigbee_world(*, coordinator: str | None = COORDINATOR, **health_kwargs) -> World:
    """A house whose four ordinary zones all sit on one Zigbee radio."""
    config = house_with_health(
        radios=(Radio("zigbee", "Zigbee", "entry1", coordinator),),
        **health_kwargs,
    )
    world = World(config)
    entity_ids = [config.zone(z).entity_id for z in RADIO_ZONES]
    world.on_radio("zigbee", *entity_ids)
    if coordinator:
        world.entities[coordinator] = EntityState("ok", last_reported=NOW)
    return world


def silence(world: World, zones: tuple[str, ...], *, apart: float = 1.0) -> None:
    """Zones going unavailable one after another, ``apart`` seconds apart."""
    for zone_id in zones:
        entity_id = world.config.zone(zone_id).entity_id
        world.set(entity_id, "unavailable")
        world.advance(apart)


def moments(world: World) -> list[Moment]:
    return list(world.last.moments) if world.last else []


# --- mains power (§12.1) -----------------------------------------------------------


def test_mains_failure_is_announced_and_is_never_a_quiet_night():
    world = World(house_with_health(mains_entity_id=MAINS))
    world.set(MAINS, "off")
    assert Moment.SYSTEM_POWER_LOST not in moments(world)

    world.set(MAINS, "on")
    assert Moment.SYSTEM_POWER_LOST in moments(world)
    assert world.state.health.mains_lost_since == world.now
    assert HealthCause.MAINS_LOST in health.causes(
        world.state.health, world.config, world.snapshot()
    )


def test_mains_returning_says_so_and_how_long_it_was_gone():
    world = World(house_with_health(mains_entity_id=MAINS))
    world.set(MAINS, "on")
    world.advance(600)
    world.set(MAINS, "off")
    restored = next(
        o for o in world.last.occurrences if o.moment is Moment.SYSTEM_POWER_RESTORED
    )
    assert restored.detail["seconds"] == "600"
    assert world.state.health.mains_lost_since is None


def test_a_mains_entity_that_cannot_be_read_is_not_a_power_cut():
    """INV-4 in the one place where reporting a fault loudly would be worse.

    An unreadable entity is never "all quiet" — it is a cause of its own —
    but calling it a power cut would announce one at every restart, before
    the UPS integration has finished loading.
    """
    world = World(house_with_health(mains_entity_id=MAINS))
    world.set(MAINS, "unavailable")
    assert Moment.SYSTEM_POWER_LOST not in moments(world)
    causes = health.causes(world.state.health, world.config, world.snapshot())
    assert HealthCause.MAINS_UNKNOWN in causes
    assert HealthCause.MAINS_LOST not in causes


def test_the_state_that_means_lost_is_the_households_to_say():
    """INV-5 is not only about zones: a UPS says ``on`` for a failure and a
    power sensor says ``off``, and a default that guesses never fires."""
    world = World(house_with_health(mains_entity_id=MAINS, mains_lost_states=("off",)))
    world.set(MAINS, "on")
    assert Moment.SYSTEM_POWER_LOST not in moments(world)
    world.set(MAINS, "off")
    assert Moment.SYSTEM_POWER_LOST in moments(world)


# --- the external watchdog (§12.3) -------------------------------------------------


def watchdog_world(**kwargs) -> World:
    settings = WatchdogSettings(
        enabled=True, url="https://hc-ping.example/abc", **kwargs
    )
    return World(house_with_health(watchdog=settings))


def test_three_missed_pings_are_reported_locally_and_only_once():
    """Foyer watches the watchdog (§12.3): being unable to reach it means no
    internet-based notification would go out either."""
    world = watchdog_world()
    for _ in range(2):
        world.health(watchdog=False)
        assert Moment.WATCHDOG_UNREACHABLE not in moments(world)

    world.health(watchdog=False)
    assert Moment.WATCHDOG_UNREACHABLE in moments(world)
    assert world.state.health.watchdog.down_since == world.now

    world.health(watchdog=False)
    assert Moment.WATCHDOG_UNREACHABLE not in moments(world)


def test_a_watchdog_that_answers_again_says_so():
    world = watchdog_world()
    for _ in range(3):
        world.health(watchdog=False)
    world.health(watchdog=True)
    assert Moment.WATCHDOG_RECOVERED in moments(world)
    assert world.state.health.watchdog.down_since is None
    assert world.state.health.watchdog.ever_ok


def test_a_watchdog_that_never_worked_says_that_instead():
    """Almost always a mistyped URL, and a different sentence from "it stopped"."""
    world = watchdog_world()
    for _ in range(3):
        world.health(watchdog=False, watchdog_error="nodename nor servname")
    row = next(
        o for o in world.last.occurrences if o.moment is Moment.WATCHDOG_UNREACHABLE
    )
    assert row.detail["ever_ok"] == ""
    assert row.detail["error"] == "nodename nor servname"


def test_a_disabled_watchdog_reports_nothing():
    world = World(make_house())
    for _ in range(5):
        world.health(watchdog=False)
    assert Moment.WATCHDOG_UNREACHABLE not in moments(world)
    assert HealthCause.WATCHDOG_UNREACHABLE not in health.causes(
        world.state.health, world.config, world.snapshot()
    )


def test_the_watchdog_payload_is_empty_unless_explicitly_enabled():
    """SPEC §19 asks for this one by name, and P-1 is why it exists: a ping
    saying "armed, Night, nobody home" tells a third party when to come."""
    world = watchdog_world()
    assert health.watchdog_payload(world.config, world.snapshot()) is None

    louder = replace(
        world.config,
        health=replace(
            world.config.health,
            watchdog=replace(world.config.health.watchdog, payload=True),
        ),
    )
    payload = health.watchdog_payload(louder, world.snapshot())
    assert payload is not None
    # Even switched on it never names a scenario, an area or a zone.
    assert set(payload) == {"armed_areas", "areas", "healthy"}


# --- notification channel health (§12.2) -------------------------------------------


def contactable() -> tuple[Contact, ...]:
    return (
        Contact(
            "luca",
            "Luca",
            channels=(
                ContactChannel("push", ContactChannelKind.PUSH, "notify.mobile_luca"),
                ContactChannel("sms", ContactChannelKind.SMS, "notify.gsm"),
            ),
        ),
    )


def channels_world() -> World:
    config = replace(make_house(), contacts=contactable())
    return World(replace(config, health=HealthSettings()))


PUSH = channel_key("luca", "push")
SMS = channel_key("luca", "sms")


def test_a_service_removed_in_an_update_is_broken_at_once():
    world = channels_world()
    world.health(channels_present={PUSH: False, SMS: True})
    assert Moment.NOTIFICATION_CHANNEL_DOWN in moments(world)
    assert world.state.health.channel(PUSH).fault is ChannelFault.MISSING_SERVICE
    assert world.state.health.channel(SMS).fault is None


def test_the_broken_channel_is_announced_over_one_that_still_works():
    world = channels_world()
    world.health(channels_present={PUSH: False, SMS: True})
    row = next(
        o
        for o in world.last.occurrences
        if o.moment is Moment.NOTIFICATION_CHANNEL_DOWN
    )
    assert (row.detail["over_contact_id"], row.detail["over_channel_id"]) == (
        "luca",
        "sms",
    )


def test_when_every_channel_is_broken_there_is_nothing_to_announce_it_over():
    world = channels_world()
    world.health(channels_present={PUSH: False, SMS: False})
    rows = [
        o
        for o in world.last.occurrences
        if o.moment is Moment.NOTIFICATION_CHANNEL_DOWN
    ]
    assert len(rows) == 2
    assert all(r.detail["over_channel_id"] == "" for r in rows)


def test_one_failed_send_is_a_hiccup_and_two_are_a_pattern():
    world = channels_world()
    world.health(channels_present={PUSH: True, SMS: True})
    world.health(channel_sends={PUSH: False})
    assert Moment.NOTIFICATION_CHANNEL_DOWN not in moments(world)

    world.health(channel_sends={PUSH: False})
    assert Moment.NOTIFICATION_CHANNEL_DOWN in moments(world)
    assert world.state.health.channel(PUSH).fault is ChannelFault.SEND_FAILED


def test_a_successful_send_clears_everything():
    world = channels_world()
    world.health(channel_sends={PUSH: False})
    world.health(channel_sends={PUSH: False})
    world.health(channel_sends={PUSH: True})
    assert Moment.NOTIFICATION_CHANNEL_RESTORED in moments(world)
    assert world.state.health.channel(PUSH).fault is None
    assert world.state.health.channel(PUSH).failures == 0


def test_a_channel_nothing_has_been_learned_about_is_not_broken():
    """An installation that has just started has learned nothing, and
    reporting every channel as broken for the first sweep would be its own
    false alarm."""
    world = channels_world()
    assert health.broken_channels(world.state.health, world.config) == ()


# --- RF interference (§12.5) -------------------------------------------------------


def test_four_zones_on_one_radio_with_the_coordinator_answering():
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    # The threshold is met; nothing is announced until the confirmation
    # window has passed, so a coordinator reboot walks into this minute.
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)
    assert world.state.health.radio("zigbee").suspected_since is not None

    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
    row = next(
        o
        for o in world.last.occurrences
        if o.moment is Moment.RF_INTERFERENCE_SUSPECTED
    )
    assert row.detail["radio"] == "Zigbee"
    assert row.detail["count"] == "4"
    assert row.detail["coordinator"] == "answering"


def test_the_same_silence_with_the_coordinator_gone_is_a_different_fault():
    """A PoE coordinator dies with its switch: a different fault with a
    different fix, and conflating them teaches people to ignore both."""
    world = zigbee_world()
    world.set(COORDINATOR, "unavailable")
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)
    assert world.state.health.radio("zigbee").confirmed is False
    assert world.state.health.radio("zigbee").coordinator_down_since is not None


def test_a_coordinator_that_goes_during_a_suspicion_withdraws_it():
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert world.state.health.radio("zigbee").confirmed

    world.set(COORDINATOR, "unavailable")
    assert Moment.RF_INTERFERENCE_CLEARED in moments(world)
    assert Moment.RADIO_COORDINATOR_DOWN in moments(world)


def test_a_zigbee_outage_says_nothing_about_z_wave():
    """Counted per radio integration (§12.5), and only per radio.

    Every zone of one radio going quiet is that radio's event; the radio
    beside it, whose own zones are answering, is not in it.
    """
    config = house_with_health(
        radios=(
            Radio("zigbee", "Zigbee", "entry1", COORDINATOR),
            Radio("zwave", "Z-Wave", "entry2", "sensor.zwave_controller"),
        )
    )
    world = World(config)
    world.entities[COORDINATOR] = EntityState("ok", last_reported=NOW)
    world.entities["sensor.zwave_controller"] = EntityState("ok", last_reported=NOW)
    world.on_radio("zigbee", *(config.zone(z).entity_id for z in RADIO_ZONES[:2]))
    world.on_radio("zwave", *(config.zone(z).entity_id for z in RADIO_ZONES[2:]))
    silence(world, RADIO_ZONES[:2])
    world.advance(61)

    row = next(
        o
        for o in world.last.occurrences
        if o.moment is Moment.RF_INTERFERENCE_SUSPECTED
    )
    assert row.detail["radio"] == "Zigbee"
    assert world.state.health.radio("zigbee").confirmed
    assert world.state.health.radio("zwave").confirmed is False


def test_one_zone_of_several_going_quiet_is_a_flat_battery():
    """§12.5 opens with this sentence, and the threshold is what keeps it
    true: four zones on a radio raise at two, not at one."""
    world = zigbee_world()
    silence(world, RADIO_ZONES[:1])
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)


def test_a_radio_with_no_coordinator_named_raises_nothing():
    """The gate is what makes the heuristic worth having; without it Foyer
    says nothing at all rather than guessing which entity is the coordinator."""
    world = zigbee_world(coordinator=None)
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)


def test_silences_spread_over_hours_are_flat_batteries_not_jamming():
    world = zigbee_world()
    silence(world, RADIO_ZONES, apart=3600)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)


def test_zones_coming_back_end_the_suspicion():
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert world.state.health.radio("zigbee").confirmed

    # Below the threshold again, which on a four-zone radio is two: §12.5
    # takes the lower of four and 40 % of that radio's zones.
    for zone_id in RADIO_ZONES[:3]:
        world.set(world.config.zone(zone_id).entity_id, "off")
    assert Moment.RF_INTERFERENCE_CLEARED in moments(world)
    assert world.state.health.radio("zigbee").confirmed is False


def test_a_disarmed_house_is_warned_and_nothing_is_triggered():
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
    assert set(world.states().values()) == {"disarmed"}
    assert world.state.incident is None


def test_an_armed_house_treats_it_as_tamper_and_opens_an_incident():
    """Armed, jamming is alarm-grade (§12.5), as it is in professional panels.

    The incident opens with no zone of its own, because no zone did this —
    the radio did.
    """
    world = zigbee_world()
    world.arm("away")
    world.advance(31)
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
    assert world.state.incident is not None
    assert world.state.incident.zone_ids == ()
    assert world.area("ground").state is AreaState.TRIGGERED


def test_the_confirmation_window_is_what_a_firmware_update_walks_into():
    world = zigbee_world()
    world.arm("away")
    world.advance(31)
    silence(world, RADIO_ZONES)
    world.advance(30)
    # Still inside the window: the coordinator rebooted, the zones are back.
    for zone_id in RADIO_ZONES:
        world.set(world.config.zone(zone_id).entity_id, "off")
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)
    assert world.state.incident is None


def test_a_radio_with_few_zones_uses_the_lower_of_four_and_forty_percent():
    settings = HealthSettings()
    radio = Radio("zigbee", "Zigbee", "entry1", COORDINATOR)
    assert settings.rf_threshold(radio, 40) == 4
    assert settings.rf_threshold(radio, 8) == 3
    # Never below two: one sensor going quiet is a flat battery.
    assert settings.rf_threshold(radio, 5) == 2


# --- the rule that defeats the feature if it is missed (§12.5) ---------------------


def test_a_zigbee_blackout_is_never_announced_through_a_zigbee_siren():
    siren = "siren.zigbee_indoor"
    other = "siren.wired_outdoor"
    config = house_with_health(
        radios=(Radio("zigbee", "Zigbee", "entry1", COORDINATOR),)
    )
    config = replace(
        config,
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "sirens",
                        ActionKind.SIREN,
                        frozenset({Moment.RF_INTERFERENCE_SUSPECTED}),
                        params={"entity_ids": [siren, other]},
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(config)
    world.on_radio("zigbee", *(config.zone(z).entity_id for z in RADIO_ZONES), siren)
    world.entities[COORDINATOR] = EntityState("ok", last_reported=NOW)
    silence(world, RADIO_ZONES)
    world.advance(61)

    intent = next(i for i in world.last.actions if i.kind == "siren")
    assert intent.params["entity_ids"] == [other]
    assert intent.params["skipped_entity_ids"] == [siren]
    # And the message says so, rather than leaving somebody to find out.
    assert intent.placeholders["skipped"] == siren


def test_an_action_whose_every_target_is_on_the_affected_radio_is_skipped():
    siren = "siren.zigbee_indoor"
    config = house_with_health(
        radios=(Radio("zigbee", "Zigbee", "entry1", COORDINATOR),)
    )
    config = replace(
        config,
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "sirens",
                        ActionKind.SIREN,
                        frozenset({Moment.RF_INTERFERENCE_SUSPECTED}),
                        params={"entity_ids": [siren]},
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(config)
    world.on_radio("zigbee", *(config.zone(z).entity_id for z in RADIO_ZONES), siren)
    world.entities[COORDINATOR] = EntityState("ok", last_reported=NOW)
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert not [i for i in world.last.actions if i.kind == "siren"]


# --- state survives a restart (INV-3) ----------------------------------------------


def test_a_suspicion_in_progress_survives_a_restart():
    """A restart in the middle of a jamming attempt must not restart the
    count from zero — on a house being configured that is several times an
    hour, and the attempt would never be confirmed."""
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    suspected = world.state.health.radio("zigbee").suspected_since
    assert suspected is not None

    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.health.radio("zigbee").suspected_since == suspected
    assert restored.health.quiet_since.keys() == set(RADIO_ZONES)


@pytest.mark.parametrize("window", [30, 60, 120])
def test_burst_counts_how_close_together_the_silences_began(window):
    quiet = {
        "a": NOW,
        "b": NOW + timedelta(seconds=20),
        "c": NOW + timedelta(seconds=45),
        "d": NOW + timedelta(seconds=100),
    }
    counted = health.burst(quiet, ("a", "b", "c", "d"), window)
    assert len(counted) == {30: 2, 60: 3, 120: 4}[window]


def test_a_zone_that_is_not_on_any_radio_is_counted_by_no_radio():
    world = zigbee_world()
    silence(world, RADIO_ZONES[:1])
    world.set(world.config.zone("door").entity_id, "unavailable")
    world.set(world.config.zone("hall").entity_id, "unavailable")
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)


def test_system_health_lists_every_cause_it_has():
    world = zigbee_world(mains_entity_id=MAINS)
    world.set(MAINS, "on")
    silence(world, RADIO_ZONES)
    world.advance(61)
    causes = health.causes(world.state.health, world.config, world.snapshot())
    assert HealthCause.MAINS_LOST in causes
    assert HealthCause.RF_INTERFERENCE in causes
    assert HealthCause.ZONE_FAULT in causes


def test_a_health_problem_warns_and_never_blocks_arming():
    """INV-4 makes a zone fault block arming. A dead notification channel is
    not a zone, and a house nobody can arm because a Telegram integration was
    removed is a worse outcome than one that arms and says so."""
    world = channels_world()
    world.health(channels_present={PUSH: False, SMS: False})
    decision = world.arm("away")
    assert decision.accepted


def test_switching_a_radio_off_mid_suspicion_says_it_is_over():
    """Every moment raised here has the one that says it is over. A
    suspicion that simply vanished from the log would be the one row
    somebody looks for the next morning."""
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert world.state.health.radio("zigbee").confirmed

    world.config = replace(
        world.config,
        health=replace(
            world.config.health,
            radios=(replace(world.config.health.radios[0], enabled=False),),
        ),
    )
    world.advance(1)
    assert Moment.RF_INTERFERENCE_CLEARED in moments(world)
    assert "zigbee" not in world.state.health.radios


def test_the_warning_about_a_dead_channel_never_goes_over_it():
    """§12.2's rule, in the one place it can actually be enforced: the
    message that says a channel is broken does not use that channel."""
    config = replace(
        make_house(),
        contacts=contactable(),
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "tell",
                        ActionKind.NOTIFY,
                        frozenset({Moment.NOTIFICATION_CHANNEL_DOWN}),
                        params={
                            "contacts": [
                                {"contact_id": "luca", "channel_id": "push"},
                                {"contact_id": "luca", "channel_id": "sms"},
                            ]
                        },
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(replace(config, health=HealthSettings()))
    world.health(channels_present={PUSH: False, SMS: True})

    intent = next(i for i in world.last.actions if i.kind == "notify")
    reached = [r["channel_id"] for r in intent.params["recipients"]]
    assert reached == ["sms"]


def test_an_ordinary_alarm_still_tries_a_channel_believed_broken():
    """Being wrong about a channel must never be the reason an alarm
    reached nobody: two failed sends can be a provider with a hiccup."""
    config = replace(
        make_house(),
        contacts=contactable(),
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "tell",
                        ActionKind.NOTIFY,
                        frozenset({Moment.TRIGGERED}),
                        params={
                            "contacts": [{"contact_id": "luca", "channel_id": "push"}]
                        },
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(replace(config, health=HealthSettings()))
    world.health(channels_present={PUSH: False, SMS: True})
    world.arm("away")
    world.advance(31)
    world.set(world.config.zone("window").entity_id, "on")

    intent = next(i for i in world.last.actions if i.kind == "notify")
    assert [r["channel_id"] for r in intent.params["recipients"]] == ["push"]


# --- what the review pass found (the regressions, one per finding) ----------------


def test_a_restart_of_an_armed_house_does_not_raise_a_false_alarm():
    """The worst thing this feature could do, and it did it.

    At a restart, battery-powered end devices are unavailable until they
    have been interviewed while the mains-powered coordinator answers at
    once. That is the §12.5 burst signature exactly, produced by nothing
    but a reboot — into an armed house.
    """
    world = zigbee_world()
    world.arm("away")
    world.advance(31)
    world.now += timedelta(seconds=90)
    for zone_id in RADIO_ZONES:
        world.entities[world.config.zone(zone_id).entity_id] = EntityState(
            "unavailable", last_reported=world.now
        )
    world.send(Startup(down_since=world.now - timedelta(seconds=80), cause="ha_start"))
    world.advance(61)

    assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)
    assert world.state.incident is None
    assert world.state.health.unknown_zones == frozenset(RADIO_ZONES)
    # And they are all faults the whole time, which is what is not silent.
    assert world.state.faults == frozenset(RADIO_ZONES)


def test_a_zone_that_comes_back_after_a_restart_is_countable_again():
    world = zigbee_world()
    for zone_id in RADIO_ZONES:
        world.entities[world.config.zone(zone_id).entity_id] = EntityState(
            "unavailable", last_reported=world.now
        )
    world.send(Startup(down_since=None, cause="ha_start"))
    assert world.state.health.unknown_zones == frozenset(RADIO_ZONES)

    for zone_id in RADIO_ZONES:
        world.set(world.config.zone(zone_id).entity_id, "off")
    assert world.state.health.unknown_zones == frozenset()

    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)


def test_a_walk_test_never_sounds_the_siren_for_a_radio_event():
    """A walk test arms every area itself (§11.3), so the armed house here
    is not the household's arming — and §11.3 says all actions are
    inhibited and means it."""
    world = zigbee_world()
    world.walk_test(True, code=CodeResult.VALID, user_id="luca")
    silence(world, RADIO_ZONES)
    world.advance(61)

    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
    assert world.state.incident is None
    assert all(rt.state is not AreaState.TRIGGERED for rt in world.state.areas.values())


def test_a_dead_coordinator_is_not_announced_through_its_own_radio():
    siren = "siren.zigbee_indoor"
    other = "siren.wired_outdoor"
    config = replace(
        house_with_health(radios=(Radio("zigbee", "Zigbee", "entry1", COORDINATOR),)),
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "sirens",
                        ActionKind.SIREN,
                        frozenset({Moment.RADIO_COORDINATOR_DOWN}),
                        params={"entity_ids": [siren, other]},
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(config)
    world.on_radio("zigbee", *(config.zone(z).entity_id for z in RADIO_ZONES), siren)
    world.entities[COORDINATOR] = EntityState("ok", last_reported=NOW)
    world.advance(1)
    world.set(COORDINATOR, "unavailable")

    intent = next(i for i in world.last.actions if i.kind == "siren")
    assert intent.params["entity_ids"] == [other]


def test_a_call_service_action_is_filtered_too():
    """§6.2 calls call_service the escape hatch for everything Foyer does
    not model natively, which is what somebody reaches for exactly when the
    native siren action does not fit."""
    config = replace(
        house_with_health(radios=(Radio("zigbee", "Zigbee", "entry1", COORDINATOR),)),
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "shout",
                        ActionKind.CALL_SERVICE,
                        frozenset({Moment.RF_INTERFERENCE_SUSPECTED}),
                        params={
                            "domain": "siren",
                            "service": "turn_on",
                            "target": {
                                "entity_id": ["siren.zigbee_indoor", "siren.wired"]
                            },
                        },
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
    )
    world = World(config)
    world.on_radio(
        "zigbee",
        *(config.zone(z).entity_id for z in RADIO_ZONES),
        "siren.zigbee_indoor",
    )
    world.entities[COORDINATOR] = EntityState("ok", last_reported=NOW)
    silence(world, RADIO_ZONES)
    world.advance(61)

    intent = next(i for i in world.last.actions if i.kind == "call_service")
    assert intent.params["target"]["entity_id"] == ["siren.wired"]
    assert intent.params["skipped_entity_ids"] == ["siren.zigbee_indoor"]


def test_a_flapping_coordinator_sounds_the_alarm_once_not_once_per_flap():
    """A coordinator on a failing switch is the fault class §12.5 insists
    must not be reported as interference at all."""
    world = zigbee_world()
    world.arm("away")
    world.advance(31)
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
    world.disarm(code=CodeResult.VALID, user_id="luca")

    for _ in range(3):
        world.set(COORDINATOR, "unavailable")
        world.advance(5)
        world.set(COORDINATOR, "ok")
        world.advance(120)
        assert Moment.RF_INTERFERENCE_SUSPECTED not in moments(world)


def test_deleting_a_radio_says_what_it_was_reporting_is_over():
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    world.advance(61)
    assert world.state.health.radio("zigbee").confirmed

    world.config = replace(world.config, health=HealthSettings())
    world.advance(1)
    assert Moment.RF_INTERFERENCE_CLEARED in moments(world)
    assert world.state.health.radios == {}


def test_clearing_the_mains_picker_does_not_claim_the_power_came_back():
    world = World(house_with_health(mains_entity_id=MAINS))
    world.set(MAINS, "on")
    assert Moment.SYSTEM_POWER_LOST in moments(world)

    world.config = replace(
        world.config, health=replace(world.config.health, mains_entity_id=None)
    )
    world.advance(1)
    assert Moment.SYSTEM_POWER_RESTORED not in moments(world)
    assert world.state.health.mains_lost_since is None


def test_the_ups_dying_with_the_power_does_not_withdraw_the_power_cut():
    """The realistic case: the NUT server and the router die with the mains,
    which is the scenario §12.3 closes on."""
    world = World(house_with_health(mains_entity_id=MAINS))
    world.set(MAINS, "on")
    world.set(MAINS, "unavailable")

    assert Moment.SYSTEM_POWER_RESTORED not in moments(world)
    causes = health.causes(world.state.health, world.config, world.snapshot())
    assert HealthCause.MAINS_LOST in causes
    assert HealthCause.MAINS_UNKNOWN in causes


def test_a_confirmation_deadline_already_past_is_not_a_wake_up():
    """Every other branch of next_wakeup filters a past due time, and this
    one has the worst consequence if it does not: while Home Assistant is
    still starting, reconcile_health is skipped, so a Tick at a past
    deadline decides nothing, reschedules the same past time and fires
    again — spinning through the whole of startup, with a store write and a
    log write each time round."""
    from custom_components.foyer.core.engine import next_wakeup

    world = zigbee_world()
    silence(world, RADIO_ZONES)
    assert world.state.health.radio("zigbee").suspected_since is not None

    world.now += timedelta(seconds=600)
    assert next_wakeup(world.snapshot(), world.config, world.now) is None


def test_a_suspicion_that_was_already_open_still_confirms_after_a_restart():
    """The counterpart of the restart rule above: zones Foyer had already
    timed keep their timestamps, so an attempt that began before the restart
    is not forgotten — only zones it never heard go quiet are uncounted."""
    world = zigbee_world()
    silence(world, RADIO_ZONES)
    assert world.state.health.radio("zigbee").suspected_since is not None

    world.now += timedelta(seconds=300)
    world.send(Startup(down_since=world.now - timedelta(seconds=290), cause="ha_start"))
    assert Moment.RF_INTERFERENCE_SUSPECTED in moments(world)
