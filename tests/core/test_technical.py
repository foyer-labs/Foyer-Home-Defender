"""The technical alarm channel (SPEC §5.5, §19): a separate machine."""

from __future__ import annotations

from dataclasses import replace
import json

from custom_components.foyer.core.engine import master_state
from custom_components.foyer.core.models import (
    AcknowledgeIncident,
    AcknowledgeTechnical,
    Actor,
    AreaState,
    Channel,
    CodePolicy,
    Moment,
    Reason,
    ZoneType,
)
from custom_components.foyer.core.presets import PRESETS
from custom_components.foyer.store.schema import state_from_dict, state_to_dict

from .helpers import DOOR, WINDOW, World, make_house, user, zone

SMOKE = "binary_sensor.kitchen_smoke"
LEAK = "binary_sensor.basement_leak"


def technical(zone_id: str, entity_id: str, area_id: str = "ground", **props):
    return zone(
        zone_id,
        entity_id,
        area_id,
        type=ZoneType.TECHNICAL,
        **{**PRESETS[ZoneType.TECHNICAL], **props},
    )


def house(**smoke_props):
    config = make_house()
    return replace(
        config,
        zones=(
            *config.zones,
            technical("smoke", SMOKE, **smoke_props),
            technical("leak", LEAK, "upstairs"),
        ),
    )


def world(**smoke_props) -> World:
    return World(house(**smoke_props))


def armed(scenario: str = "away") -> World:
    w = world()
    w.arm(scenario)
    w.advance(30)
    assert w.area("ground").state is AreaState.ARMED
    return w


def test_a_technical_zone_fires_while_disarmed():
    w = world()
    decision = w.set(SMOKE, "on")

    assert set(w.state.technical) == {"smoke"}
    assert decision.moments == (Moment.TECHNICAL_RAISED,)
    assert set(w.states().values()) == {"disarmed"}


def test_it_is_live_whatever_the_arming_state():
    for state_name, prepare in (
        ("arming", lambda w: w.arm("away")),
        ("armed", lambda w: (w.arm("away"), w.advance(30))),
        ("entry", lambda w: (w.arm("away"), w.advance(30), w.set(DOOR, "on"))),
        ("triggered", lambda w: (w.arm("away"), w.advance(30), w.set(WINDOW, "on"))),
    ):
        w = world()
        prepare(w)
        assert w.states()["ground"] == state_name
        w.set(SMOKE, "on")
        assert "smoke" in w.state.technical, state_name


def test_it_never_touches_any_area_or_the_master():
    """§19: it never changes any alarm_control_panel state."""
    w = armed()
    areas_before = dict(w.state.areas)
    master_before = master_state(w.state, w.config)

    w.set(SMOKE, "on")
    w.send(AcknowledgeTechnical())
    w.set(SMOKE, "off")

    assert dict(w.state.areas) == areas_before
    assert master_state(w.state, w.config) == master_before


def test_disarming_does_not_clear_it():
    w = armed()
    w.set(SMOKE, "on")
    w.set(SMOKE, "off")  # back to normal, not acknowledged: memory
    w.disarm()

    assert set(w.states().values()) == {"disarmed"}
    assert set(w.state.technical) == {"smoke"}
    assert not w.state.technical["smoke"].acknowledged


def test_acknowledged_while_active_clears_once_back_to_normal():
    w = world()
    w.set(SMOKE, "on")
    decision = w.send(AcknowledgeTechnical(Actor(channel="ha_ui")))

    assert decision.accepted
    assert decision.moments == (Moment.TECHNICAL_ACKNOWLEDGED,)
    alarm = w.state.technical["smoke"]
    assert alarm.acknowledged and alarm.acknowledged_channel == "ha_ui"

    cleared = w.set(SMOKE, "off")
    assert w.state.technical == {}
    assert cleared.moments == (Moment.TECHNICAL_CLEARED,)


def test_back_to_normal_first_then_acknowledged_clears_at_once():
    w = world()
    w.set(SMOKE, "on")
    w.set(SMOKE, "off")
    assert set(w.state.technical) == {"smoke"}  # memory

    decision = w.send(AcknowledgeTechnical())
    assert decision.moments == (
        Moment.TECHNICAL_ACKNOWLEDGED,
        Moment.TECHNICAL_CLEARED,
    )
    assert w.state.technical == {}


def test_one_acknowledgement_covers_every_pending_technical_alarm():
    """Part 2 decision 11."""
    w = world()
    w.set(SMOKE, "on")
    w.set(LEAK, "on")
    decision = w.send(AcknowledgeTechnical())

    assert decision.occurrences[0].zone_ids == ("smoke", "leak")
    assert all(a.acknowledged for a in w.state.technical.values())


