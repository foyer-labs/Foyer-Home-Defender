"""What the log records, decided in core and tested without Home Assistant.

SPEC §10.1-10.3: categories, default verbosity, the incident id on every
related row, the restart gap, and the refusal that must not be silent.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.foyer.core.journal import (
    CATEGORY,
    SEVERITY,
    action_row,
    config_row,
    rows_for,
)
from custom_components.foyer.core.models import (
    ArmPolicy,
    Channel,
    LogCategory,
    LogSettings,
    LogSeverity,
    Moment,
    Outcome,
    Startup,
)

from .helpers import DOOR, WINDOW, World


def rows(world: World, decision, *, old: str | None = None):
    return rows_for(
        world.last_event,
        decision,
        world.config,
        old_state=old,
        was_active=world.was_active,
    )


class Logged(World):
    """A World that remembers what a runtime would, to build its rows."""

    last_event = None
    was_active: frozenset[str] = frozenset()

    def send(self, event):  # type: ignore[override]
        self.last_event = event
        self.was_active = self.state.active_zones
        return super().send(event)


def armed_house() -> Logged:
    world = Logged()
    world.arm("away")
    world.advance(30)
    return world


# --- the tables themselves ------------------------------------------------------


def test_every_moment_has_a_category_and_a_severity():
    """A moment added without one would silently vanish from the log."""
    assert set(CATEGORY) == set(Moment)
    assert set(SEVERITY) == set(Moment)


def test_default_verbosity_matches_the_spec():
    """§10.2: every category on, except zone activity while disarmed."""
    log = LogSettings()
    for category in LogCategory:
        assert log.is_enabled(category.value) is (
            category is not LogCategory.ZONE_DISARMED
        )
        assert log.retention(category.value) == 30


def test_a_setting_equal_to_the_default_is_still_honoured():
    log = LogSettings(enabled={"zone_disarmed": True}, retention_days={"alarm": 90})
    assert log.is_enabled("zone_disarmed") is True
    assert log.retention("alarm") == 90
    assert log.retention("arming") == 30


# --- rows from a decision -------------------------------------------------------


def test_arming_is_one_arming_row_per_area_with_who_and_where():
    world = Logged()
    decision = world.arm("away", channel="ha_ui")
    armed = [r for r in rows(world, decision) if r.event_type == "armed"]
    # An "armed" row lands when the exit delay is over; the request itself is
    # the arming of each area.
    assert all(r.category is LogCategory.ARMING for r in armed)
    assert all(r.channel == "ha_ui" for r in armed)
    assert all(r.outcome == Outcome.OK.value for r in armed)


def test_a_trigger_is_an_alarm_row_and_carries_the_incident_id():
    world = armed_house()
    decision = world.set(WINDOW, "on")
    written = rows(world, decision, old="off")
    alarm = [r for r in written if r.category is LogCategory.ALARM]
    assert {r.event_type for r in alarm} >= {"triggered", "incident_opened"}
    assert all(r.incident_id == world.state.incident.id for r in alarm)
    assert any(r.severity is LogSeverity.ALARM for r in alarm)


def test_a_technical_alarm_never_carries_an_incident_id():
    """§5.5: a different channel, a different acknowledgement, never merged."""
    world = Logged()
    world.config = replace(
        world.config,
        zones=tuple(
            replace(z, channel=Channel.TECHNICAL, always_on=True)
            if z.id == "window"
            else z
            for z in world.config.zones
        ),
    )
    decision = world.set(WINDOW, "on")
    technical = [r for r in rows(world, decision) if r.event_type == "technical_raised"]
    assert technical and all(r.incident_id is None for r in technical)
    assert technical[0].category is LogCategory.ALARM


def test_zone_movement_is_filed_by_whether_its_area_was_watching():
    world = Logged()
    disarmed = rows(world, world.set(DOOR, "on"), old="off")
    assert [r.category for r in disarmed if r.event_type == "zone_state"] == [
        LogCategory.ZONE_DISARMED
    ]
    world.set(DOOR, "off")
    world.arm("away")
    world.advance(30)
    armed = rows(world, world.set(DOOR, "on"), old="off")
    zone_rows = [r for r in armed if r.event_type == "zone_state"]
    assert [r.category for r in zone_rows] == [LogCategory.ZONE_ARMED]
    assert zone_rows[0].detail["from"] == "off"
    assert zone_rows[0].detail["to"] == "on"


def test_a_refused_arming_says_why_and_which_zone():
    """Why it did not arm last night is a question users ask (§9.4)."""
    world = Logged()
    world.config = replace(
        world.config,
        zones=tuple(
            replace(z, arm_policy=ArmPolicy.BLOCK) if z.id == "window" else z
            for z in world.config.zones
        ),
    )
    world.set(WINDOW, "on")
    decision = world.arm("away")
    assert not decision.accepted
    refusal = [r for r in rows(world, decision) if r.event_type == "arm_rejected"]
    assert len(refusal) == 1
    assert refusal[0].category is LogCategory.ARMING
    assert refusal[0].outcome == Outcome.BLOCKED.value
    assert refusal[0].detail["reason"] == decision.reason.value
    assert refusal[0].detail["blocking_zones"] == ["window"]


def test_a_bypass_is_security_not_arming():
    world = Logged()
    decision = world.bypass("window", channel="ha_ui")
    bypass = [r for r in rows(world, decision) if r.event_type == "zone_bypassed"]
    assert bypass and bypass[0].category is LogCategory.SECURITY
    assert bypass[0].severity is LogSeverity.WARNING


def test_the_restart_gap_is_one_system_unavailable_row_from_t1_to_t2():
    """INV-3: the log must never imply the house was covered when it was not."""
    world = Logged()
    down = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    decision = world.send(Startup(down_since=down, cause="ha_start"))
    gap = [r for r in rows(world, decision) if r.category is LogCategory.SYSTEM]
    assert [r.event_type for r in gap] == ["system_unavailable"]
    assert gap[0].severity is LogSeverity.WARNING
    assert gap[0].detail["down_since"] == down.isoformat()
    assert gap[0].detail["cause"] == "ha_start"


def test_a_tick_that_changes_nothing_writes_nothing():
    world = armed_house()
    assert rows(world, world.advance(1)) == ()


# --- rows the runtime builds ----------------------------------------------------


def test_a_failed_action_is_a_warning_naming_what_failed():
    row = action_row(
        datetime(2026, 9, 14, 19, 32, tzinfo=UTC),
        action_id="a1",
        kind="siren",
        moment=Moment.TRIGGERED,
        ok=False,
        error="service not found",
        incident_id="i1",
    )
    assert row.category is LogCategory.ACTION
    assert row.outcome == Outcome.FAILED.value
    assert row.severity is LogSeverity.WARNING
    assert row.incident_id == "i1"
    assert row.detail["error"] == "service not found"


def test_a_config_edit_records_who_and_a_summary():
    row = config_row(
        datetime(2026, 9, 14, 19, 32, tzinfo=UTC),
        operation="save",
        kind="zone",
        item_id="z1",
        user_name="Luca",
        channel="ha_ui",
        changes={"zones": {"changed": {"Kitchen window": ["arm_policy"]}}},
    )
    assert row.category is LogCategory.CONFIG
    assert row.user_name == "Luca"
    assert row.detail["changes"]["zones"]["changed"] == {
        "Kitchen window": ["arm_policy"]
    }


def test_an_attribute_only_report_is_not_zone_activity():
    """Home Assistant reports a battery level as a state change; the log must
    not pretend a door opened and closed every time a radio says hello."""
    world = Logged()
    world.set(DOOR, "on")
    decision = world.set(DOOR, "on", battery_level=61)

    assert [
        r for r in rows(world, decision, old="on") if r.event_type == "zone_state"
    ] == []


def test_a_numeric_trigger_crossing_its_band_is_recorded_though_the_state_is_the_same():
    """The opposite case, and the reason the check is not simply "did the
    state string change": a numeric attribute trigger moves nothing visible."""
    from custom_components.foyer.core.models import NumericOperator, NumericTrigger

    world = Logged()
    world.config = replace(
        world.config,
        zones=tuple(
            replace(
                z,
                trigger=NumericTrigger(
                    operator=NumericOperator.GT, value=30.0, attribute="level"
                ),
            )
            if z.id == "window"
            else z
            for z in world.config.zones
        ),
    )
    world.set(WINDOW, "on", level=10)
    decision = world.set(WINDOW, "on", level=40)

    zone_rows = [
        r for r in rows(world, decision, old="on") if r.event_type == "zone_state"
    ]
    assert len(zone_rows) == 1
    assert zone_rows[0].detail["active"] is True


def test_a_configuration_reload_is_not_an_outage():
    """Saving a setting reloads the integration. Recording that as "Foyer was
    not running", in warning, next to the change that caused it, teaches
    people to ignore the row that matters."""
    world = Logged()
    decision = world.send(
        Startup(down_since=world.now - timedelta(seconds=1), cause="reload")
    )

    [row] = [r for r in rows(world, decision) if r.category is LogCategory.SYSTEM]
    assert row.event_type == "reloaded"
    assert row.severity is LogSeverity.INFO


def test_a_long_gap_is_an_outage_whatever_caused_it():
    """The integration can also be disabled and re-enabled by hand, and that
    is an hour in which the house was not protected."""
    world = Logged()
    decision = world.send(
        Startup(down_since=world.now - timedelta(hours=1), cause="reload")
    )

    [row] = [r for r in rows(world, decision) if r.category is LogCategory.SYSTEM]
    assert row.event_type == "system_unavailable"
    assert row.severity is LogSeverity.WARNING
    assert row.detail["gap_seconds"] == "3600"
