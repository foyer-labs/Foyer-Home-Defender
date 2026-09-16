"""Response profiles: who answers, with what, and under which conditions.

SPEC §6 and §19. The rule the whole part turns on (part 3 decision 1): the
area is the unit of response, and a zone's own profile is read only for its
own alarm.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core.models import (
    ActionKind,
    AreaState,
    ChimeSettings,
    ChimeTarget,
    ConditionMode,
    Group,
    Moment,
    ProfileAction,
    ResponseProfile,
    Settings,
    StateCondition,
    StateOperator,
    TimeCondition,
)
from custom_components.foyer.core.response import effective_profile
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import BATH, DOOR, PATIO, WINDOW, World, make_house

SIREN = "siren.outdoor"
LAMP = "switch.porch"


def action(
    action_id: str, kind: ActionKind, *moments: Moment, **params
) -> ProfileAction:
    conditions = params.pop("conditions", ())
    mode = params.pop("condition_mode", ConditionMode.ALL)
    return ProfileAction(
        id=action_id,
        kind=kind,
        moments=frozenset(moments),
        params=params,
        conditions=conditions,
        condition_mode=mode,
    )


def notify(action_id: str, *moments: Moment, **params) -> ProfileAction:
    params.setdefault("service", "notify.mobile_app_luca")
    params.setdefault("message", "{{ zone }}")
    return action(action_id, ActionKind.NOTIFY, *moments, **params)


def siren(action_id: str, *moments: Moment, **params) -> ProfileAction:
    params.setdefault("entity_ids", (SIREN,))
    return action(action_id, ActionKind.SIREN, *moments, **params)


def profile(profile_id: str, *actions: ProfileAction, severity: int = 1):
    return ResponseProfile(profile_id, profile_id.title(), severity, actions)


def house(*profiles: ResponseProfile, default: str | None = None, **changes):
    """A house whose profiles are exactly the ones a test cares about.

    The first profile is the global default unless a test says otherwise.
    """
    config = make_house()
    return replace(
        config,
        profiles=profiles,
        settings=replace(
            config.settings, default_profile_id=default or profiles[0].id
        ),
        **changes,
    )


def kinds(decision, moment: Moment | None = None) -> list[str]:
    return [a.kind for a in decision.actions if moment is None or a.moment is moment]


def armed(config, scenario: str = "away") -> World:
    world = World(config)
    world.arm(scenario)
    world.advance(30)
    return world


# --- who answers -------------------------------------------------------------------


def test_the_area_answers_for_what_happens_in_it():
    """Part 3 decision 1: the area is the unit of response."""
    config = house(
        profile("quiet", notify("q", Moment.ARMED, Moment.TRIGGERED)),
        profile("loud", siren("s", Moment.ARMED, Moment.TRIGGERED)),
    )
    config = replace(
        config,
        areas=tuple(
            replace(a, response_profile_id="loud") if a.id == "ground" else a
            for a in config.areas
        ),
    )
    world = armed(config, "night")  # night arms the ground floor only

    assert kinds(world.last, Moment.ARMED) == ["siren"]
    assert kinds(world.set(WINDOW, "on"), Moment.TRIGGERED) == ["siren"]


def test_a_zone_profile_is_read_only_for_its_own_alarm():
    """A quiet beam in a loud area: quiet when it fires, the area otherwise."""
    config = house(
        profile("quiet", notify("q", Moment.TRIGGERED, Moment.ZONE_FAULT)),
        profile("loud", siren("s", Moment.TRIGGERED), notify("n", Moment.ZONE_FAULT)),
        default="loud",
    )
    config = replace(
        config,
        zones=tuple(
            replace(z, response_profile_id="quiet") if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = armed(config)

    assert kinds(world.set(WINDOW, "on"), Moment.TRIGGERED) == ["notify"]
    # The same zone's fault is not its alarm: the area answers, loudly.
    assert kinds(world.set(BATH, None), Moment.ZONE_FAULT) == ["notify"]
    assert world.last.actions[0].profile_id == "loud"


def test_inheritance_falls_through_area_then_scenario_then_default():
    config = house(
        profile("quiet", notify("q", Moment.ARMED)),
        profile("scenario", notify("sc", Moment.ARMED)),
        profile("area", notify("ar", Moment.ARMED)),
    )
    assert effective_profile(config, area_id="ground", moment=Moment.ARMED).id == (
        "quiet"
    )

    with_scenario = replace(
        config,
        scenarios=tuple(
            replace(s, response_profile_id="scenario") if s.id == "away" else s
            for s in config.scenarios
        ),
    )
    assert (
        effective_profile(
            with_scenario, area_id="ground", scenario_id="away", moment=Moment.ARMED
        ).id
        == "scenario"
    )

    with_area = replace(
        with_scenario,
        areas=tuple(
            replace(a, response_profile_id="area") if a.id == "ground" else a
            for a in with_scenario.areas
        ),
    )
    assert (
        effective_profile(
            with_area, area_id="ground", scenario_id="away", moment=Moment.ARMED
        ).id
        == "area"
    )


def test_a_reference_to_a_missing_profile_falls_back_to_the_default():
    """Validation refuses to store one; if one ever survives, it is not silence."""
    config = house(profile("quiet", notify("q", Moment.ARMED)))
    config = replace(
        config,
        areas=tuple(
            replace(a, response_profile_id="gone") if a.id == "ground" else a
            for a in config.areas
        ),
    )
    assert effective_profile(config, area_id="ground", moment=Moment.ARMED).id == (
        "quiet"
    )


# --- the technical channel (part 3 decision 2) --------------------------------------


def test_the_technical_channel_has_its_own_default_not_the_area_s():
    from .test_technical import SMOKE, house as technical_house

    config = technical_house()
    config = replace(
        config,
        profiles=(
            profile("intrusion", siren("s", Moment.TECHNICAL_RAISED)),
            profile("technical", notify("t", Moment.TECHNICAL_RAISED)),
        ),
        settings=Settings(
            default_profile_id="intrusion", technical_profile_id="technical"
        ),
    )
    world = World(config)

    assert kinds(world.set(SMOKE, "on"), Moment.TECHNICAL_RAISED) == ["notify"]
    assert world.last.actions[0].profile_id == "technical"


def test_a_technical_zone_may_still_override_its_channel_s_profile():
    from .test_technical import SMOKE, house as technical_house

    config = technical_house()
    config = replace(
        config,
        profiles=(
            profile("technical", notify("t", Moment.TECHNICAL_RAISED)),
            profile("own", siren("s", Moment.TECHNICAL_RAISED)),
        ),
        settings=Settings(technical_profile_id="technical"),
        zones=tuple(
            replace(z, response_profile_id="own") if z.id == "smoke" else z
            for z in technical_house().zones
        ),
    )
    world = World(config)
    assert kinds(world.set(SMOKE, "on"), Moment.TECHNICAL_RAISED) == ["siren"]


# --- graduated response (§4.8, the acceptance item) ---------------------------------


def test_a_group_produces_graduated_response():
    """One PIR notifies; two within the window sound the siren (§4.8)."""
    config = house(
        profile("quiet", notify("q", Moment.TRIGGERED)),
        profile("full", siren("s", Moment.VERIFICATION_SATISFIED), severity=3),
        groups=(
            Group(
                "open_plan",
                "Open plan",
                "ground",
                ("window", "patio"),
                2,
                60,
                response_profile_id="full",
            ),
        ),
    )
    world = armed(config)

    first = world.set(WINDOW, "on")
    assert kinds(first, Moment.TRIGGERED) == ["notify"]  # member's own profile
    assert "siren" not in kinds(first)

    world.advance(20)
    second = world.set(PATIO, "on")
    assert kinds(second, Moment.VERIFICATION_SATISFIED) == ["siren"]
    assert second.actions[-1].profile_id == "full"


def test_the_incident_records_the_profile_and_severity_of_each_contributor():
    """§5.6: Phase 4's escalation takes the highest-severity contributor."""
    config = house(
        profile("quiet", notify("q", Moment.TRIGGERED), severity=1),
        profile("full", siren("s", Moment.TRIGGERED), severity=3),
    )
    config = replace(
        config,
        zones=tuple(
            replace(z, response_profile_id="full") if z.id == "patio" else z
            for z in config.zones
        ),
    )
    world = armed(config)
    world.set(WINDOW, "on")
    world.advance(10)
    world.set(PATIO, "on")

    contributors = world.state.incident.contributors
    assert [(c.zone_id, c.profile_id, c.severity) for c in contributors] == [
        ("window", "quiet", 1),
        ("patio", "full", 3),
    ]
    assert max(c.severity for c in contributors) == 3


