"""A duress code: its owner's code everywhere, and one silent occurrence.

SPEC §8.1, §6.1, §11.2, §11.3, decisions 131-134. The code does exactly what
the ordinary code would — the same answer, the same lockout counter, the same
acknowledgement — and every request it comes with raises `duress` once,
whatever it asked for and whether or not it was granted. The occurrence names
what was asked, belongs to no area and to no incident, is answered by the
default profile alone, runs silent, never escalates and is never held back by
a walk test.

What reaches the screens of the house is tested inside Home Assistant
(tests/ha/test_duress.py): these tests are the engine's half.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.foyer.core import authz
from custom_components.foyer.core.journal import (
    action_row,
    glanceable,
    row_for,
    rows_for,
)
from custom_components.foyer.core.models import (
    AcknowledgeIncident,
    AcknowledgeTechnical,
    ActionKind,
    Actor,
    ArmRequest,
    BypassZone,
    CodeAttempt,
    CodeResult,
    Decision,
    DisarmRequest,
    DuressNotice,
    Moment,
    Occurrence,
    Operation,
    Permission,
    ProfileAction,
    Purpose,
    Reason,
    ResponseProfile,
    Suspension,
    SuspensionKind,
)
from custom_components.foyer.core.response import PlanContext, variables
from custom_components.foyer.core.simulate import SimulationRequest, as_dict, run
from custom_components.foyer.core.templates import TEMPLATE_VARIABLES, render
from custom_components.foyer.core.validation import validate
from custom_components.foyer.store.seed import SEED_MOMENTS

from .helpers import NOW, WINDOW, World, closed_entities, make_house, user

# Who is asking, as security/ hands it over: the same person, the same keypad,
# a code that verified — and, on one of them, the flag that says it was the
# duress code.
ORDINARY = {"user_id": "luca", "channel": "keypad", "code": CodeResult.VALID}
DURESS = {**ORDINARY, "duress": True}


def house(config=None) -> World:
    """The shared house with one person holding a code, so the policy is in
    force (decision 78)."""
    config = config or make_house()
    return World(replace(config, users=(user(),)))


def answering_duress(config, *actions: ProfileAction):
    """The default profile, given these actions besides its own."""
    default = config.profiles[0]
    return replace(
        config,
        profiles=(replace(default, actions=(*default.actions, *actions)),),
    )


def duress_of(decision: Decision) -> list[Occurrence]:
    return [o for o in decision.occurrences if o.moment is Moment.DURESS]


def one_duress(decision: Decision) -> Occurrence:
    found = duress_of(decision)
    assert len(found) == 1, decision.moments
    return found[0]


def armed(world: World) -> None:
    world.arm("night", **ORDINARY)
    world.advance(10)


def in_alarm(world: World) -> None:
    """Night armed, and the kitchen window opened: an incident is open."""
    armed(world)
    world.set(WINDOW, "on")
    assert world.state.incident is not None


def suspended(world: World) -> None:
    world.suspend(Suspension("s", SuspensionKind.NEXT), **ORDINARY)


def excluded(world: World) -> None:
    assert world.bypass("window", **ORDINARY).accepted


def walking(world: World) -> None:
    assert world.walk_test(True, **ORDINARY).accepted


def nothing(world: World) -> None:
    pass


# (what the house is doing first, the request, the operation, what it named)
CASES: dict[str, tuple[Callable, Callable, str, dict[str, str]]] = {
    "arm": (
        nothing,
        lambda w, who: w.arm("night", **who),
        "arm",
        {"scenario": "night"},
    ),
    "force_arm": (
        nothing,
        lambda w, who: w.arm("night", force=True, **who),
        "force_arm",
        {"scenario": "night"},
    ),
    "arm_area": (
        nothing,
        lambda w, who: w.arm_area("garage", **who),
        "arm",
        {"area": "garage"},
    ),
    "arm_mode": (
        nothing,
        lambda w, who: w.arm_mode("armed_night", **who),
        "arm",
        {"mode": "armed_night"},
    ),
    "switch": (
        armed,
        lambda w, who: w.arm("away", **who),
        "change_scenario",
        {"scenario": "away"},
    ),
    "disarm_all": (
        armed,
        lambda w, who: w.disarm(**who),
        "disarm",
        {"areas": "ground,upstairs,garage"},
    ),
    "disarm_named": (
        armed,
        lambda w, who: w.disarm("ground", **who),
        "disarm",
        {"areas": "ground"},
    ),
    "bypass": (
        nothing,
        lambda w, who: w.bypass("window", **who),
        "bypass_zone",
        {"zone": "window"},
    ),
    "unbypass": (
        excluded,
        lambda w, who: w.send(BypassZone("window", bypass=False, actor=Actor(**who))),
        "unbypass_zone",
        {"zone": "window"},
    ),
    "acknowledge": (
        in_alarm,
        lambda w, who: w.send(AcknowledgeIncident(Actor(**who))),
        "acknowledge",
        {"target": "incident"},
    ),
    "acknowledge_technical": (
        nothing,
        lambda w, who: w.send(AcknowledgeTechnical(Actor(**who))),
        "acknowledge",
        {"target": "technical"},
    ),
    "walk_test_start": (
        nothing,
        lambda w, who: w.walk_test(True, **who),
        "walk_test",
        {"enabled": "true"},
    ),
    "walk_test_end": (
        walking,
        lambda w, who: w.walk_test(False, **who),
        "walk_test",
        {"enabled": "false"},
    ),
    "cancel": (
        nothing,
        lambda w, who: w.cancel(**who),
        "cancel_auto_action",
        {},
    ),
    "auto_arming": (
        nothing,
        lambda w, who: w.auto_arming(False, **who),
        "auto_arming",
        {"enabled": "false"},
    ),
    "suspend": (
        nothing,
        lambda w, who: w.suspend(Suspension("s", SuspensionKind.NEXT), **who),
        "suspend_auto_arming",
        {},
    ),
    "lift_suspension": (
        suspended,
        lambda w, who: w.suspend(suspension_id="s", **who),
        "lift_suspension",
        {},
    ),
    "edit_config": (
        nothing,
        lambda w, who: w.send(CodeAttempt(Operation.EDIT_CONFIG, Actor(**who))),
        "edit_config",
        {},
    ),
    "export_log": (
        nothing,
        lambda w, who: w.send(
            CodeAttempt(Operation.EDIT_CONFIG, Actor(**who), purpose=Purpose.EXPORT_LOG)
        ),
        "export_log",
        {},
    ),
    "test_action": (
        nothing,
        lambda w, who: w.send(CodeAttempt(Operation.TEST_ACTION, Actor(**who))),
        "test_action",
        {},
    ),
    "unlock": (
        nothing,
        lambda w, who: w.send(CodeAttempt(None, Actor(**who), purpose=Purpose.UNLOCK)),
        "unlock",
        {},
    ),
    "refused_before_the_engine": (
        nothing,
        lambda w, who: w.send(
            DuressNotice("disarm", {"areas": "ground"}, Actor(**who))
        ),
        "disarm",
        {"areas": "ground"},
    ),
}


# --- every operation, one occurrence (decision 131) ------------------------------


@pytest.mark.parametrize("case", list(CASES))
def test_every_request_with_a_duress_code_raises_one_duress_naming_it(case):
    before, request, operation, named = CASES[case]
    world = house()
    before(world)
    occurrence = one_duress(request(world, DURESS))

    assert dict(occurrence.detail) == {"operation": operation, **named}
    # Who, through what: the row names the person the code belongs to.
    assert occurrence.user_id == "luca"
    assert occurrence.user_name == "Luca"
    assert occurrence.channel == "keypad"
    # And nothing that would make it an area's, a scenario's or an incident's
    # to answer, or put it on every card (decision 132).
    assert occurrence.area_id is None
    assert occurrence.zone_id is None
    assert occurrence.scenario_id is None
    assert occurrence.incident_id is None


def _answer(decision: Decision) -> tuple:
    """Everything in a decision but its `duress` and what answered it."""
    return (
        decision.accepted,
        decision.reason,
        decision.blocking_zones,
        decision.bypassed_zones,
        decision.low_battery_zones,
        decision.code_required_by,
        # The planner numbers every batch it answers, and `duress` is one
        # more: an internal counter, and nothing anybody is shown.
        replace(decision.state, run_seq=0),
        [o for o in decision.occurrences if o.moment is not Moment.DURESS],
        [
            replace(i, run_id="")
            for i in decision.actions
            if i.moment is not Moment.DURESS
        ],
        [
            replace(i, run_id="")
            for i in decision.inhibited
            if i.moment is not Moment.DURESS
        ],
    )


@pytest.mark.parametrize("case", list(CASES))
def test_the_ordinary_code_raises_nothing_and_gets_the_same_answer(case):
    """Nothing the person at the keypad is told differs (§8.1): not the
    answer, not the state, not the rows beside the one that is hidden."""
    before, request, _, _ = CASES[case]
    ordinary, duress = house(), house()
    before(ordinary)
    before(duress)
    plain = request(ordinary, ORDINARY)
    coerced = request(duress, DURESS)

    assert duress_of(plain) == []
    assert _answer(plain) == _answer(coerced)


def test_a_code_spent_as_a_wrong_one_is_not_a_use_of_it():
    """The shape api/websocket builds for a code offered as somebody's new
    one: the gate's actor, with the code marked wrong. It is a collision,
    counted as a failed attempt (§8.4), and raises no `duress` (§8.1)."""
    world = house()
    wrong = Actor(
        user_id="luca", channel="keypad", code=CodeResult.INVALID, duress=True
    )
    decision = world.send(CodeAttempt(Operation.EDIT_CONFIG, wrong))

    assert decision.reason is Reason.BAD_CODE
    assert duress_of(decision) == []
    assert Moment.CODE_REJECTED in decision.moments


def test_once_per_request_however_many_times_it_is_authorised():
    """A forced switch asks the policy three times — arm, change scenario,
    force arm — and is still one request (decision 131)."""
    world = house()
    armed(world)
    decision = world.arm("away", force=True, **DURESS)

    assert decision.accepted
    assert one_duress(decision).detail["operation"] == "force_arm"


def test_it_comes_before_what_the_request_did():
    """Cause before consequence: the row that says a duress code was used is
    read before the disarm it was used for."""
    world = house()
    armed(world)
    moments_ = list(world.disarm(**DURESS).moments)

    assert moments_.index(Moment.DURESS) < moments_.index(Moment.DISARMED)


# --- refused requests raise it too ---------------------------------------------------


def _restricted(**changes) -> Callable[[World], None]:
    """Armed by the ordinary code, and only then narrowed: what the duress
    code is refused for is the person's own reach."""

    def before(world: World) -> None:
        armed(world)
        world.config = replace(world.config, users=(user(**changes),))

    return before


