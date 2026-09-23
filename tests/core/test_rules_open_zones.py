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
