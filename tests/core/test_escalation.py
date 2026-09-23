"""Escalation, acknowledgement and quiet hours (SPEC §7). Pure: no Home Assistant.

The acceptance sentence of the phase is a test: an alarm nobody acknowledges
climbs from one person's push to their SMS to a second person's phone, in that
order and at those times, across a restart; one press of anything stops the
whole thing.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core import escalation as escalation_engine
from custom_components.foyer.core.models import (
    AcknowledgeIncident,
    AcknowledgeTechnical,
    ActionKind,
    AlarmKind,
    Channel,
    Contact,
    ContactChannel,
    ContactChannelKind,
    EscalationKind,
    LogSeverity,
    Moment,
    ProfileAction,
    ResponseProfile,
    Settings,
    Startup,
    ZoneType,
)
from custom_components.foyer.core.response import (
    SKIP_NO_CHANNEL,
    SKIP_QUIET_HOURS,
    PlanContext,
    reachable,
    sequence,
)

from .helpers import NOW, TAMPER, WINDOW, World, make_house, zone

SMOKE = "binary_sensor.smoke"


def contacts() -> tuple[Contact, ...]:
    return (
        Contact(
            "luca",
            "Luca",
            channels=(
                ContactChannel("luca-push", ContactChannelKind.PUSH, "notify.luca_app"),
                ContactChannel("luca-sms", ContactChannelKind.SMS, "notify.sms"),
            ),
            linked_user_id="luca",
        ),
        Contact(
            "partner",
            "Partner",
            channels=(
                ContactChannel(
                    "partner-push", ContactChannelKind.PUSH, "notify.partner_app"
                ),
            ),
        ),
    )


def step(
    action_id: str,
    offset: int,
    contact_id: str,
    channel_id: str | None = None,
    moment: Moment = Moment.TRIGGERED,
) -> ProfileAction:
    return ProfileAction(
        id=action_id,
        kind=ActionKind.NOTIFY,
        moments=frozenset({moment}),
        params={
            "message": "Alarm",
            "contacts": [{"contact_id": contact_id, "channel_id": channel_id}],
        },
        escalation_offset=offset,
    )


def escalating_house(
    steps: tuple[ProfileAction, ...] | None = None,
    **profile_kwargs,
):
    """The house of the shared helpers, with an address book and a policy."""
    config = make_house()
    policy = ResponseProfile(
        "loud",
        "Loud",
        actions=steps
        or (
            step("s0", 0, "luca", "luca-push"),
            step("s1", 60, "luca", "luca-sms"),
            step("s2", 120, "partner", "partner-push"),
        ),
        **profile_kwargs,
    )
    return replace(
        config,
        contacts=contacts(),
        profiles=(*config.profiles, policy),
        areas=tuple(
            replace(a, response_profile_id="loud" if a.id == "ground" else None)
            for a in config.areas
        ),
    )


def fire(world: World) -> None:
    """Arm, then break in through the instant window zone."""
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "on")


def notified(decision) -> list[str]:
    """Which contacts this decision's notifications reach, in order."""
    out: list[str] = []
    for intent in decision.actions:
        for recipient in intent.params.get("recipients") or ():
            out.append(f"{recipient['contact_id']}/{recipient['channel_id']}")
    return out


def test_an_unacknowledged_alarm_climbs_from_push_to_sms_to_a_second_person():
    world = World(escalating_house())
    fire(world)

    assert notified(world.last) == ["luca/luca-push"]
    # And it says what is still coming, read off the Decision (§11.2).
    assert [(s.index, s.offset) for s in world.last.escalation] == [(1, 60), (2, 120)]

    assert notified(world.advance(30)) == []
    assert notified(world.advance(30)) == ["luca/luca-sms"]
    assert notified(world.advance(60)) == ["partner/partner-push"]


def test_the_steps_carry_their_number_and_are_not_run_by_the_ordinary_sequence():
    config = escalating_house()
    policy = config.profile("loud")
    assert sequence(policy, Moment.TRIGGERED) == ()
    assert [a.id for a in escalation_engine.steps(policy, Moment.TRIGGERED)] == [
        "s0",
        "s1",
        "s2",
    ]

    world = World(config)
    fire(world)
    intent = next(i for i in world.last.actions if i.kind == ActionKind.NOTIFY.value)
    assert intent.params["escalation"] == "incident"
    assert intent.params["escalation_step"] == 0


def test_one_acknowledgement_stops_the_whole_thing_and_says_who():
    world = World(escalating_house())
    fire(world)
    world.advance(10)

    decision = world.send(AcknowledgeIncident())
    assert decision.accepted
    assert world.state.escalations == ()
    assert decision.escalation == ()
    acknowledgement = world.state.incident.acknowledgements[-1]
    assert acknowledgement.via == "acknowledge"

    assert notified(world.advance(300)) == []