def _open_window(world: World) -> None:
    world.set(WINDOW, "on")


def _locked(world: World) -> None:
    armed(world)
    for _ in range(5):
        world.disarm(user_id=None, channel="keypad", code=CodeResult.INVALID)
    assert world.state.lockouts["keypad:"].until is not None


WHO = Actor(**DURESS)

# (what the house is doing first, the request, why it is refused, the row
# that says so besides the `duress` one)
REFUSALS: dict[str, tuple[Callable, object, Reason, str]] = {
    "nothing_to_disarm": (
        nothing,
        DisarmRequest(None, WHO),
        Reason.INVALID_STATE,
        "disarm_rejected",
    ),
    "not_permitted": (
        _restricted(
            permissions=frozenset(p.value for p in Permission) - {Permission.DISARM}
        ),
        DisarmRequest(None, WHO),
        Reason.NOT_PERMITTED,
        "code_rejected",
    ),
    "area_not_allowed": (
        _restricted(allowed_area_ids=("garage",)),
        DisarmRequest(("ground",), WHO),
        Reason.AREA_NOT_ALLOWED,
        "code_rejected",
    ),
    "zone_open": (
        _open_window,
        ArmRequest("night", WHO),
        Reason.ZONE_OPEN,
        "arm_rejected",
    ),
    "walk_test_running": (
        walking,
        ArmRequest("night", WHO),
        Reason.WALK_TEST_ACTIVE,
        "arm_rejected",
    ),
    "nothing_to_acknowledge": (
        nothing,
        AcknowledgeIncident(WHO),
        Reason.NOTHING_TO_ACKNOWLEDGE,
        "acknowledge_rejected",
    ),
    "locked_out": (
        _locked,
        DisarmRequest(None, WHO),
        Reason.LOCKED_OUT,
        "code_rejected",
    ),
}


