"""What the third full review found in core/ and store/, pinned down.

Every test here failed before its fix. They are grouped by the rule each
one restores, and each docstring says what the house did wrong.
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.journal import rejection_row
from custom_components.foyer.core.models import (
    ActionKind,
    Actor,
    AreaState,
    ChannelFault,
    Contact,
    ContactChannel,
    ContactChannelKind,
    DisarmRequest,
    Group,
    HealthSettings,
    Moment,
    ProfileAction,
    Reason,
)
from custom_components.foyer.core.privacy import NAMED_CATEGORIES
from custom_components.foyer.core.response import recipients_for
from custom_components.foyer.store.editing import touches_people
from custom_components.foyer.store.schema import state_from_dict, state_to_dict
from custom_components.foyer.store.seed import SEED_MOMENTS

from .helpers import BATH, HALL, NOW, TAMPER, WINDOW, World, make_house, user, zone
from .test_groups import PIR1, armed, house, open_plan, pulse, verification
from .test_health import PUSH, channels_world

# --- §4.8: a group counts only what its area watches ---


def test_a_suppressing_group_across_an_armed_and_a_disarmed_area_still_alarms():
    """The landing PIR is in a disarmed area and can never count, so the one
    PIR watching the armed ground floor acts on its own — as it does when the
    other member is bypassed or in fault. Held for ever, the intruder it saw
    met silence."""
    group = open_plan(members=("pir1", "bath"), n=2, suppress_members=True)
    world = armed(house(group), "night")  # ground only
    pulse(world, PIR1)
    assert world.area("ground").state is AreaState.TRIGGERED


def test_with_both_areas_armed_the_group_is_still_a_group():
    group = open_plan(members=("pir1", "bath"), n=2, suppress_members=True)
    world = armed(house(group))  # away: both floors
    decision = pulse(world, PIR1)
    assert verification(decision)[0].moment is Moment.VERIFICATION_PENDING
    assert world.area("ground").state is AreaState.ARMED


# --- §5.2: alarm memory stays until a disarm or a new arming ---


def test_an_arming_the_cutoff_resumed_and_that_then_failed_keeps_the_memory():
    """Arm, open a window during the exit delay, trip the tamper: the cutoff
    resumes the arming, which fails on the open window. Nobody disarmed, so
    the card must still say an alarm happened."""
    world = World()
    world.arm("away")  # exit delay running
    world.set(WINDOW, "on")
    world.set(TAMPER, "on")
    rt = world.area("ground")
    assert rt.state is AreaState.TRIGGERED and rt.resume is AreaState.ARMING
    world.advance(180)  # cutoff -> arming -> exit over -> window open
    rt = world.area("ground")
    assert rt.state is AreaState.DISARMED
    assert rt.memory
    assert "tamper" in rt.causes
    assert world.state.incident is not None


# --- §11.3: a walk test never arms over alarm memory ---


def test_the_walk_test_leaves_an_area_holding_memory_alone():
    """Armed by the test, its memory read as "in alarm" when the test ended,
    and the house came out of a walk test armed with somebody inside."""
    world = World()
    world.set(TAMPER, "on")
    world.advance(180)  # cutoff: disarmed, with memory
    world.set(TAMPER, "off")  # nothing open: the area could arm
    assert world.area("ground").memory
    world.walk_test()
    assert "ground" not in world.state.walk_test.armed_areas
    assert world.area("ground").state is AreaState.DISARMED
    # Its zones are still walked: a detection is recorded whatever the area
    # is doing.
    world.set(HALL, "on")
    assert "hall" in world.state.walk_test.detections
    world.walk_test(False)
    assert world.area("ground").state is AreaState.DISARMED
    assert world.area("ground").memory


# --- §8.2: the scenario has a say only over the areas it armed ---


def test_disarming_an_area_armed_on_its_own_is_not_judged_by_the_active_scenario():
    """Night runs on the ground floor; Luca, who may only use Away, armed the
    garage by itself. Disarming the garage is the garage's business."""
    world = World(replace(make_house(), users=(user(allowed_scenario_ids=("away",)),)))
    world.arm("night")  # somebody else, no code needed to arm
    assert world.state.active_scenario_id == "night"
    assert world.arm_area(
        "garage", actor=Actor(user_id="luca", channel="ha_ui", code=_valid())
    ).accepted
    decision = world.disarm(
        "garage", actor=Actor(user_id="luca", channel="ha_ui", code=_valid())
    )
    assert decision.accepted, decision.reason
    assert world.area("garage").state is AreaState.DISARMED
    assert world.area("ground").state is not AreaState.DISARMED


def test_disarming_the_scenarios_own_areas_is_still_the_scenarios_call():
    world = World(replace(make_house(), users=(user(allowed_scenario_ids=("away",)),)))
    world.arm("night")
    decision = world.disarm(
        "ground", actor=Actor(user_id="luca", channel="ha_ui", code=_valid())
    )
    assert decision.reason is Reason.SCENARIO_NOT_ALLOWED


