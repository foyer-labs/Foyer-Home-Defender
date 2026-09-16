"""Shared builders for the pure test suite. Nothing here may import homeassistant."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.foyer.core.engine import decide
from custom_components.foyer.core.models import (
    ActionKind,
    AlarmKind,
    Area,
    AreaRuntime,
    ArmAreaRequest,
    ArmModeRequest,
    ArmPolicy,
    ArmRequest,
    CodePolicy,
    Decision,
    DisarmRequest,
    EntityState,
    EntryMode,
    Event,
    FoyerConfig,
    BypassZone,
    Moment,
    ProfileAction,
    ResponseProfile,
    RuntimeState,
    Scenario,
    Settings,
    StateTrigger,
    SystemSnapshot,
    Tick,
    Zone,
    ZoneStateChanged,
    ZoneType,
)

NOW = datetime(2026, 9, 14, 19, 32, tzinfo=UTC)

DOOR = "binary_sensor.front_door"
HALL = "binary_sensor.hall_pir"
WINDOW = "binary_sensor.kitchen_window"
PATIO = "binary_sensor.patio_door"
TAMPER = "binary_sensor.siren_tamper"
BATH = "binary_sensor.bath_window"
LANDING = "binary_sensor.landing_pir"
GARAGE = "cover.garage"


def zone(
    zone_id: str,
    entity_id: str,
    area_id: str,
    *,
    states: tuple[str, ...] = ("on",),
    **props,
) -> Zone:
    return Zone(
        id=zone_id,
        name=zone_id.replace("_", " ").capitalize(),
        entity_id=entity_id,
        area_id=area_id,
        trigger=StateTrigger(frozenset(states)),
        **props,
    )


def make_house() -> FoyerConfig:
    """Three areas, two scenarios, one zone of every kind part 1 knows."""
    return FoyerConfig(
        areas=(
            Area("ground", "Ground floor", "armed_away", 30, 30),
            Area("upstairs", "Upstairs", "armed_away", 30, 20),
            Area("garage", "Garage", "armed_away", 15, 10),
        ),
        zones=(
            zone(
                "door",
                DOOR,
                "ground",
                type=ZoneType.DELAYED,
                entry_mode=EntryMode.DELAYED,
            ),
            zone(
                "hall",
                HALL,
                "ground",
                type=ZoneType.FOLLOWER,
                entry_mode=EntryMode.FOLLOWER,
                arm_policy=ArmPolicy.IGNORE,
            ),
            zone("window", WINDOW, "ground"),
            zone("patio", PATIO, "ground", arm_policy=ArmPolicy.ARM_AFTER_CLOSING),
            zone(
                "tamper",
                TAMPER,
                "ground",
                type=ZoneType.TAMPER,
                alarm_kind=AlarmKind.TAMPER,
                always_on=True,
                bypassable=False,
            ),
            zone("bath", BATH, "upstairs", arm_policy=ArmPolicy.AUTO_BYPASS),
            zone(
                "landing",
                LANDING,
                "upstairs",
                type=ZoneType.FOLLOWER,
                entry_mode=EntryMode.FOLLOWER,
            ),
            zone(
                "garage_door",
                GARAGE,
                "garage",
                states=("open", "opening"),
                type=ZoneType.DELAYED,
                entry_mode=EntryMode.DELAYED,
            ),
        ),
        scenarios=(
            Scenario("away", "Away", ("ground", "upstairs", "garage"), "armed_away"),
            Scenario(
                "night", "Night", ("ground",), "armed_night", exit_delay_override=5
            ),
        ),
        profiles=(
            ResponseProfile(
                "default",
                "Default",
                actions=(
                    ProfileAction(
                        "notify",
                        ActionKind.PERSISTENT_NOTIFICATION,
                        frozenset(
                            {
                                Moment.ARMED,
                                Moment.DISARMED,
                                Moment.ZONE_FAULT,
                                Moment.ARM_FAILED,
                            }
                        ),
                    ),
                ),
            ),
        ),
        settings=Settings(default_profile_id="default"),
        code_policy=CodePolicy(),
    )


def closed_entities(config: FoyerConfig, at: datetime = NOW) -> dict[str, EntityState]:
    idle = {"cover": "closed"}
    return {
        z.entity_id: EntityState(
            idle.get(z.entity_id.split(".")[0], "off"), last_reported=at
        )
        for z in config.zones
    }


class World:
    """A tiny stand-in for the runtime: decide(), store, repeat.

    It performs no side effects either; it only keeps the state a real runtime
    would keep, so tests can read as sequences of things happening.
    """

    def __init__(
        self,
        config: FoyerConfig | None = None,
        entities: dict[str, str | None] | None = None,
    ) -> None:
        self.config = config or make_house()
        self.now = NOW
        self.settling = False
        self.timezone = UTC
        self.last: Decision | None = None
        self.state = RuntimeState(
            areas={a.id: AreaRuntime() for a in self.config.areas}
        )
        self.entities = closed_entities(self.config)
        for entity_id, value in (entities or {}).items():
            self.entities[entity_id] = EntityState(value, last_reported=self.now)
        # Start from a world whose zones are already known: the initial open
        # zones count as active, exactly as a running system would have them.
        self.state = self.send(Tick()).state

    # --- driving -----------------------------------------------------------------

    def snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(self.state, self.entities, self.settling, self.timezone)

    def send(self, event: Event) -> Decision:
        decision = decide(self.snapshot(), event, self.config, self.now)
        self.state = decision.state
        if isinstance(event, ZoneStateChanged):
            self.entities[event.entity_id] = event.new
        self.last = decision
        return decision

    def set(self, entity_id: str, value: str | None, **attributes) -> Decision:
        return self.send(
            ZoneStateChanged(entity_id, EntityState(value, attributes, self.now))
        )

    def heartbeat(self, entity_id: str) -> None:
        """The entity reports again without changing (last_reported moves)."""
        self.entities[entity_id] = replace(
            self.entities[entity_id], last_reported=self.now
        )

    def advance(self, seconds: float) -> Decision:
        self.now += timedelta(seconds=seconds)
        return self.send(Tick())

    def arm(self, scenario_id: str, **kwargs) -> Decision:
        return self.send(ArmRequest(scenario_id, **kwargs))

    def arm_area(self, area_id: str, **kwargs) -> Decision:
        return self.send(ArmAreaRequest(area_id, **kwargs))

    def arm_mode(self, mode: str, **kwargs) -> Decision:
        return self.send(ArmModeRequest(mode, **kwargs))

    def disarm(self, *area_ids: str, **kwargs) -> Decision:
        return self.send(DisarmRequest(area_ids or None, **kwargs))

    def bypass(self, zone_id: str, **kwargs) -> Decision:
        return self.send(BypassZone(zone_id, **kwargs))

    # --- reading -----------------------------------------------------------------

    def area(self, area_id: str) -> AreaRuntime:
        return self.state.area(area_id)

    def states(self) -> dict[str, str]:
        return {a: rt.state.value for a, rt in self.state.areas.items()}