def test_disarming_an_area_the_incident_touched_stops_the_escalation():
    world = World(escalating_house())
    fire(world)

    world.disarm("ground")
    assert world.state.escalations == ()
    assert notified(world.advance(300)) == []


def test_disarming_an_untouched_area_does_not_stop_it():
    world = World(escalating_house())
    fire(world)

    world.disarm("upstairs")
    assert world.state.escalations != ()
    assert notified(world.advance(60)) == ["luca/luca-sms"]


def test_a_step_that_fell_due_while_home_assistant_was_down_is_skipped_and_said():
    world = World(escalating_house())
    fire(world)
    # Four hours later the house comes back. Steps 1 and 2 fell due in the
    # gap: a notification that late is worse than none (part 1 decision 5).
    world.now += timedelta(hours=4)
    decision = world.send(Startup(down_since=NOW))

    assert notified(decision) == []
    skipped = [o for o in decision.occurrences if o.moment is Moment.ESCALATION_SKIPPED]
    assert skipped and skipped[0].detail["steps"] == "1,2"
    assert skipped[0].detail["reasons"] == "restart,restart"
    # The escalation is finished rather than left open for ever — but it was
    # never exhausted: nothing went out past step 0, and a profile answering
    # "the whole list failed" must not fire for a list nobody tried.
    assert decision.state.escalations == ()
    assert not any(
        o.moment is Moment.ESCALATION_EXHAUSTED for o in decision.occurrences
    )


def test_a_reload_does_not_lose_the_step_it_interrupted():
    world = World(escalating_house())
    fire(world)
    world.advance(61)  # step 1 is one second overdue
    world.state = replace(world.state, escalations=world.state.escalations)
    world.now += timedelta(seconds=1)
    # Saving a setting reloads the integration; the gap is a second, not an
    # outage, and a step lost to it would be a push nobody can explain.
    decision = world.send(Startup(down_since=world.now, cause="reload"))
    assert notified(decision) == []  # step 1 already went out at +60


def test_an_escalation_that_runs_out_raises_escalation_exhausted_once():
    world = World(escalating_house())
    fire(world)
    world.advance(60)
    decision = world.advance(60)  # the last step

    moments = [o.moment for o in decision.occurrences]
    assert Moment.ESCALATION_EXHAUSTED in moments
    assert world.state.escalations == ()
    assert not any(
        o.moment is Moment.ESCALATION_EXHAUSTED for o in world.advance(60).occurrences
    )


def test_the_incident_adopts_the_loudest_contributing_policy_and_keeps_its_clock():
    config = escalating_house()
    louder = ResponseProfile(
        "louder",
        "Louder",
        severity=5,
        actions=(
            step("n0", 0, "partner", "partner-push"),
            step("n1", 300, "luca", "luca-sms"),
        ),
    )
    config = replace(
        config,
        profiles=(*config.profiles, louder),
        zones=tuple(
            replace(z, response_profile_id="louder" if z.id == "tamper" else None)
            for z in config.zones
        ),
    )
    world = World(config)
    fire(world)
    assert world.state.escalation(EscalationKind.INCIDENT).profile_id == "loud"
    started = world.state.escalation(EscalationKind.INCIDENT).started_at

    world.advance(10)
    decision = world.set(TAMPER, "on")

    current = decision.state.escalation(EscalationKind.INCIDENT)
    assert current.profile_id == "louder"
    # The escalation began when the house was broken into, not when the
    # louder zone went: its step 0 is already due and goes out at once.
    assert current.started_at == started
    assert "partner/partner-push" in notified(decision)


def technical_house(second_step: int = 60):
    """The house, plus a smoke detector and an escalation of its own."""
    config = escalating_house()
    technical = ResponseProfile(
        "technical",
        "Technical",
        actions=(
            step("t0", 0, "luca", "luca-push", moment=Moment.TECHNICAL_RAISED),
            step(
                "t1",
                second_step,
                "partner",
                "partner-push",
                moment=Moment.TECHNICAL_RAISED,
            ),
        ),
    )
    return replace(
        config,
        profiles=(*config.profiles, technical),
        zones=(
            *config.zones,
            zone(
                "smoke",
                SMOKE,
                "ground",
                type=ZoneType.TECHNICAL,
                channel=Channel.TECHNICAL,
                alarm_kind=AlarmKind.INTRUSION,
                always_on=True,
                bypassable=False,
            ),
        ),
        settings=replace(config.settings, technical_profile_id="technical"),
    )


