"""What the second full review found in the pure engine (2026-09-23).

Each test is the sequence a reviewer used to show the defect, asserted the
right way round. Pure: no Home Assistant.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from custom_components.foyer.core.models import (
    ActionKind,
    AreaState,
    Channel,
    CodeResult,
    Contact,
    ContactChannel,
    ContactChannelKind,
    EventTrigger,
    Group,
    KeyAction,
    KeyCommand,
    Moment,
    ProfileAction,
    Reason,
    ResponseProfile,
    RuleActionKind,
    RuleTriggerKind,
    RunningAction,
    ZoneType,
)
from custom_components.foyer.core.response import PlanContext, reachable, run_sequence
from custom_components.foyer.core.validation import validate
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import (
    LUCA,
    NOW,
    PARTNER,
    World,
    make_house,
    rule,
    user,
    zone,
)

SMOKE = "binary_sensor.smoke"
PANIC = "event.panic_button"
KEY = "switch.key"


# --- the smoke sounder across a restart -------------------------------------------


def test_a_technical_sounder_is_still_technical_after_a_restart():
    world = World()
    world.state = replace(
        world.state,
        running=(
            RunningAction(
                "siren", "siren", ("siren.smoke",), area_id="ground", technical=True
            ),
        ),
    )
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.running[0].technical is True


# --- a rule never closes a live alarm ------------------------------------------------


def test_a_disarm_rule_never_acknowledges_an_alarm_after_the_siren_cutoff():
    config = replace(
        make_house(),
        rules=(
            rule(
                "let_me_in",
                kind=RuleTriggerKind.PRESENCE,
                action=RuleActionKind.DISARM,
                area_ids=("upstairs",),
                scenario_id=None,
                grace=0,
            ),
        ),
        settings=replace(make_house().settings, allow_auto_disarm=True),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    world.person(LUCA, "not_home")
    world.person(PARTNER, "not_home")
    world.set("binary_sensor.bath_window", "on")  # upstairs, auto_bypass: open
    world.set("binary_sensor.landing_pir", "on")  # upstairs follower → triggered
    assert world.area("upstairs").state is AreaState.TRIGGERED
    world.advance(181)  # the siren cutoff: back to armed, memory set
    assert world.area("upstairs").state is AreaState.ARMED

    decision = world.person(LUCA, "home")

    assert world.area("upstairs").state is AreaState.ARMED
    assert Moment.INCIDENT_ACKNOWLEDGED not in decision.moments
    assert world.state.incident is not None and not world.state.incident.acknowledged


# --- a walk test is not a way to arm -------------------------------------------------


def test_arming_during_a_walk_test_is_refused():
    world = World()
    world.walk_test()
    assert world.state.walk_test is not None

    for decision in (world.arm("away"), world.arm_area("garage")):
        assert not decision.accepted
        assert decision.reason is Reason.WALK_TEST_ACTIVE


# --- a suppressing group with a member excluded --------------------------------------


def test_a_suppressing_group_left_unable_to_count_lets_its_member_alarm():
    config = replace(
        make_house(),
        zones=(
            *make_house().zones,
            zone("pir1", "binary_sensor.pir1", "ground"),
            zone("pir2", "binary_sensor.pir2", "ground"),
        ),
        groups=(Group("open", "Open plan", "ground", ("pir1", "pir2"), 2, 60, True),),
    )
    world = World(config)
    world.bypass("pir2")
    world.arm("away")
    world.advance(30)

    world.set("binary_sensor.pir1", "on")
    assert world.area("ground").state is AreaState.TRIGGERED


# --- rules start from a baseline -----------------------------------------------------


def test_a_time_rule_saved_after_its_hour_waits_for_the_next_day():
    config = replace(
        make_house(),
        rules=(
            rule(
                "morning",
                kind=RuleTriggerKind.TIME,
                at="07:00",
                entity_ids=(),
                action=RuleActionKind.ARM,
                scenario_id="away",
                grace=0,
            ),
        ),
    )
    world = World(config)  # 19:32: 07:00 is long past today
    world.advance(60)
    assert world.states()["ground"] == "disarmed"
    world.now = datetime(2026, 9, 15, 7, 0, tzinfo=UTC)
    world.advance(1)
    assert world.states()["ground"] == "arming"


def test_a_presence_rule_switched_back_on_has_not_seen_anybody_arrive():
    presence = rule(
        "let_me_in",
        kind=RuleTriggerKind.PRESENCE,
        action=RuleActionKind.DISARM,
        area_ids=("upstairs",),
        scenario_id=None,
        grace=0,
    )
    config = replace(
        make_house(),
        rules=(replace(presence, enabled=False),),
        settings=replace(make_house().settings, allow_auto_disarm=True),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    world.config = replace(world.config, rules=(presence,))
    world.advance(1)
    assert world.states()["upstairs"] == "armed"


def test_a_key_zone_switched_back_on_is_a_baseline_not_a_turn():
    key = zone(
        "key",
        KEY,
        "garage",
        type=ZoneType.KEY,
        channel=Channel.KEY,
        key=KeyAction(on_activate=KeyCommand.TOGGLE, scenario_id="night"),
    )
    config = replace(make_house(), zones=(*make_house().zones, key))
    world = World(config)
    world.arm("night")
    world.advance(5)
    world.config = replace(
        world.config,
        zones=tuple(
            replace(z, enabled=False) if z.id == "key" else z
            for z in world.config.zones
        ),
    )
    world.set(KEY, "on")
    world.config = replace(
        world.config,
        zones=tuple(
            replace(z, enabled=True) if z.id == "key" else z for z in world.config.zones
        ),
    )
    world.advance(1)
    assert world.states()["ground"] == "armed"


# --- the first press of a new button -------------------------------------------------


def test_the_first_event_of_a_button_that_never_fired_counts():
    panic = zone(
        "panic",
        PANIC,
        "ground",
        type=ZoneType.PANIC,
        always_on=True,
        bypassable=False,
    )
    panic = replace(panic, trigger=EventTrigger())
    world = World(replace(make_house(), zones=(*make_house().zones, panic)))
    world.set(PANIC, "unknown")
    world.advance(1)

    world.set(PANIC, "2026-09-14T19:33:00+00:00")
    assert world.area("ground").state is AreaState.TRIGGERED


def test_a_restore_out_of_unavailable_is_still_not_a_press():
    panic = replace(
        zone("panic", PANIC, "ground", always_on=True, bypassable=False),
        trigger=EventTrigger(),
    )
    last = "2026-09-10T08:00:00+00:00"
    world = World(
        replace(make_house(), zones=(*make_house().zones, panic)), {PANIC: last}
    )
    world.set(PANIC, "unavailable")
    world.set(PANIC, last)
    assert world.area("ground").state is AreaState.DISARMED


# --- the response ---------------------------------------------------------------------


def _contacts():
    return (
        Contact(
            "luca",
            "Luca",
            channels=(
                ContactChannel("push", ContactChannelKind.PUSH, "notify.app"),
                ContactChannel("sms", ContactChannelKind.SMS, "notify.sms"),
            ),
        ),
    )


def test_the_warning_about_a_dead_channel_falls_back_to_the_next_one():
    config = replace(make_house(), contacts=_contacts())
    world = World(config)
    action = ProfileAction(
        "tell",
        ActionKind.NOTIFY,
        frozenset({Moment.NOTIFICATION_CHANNEL_DOWN}),
        params={
            "message": "x",
            "contacts": [{"contact_id": "luca", "channel_id": None}],
        },
    )
    ctx = PlanContext(
        config=config,
        snapshot=world.snapshot(),
        now=NOW,
        areas=world.state.areas,
        broken_channels=frozenset({"luca:push"}),
    )
    recipients, _ = reachable(ctx, action, Moment.NOTIFICATION_CHANNEL_DOWN)
    assert [r["channel_id"] for r in recipients] == ["sms"]


def _answering(*actions):
    config = make_house()
    return replace(
        config,
        profiles=(ResponseProfile("default", "Default", actions=actions),),
        settings=replace(config.settings, default_profile_id="default"),
    )


def test_an_action_whose_only_target_is_on_the_jammed_radio_does_not_run():
    siren = ProfileAction(
        "siren",
        ActionKind.SIREN,
        frozenset({Moment.TRIGGERED}),
        params={"entity_ids": "siren.zb"},
    )
    config = _answering(siren)
    world = World(config)
    world.on_radio("zigbee", "siren.zb")
    ctx = PlanContext(
        config=config,
        snapshot=world.snapshot(),
        now=NOW,
        areas=world.state.areas,
        impaired=frozenset({"zigbee"}),
    )
    plan = run_sequence(ctx, config.profiles[0], Moment.TRIGGERED, {})
    assert not plan.intents and not plan.running


def test_a_picture_folder_under_www_is_refused_on_the_action_too():
    notify = ProfileAction(
        "n",
        ActionKind.NOTIFY,
        frozenset({Moment.TRIGGERED}),
        params={"service": "notify.x", "message": "m", "directory": "www/leak"},
    )
    problems = validate(_answering(notify))
    assert any(p.code == "camera_dir_invalid" for p in problems)


def test_user_is_the_person_who_asked():
    notify = ProfileAction(
        "n",
        ActionKind.NOTIFY,
        frozenset({Moment.DISARMED}),
        params={"service": "notify.x", "message": "Disarmed by {{ user }}"},
    )
    config = replace(
        _answering(notify),
        users=(user("luca", "Luca"),),
    )
    world = World(config)
    world.arm("away")
    world.advance(30)
    decision = world.disarm(user_id="luca", code=CodeResult.VALID)
    sent = next(i for i in decision.actions if i.action_id == "n")
    assert sent.params["message"] == "Disarmed by Luca"


def test_a_smoke_sounder_ignores_the_night_scenarios_shorter_siren():
    siren = ProfileAction(
        "siren",
        ActionKind.SIREN,
        frozenset({Moment.TECHNICAL_RAISED}),
        params={"entity_ids": ["siren.indoor"]},
    )
    config = _answering(siren)
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
            ),
        ),
        scenarios=tuple(
            replace(s, siren_duration_override=60) if s.id == "night" else s
            for s in config.scenarios
        ),
        settings=replace(config.settings, siren_duration=180),
    )
    world = World(config)
    world.arm("night")
    world.advance(5)
    decision = world.set(SMOKE, "on")
    sent = next(i for i in decision.actions if i.action_id == "siren")
    assert sent.params["duration"] == 180


def test_a_detector_switched_back_on_while_detecting_is_an_alarm():
    """Only a key zone re-enabled is a baseline; a tamper switch or a smoke
    detector re-enabled while it detects must alarm (second review)."""
    config = make_house()
    world = World(config)
    world.config = replace(
        world.config,
        zones=tuple(
            replace(z, enabled=False) if z.id == "tamper" else z
            for z in world.config.zones
        ),
    )
    world.set("binary_sensor.siren_tamper", "on")
    world.config = config
    world.advance(1)
    assert world.area("ground").state is AreaState.TRIGGERED
