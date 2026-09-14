"""Shared builders for the pure test suite. Nothing here may import homeassistant."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.foyer.core.models import (
    Area,
    AreaState,
    CodePolicy,
    FoyerConfig,
    Moment,
    NotificationAction,
    Scenario,
    StateTrigger,
    SystemSnapshot,
    Zone,
)

NOW = datetime(2026, 9, 14, 19, 32, tzinfo=UTC)
ZONE_ENTITY = "binary_sensor.front_door"


def make_config() -> FoyerConfig:
    return FoyerConfig(
        areas=(Area(id="home", name="Home", ha_state_when_armed="armed_away"),),
        zones=(
            Zone(
                id="door",
                name="Front door",
                entity_id=ZONE_ENTITY,
                area_id="home",
                trigger=StateTrigger(states=frozenset({"on"})),
            ),
        ),
        scenarios=(
            Scenario(
                id="away",
                name="Away",
                areas=("home",),
                ha_master_state="armed_away",
            ),
        ),
        actions=(
            NotificationAction(
                id="notify",
                moments=frozenset({Moment.ARMED, Moment.DISARMED, Moment.ZONE_FAULT}),
            ),
        ),
        code_policy=CodePolicy(arm=False, disarm=False),
    )


def snapshot(
    state: AreaState = AreaState.DISARMED,
    zone_state: str | None = "off",
    scenario: str | None = None,
) -> SystemSnapshot:
    return SystemSnapshot(
        area_states={"home": state},
        active_scenario_id=scenario,
        entity_states={ZONE_ENTITY: zone_state},
    )