def test_the_technical_channel_escalates_on_its_own_and_a_disarm_does_not_stop_it():
    world = World(technical_house())
    world.set(SMOKE, "on")
    assert notified(world.last) == ["luca/luca-push"]

    # Disarming is an intrusion command and has no authority here (§5.5).
    world.disarm()
    assert world.state.escalation(EscalationKind.TECHNICAL) is not None
    assert notified(world.advance(60)) == ["partner/partner-push"]

    world.set(SMOKE, "off")
    world.send(AcknowledgeTechnical())
    assert world.state.escalation(EscalationKind.TECHNICAL) is None


def test_an_intrusion_acknowledgement_leaves_the_technical_escalation_running():
    config = escalating_house()
    technical = ResponseProfile(
        "technical",
        "Technical",
        actions=(
            step("t0", 0, "luca", "luca-push", moment=Moment.TECHNICAL_RAISED),
            step("t1", 600, "partner", "partner-push", moment=Moment.TECHNICAL_RAISED),
        ),
    )
    config = replace(
        config,
        profiles=(*config.profiles, technical),
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
        settings=replace(config.settings, technical_profile_id="technical"),
    )
    world = World(config)
    fire(world)
    world.set(SMOKE, "on")

    world.send(AcknowledgeIncident())
    assert world.state.escalation(EscalationKind.INCIDENT) is None
    assert world.state.escalation(EscalationKind.TECHNICAL) is not None


# --- quiet hours (§7.1) ------------------------------------------------------------


def quiet_world(min_severity: LogSeverity = LogSeverity.ALARM) -> World:
    config = escalating_house()
    config = replace(
        config,
        contacts=(
            replace(
                config.contacts[0],
                quiet_start="22:00",
                quiet_end="07:00",
                quiet_min_severity=min_severity,
            ),
            config.contacts[1],
        ),
    )
    world = World(config)
    world.now = NOW.replace(hour=23)
    return world


def test_quiet_hours_let_a_break_in_through():
    world = quiet_world()
    fire(world)
    assert notified(world.last) == ["luca/luca-push"]


def test_quiet_hours_hold_back_what_is_not_loud_enough():
    world = quiet_world(LogSeverity.ALARM)
    config = world.config
    armed = ProfileAction(
        "armed",
        ActionKind.NOTIFY,
        frozenset({Moment.ARMED}),
        params={
            "message": "Armed",
            "contacts": [{"contact_id": "luca", "channel_id": "luca-push"}],
        },
    )
    policy = config.profile("loud")
    world.config = replace(
        config,
        profiles=tuple(
            replace(p, actions=(*p.actions, armed)) if p.id == policy.id else p
            for p in config.profiles
        ),
    )
    decision = world.arm("away")
    assert notified(decision) == []


def test_a_contact_who_wants_warnings_gets_them_inside_the_window():
    world = quiet_world(LogSeverity.WARNING)
    ctx = PlanContext(
        config=world.config,
        snapshot=world.snapshot(),
        now=world.now,
        areas=world.state.areas,
    )
    action = ProfileAction(
        "entry",
        ActionKind.NOTIFY,
        frozenset({Moment.ENTRY_STARTED}),
        params={
            "message": "Entry",
            "contacts": [{"contact_id": "luca", "channel_id": "luca-push"}],
        },
    )
    recipients, quiet = reachable(ctx, action, Moment.ENTRY_STARTED)
    assert [r["contact_id"] for r in recipients] == ["luca"]
    assert quiet == ()

    recipients, quiet = reachable(ctx, action, Moment.ARMED)
    assert recipients == ()
    assert quiet == ("luca",)


def test_an_action_nobody_is_left_to_receive_is_skipped_for_that_reason():
    from custom_components.foyer.core.response import skip_reason

    world = quiet_world()
    ctx = PlanContext(
        config=world.config,
        snapshot=world.snapshot(),
        now=world.now,
        areas=world.state.areas,
    )
    action = ProfileAction(
        "armed",
        ActionKind.NOTIFY,
        frozenset({Moment.ARMED}),
        params={
            "message": "Armed",
            "contacts": [{"contact_id": "luca", "channel_id": "luca-push"}],
        },
    )
    why = skip_reason(
        action,
        ctx,
        moment=Moment.ARMED,
        suppressed=frozenset(),
        already_started=frozenset(),
    )
    assert why == SKIP_QUIET_HOURS


# --- the actionable button (§7.2) --------------------------------------------------