def test_an_incident_unions_actions_without_restarting_a_running_siren():
    config = house(
        profile("full", siren("s", Moment.TRIGGERED), notify("n", Moment.TRIGGERED))
    )
    world = armed(config)

    first = world.set(WINDOW, "on")
    assert sorted(kinds(first, Moment.TRIGGERED)) == ["notify", "siren"]
    assert world.state.incident.actions_started == ("s", "n")

    world.advance(10)
    joined = world.set(PATIO, "on")
    # The second zone joins: nothing is started again (§5.6).
    assert joined.actions == ()


# --- conditions (§6.3) ---------------------------------------------------------------


def test_a_time_window_crossing_midnight():
    night = TimeCondition(after="22:00", before="07:00")
    config = house(profile("p", notify("n", Moment.TRIGGERED, conditions=(night,))))
    world = armed(config)  # NOW is 19:32 UTC

    assert kinds(world.set(WINDOW, "on")) == []

    world = armed(config)
    world.now = world.now.replace(hour=23)
    assert kinds(world.set(WINDOW, "on")) == ["notify"]

    world = armed(config)
    world.now = world.now.replace(hour=3)
    assert kinds(world.set(WINDOW, "on")) == ["notify"]


def test_two_conditions_combine_as_the_user_chose():
    """Part 3 decision 4: AND or OR, selectable."""
    night = TimeCondition(after="22:00", before="07:00")
    away = StateCondition("binary_sensor.nobody_home", StateOperator.IS, "on")
    both = house(profile("p", notify("n", Moment.TRIGGERED, conditions=(night, away))))
    either = house(
        profile(
            "p",
            notify(
                "n",
                Moment.TRIGGERED,
                conditions=(night, away),
                condition_mode=ConditionMode.ANY,
            ),
        )
    )

    world = armed(both)
    world.entities["binary_sensor.nobody_home"] = world.entities[DOOR]
    assert kinds(world.set(WINDOW, "on")) == []  # 19:32, and nobody_home is "off"

    world = armed(either)
    world.entities["binary_sensor.nobody_home"] = replace(
        world.entities[DOOR], state="on"
    )
    assert kinds(world.set(WINDOW, "on")) == ["notify"]


