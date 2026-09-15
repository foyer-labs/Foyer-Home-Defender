"""Verification groups, cross-zone and trigger counting: one engine (§4.2, §4.8)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import json

from custom_components.foyer.core.engine import next_wakeup
from custom_components.foyer.core.models import (
    AreaState,
    ArmPolicy,
    Group,
    Moment,
)
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import BATH, DOOR, HALL, WINDOW, World, make_house, zone

PIR1, PIR2, PIR3 = (f"binary_sensor.pir{i}" for i in (1, 2, 3))
VERIFICATION = {
    Moment.VERIFICATION_PENDING,
    Moment.VERIFICATION_SATISFIED,
    Moment.VERIFICATION_EXPIRED,
}


def house(*groups: Group, **zone_changes):
    """The test house plus three open-plan PIRs; zone_changes by zone id."""
    config = make_house()
    pirs = tuple(
        zone(f"pir{i}", f"binary_sensor.pir{i}", "ground", arm_policy=ArmPolicy.IGNORE)
        for i in (1, 2, 3)
    )
    zones = tuple(
        replace(z, **zone_changes[z.id]) if z.id in zone_changes else z
        for z in (*config.zones, *pirs)
    )
    return replace(config, zones=zones, groups=groups)


def open_plan(**changes) -> Group:
    group = Group("open", "Open plan", "ground", ("pir1", "pir2", "pir3"), 2, 60)
    return replace(group, **changes)


def armed(config, scenario: str = "away") -> World:
    world = World(config)
    world.arm(scenario)
    world.advance(30)
    assert world.area("ground").state is AreaState.ARMED
    return world


def pulse(world: World, entity_id: str):
    decision = world.set(entity_id, "on")
    world.set(entity_id, "off")
    return decision


def verification(decision):
    return [o for o in decision.occurrences if o.moment in VERIFICATION]


# --- N of M -------------------------------------------------------------------------


def test_a_member_alone_alarms_and_the_group_waits():
    """Part 2 decision 5: a non-suppressing member alarms normally."""
    world = armed(house(open_plan()))
    decision = pulse(world, PIR1)

    assert decision.moments == (
        Moment.VERIFICATION_PENDING,
        Moment.TRIGGERED,
        Moment.INCIDENT_OPENED,
    )
    pending = decision.occurrences[0]
    assert (pending.group_id, dict(pending.detail)) == (
        "open",
        {"verification": "group", "count": "1", "n": "2", "window": "60"},
    )
    assert world.area("ground").state is AreaState.TRIGGERED


def test_n_of_m_within_the_window_is_satisfied():
    world = armed(house(open_plan()))
    pulse(world, PIR1)
    world.advance(30)
    decision = pulse(world, PIR2)

    satisfied = verification(decision)
    assert [o.moment for o in satisfied] == [Moment.VERIFICATION_SATISFIED]
    assert satisfied[0].zone_ids == ("pir1", "pir2")
    assert satisfied[0].detail["count"] == "2"
    assert "group:open" not in world.state.windows  # a new window starts empty
    contributors = world.state.incident.contributors
    assert {c.group_id for c in contributors} == {"open"}


def test_the_same_member_twice_does_not_satisfy_a_group():
    world = armed(house(open_plan()))
    pulse(world, PIR1)
    world.advance(5)
    decision = pulse(world, PIR1)
    assert decision.occurrences[0].moment is Moment.VERIFICATION_PENDING
    assert decision.occurrences[0].detail["count"] == "1"


def test_the_window_expires():
    world = armed(house(open_plan(suppress_members=True)))
    pulse(world, PIR1)
    due = world.now + timedelta(seconds=60, microseconds=1)
    assert next_wakeup(world.snapshot(), world.config, world.now) == due

    world.advance(59)
    assert "group:open" in world.state.windows
    decision = world.advance(2)
    assert [o.moment for o in decision.occurrences] == [Moment.VERIFICATION_EXPIRED]
    assert decision.occurrences[0].zone_ids == ("pir1",)
    assert world.state.windows == {}

    later = pulse(world, PIR2)
    assert later.occurrences[0].detail["count"] == "1"
    assert world.area("ground").state is AreaState.ARMED  # never satisfied


def test_suppressed_members_do_nothing_until_the_group_is_satisfied():
    world = armed(house(open_plan(suppress_members=True)))
    decision = pulse(world, PIR1)

    assert decision.moments == (Moment.VERIFICATION_PENDING,)
    assert world.area("ground").state is AreaState.ARMED
    assert world.state.incident is None

    world.advance(20)
    decision = pulse(world, PIR2)
    assert decision.moments[0] is Moment.VERIFICATION_SATISFIED
    assert world.area("ground").state is AreaState.TRIGGERED
    assert world.area("ground").causes == ("pir1", "pir2")  # the held one fires too
    assert world.state.incident.zone_ids == ("pir1", "pir2")


def test_members_in_other_areas_act_in_their_own():
    """Part 2 decision 9."""
    group = open_plan(members=("pir1", "bath"), suppress_members=True)
    world = armed(house(group))
    pulse(world, PIR1)
    pulse(world, BATH)

    assert world.area("ground").state is AreaState.TRIGGERED
    assert world.area("upstairs").state is AreaState.TRIGGERED
    assert world.state.incident.area_ids == ("ground", "upstairs")


def test_a_member_whose_area_is_not_armed_does_not_count():
    world = armed(house(open_plan(members=("pir1", "bath"))), "night")  # ground only
    decision = pulse(world, BATH)  # upstairs is disarmed
    assert verification(decision) == []
    decision = pulse(world, PIR1)
    assert decision.occurrences[0].detail["count"] == "1"


def test_coming_home_never_counts_towards_a_group():
    """Part 2 decision 6: activations the entry delay absorbs act normally."""
    group = open_plan(members=("door", "hall", "window"))
    world = armed(house(group))
    for entity_id in (DOOR, HALL):
        decision = world.set(entity_id, "on")
        assert verification(decision) == [], entity_id
    assert world.area("ground").state is AreaState.ENTRY
    # An instant zone during entry would alarm at once: that one counts.
    decision = world.set(WINDOW, "on")
    assert verification(decision)[0].detail["count"] == "1"


def test_disarming_forgets_pending_activations():
    world = armed(house(open_plan(suppress_members=True)))
    pulse(world, PIR1)
    world.disarm()
    assert world.state.windows == {}


def test_windows_survive_a_restart():
    world = armed(house(open_plan(suppress_members=True)))
    pulse(world, PIR1)

    document = json.loads(json.dumps(state_to_dict(world.state)))
    restored = state_from_dict(document, world.config)
    assert restored == world.state
    assert restored.windows["group:open"][0].held


# --- cross-zone is a 2-of-2 group ----------------------------------------------------


CROSS = house(window={"cross_zone_id": "pir1", "cross_zone_window": 60})
EXPLICIT = house(Group("grp-pair", "Pair", "ground", ("pir1", "window"), 2, 60))


def _normalised(decision) -> str:
    return repr(decision).replace("cross:pir1+window", "G").replace("grp-pair", "G")


def _script(world: World) -> list[str]:
    """The same events in both worlds: alone, both ways round, expiry, re-arm."""
    out = []

    def step(decision):
        out.append(_normalised(decision))

    step(world.arm("away"))
    step(world.advance(30))
    step(world.set(PIR1, "on"))  # the partner first: the pair is symmetric
    step(world.advance(10))
    step(world.set(WINDOW, "on"))  # confirms within the window
    step(world.set(PIR1, "off"))
    step(world.set(WINDOW, "off"))
    step(world.disarm())
    step(world.arm("away"))
    step(world.advance(30))
    step(world.set(WINDOW, "on"))  # alone this time
    step(world.advance(61))  # the window runs out
    step(world.set(PIR1, "on"))  # too late: a new window
    step(world.disarm())
    return out


def test_cross_zone_gives_the_same_decisions_as_the_equivalent_2_of_2_group():
    """§19: the assertion that keeps both configuration surfaces on one engine."""
    cross, explicit = _script(World(CROSS)), _script(World(EXPLICIT))
    assert len(cross) == len(explicit)
    for step, (a, b) in enumerate(zip(cross, explicit, strict=True)):
        assert a == b, f"step {step} differs"


def test_a_cross_zone_pair_is_symmetric_and_never_suppresses():
    """Part 2 decision 4."""
    world = armed(CROSS)
    decision = pulse(world, PIR1)  # PIR1 declares nothing; it is still in the pair
    assert decision.occurrences[0].moment is Moment.VERIFICATION_PENDING
    assert decision.occurrences[0].group_id == "cross:pir1+window"
    assert world.area("ground").state is AreaState.TRIGGERED  # alone, it alarms


# --- trigger counting ---------------------------------------------------------------


def test_a_zone_needs_its_count_within_the_window():
    world = armed(house(pir1={"trigger_count": 3, "trigger_window": 60}))
    for count in (1, 2):
        decision = pulse(world, PIR1)
        assert decision.moments == (Moment.VERIFICATION_PENDING,)
        assert decision.occurrences[0].detail == {
            "verification": "count",
            "count": str(count),
            "n": "3",
            "window": "60",
        }
        assert world.area("ground").state is AreaState.ARMED
        world.advance(10)
    decision = pulse(world, PIR1)
    assert decision.moments[:2] == (Moment.VERIFICATION_SATISFIED, Moment.TRIGGERED)


def test_a_trigger_count_expires_like_a_group():
    world = armed(house(pir1={"trigger_count": 2, "trigger_window": 30}))
    pulse(world, PIR1)
    world.advance(31)
    assert world.state.windows == {}
    pulse(world, PIR1)
    assert world.area("ground").state is AreaState.ARMED


def test_a_counted_delayed_zone_still_opens_the_entry_delay_at_once():
    """Part 2 decision 12: counting follows the group rule."""
    world = armed(house(door={"trigger_count": 2}))
    decision = world.set(DOOR, "on")
    assert decision.moments == (Moment.ENTRY_STARTED,)
