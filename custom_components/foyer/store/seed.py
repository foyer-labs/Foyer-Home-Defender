"""The Phase 0 configuration, built from the config flow's answers.

Phase 0 wires exactly one area, one zone, one scenario and one action. The user
supplies the names, the zone entity and its trigger states (INV-5); everything
else is fixed here until the configuration pages exist.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
import uuid

from ..core.models import (
    Area,
    CodePolicy,
    FoyerConfig,
    Moment,
    NotificationAction,
    Scenario,
    StateTrigger,
    Zone,
)


def seed_config(
    *,
    area_name: str,
    scenario_name: str,
    zone_entity_id: str,
    zone_name: str,
    trigger_states: Iterable[str],
    new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> FoyerConfig:
    area = Area(id=new_id(), name=area_name, ha_state_when_armed="armed_away")
    return FoyerConfig(
        areas=(area,),
        zones=(
            Zone(
                id=new_id(),
                name=zone_name,
                entity_id=zone_entity_id,
                area_id=area.id,
                trigger=StateTrigger(states=frozenset(trigger_states)),
            ),
        ),
        scenarios=(
            Scenario(
                id=new_id(),
                name=scenario_name,
                areas=(area.id,),
                ha_master_state="armed_away",
            ),
        ),
        actions=(
            NotificationAction(
                id=new_id(),
                # armed/disarmed is the action chosen for Phase 0; zone_fault is
                # not optional, because INV-4 requires a fault to be announced.
                moments=frozenset({Moment.ARMED, Moment.DISARMED, Moment.ZONE_FAULT}),
            ),
        ),
        # No users or codes exist yet, so no operation can require one. The
        # engine enforces this policy and fails closed if it is ever set.
        code_policy=CodePolicy(arm=False, disarm=False),
    )