def test_a_condition_on_an_entity_that_is_not_there_is_not_met():
    """The same reasoning as INV-4: what cannot be read is never assumed."""
    config = house(
        profile(
            "p",
            notify(
                "n",
                Moment.TRIGGERED,
                conditions=(
                    StateCondition("binary_sensor.gone", StateOperator.IS, "on"),
                ),
            ),
        )
    )
    world = armed(config)
    assert kinds(world.set(WINDOW, "on")) == []


# --- templates (§6.4) ----------------------------------------------------------------


def test_templates_render_the_documented_variables():
    config = house(
        profile(
            "p",
            notify(
                "n",
                Moment.TRIGGERED,
                message="{{ zone }} in {{ area }} at {{ time }} ({{ scenario }})",
                title="{{ incident_zones }}",
            ),
        )
    )
    world = armed(config)
    [intent] = world.set(WINDOW, "on").actions

    assert intent.params["message"] == "Window in Ground floor at 19:32 (Away)"
    assert intent.params["title"] == "Window"


# --- silent zones (§4.2, part 3 decision 6) ------------------------------------------


def test_a_silent_zone_runs_the_response_without_the_sounders():
    config = house(
        profile("p", siren("s", Moment.TRIGGERED), notify("n", Moment.TRIGGERED))
    )
    config = replace(
        config,
        zones=tuple(
            replace(z, silent=True) if z.id == "window" else z for z in config.zones
        ),
    )
    world = armed(config)

    assert kinds(world.set(WINDOW, "on"), Moment.TRIGGERED) == ["notify"]
    # A zone that is not silent still sounds, in the same incident: silence
    # belongs to the zone, not to the alarm.
    world.advance(10)
    assert kinds(world.set(BATH, "on"), Moment.TRIGGERED) == ["siren"]


