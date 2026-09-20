"""Shared builders for the pure test suite. Nothing here may import homeassistant."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.foyer.core.engine import decide
from custom_components.foyer.core.models import (
    ActionKind,
    Actor,
    AlarmKind,
    Area,
    AreaRuntime,
    ArmAreaRequest,
    ArmModeRequest,
    ArmPolicy,
    ArmRequest,
    AutoRule,
    BypassZone,
    CancelAutoAction,
    CodePolicy,
    Decision,
    DisarmRequest,
    EntityState,
    EntryMode,
    Event,
    FoyerConfig,
    HealthReport,
    Moment,
    Permission,
    ProfileAction,
    ResponseProfile,
    RuleActionKind,
    RuleTrigger,
    RuleTriggerKind,
    RuntimeState,
    Scenario,
    SetAutoArming,
    SetSuspension,
    Settings,
    StateTrigger,
    Suspension,
    SystemSnapshot,
    Tick,
    User,
    WalkTestRequest,
    Zone,
    ZoneStateChanged,
    ZoneType,
)

NOW = datetime(2026, 9, 14, 19, 32, tzinfo=UTC)

# What the engine is told about whoever is asking (§8.2). Tests say
# `channel="ha_ui"` or `code=CodeResult.VALID`; this turns that into the Actor
# the event carries, so no test has to know how identity is plumbed.
_ACTOR_FIELDS = (
    "user_id",
    "channel",
    "device_id",
    "code",
    "identified",
    "duress",
    "is_admin",
    "token",
    "claimed",
)


def user(
    user_id: str = "luca",
    name: str = "Luca",
    *,
    permissions: frozenset[str] | None = None,
    **kwargs,
) -> User:
    """A user holding a code, which is what puts the policy in force.

    The hash is a placeholder: nothing in core/ ever verifies a code — that is
    security/'s work — and what the engine reads here is only "this person
    exists and holds one".
    """
    return User(
        id=user_id,
        name=name,
        code_hash=kwargs.pop("code_hash", "$2b$12$placeholder"),
        permissions=(
            frozenset(p.value for p in Permission)
            if permissions is None
            else permissions
        ),
        **kwargs,
    )


def _actor(kwargs: dict) -> dict:
    if "actor" in kwargs:
        return kwargs
    fields = {k: kwargs.pop(k) for k in list(kwargs) if k in _ACTOR_FIELDS}
    if fields:
        kwargs["actor"] = Actor(**fields)
    return kwargs


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


LUCA = "person.luca"
PARTNER = "person.partner"


def rule(
    rule_id: str = "empty_house",
    *,
    kind: RuleTriggerKind = RuleTriggerKind.ABSENCE,
    entity_ids: tuple[str, ...] = (LUCA, PARTNER),
    minutes: int = 30,
    at: str | None = None,
    weekdays: tuple[int, ...] = (),
    state: str | None = None,
    action: RuleActionKind = RuleActionKind.ARM,
    scenario_id: str | None = "away",
    area_ids: tuple[str, ...] = (),
    grace: int = 120,
    **props,
) -> AutoRule:
    return AutoRule(
        id=rule_id,
        name=rule_id.replace("_", " ").capitalize(),
        trigger=RuleTrigger(
            kind=kind,
            entity_ids=entity_ids,
            state=state,
            minutes=minutes,
            at=at,
            weekdays=weekdays,
        ),
        action=action,
        scenario_id=scenario_id,
        area_ids=area_ids,
        grace_seconds=grace,
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
    entities = {
        z.entity_id: EntityState(
            idle.get(z.entity_id.split(".")[0], "off"),
            last_reported=at,
            last_changed=at,
        )
        for z in config.zones
    }
    # The household, at home unless a test says otherwise (§9.4). Their
    # entities exist even when no rule reads them: a person entity that
    # cannot be read is not evidence of anything, and a test that forgot to
    # create one would be testing that rather than the rule.
    for person in (LUCA, PARTNER):
        entities.setdefault(
            person, EntityState("home", last_reported=at, last_changed=at)
        )
    return entities


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
        # Which radio each entity sits on (§12.5). The runtime works this out
        # from the config entries; a test says it outright.
        self.radios: dict[str, str] = {}
        for entity_id, value in (entities or {}).items():
            self.entities[entity_id] = EntityState(
                value, last_reported=self.now, last_changed=self.now
            )
        # Start from a world whose zones are already known: the initial open
        # zones count as active, exactly as a running system would have them.
        self.state = self.send(Tick()).state

    # --- driving -----------------------------------------------------------------

    def snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(
            self.state, self.entities, self.settling, self.timezone, self.radios
        )

    def send(self, event: Event) -> Decision:
        decision = decide(self.snapshot(), event, self.config, self.now)
        self.state = decision.state
        if isinstance(event, ZoneStateChanged):
            self.entities[event.entity_id] = event.new
        self.last = decision
        return decision

    def set(self, entity_id: str, value: str | None, **attributes) -> Decision:
        return self.send(
            ZoneStateChanged(
                entity_id,
                EntityState(value, attributes, self.now, last_changed=self.now),
            )
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
        return self.send(ArmRequest(scenario_id, **_actor(kwargs)))

    def arm_area(self, area_id: str, **kwargs) -> Decision:
        return self.send(ArmAreaRequest(area_id, **_actor(kwargs)))

    def arm_mode(self, mode: str, **kwargs) -> Decision:
        return self.send(ArmModeRequest(mode, **_actor(kwargs)))

    def disarm(self, *area_ids: str, **kwargs) -> Decision:
        return self.send(DisarmRequest(area_ids or None, **_actor(kwargs)))

    def bypass(self, zone_id: str, **kwargs) -> Decision:
        return self.send(BypassZone(zone_id, **_actor(kwargs)))

    def walk_test(self, enable: bool = True, **kwargs) -> Decision:
        duration = kwargs.pop("duration", None)
        return self.send(WalkTestRequest(enable, duration=duration, **_actor(kwargs)))

    # --- automatic rules (§9.4) ---------------------------------------------------

    def cancel(self, pending_id: str | None = None, **kwargs) -> Decision:
        return self.send(CancelAutoAction(pending_id, **_actor(kwargs)))

    def auto_arming(self, enabled: bool, **kwargs) -> Decision:
        return self.send(SetAutoArming(enabled, **_actor(kwargs)))

    def suspend(self, suspension: Suspension | None = None, **kwargs) -> Decision:
        suspension_id = kwargs.pop("suspension_id", None)
        return self.send(SetSuspension(suspension, suspension_id, **_actor(kwargs)))

    # --- system health (§12) ------------------------------------------------------

    def health(self, **kwargs) -> Decision:
        """The runtime reports what it went and looked at (§12)."""
        return self.send(HealthReport(**kwargs))

    def on_radio(self, radio_id: str, *entity_ids: str) -> None:
        for entity_id in entity_ids:
            self.radios[entity_id] = radio_id

    def person(self, entity_id: str, state: str) -> Decision:
        """Somebody's presence entity changed, which is an ordinary state
        change: the rules are evaluated on every decision, like everything."""
        return self.set(entity_id, state)

    def pending(self) -> tuple:
        return self.state.pending_rules

    def blocked(self) -> list[str]:
        """The reasons the last decision recorded for a rule that did not act."""
        return [
            o.detail.get("reason", "")
            for o in (self.last.occurrences if self.last else ())
            if o.moment is Moment.AUTO_BLOCKED
        ]

    # --- reading -----------------------------------------------------------------

    def area(self, area_id: str) -> AreaRuntime:
        return self.state.area(area_id)

    def states(self) -> dict[str, str]:
        return {a: rt.state.value for a, rt in self.state.areas.items()}
