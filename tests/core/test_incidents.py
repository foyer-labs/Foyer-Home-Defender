"""Incidents: one alarm, one unit, one acknowledgement (SPEC §5.6, §19)."""

from __future__ import annotations

from dataclasses import replace
import json

from custom_components.foyer.core.models import (
    AcknowledgeIncident,
    AreaState,
    CodePolicy,
    Moment,
    Reason,
    TimerKind,
)
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import BATH, DOOR, HALL, PATIO, TAMPER, WINDOW, World


def armed(scenario: str = "away") -> World:
    world = World()
    world.arm(scenario)
    world.advance(30)
    assert world.area("ground").state is AreaState.ARMED
    return world


def test_the_first_trigger_opens_an_incident_and_carries_its_id():
    world = armed()
    decision = world.set(WINDOW, "on")

    incident = world.state.incident
    assert incident is not None
    assert incident.zone_ids == ("window",)
    assert incident.opened_at == world.now
    triggered, opened = decision.occurrences
    assert (triggered.moment, opened.moment) == (
        Moment.TRIGGERED,
        Moment.INCIDENT_OPENED,
    )
    assert triggered.incident_id == opened.incident_id == incident.id


def test_a_second_zone_joins_without_restarting_anything():
    """§19: a second trigger joins the open incident."""
    world = armed()
    world.set(WINDOW, "on")
    incident_id = world.state.incident.id
    siren = world.area("ground").timer
    world.advance(20)
    decision = world.set(PATIO, "on")

    assert world.state.incident.id == incident_id
    assert world.state.incident.zone_ids == ("window", "patio")
    assert world.area("ground").timer == siren  # the siren is not restarted
    assert decision.moments == (Moment.INCIDENT_JOINED,)
    assert decision.occurrences[0].zone_ids == ("patio",)


def test_zones_in_several_areas_make_one_incident():
    world = armed()
    world.set(WINDOW, "on")
    world.set(BATH, "on")  # upstairs, instant

    incident = world.state.incident
    assert incident.area_ids == ("ground", "upstairs")
    assert incident.zone_ids == ("window", "bath")


def test_an_entry_delay_does_not_open_an_incident():
    """Part 2 decision 2: coming home is not an incident."""
    world = armed()
    world.set(DOOR, "on")
    world.set(HALL, "on")
    assert world.state.incident is None
    world.disarm()
    assert world.state.incident is None


def test_an_expired_entry_opens_it_with_the_whole_entry_route():
    world = armed()
    world.set(DOOR, "on")
    world.set(HALL, "on")
    world.advance(30)

    assert world.state.incident.zone_ids == ("door", "hall")


def test_disarming_acknowledges_and_closes_the_incident():
    """Part 2 decision 3: disarming is the acknowledgement (§7.2)."""
    world = armed()
    world.set(WINDOW, "on")
    incident_id = world.state.incident.id
    decision = world.disarm(channel="ha_ui")

    assert world.state.incident is None
    moments = decision.moments
    assert Moment.INCIDENT_ACKNOWLEDGED in moments
    assert moments[-1] is Moment.INCIDENT_CLOSED
    ack = next(
        o for o in decision.occurrences if o.moment is Moment.INCIDENT_ACKNOWLEDGED
    )
    assert ack.detail["via"] == "disarm" and ack.channel == "ha_ui"
    # Every related occurrence carries the id, the disarm included; the
    # areas the incident never touched are not part of it.
    related = [
        o
        for o in decision.occurrences
        if o.area_id == "ground" or o.moment.value.startswith("incident_")
    ]
    assert {o.incident_id for o in related} == {incident_id}
    assert {o.incident_id for o in decision.occurrences if o.area_id == "upstairs"} == {
        None
    }


def test_one_acknowledgement_then_the_areas_settling_closes_it():
    """§19: one acknowledgement closes everything, once the areas settle."""
    world = armed()
    world.set(WINDOW, "on")
    world.set(BATH, "on")
    decision = world.send(AcknowledgeIncident(channel="ha_ui"))

    assert decision.accepted
    assert world.state.incident.acknowledged  # both areas still triggered
    world.advance(180)  # siren cutoff: both back to armed

    assert world.states()["ground"] == "armed"
    assert world.state.incident is None


def test_an_unacknowledged_incident_stays_open_after_the_sounders_stop():
    world = armed()
    world.set(WINDOW, "on")
    world.advance(180)

    assert world.area("ground").state is AreaState.ARMED
    assert world.area("ground").memory
    assert world.state.incident is not None