@pytest.mark.parametrize("case", list(REFUSALS))
def test_a_refused_request_raises_it_and_keeps_its_own_row(case):
    """A person asking for help has asked, whatever the answer (decision
    131) — and the log still says why the request was refused."""
    before, event, reason, row = REFUSALS[case]
    world = house()
    before(world)
    decision = world.send(event)

    assert not decision.accepted
    assert decision.reason is reason
    one_duress(decision)
    rows = [r.event_type for r in rows_for(event, decision, world.config)]
    assert "duress" in rows
    assert row in rows


def test_a_locked_channel_raises_it_and_counts_nothing():
    """The lockout sees the duress code exactly as it sees the ordinary one:
    a locked channel is answered without another attempt counting."""
    world = house()
    _locked(world)
    before = dict(world.state.lockouts)
    decision = world.disarm(**DURESS)

    assert decision.reason is Reason.LOCKED_OUT
    one_duress(decision)
    assert dict(world.state.lockouts) == before


def test_it_clears_a_run_of_failures_exactly_as_the_ordinary_code_does():
    """The same counter (§8.4): a right code ends a run of wrong ones, and a
    duress code is a right code."""
    wrong = Actor(channel="keypad", code=CodeResult.INVALID)
    worlds = []
    for who in (ORDINARY, DURESS):
        world = house()
        for _ in range(3):
            world.send(CodeAttempt(Operation.EDIT_CONFIG, wrong))
        world.send(CodeAttempt(Operation.EDIT_CONFIG, Actor(**who)))
        worlds.append(world)

    assert worlds[0].state.lockouts == worlds[1].state.lockouts
    assert authz.lockout_key(wrong) not in worlds[1].state.lockouts