def test_a_repeat_before_acknowledgement_is_announced_again():
    w = world()
    w.set(SMOKE, "on")
    since = w.state.technical["smoke"].since
    w.advance(10)
    w.set(SMOKE, "off")
    decision = w.set(SMOKE, "on")

    assert decision.moments == (Moment.TECHNICAL_RAISED,)
    assert decision.occurrences[0].detail["repeat"] == "true"
    assert w.state.technical["smoke"].since == since


def test_nothing_to_acknowledge_is_refused():
    decision = world().send(AcknowledgeTechnical())
    assert not decision.accepted
    assert decision.reason is Reason.NOTHING_TO_ACKNOWLEDGE


def test_acknowledgement_goes_through_the_code_check():
    """Acknowledging needs no code by default (decision 77) — unless the
    installation says otherwise, and somebody holds a code to say it with."""
    config = replace(house(), code_policy=CodePolicy(acknowledge=True), users=(user(),))
    w = World(config)
    w.set(SMOKE, "on")
    decision = w.send(AcknowledgeTechnical())

    assert decision.reason is Reason.CODE_REQUIRED
    assert not w.state.technical["smoke"].acknowledged


def test_it_never_joins_an_intrusion_incident():
    w = armed()
    w.set(WINDOW, "on")
    incident = w.state.incident
    assert incident is not None

    decision = w.set(SMOKE, "on")

    assert w.state.incident == incident  # nothing joined
    assert decision.occurrences[0].incident_id is None
    assert "smoke" not in w.state.incident.zone_ids


def test_both_can_be_active_and_are_acknowledged_separately():
    w = armed()
    w.set(WINDOW, "on")
    w.set(SMOKE, "on")

    w.send(AcknowledgeIncident())
    assert not w.state.technical["smoke"].acknowledged
    w.send(AcknowledgeTechnical())
    assert w.state.incident is not None  # still triggered: not closed yet
    assert w.state.incident.acknowledged


def test_bypass_has_no_authority_over_it():
    """A technical zone excluded by a forced arm while in fault still fires
    once it comes back: the channel is live whatever the areas do."""
    w = World(house(bypassable=True))
    w.set(SMOKE, "unavailable")
    decision = w.arm("away", force=True)
    assert decision.accepted and "smoke" in decision.bypassed_zones

    w.set(SMOKE, "on")
    assert "smoke" in w.state.technical


def test_a_faulted_technical_zone_blocks_arming_its_area():
    """Part 2 decision 1: INV-4 as for every zone."""
    w = World(house(), entities={SMOKE: "unavailable"})
    decision = w.arm("away")
    assert decision.reason is Reason.ZONE_FAULT
    assert decision.blocking_zones == ("smoke",)

    allowed = World(house(allow_arm_when_faulted=True), entities={SMOKE: "unavailable"})
    assert allowed.arm("away").accepted


def test_an_active_technical_zone_never_counts_as_open_at_arming():
    w = world()
    w.set(SMOKE, "on")
    assert w.arm("away").accepted


def test_the_technical_notification_is_an_intent():
    """Part 2 decision 10: a technical alarm is never silent."""
    config = house()
    profile = config.profiles[0]
    action = replace(
        profile.actions[0],
        moments=profile.actions[0].moments | {Moment.TECHNICAL_RAISED},
    )
    w = World(replace(config, profiles=(replace(profile, actions=(action,)),)))
    decision = w.set(SMOKE, "on")

    [intent] = decision.actions
    assert intent.moment is Moment.TECHNICAL_RAISED
    assert intent.placeholders["zone"] == "Smoke"


def test_technical_state_survives_a_restart():
    w = world()
    w.set(SMOKE, "on")
    w.set(LEAK, "on")
    w.send(AcknowledgeTechnical())
    w.set(LEAK, "off")  # cleared
    w.set(SMOKE, "on")  # still active, acknowledged

    document = json.loads(json.dumps(state_to_dict(w.state)))
    assert state_from_dict(document, w.config) == w.state


def test_technical_channel_is_a_zone_property_not_its_type():
    """Decision 36: the engine reads channel, never the type label."""
    config = make_house()
    relabelled = replace(
        config,
        zones=(
            *config.zones,
            zone(
                "odd",
                SMOKE,
                "ground",
                type=ZoneType.INSTANT,  # a label only
                channel=Channel.TECHNICAL,
                always_on=True,
            ),
        ),
    )
    w = World(relabelled)
    w.set(SMOKE, "on")
    assert "odd" in w.state.technical