def test_disarming_one_area_acknowledges_but_the_other_keeps_it_open():
    world = armed()
    world.set(WINDOW, "on")
    world.set(BATH, "on")
    world.disarm("ground")

    incident = world.state.incident
    assert incident is not None and incident.acknowledged
    assert world.area("upstairs").state is AreaState.TRIGGERED
    world.disarm("upstairs")
    assert world.state.incident is None


def test_disarming_an_area_the_incident_never_touched_is_no_acknowledgement():
    """Decision 57: whoever disarms the bedrooms has not seen the perimeter."""
    world = armed()
    world.set(BATH, "on")  # upstairs only
    decision = world.disarm("garage")

    assert Moment.INCIDENT_ACKNOWLEDGED not in decision.moments
    assert not world.state.incident.acknowledged


def test_a_zone_joining_after_the_acknowledgement_clears_it():
    """Part 2 decision 8: someone must hear that a second zone went."""
    world = armed()
    world.set(WINDOW, "on")
    world.send(AcknowledgeIncident(channel="ha_ui"))
    decision = world.set(PATIO, "on")

    incident = world.state.incident
    assert decision.moments == (Moment.INCIDENT_JOINED,)
    assert not incident.acknowledged
    assert [a.via for a in incident.acknowledgements] == ["acknowledge"]  # kept

    decision = world.disarm()
    assert world.state.incident is None
    assert Moment.INCIDENT_ACKNOWLEDGED in decision.moments


def test_a_trigger_after_closure_opens_a_new_incident():
    world = armed()
    world.set(WINDOW, "on")
    first = world.state.incident.id
    world.send(AcknowledgeIncident())
    world.advance(180)  # closes
    world.set(WINDOW, "off")
    world.advance(1)
    world.set(WINDOW, "on")

    assert world.state.incident is not None
    assert world.state.incident.id != first
    assert world.state.incident_seq == 2


def test_a_24h_zone_on_a_disarmed_house_opens_an_incident():
    world = World()
    world.set(TAMPER, "on")
    assert world.state.incident.zone_ids == ("tamper",)
    world.advance(180)  # cutoff: back to disarmed, with memory
    assert world.area("ground").state is AreaState.DISARMED
    assert world.state.incident is not None
    world.send(AcknowledgeIncident())
    assert world.state.incident is None


def test_each_contributor_is_recorded_with_its_profile_and_severity():
    """§19: the highest-severity contributing profile supplies the escalation
    in Phase 4; part 3 fills the record as each zone joins."""
    world = armed()
    world.set(WINDOW, "on")
    world.set(BATH, "on")

    contributors = world.state.incident.contributors
    assert [(c.area_id, c.zone_id) for c in contributors] == [
        ("ground", "window"),
        ("upstairs", "bath"),
    ]
    # Both areas inherit the house's one profile (tests/core/helpers.py).
    assert all(c.profile_id == "default" and c.severity == 1 for c in contributors)
    # It sends a notification on armed and disarmed, not on an alarm.
    assert world.state.incident.actions_started == ()


def test_siren_cutoff_and_disarm_rows_carry_the_incident_id():
    world = armed()
    world.set(WINDOW, "on")
    incident_id = world.state.incident.id
    assert world.area("ground").timer.kind is TimerKind.SIREN
    cutoff = world.advance(180)
    assert cutoff.occurrences[0].moment is Moment.SIREN_CUTOFF
    assert cutoff.occurrences[0].incident_id == incident_id


def test_nothing_to_acknowledge_and_the_code_check():
    world = armed()
    assert world.send(AcknowledgeIncident()).reason is Reason.NOTHING_TO_ACKNOWLEDGE

    coded = World(replace(World().config, code_policy=CodePolicy(acknowledge=True)))
    coded.arm("away")
    coded.advance(30)
    coded.set(WINDOW, "on")
    assert coded.send(AcknowledgeIncident()).reason is Reason.CODE_REQUIRED
    assert not coded.state.incident.acknowledged


def test_an_incident_survives_a_restart():
    world = armed()
    world.set(WINDOW, "on")
    world.send(AcknowledgeIncident(channel="ha_ui"))
    world.set(BATH, "on")

    document = json.loads(json.dumps(state_to_dict(world.state)))
    assert state_from_dict(document, world.config) == world.state