def test_a_request_refused_before_the_engine_moves_no_counter():
    """The duress and nothing else (decision 131): the ordinary code at the
    same refusal never reaches the engine, so neither may the duress code's
    notice spend or clear a failure."""
    world = house()
    for _ in range(3):
        world.disarm(user_id=None, channel="keypad", code=CodeResult.INVALID)
    before = dict(world.state.lockouts)
    decision = world.send(DuressNotice("bypass_zone", {}, Actor(**DURESS)))

    one_duress(decision)
    assert dict(world.state.lockouts) == before
    assert decision.accepted


# --- no area, no incident, the default profile (decision 132) --------------------


def test_it_joins_no_incident_while_one_is_open():
    world = house()
    in_alarm(world)
    incident = world.state.incident
    decision = world.disarm(**DURESS)

    duress = one_duress(decision)
    assert duress.incident_id is None
    # The disarm itself is the incident's, as it always is.
    disarmed = [o for o in decision.occurrences if o.moment is Moment.DISARMED]
    assert disarmed and all(o.incident_id == incident.id for o in disarmed)
    assert Moment.INCIDENT_JOINED not in decision.moments


def test_only_the_default_profile_answers_it():
    """An area's profile and a scenario's are never asked: `duress` belongs
    to no area, and one alert set up once is the one that works."""
    config = make_house()
    elsewhere = ResponseProfile(
        "ground",
        "Ground",
        actions=(
            ProfileAction(
                "ground_duress",
                ActionKind.PERSISTENT_NOTIFICATION,
                frozenset({Moment.DURESS}),
            ),
        ),
    )
    config = answering_duress(
        config,
        ProfileAction("default_duress", ActionKind.NOTIFY, frozenset({Moment.DURESS})),
    )
    config = replace(
        config,
        profiles=(*config.profiles, elsewhere),
        areas=tuple(replace(a, response_profile_id="ground") for a in config.areas),
        scenarios=tuple(
            replace(s, response_profile_id="ground") for s in config.scenarios
        ),
    )
    world = house(config)
    armed(world)
    decision = world.disarm(**DURESS)

    answered = [i for i in decision.actions if i.moment is Moment.DURESS]
    assert [(i.profile_id, i.action_id) for i in answered] == [
        ("default", "default_duress")
    ]


def test_it_always_runs_silent():
    """The global silent list is left out, as for a silent zone (§6.1):
    a siren answering a code nobody may know was used would tell the room."""
    config = answering_duress(
        make_house(),
        ProfileAction(
            "siren",
            ActionKind.SIREN,
            frozenset({Moment.DURESS}),
            params={"entity_ids": ["siren.hall"]},
        ),
        ProfileAction(
            "tts",
            ActionKind.TTS,
            frozenset({Moment.DURESS}),
            params={"entity_id": "media_player.hall", "message": "{{ user }}"},
        ),
        ProfileAction("tell", ActionKind.NOTIFY, frozenset({Moment.DURESS})),
    )
    world = house(config)
    armed(world)
    decision = world.disarm(**DURESS)

    answered = [i for i in decision.actions if i.moment is Moment.DURESS]
    assert [i.action_id for i in answered] == ["tell"]
    assert all(i.silent for i in answered)
    # Nothing was switched on for it either.
    assert not world.state.running


def test_it_is_never_an_escalation_step():
    step = ProfileAction(
        "a",
        ActionKind.NOTIFY,
        frozenset({Moment.DURESS}),
        escalation_offset=60,
    )
    config = replace(
        make_house(), profiles=(ResponseProfile("p", "P", actions=(step,)),)
    )
    config = replace(config, settings=replace(config.settings, default_profile_id="p"))

    assert "escalation_moment_invalid" in {p.code for p in validate(config)}


