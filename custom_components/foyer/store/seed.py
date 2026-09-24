"""The first configuration, built from the config flow's answers.

The config flow creates one area, one zone and one scenario so that Foyer does
something from the first minute; everything else is added from the panel. The
user supplies the names, the zone entity and its trigger states (INV-5).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
import uuid

from ..core.models import (
    ActionKind,
    Area,
    CodePolicy,
    FoyerConfig,
    Moment,
    ProfileAction,
    ResponseProfile,
    Scenario,
    Settings,
    StateTrigger,
    Zone,
    ZoneType,
)
from ..core.presets import PRESETS

# What the default response profile does on a new installation. zone_fault is
# not optional: INV-4 requires a fault to be announced. A failed arming and an
# automatic bypass are announced because §5.4 says so, a technical alarm
# because it must never be silent (part 2 decision 10), and an alarm because
# an alarm that says nothing is the worst failure there is (part 3 decision 3).
#
# Never `duress`. This profile's one action is a persistent notification,
# which appears on every Home Assistant screen — the wall tablet the duress
# code was typed at included (§6.1). The household answers it with a
# notification to somebody outside, which only it can choose.
SEED_MOMENTS = frozenset(
    {
        Moment.ARMED,
        Moment.DISARMED,
        Moment.ZONE_FAULT,
        Moment.ARM_FAILED,
        Moment.ZONE_BYPASSED,
        Moment.TECHNICAL_RAISED,
        Moment.TRIGGERED,
        # A second zone tripping during an alarm is the intruder moving
        # through the house (§5.6); a profile that announced the first and
        # nothing after left the household with half the story (third
        # review).
        Moment.INCIDENT_JOINED,
        # §11.3 requires a notification on the start and the end of a walk
        # test, among the safeguards it calls mandatory. A safeguard that
        # only reaches whoever configured it is not one.
        Moment.WALK_TEST_STARTED,
        Moment.WALK_TEST_ENDED,
        # System health (§12). The same reasoning as the alarm above: a
        # house that loses its power, its radio or its only way of speaking
        # and says nothing about it has failed in the way this whole
        # section exists to prevent. All four are announced by the default
        # profile, and a household that finds them noisy unticks them.
        Moment.SYSTEM_POWER_LOST,
        Moment.NOTIFICATION_CHANNEL_DOWN,
        Moment.WATCHDOG_UNREACHABLE,
        Moment.RF_INTERFERENCE_SUSPECTED,
    }
)


# A configuration value, not a user-visible string: the user renames it from
# the panel, and a migrated installation gets the same name.
DEFAULT_PROFILE_NAME = "Default"


def seed_config(
    *,
    area_name: str,
    scenario_name: str,
    zone_entity_id: str,
    zone_name: str,
    trigger_states: Iterable[str],
    zone_type: ZoneType = ZoneType.INSTANT,
    new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> FoyerConfig:
    area = Area(id=new_id(), name=area_name, ha_state_when_armed="armed_away")
    # One profile, inherited by everything: the chain of §6 ends here, and the
    # panel's page 5 is where the user grows it.
    default_profile = ResponseProfile(
        id=new_id(),
        name=DEFAULT_PROFILE_NAME,
        actions=(
            ProfileAction(
                id=new_id(),
                kind=ActionKind.PERSISTENT_NOTIFICATION,
                moments=SEED_MOMENTS,
            ),
        ),
    )
    return FoyerConfig(
        areas=(area,),
        zones=(
            Zone(
                id=new_id(),
                name=zone_name,
                entity_id=zone_entity_id,
                area_id=area.id,
                trigger=StateTrigger(states=frozenset(trigger_states)),
                # What the zone editor proposes for this entity: a door is
                # the way in and starts the entry delay, a smoke detector is
                # the technical channel and never a break-in (fix phase).
                type=zone_type,
                **PRESETS[zone_type],
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
        profiles=(default_profile,),
        settings=Settings(default_profile_id=default_profile.id),
        # No users or codes exist yet, so no operation can require one. The
        # engine enforces this policy and fails closed if it is ever set.
        code_policy=CodePolicy(),
    )
