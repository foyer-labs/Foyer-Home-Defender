"""The first configuration, built from the config flow's answers.

The config flow creates one area, one zone and one scenario so that Foyer does
something from the first minute; everything else is added from the panel. The
user supplies the names, the zone entity and its trigger states (INV-5).
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
    ZoneType,
)

# The notifications every installation gets until response profiles exist.
# zone_fault is not optional: INV-4 requires a fault to be announced. A failed
# arming and an automatic bypass are announced because §5.4 says so, and a
# technical alarm because it must never be silent (part 2 decision 10).
SEED_MOMENTS = frozenset(
    {
        Moment.ARMED,
        Moment.DISARMED,
        Moment.ZONE_FAULT,
        Moment.ARM_FAILED,
        Moment.ZONE_BYPASSED,
        Moment.TECHNICAL_RAISED,
    }
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
                type=ZoneType.INSTANT,
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
        actions=(NotificationAction(id=new_id(), moments=SEED_MOMENTS),),
        # No users or codes exist yet, so no operation can require one. The
        # engine enforces this policy and fails closed if it is ever set.
        code_policy=CodePolicy(),
    )