def test_only_an_actionable_channel_on_an_alarm_carries_the_acknowledge_button():
    config = escalating_house()
    config = replace(
        config,
        contacts=(
            replace(
                config.contacts[0],
                channels=(
                    replace(config.contacts[0].channels[0], actionable=True),
                    config.contacts[0].channels[1],
                ),
            ),
            config.contacts[1],
        ),
    )
    world = World(config)
    fire(world)
    push = next(i for i in world.last.actions if i.params.get("recipients"))
    assert push.params["recipients"][0]["ack"] is True

    sms = next(i for i in world.advance(60).actions if i.params.get("recipients"))
    assert sms.params["recipients"][0]["ack"] is False


@pytest.mark.parametrize("settings", [Settings()])
def test_an_escalation_survives_a_round_trip_through_the_store(settings):
    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    world = World(escalating_house())
    fire(world)
    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.escalations == world.state.escalations


# --- the walk test (§11.3) ---------------------------------------------------------


def test_a_walk_test_starts_no_escalation_for_an_ordinary_detection():
    """A walk test holds back the response, and an escalation is a response.

    It needs no case of its own in the escalation: part 2 decision 3 already
    keeps an ordinary detection out of the state machine, so there is no
    incident to escalate.
    """
    world = World(escalating_house())
    world.walk_test(True)
    world.set(WINDOW, "on")

    assert world.state.escalations == ()
    assert notified(world.advance(120)) == []


def test_a_walk_test_never_holds_back_the_escalation_of_a_tamper_zone():
    """`always_on` zones stay fully live (§11.3), and an alarm of theirs is a
    real incident: the people on the list are reached."""
    config = escalating_house()
    world = World(config)
    world.walk_test(True)
    world.set(TAMPER, "on")

    assert notified(world.last) == ["luca/luca-push"]
    assert notified(world.advance(60)) == ["luca/luca-sms"]


# --- what the agents' review closed --------------------------------------------------


def test_a_step_that_reaches_nobody_says_so_instead_of_vanishing():
    """A notification that never went out is the silence this whole feature
    exists to end, so it is recorded with the reason skip_reason gave."""
    config = escalating_house()
    config = replace(
        config,
        contacts=(
            replace(config.contacts[0], enabled=False),
            replace(config.contacts[1], enabled=False),
        ),
    )
    world = World(config)
    fire(world)

    assert notified(world.last) == []
    skipped = [
        o for o in world.last.occurrences if o.moment is Moment.ESCALATION_SKIPPED
    ]
    assert skipped and skipped[0].detail["steps"] == "0"
    # Nobody was inside quiet hours: they were all switched off, and the row
    # says which it was (found in the second review).
    assert skipped[0].detail["reasons"] == SKIP_NO_CHANNEL


def test_a_technical_escalation_does_not_outlive_the_zone_that_raised_it():
    """Deleting the zone empties the channel, and an escalation nobody can
    acknowledge — the technical acknowledgement refuses when nothing is
    pending — would call people about an alarm that no longer exists."""
    config = technical_house()
    world = World(config)
    world.set(SMOKE, "on")
    assert world.state.escalation(EscalationKind.TECHNICAL) is not None

    world.config = replace(
        world.config, zones=tuple(z for z in world.config.zones if z.id != "smoke")
    )
    assert notified(world.advance(60)) == []
    assert world.state.escalation(EscalationKind.TECHNICAL) is None


def test_a_restart_that_cannot_say_how_long_it_was_is_still_a_restart():
    """`down_since` is optional and a state file may not carry it. Unknown is
    read as an outage, not as no outage: the alternative is every overdue
    step going out at once, which is what decision 5 forbids."""
    world = World(escalating_house())
    fire(world)
    world.now += timedelta(hours=4)
    decision = world.send(Startup(down_since=None))

    assert notified(decision) == []
    assert any(o.moment is Moment.ESCALATION_SKIPPED for o in decision.occurrences)


def test_an_escalation_whose_profile_was_deleted_ends_with_a_row_after_a_restart():
    """The same event must read the same in the log whether the profile was
    deleted before or after the restart."""
    from custom_components.foyer.store.schema import state_from_dict, state_to_dict

    world = World(escalating_house())
    fire(world)
    stored = state_to_dict(world.state)

    world.config = replace(
        world.config,
        profiles=tuple(p for p in world.config.profiles if p.id != "loud"),
        areas=tuple(replace(a, response_profile_id=None) for a in world.config.areas),
    )
    world.state = state_from_dict(stored, world.config)
    assert world.state.escalations != ()

    decision = world.advance(60)
    exhausted = [
        o for o in decision.occurrences if o.moment is Moment.ESCALATION_EXHAUSTED
    ]
    assert exhausted and exhausted[0].detail["cause"] == "profile_gone"
    assert decision.state.escalations == ()