def test_the_silent_list_is_a_setting():
    config = house(
        profile("p", siren("s", Moment.TRIGGERED), notify("n", Moment.TRIGGERED))
    )
    config = replace(
        config,
        settings=replace(config.settings, silent_suppresses=("notify",)),
        zones=tuple(
            replace(z, silent=True) if z.id == "window" else z for z in config.zones
        ),
    )
    world = armed(config)
    assert kinds(world.set(WINDOW, "on"), Moment.TRIGGERED) == ["siren"]


def test_a_silent_zone_does_not_chime():
    config = house(
        profile("p", notify("n", Moment.TRIGGERED)),
        chime=ChimeSettings(targets=(ChimeTarget("siren.hall"),)),
    )
    config = replace(
        config,
        zones=tuple(
            replace(z, silent=True, chime=True) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)  # disarmed: the zone is not monitored
    assert kinds(world.set(WINDOW, "on")) == []


# --- delays, durations and reverts (§6.2, part 3 decision 5) -------------------------


def test_a_delay_holds_the_rest_of_the_sequence():
    config = house(
        profile(
            "p",
            notify("first", Moment.TRIGGERED),
            action("wait", ActionKind.DELAY, Moment.TRIGGERED, seconds=30),
            siren("later", Moment.TRIGGERED),
        )
    )
    world = armed(config)

    assert kinds(world.set(WINDOW, "on"), Moment.TRIGGERED) == ["notify"]
    [pending] = world.state.pending_runs
    assert pending.due == world.now + timedelta(seconds=30)

    assert kinds(world.advance(29)) == []
    assert "siren" in kinds(world.advance(1))
    assert world.state.pending_runs == ()


def test_a_held_sequence_survives_a_restart():
    """INV-3: a pending delay is state, not a task (part 3 decision 5)."""
    config = house(
        profile(
            "p",
            action("wait", ActionKind.DELAY, Moment.TRIGGERED, seconds=60),
            siren("later", Moment.TRIGGERED),
        )
    )
    world = armed(config)
    world.set(WINDOW, "on")
    assert len(world.state.pending_runs) == 1

    restored = state_from_dict(state_to_dict(world.state), config)
    assert restored.pending_runs == world.state.pending_runs

    world.state = restored
    assert "siren" in kinds(world.advance(60))


def test_a_switch_reverts_when_its_time_is_up():
    config = house(
        profile(
            "p",
            action(
                "porch",
                ActionKind.SWITCH,
                Moment.TRIGGERED,
                entity_ids=(LAMP,),
                state="on",
                revert_after=120,
            ),
        )
    )
    world = armed(config)
    world.set(WINDOW, "on")
    assert kinds(world.last) == ["switch"]
    [running] = world.state.running
    assert running.entity_ids == (LAMP,) and running.restore == "off"

    decision = world.advance(120)
    [revert] = decision.actions
    assert revert.kind == "revert"
    assert revert.params["entity_ids"] == (LAMP,) and revert.params["state"] == "off"
    assert world.state.running == ()


def test_a_siren_never_sounds_beyond_the_cutoff_and_stops_on_disarm():
    config = house(profile("p", siren("s", Moment.TRIGGERED, duration=900)))
    world = armed(config)
    [intent] = world.set(WINDOW, "on").actions
    # The house's siren cutoff is the global default, 180 s (§5.3).
    assert intent.params["duration"] == 180

    decision = world.disarm()
    assert [a.kind for a in decision.actions] == ["revert"]
    assert decision.actions[0].params["entity_ids"] == (SIREN,)
    assert world.state.running == ()


def test_the_siren_cutoff_stops_what_it_started():
    config = house(profile("p", siren("s", Moment.TRIGGERED)))
    world = armed(config)
    world.set(WINDOW, "on")

    decision = world.advance(180)
    assert world.area("ground").state is AreaState.ARMED
    assert [a.kind for a in decision.actions] == ["revert"]


def test_a_sequence_is_abandoned_when_its_area_is_disarmed():
    config = house(
        profile(
            "p",
            action("wait", ActionKind.DELAY, Moment.TRIGGERED, seconds=60),
            siren("later", Moment.TRIGGERED),
        )
    )
    world = armed(config)
    world.set(WINDOW, "on")
    world.disarm()

    assert world.state.pending_runs == ()
    assert kinds(world.advance(120)) == []
