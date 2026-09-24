"""Fix phase: a scenario limited to some people needs somebody established."""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import AreaState, CodeResult

from .helpers import World, make_house, user


def _house():
    config = replace(
        make_house(), users=(user("luca", "Luca"), user("guest", "Guest"))
    )
    return replace(
        config,
        scenarios=tuple(
            replace(s, allowed_user_ids=("luca",)) if s.id == "night" else s
            for s in config.scenarios
        ),
    )


def test_nobody_established_cannot_arm_a_limited_scenario():
    world = World(_house())
    decision = world.arm("night")
    assert decision.reason is not None and decision.reason.value == "code_required"
    assert world.area("ground").state is AreaState.DISARMED


def test_a_name_a_message_typed_is_not_on_the_list():
    """Decisions 88 and 102: a claimed user_id buys nothing, a list included."""
    world = World(_house())
    decision = world.arm("night", user_id="luca", claimed=True)
    assert decision.reason is not None and decision.reason.value == "code_required"


def test_a_person_on_the_list_with_a_code_arms_it():
    world = World(_house())
    world.arm("night", user_id="luca", code=CodeResult.VALID)
    assert world.area("ground").state is not AreaState.DISARMED


def test_somebody_not_on_the_list_is_refused_as_before():
    world = World(_house())
    decision = world.arm("night", user_id="guest", code=CodeResult.VALID)
    assert decision.reason.value == "scenario_not_allowed"


def test_an_automatic_rule_is_the_households_own_and_arms_it():
    world = World(_house())
    world.arm("night", channel="auto_rule")
    assert world.area("ground").state is not AreaState.DISARMED
