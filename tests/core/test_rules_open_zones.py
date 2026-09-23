"""A rule meets an open window (SPEC §9.4 "When the house is not ready").

Everybody has left and the kitchen window is open. The countdown names it
(decision 125), the rule's contacts are told what came of the arming
(decision 124), and a rule may arm excluding open bypassable zones if its
owner chose that (decision 126).
"""

from __future__ import annotations

from dataclasses import replace

from custom_components.foyer.core.models import (
    ActionKind,
    Contact,
    ContactChannel,
    ContactChannelKind,
    Moment,
)

from .helpers import LUCA, PARTNER, WINDOW, World, make_house, rule


def house(**rule_changes):
    contact = Contact(
        "anna",
        "Anna",
        channels=(ContactChannel("push", ContactChannelKind.PUSH, "notify.anna"),),
        quiet_start="00:00",
        quiet_end="23:59",
    )
    config = make_house()
    return replace(
        config,
        contacts=(contact,),
        rules=(rule(notify_contact_ids=("anna",), **rule_changes),),
    )


def leave(world: World) -> None:
    world.person(LUCA, "not_home")
    world.person(PARTNER, "not_home")


def _occurrences(decision, moment):
    return [o for o in decision.occurrences if o.moment is moment]


def _told(decision):
    return [
        a
        for a in decision.actions
        if a.kind == ActionKind.NOTIFY.value and a.moment is Moment.AUTO_OUTCOME
    ]


# --- decision 125: the countdown names the open zones -------------------------------


def test_the_countdown_says_the_window_is_open_and_what_will_happen():
    world = World(house())
    world.set(WINDOW, "on")
    leave(world)
    decision = world.advance(30 * 60)
    (pending,) = _occurrences(decision, Moment.AUTO_PENDING)
    assert pending.detail["open"] == "Window"
    assert pending.detail["excluding"] == ""
    # The countdown is held by the contact's quiet hours, as it always was;
    # what it would say is on the occurrence the intent is built from.
    from custom_components.foyer.core.engine import _countdown_variant

    assert _countdown_variant(pending.detail) == "arm_open"


def test_a_ready_house_counts_down_as_it_always_did():
    world = World(house())
    leave(world)
    decision = world.advance(30 * 60)
    (pending,) = _occurrences(decision, Moment.AUTO_PENDING)
    assert "open" not in pending.detail


# --- decision 124: the rule's contacts hear the outcome -----------------------------


def test_not_armed_then_armed_when_the_window_shuts():
    world = World(house())
    world.set(WINDOW, "on")
    leave(world)
    world.advance(30 * 60)
    decision = world.advance(121)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "not_armed"
    assert outcome.detail["zones"] == "Window"
    (message,) = _told(decision)
    # Through quiet hours: the contact's window covers the whole day.
    assert message.params["recipients"]
    assert message.variant == "not_armed"
    assert world.states()["ground"] == "disarmed"

    # The window shuts: a new countdown, then the house arms, and says so.
    world.set(WINDOW, "off")
    decision = world.advance(121)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "armed_later"
    assert world.states()["ground"] in {"arming", "armed"}


def test_an_arming_that_went_as_announced_says_nothing_more():
    world = World(house())
    leave(world)
    world.advance(30 * 60)
    decision = world.advance(121)
    assert _occurrences(decision, Moment.AUTO_OUTCOME) == []


# --- decision 126: arm anyway, excluding open bypassable zones ----------------------


def test_the_rule_may_arm_excluding_the_open_window():
    world = World(house(exclude_open_zones=True))
    world.set(WINDOW, "on")
    leave(world)
    decision = world.advance(30 * 60)
    (pending,) = _occurrences(decision, Moment.AUTO_PENDING)
    assert pending.detail["excluding"] == "1"
    decision = world.advance(121)
    assert world.states()["ground"] in {"arming", "armed"}
    assert "window" in world.state.bypassed
    assert _occurrences(decision, Moment.FORCED_ARM)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "excluding"
    assert outcome.detail["zones"] == "Window"


def test_a_zone_in_fault_is_never_excluded_by_a_rule():
    """INV-4: a silent sensor is not 'all quiet', and nobody chose to leave it."""
    world = World(house(exclude_open_zones=True))
    world.set(WINDOW, "unavailable")
    leave(world)
    world.advance(30 * 60)
    decision = world.advance(121)
    assert world.states()["ground"] == "disarmed"
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "not_armed"
    assert "window" not in world.state.bypassed