def test_the_seeded_profile_never_answers_it():
    """Its one action is a Home Assistant notification, which shows on the
    tablet the code was typed at (§6.1)."""
    assert Moment.DURESS not in SEED_MOMENTS


# --- a walk test holds the house back, not a person (§11.3) ---------------------


def _answered(decision: Decision) -> bool:
    return any(i.moment is Moment.DURESS for i in decision.actions) and not any(
        i.moment is Moment.DURESS for i in decision.inhibited
    )


@pytest.mark.parametrize(
    ("before", "ask"),
    [
        (nothing, lambda w: w.walk_test(True, **DURESS)),
        (walking, lambda w: w.walk_test(False, **DURESS)),
        (walking, lambda w: w.disarm(**DURESS)),
        (walking, lambda w: w.bypass("window", **DURESS)),
    ],
    ids=["started_with_it", "ended_with_it", "disarm_during", "exclude_during"],
)
def test_a_walk_test_never_holds_it_back(before, ask):
    config = answering_duress(
        make_house(),
        ProfileAction("tell", ActionKind.NOTIFY, frozenset({Moment.DURESS})),
    )
    world = house(config)
    before(world)
    decision = ask(world)

    one_duress(decision)
    assert _answered(decision)


# --- what a message can say (decision 134) ----------------------------------------


def _context(world: World) -> PlanContext:
    return PlanContext(
        config=world.config,
        snapshot=world.snapshot(),
        now=world.now,
        areas=world.state.areas,
    )


def test_operation_is_a_template_variable():
    assert "operation" in TEMPLATE_VARIABLES
    assert render(
        "{{ user }}: {{ operation }}", {"user": "Luca", "operation": "disarm"}
    ) == ("Luca: disarm")


def test_a_duress_message_names_the_operation_and_the_areas_it_named():
    """The built-in message used to say "disarmed  with a duress code": the
    occurrence carries no area, so {area} was always empty. The areas the
    request named are read back from its detail."""
    world = house()
    armed(world)
    decision = world.disarm(**DURESS)
    values = variables(_context(world), duress_of(decision))

    assert values["operation"] == "disarm"
    assert values["area"] == "Ground floor, Upstairs, Garage"
    assert values["user"] == "Luca"


def test_a_duress_message_names_the_zone_and_the_scenario_it_named():
    world = house()
    zone = variables(_context(world), duress_of(world.bypass("window", **DURESS)))
    scenario = variables(_context(world), duress_of(house().arm("night", **DURESS)))

    assert (zone["operation"], zone["zone"]) == ("bypass_zone", "Window")
    assert (scenario["operation"], scenario["scenario"]) == ("arm", "Night")


def test_a_code_refused_for_its_code_names_its_operation_too():
    world = house()
    armed(world)
    decision = world.disarm(user_id=None, channel="keypad", code=CodeResult.INVALID)
    rejected = [o for o in decision.occurrences if o.moment is Moment.CODE_REJECTED]

    assert variables(_context(world), rejected)["operation"] == "disarm"


# --- the simulator (§11.2) ---------------------------------------------------------


def test_a_rehearsal_with_a_duress_code_runs_as_the_ordinary_code_would():
    """The `duress` was raised by the request that carried the code; a trace
    that showed it would put it on the screen the code was typed at."""
    config = replace(make_house(), users=(user(),))

    def rehearse(**who):
        request = SimulationRequest(
            start=NOW, scenario_id="night", actor=Actor(**{**who, "channel": "ha_ui"})
        )
        return run(config, request, closed_entities(config, NOW))

    coerced = rehearse(**DURESS)
    plain = rehearse(**ORDINARY)

    assert not any(
        o.moment is Moment.DURESS for step in coerced.steps for o in step.occurrences
    )
    assert "duress" not in str(as_dict(coerced, config))
    assert [s.kind for s in coerced.steps] == [s.kind for s in plain.steps]
    assert [o.moment for s in coerced.steps for o in s.occurrences] == [
        o.moment for s in plain.steps for o in s.occurrences
    ]


# --- what a glance may find (decision 133) ----------------------------------------


def test_the_duress_row_and_the_actions_that_answered_it_are_not_for_a_glance():
    at = NOW + timedelta(seconds=1)
    duress = row_for(Occurrence(Moment.DURESS, detail={"operation": "disarm"}), at)
    disarmed = row_for(Occurrence(Moment.DISARMED, area_id="ground"), at)

    assert not glanceable(duress)
    assert glanceable(disarmed)
    for moment, expected in ((Moment.DURESS, False), (Moment.DISARMED, True)):
        row = action_row(at, action_id="a", kind="notify", moment=moment, ok=False)
        assert glanceable(row) is expected
