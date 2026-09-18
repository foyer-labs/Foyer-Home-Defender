"""Manual and timed temporary bypass (SPEC §5.4, §16, part 3 decisions 9-10).

A zone excluded and forgotten is exactly the window somebody comes through,
which is why the timed form exists and why the return is announced.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from custom_components.foyer.core.engine import next_wakeup
from custom_components.foyer.core.models import (
    AreaState,
    BypassReason,
    BypassZone,
    CodePolicy,
    CodeResult,
    Moment,
    Reason,
)
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import WINDOW, World, user


def bypassed(world: World) -> dict[str, str]:
    return {z: r.value for z, r in world.state.bypassed.items()}


def test_a_manual_bypass_lets_an_open_zone_arm():
    world = World(entities={WINDOW: "on"})
    assert world.arm("night").reason is Reason.ZONE_OPEN

    decision = world.bypass("window")
    assert decision.accepted
    assert bypassed(world) == {"window": "manual"}
    [occurrence] = decision.occurrences
    assert occurrence.moment is Moment.ZONE_BYPASSED
    assert occurrence.detail["bypass"] == "manual"
    assert world.arm("night").accepted


def test_a_bypassed_zone_does_not_alarm():
    world = World()
    world.bypass("window")
    world.arm("night")
    world.advance(30)

    world.set(WINDOW, "on")
    assert world.area("ground").state is AreaState.ARMED


def test_closing_the_zone_does_not_cancel_a_manual_bypass():
    """Part 3 decision 10: an automatic bypass rejoins on closing; a manual
    one does not, because being closed now is the reason it was excluded."""
    world = World(entities={WINDOW: "on"})
    world.bypass("window")
    world.set(WINDOW, "off")

    assert bypassed(world) == {"window": "manual"}
    assert Moment.ZONE_REJOINED not in world.last.moments


def test_an_untimed_bypass_ends_with_the_arming():
    world = World()
    world.bypass("window")
    world.arm("night")
    world.advance(30)
    world.disarm()

    assert bypassed(world) == {}


def test_a_timed_bypass_outlives_the_disarm_and_returns_on_time():
    world = World()
    world.bypass("window", seconds=3600)
    assert world.state.bypass_until["window"] == world.now + timedelta(seconds=3600)

    world.arm("night")
    world.advance(30)
    world.disarm()
    assert bypassed(world) == {"window": "manual"}  # survives the disarm

    world.advance(3600 - 30)
    assert bypassed(world) == {}
    [rejoined] = [o for o in world.last.occurrences if o.moment is Moment.ZONE_REJOINED]
    assert rejoined.zone_id == "window"
    assert rejoined.detail == {"bypass": "manual", "cause": "expired"}


def test_the_scheduler_is_told_when_a_timed_bypass_ends():
    world = World()
    world.bypass("window", seconds=600)
    due = next_wakeup(world.snapshot(), world.config, world.now)
    assert due == world.now + timedelta(seconds=600)


def test_a_timed_bypass_survives_a_restart_and_still_returns_on_time():
    """INV-3: the zone comes back even if Home Assistant restarted meanwhile,
    which is the case where forgetting it matters most."""
    world = World()
    world.bypass("window", seconds=600)

    restored = state_from_dict(state_to_dict(world.state), world.config)
    assert restored.bypassed == world.state.bypassed
    assert restored.bypass_until == world.state.bypass_until

    world.state = restored
    assert next_wakeup(world.snapshot(), world.config, world.now) == (
        world.now + timedelta(seconds=600)
    )
    world.advance(600)
    assert bypassed(world) == {}
    assert any(o.moment is Moment.ZONE_REJOINED for o in world.last.occurrences)


def test_unbypassing_puts_the_zone_back():
    world = World()
    world.bypass("window", seconds=600)
    decision = world.bypass("window", bypass=False)

    assert decision.accepted
    assert bypassed(world) == {} and world.state.bypass_until == {}
    [occurrence] = decision.occurrences
    assert occurrence.moment is Moment.ZONE_REJOINED
    assert occurrence.detail == {"bypass": "manual", "cause": "manual"}


def test_a_zone_that_may_not_be_bypassed_is_refused():
    """A tamper zone is not bypassable: §4.3 sets it and the engine enforces it."""
    world = World()
    decision = world.bypass("tamper")

    assert not decision.accepted
    assert decision.reason is Reason.ZONE_NOT_BYPASSABLE
    assert decision.blocking_zones == ("tamper",)
    assert bypassed(world) == {}


def test_an_unknown_zone_is_refused():
    world = World()
    assert world.bypass("nope").reason is Reason.UNKNOWN_ZONE


def test_bypassing_twice_is_refused_rather_than_silently_renewed():
    world = World()
    world.bypass("window")
    assert world.bypass("window").reason is Reason.INVALID_STATE
    assert world.bypass("patio", bypass=False).reason is Reason.INVALID_STATE


def test_an_automatic_bypass_can_be_cleared_by_hand():
    """Auto and forced bypasses are the engine's; letting a zone back in is
    the user's, whichever put it out."""
    world = World(entities={WINDOW: "on"})
    world.arm("night", force=True)
    assert bypassed(world)["window"] == BypassReason.FORCED.value

    assert world.bypass("window", bypass=False).accepted
    assert "window" not in bypassed(world)


def test_excluding_a_zone_asks_for_the_code_the_policy_wants():
    """§8.2: excluding a zone is the one action that leaves a chosen part of
    the house unwatched while the rest is armed, so it needs a code."""
    world = World()
    world.config = replace(
        world.config, code_policy=CodePolicy(bypass_zone=True), users=(user(),)
    )
    decision = world.send(BypassZone("window"))

    assert not decision.accepted
    assert decision.reason is Reason.CODE_REQUIRED
    assert bypassed(world) == {}

    accepted = world.bypass("window", code=CodeResult.VALID, user_id="luca")
    assert accepted.accepted
    assert bypassed(world)["window"] == BypassReason.MANUAL.value


def test_the_policy_is_inert_until_somebody_holds_a_code():
    """Decision 78. Failing closed with no codes at all would not protect the
    house; it would only make it impossible to disarm."""
    world = World()
    world.config = replace(world.config, code_policy=CodePolicy(bypass_zone=True))
    assert world.send(BypassZone("window")).accepted


def test_a_bypassed_zone_still_reports_a_fault():
    """INV-4: excluding a zone from the alarm does not make it healthy."""
    world = World()
    world.bypass("window")
    decision = world.set(WINDOW, None)

    assert [o.moment for o in decision.occurrences] == [Moment.ZONE_FAULT]
    assert "window" in world.state.faults