def test_a_zone_that_may_not_be_bypassed_still_refuses():
    config = house(exclude_open_zones=True)
    config = replace(
        config,
        zones=tuple(
            replace(z, bypassable=False) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)
    world.set(WINDOW, "on")
    leave(world)
    decision = world.advance(30 * 60)
    (pending,) = _occurrences(decision, Moment.AUTO_PENDING)
    # The countdown does not promise an exclusion that will not happen.
    assert pending.detail["excluding"] == ""
    decision = world.advance(121)
    assert world.states()["ground"] == "disarmed"
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "not_armed"


def test_a_rule_refused_by_a_zone_that_may_not_be_bypassed_retries_once_shut():
    """The not-armed message promises it arms by itself: it must."""
    config = house(exclude_open_zones=True)
    config = replace(
        config,
        zones=tuple(
            replace(z, bypassable=False) if z.id == "window" else z
            for z in config.zones
        ),
    )
    world = World(config)
    world.set(WINDOW, "on")
    leave(world)
    world.advance(30 * 60)
    world.advance(121)
    assert world.states()["ground"] == "disarmed"
    world.set(WINDOW, "off")
    decision = world.advance(121)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "armed_later"


# --- what the review of these three found -------------------------------------------


def test_a_cancelled_retry_leaves_no_armed_later_behind():
    from custom_components.foyer.core.models import CancelAutoAction

    world = World(house())
    world.set(WINDOW, "on")
    leave(world)
    world.advance(30 * 60)
    world.advance(121)  # refused, not armed
    world.set(WINDOW, "off")  # retry: a new countdown
    assert world.state.pending_rules
    world.send(CancelAutoAction(world.state.pending_rules[0].id))
    assert not any(rt.retrying for rt in world.state.rules.values())


def test_a_time_rule_refused_says_it_will_not_try_again_and_does_not():
    """Decision 127: an instant has one turn, and the message says so."""
    from datetime import timedelta

    from custom_components.foyer.core.models import RuleTriggerKind

    from .helpers import NOW

    at = (NOW + timedelta(minutes=2)).strftime("%H:%M")
    world = World(house(kind=RuleTriggerKind.TIME, at=at, entity_ids=()))
    world.set(WINDOW, "on")
    world.advance(3 * 60)  # 23:00 comes: the countdown starts
    decision = world.advance(121)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "not_armed_once"
    world.set(WINDOW, "off")
    world.advance(600)
    assert world.states()["ground"] == "disarmed"


def test_a_zone_the_rule_would_exclude_does_not_hold_back_its_retry():
    """A stuck zone refused the arming; once it shuts, the open window the
    rule excludes is no reason to keep waiting."""
    from .helpers import PATIO

    config = house(exclude_open_zones=True)
    config = replace(
        config,
        zones=tuple(
            replace(z, bypassable=False, arm_policy=type(z.arm_policy).BLOCK)
            if z.id == "patio"
            else z
            for z in config.zones
        ),
    )
    world = World(config)
    world.set(WINDOW, "on")
    world.set(PATIO, "on")
    leave(world)
    world.advance(30 * 60)
    world.advance(121)
    assert world.states()["ground"] == "disarmed"
    world.set(PATIO, "off")  # the window is still open
    decision = world.advance(121)
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "excluding"
    assert "window" in world.state.bypassed


def test_a_zone_excluded_by_its_own_policy_is_not_the_rules_doing():
    """An auto-bypass zone at a zero exit delay is not "armed excluding"."""
    from .helpers import BATH

    config = house()
    config = replace(
        config,
        scenarios=tuple(replace(s, exit_delay_override=0) for s in config.scenarios),
    )
    world = World(config)
    world.set(BATH, "on")
    leave(world)
    world.advance(30 * 60)
    decision = world.advance(121)
    assert _occurrences(decision, Moment.AUTO_OUTCOME) == []


def test_an_exclusion_covers_only_what_was_open_when_it_armed():
    """Not a forced arming: a zone opening during the exit delay fails the
    arming as it always does, and the rule's contacts hear it."""
    world = World(house(exclude_open_zones=True))
    leave(world)
    world.advance(30 * 60)
    world.advance(121)  # arming, nothing open, nothing excluded
    assert world.states()["ground"] == "arming"
    world.set(WINDOW, "on")
    decision = world.advance(120)
    assert world.states()["ground"] == "disarmed"
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "hold_expired"
    assert outcome.detail["zones"] == "Window"


def test_one_rules_exclusion_is_not_told_as_anothers():
    """Two rules act in one decision: the second excluded nothing, and its
    contacts must not read that it did."""
    from custom_components.foyer.core.models import RuleActionKind

    config = house(exclude_open_zones=True, scenario_id="night", grace=0)
    second = rule(
        "switch_away",
        action=RuleActionKind.SWITCH,
        scenario_id="away",
        grace=0,
        notify_contact_ids=("anna",),
    )
    config = replace(config, rules=(*config.rules, second))
    world = World(config)
    world.set(WINDOW, "on")
    leave(world)
    decision = world.advance(30 * 60)
    told = {
        o.detail["rule_id"]: o.detail["outcome"]
        for o in _occurrences(decision, Moment.AUTO_OUTCOME)
    }
    assert told.get("empty_house") == "excluding"
    assert told.get("switch_away") != "excluding_switch"


def test_a_presence_rule_refused_keeps_its_word():
    """It said it would not try again: it does not, when the window shuts."""
    from custom_components.foyer.core.models import RuleTriggerKind

    world = World(house(kind=RuleTriggerKind.PRESENCE, entity_ids=(LUCA,), grace=0))
    world.person(LUCA, "not_home")
    world.advance(1)
    world.set(WINDOW, "on")
    decision = world.person(LUCA, "home")
    (outcome,) = _occurrences(decision, Moment.AUTO_OUTCOME)
    assert outcome.detail["outcome"] == "not_armed_once"
    world.set(WINDOW, "off")
    world.advance(5)
    assert world.states()["ground"] == "disarmed"