def _valid():
    from custom_components.foyer.core.models import CodeResult

    return CodeResult.VALID


# --- §5.6: what was switched off is no longer "already running" ---


def _siren_house():
    config = make_house()
    profile = config.profiles[0]
    siren = ProfileAction(
        id="bell",
        kind=ActionKind.SIREN,
        moments=frozenset({Moment.TRIGGERED, Moment.INCIDENT_JOINED}),
        params={"entity_ids": ["siren.outdoor"], "duration": 60},
    )
    return replace(config, profiles=(replace(profile, actions=(siren,)),))


def _bells(decision):
    return [a for a in decision.actions if a.kind == ActionKind.SIREN.value]


def test_a_zone_tripping_after_the_siren_ran_out_sounds_it_again():
    """The incident remembered the siren as started for its whole life, so a
    second zone an hour later found the bell 'already running' and silent."""
    world = World(_siren_house())
    world.arm("away")
    world.advance(30)
    assert _bells(world.set(WINDOW, "on"))
    world.advance(60)  # the siren's own duration: switched off
    assert "bell" not in world.state.incident.actions_started
    decision = world.set(HALL, "on")
    assert Moment.INCIDENT_JOINED in decision.moments
    assert _bells(decision), "the second zone did not sound the siren"


def test_while_the_siren_sounds_a_second_zone_does_not_restart_it():
    world = World(_siren_house())
    world.arm("away")
    world.advance(30)
    world.set(WINDOW, "on")
    world.advance(10)
    assert not _bells(world.set(HALL, "on"))


# --- §7.1: a channel the person switched off is not the end of the message ---


def test_a_message_naming_a_disabled_channel_goes_over_the_persons_next_one():
    contact = Contact(
        "anna",
        "Anna",
        channels=(
            ContactChannel("sms", ContactChannelKind.SMS, "notify.gsm", enabled=False),
            ContactChannel("push", ContactChannelKind.PUSH, "notify.anna"),
        ),
    )
    config = replace(make_house(), contacts=(contact,))
    reached, quiet = recipients_for(
        config,
        [{"contact_id": "anna", "channel_id": "sms"}],
        NOW,
        NOW.tzinfo,
        Moment.TRIGGERED,
    )
    assert [r["channel_id"] for r in reached] == ["push"]
    assert quiet == ()


# --- decision 88: a refused claimed request says the name was claimed ---


def test_a_refused_request_carries_the_claimed_note_like_an_accepted_one():
    world = World(replace(make_house(), users=(user(),)))
    event = DisarmRequest(None, actor=Actor(user_id="luca", claimed=True))
    decision = world.send(event)  # nothing armed: refused
    assert not decision.accepted
    row = rejection_row(event, decision, world.config)
    assert row is not None
    assert row.detail["attributed"] == "claimed"


# --- §5.6: the seeded profile tells the whole story ---


def test_the_seeded_profile_announces_a_second_zone_joining_the_alarm():
    assert Moment.INCIDENT_JOINED in SEED_MOMENTS


# --- decision 112: re-linking a contact is a change to people ---


def test_relinking_a_contact_to_another_person_touches_people():
    before = replace(
        make_house(),
        users=(user(), user("anna", "Anna")),
        contacts=(Contact("anna", "Anna", linked_user_id="anna"),),
    )
    after = replace(before, contacts=(Contact("anna", "Anna", linked_user_id="luca"),))
    assert touches_people(before, after)
    assert not touches_people(before, before)


# --- §12.2: a disabled channel's fault survives a restart ---


def test_a_faulted_channel_that_is_disabled_keeps_its_fault_across_a_restart():
    world = channels_world()
    world.health(channel_sends={PUSH: False})
    world.health(channel_sends={PUSH: False})
    assert world.state.health.channel(PUSH).fault is ChannelFault.SEND_FAILED
    disabled = replace(
        world.config,
        contacts=tuple(
            replace(
                c,
                channels=tuple(
                    replace(ch, enabled=False) if ch.id == "push" else ch
                    for ch in c.channels
                ),
            )
            for c in world.config.contacts
        ),
    )
    restored = state_from_dict(state_to_dict(world.state), disabled)
    assert restored.health.channel(PUSH).fault is ChannelFault.SEND_FAILED
    # And the engine keeps it too, so switching the channel back on shows
    # the fault it was in rather than a channel nothing is known about.
    world.config, world.state = disabled, restored
    world.advance(1)
    assert world.state.health.channel(PUSH).fault is ChannelFault.SEND_FAILED


# --- §10.4: the categories that name people ---


def test_the_short_retention_preset_covers_who_acknowledged():
    assert "action" in NAMED_CATEGORIES


# --- keep the imports honest ---


def test_helpers_are_what_they_say():
    assert isinstance(open_plan(), Group)
    assert zone("x", BATH, "upstairs").area_id == "upstairs"
    assert HealthSettings().channel_failures >= 1
