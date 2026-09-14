"""The decision engine: ``decide(snapshot, event, config, now) -> Decision``.

A pure function (INV-1). It performs no I/O, reads no clock or random source it
was not handed, and touches no Home Assistant state. The runtime hands the
resulting Decision to an executor; the simulator will call this same function
with a fabricated snapshot and clock and simply never execute the result.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from .models import (
    FAULT_STATES,
    ActionIntent,
    AreaState,
    ArmRequest,
    Decision,
    DisarmRequest,
    Event,
    FoyerConfig,
    Moment,
    Operation,
    Reason,
    SystemSnapshot,
    Zone,
    ZoneStateChanged,
)


def decide(
    snapshot: SystemSnapshot,
    event: Event,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    """Return what should happen in response to ``event``. Executes nothing."""
    if isinstance(event, ArmRequest):
        return _arm(snapshot, event, config, now)
    if isinstance(event, DisarmRequest):
        return _disarm(snapshot, event, config, now)
    if isinstance(event, ZoneStateChanged):
        return _zone_changed(snapshot, event, config, now)
    raise TypeError(f"unsupported event: {event!r}")


# --- helpers ---------------------------------------------------------------------


def is_fault(state: str | None) -> bool:
    """A missing, unavailable or unknown entity is a fault (INV-4)."""
    return state is None or state in FAULT_STATES


def is_triggered(zone: Zone, state: str | None) -> bool:
    """Only the zone's own trigger states count — never "on" by default (INV-5)."""
    return not is_fault(state) and state in zone.trigger.states


def _reject(
    snapshot: SystemSnapshot,
    now: datetime,
    reason: Reason,
    blocking_zones: tuple[str, ...] = (),
) -> Decision:
    return Decision(
        at=now,
        accepted=False,
        reason=reason,
        active_scenario_id=snapshot.active_scenario_id,
        blocking_zones=blocking_zones,
    )


def _code_check(config: FoyerConfig, operation: Operation) -> Reason | None:
    """Enforce the code policy server-side (INV-2).

    Phase 0 has no users and therefore no code that could be verified. If the
    policy requires a code, the request is refused whatever was supplied: the
    engine fails closed rather than accepting something it cannot check.
    """
    if not config.code_policy.requires_code(operation):
        return None
    return Reason.CODE_REQUIRED


def _intents(
    config: FoyerConfig,
    moment: Moment,
    placeholders: Mapping[str, str],
) -> tuple[ActionIntent, ...]:
    return tuple(
        ActionIntent(
            action_id=action.id,
            kind="notification",
            moment=moment,
            placeholders=placeholders,
        )
        for action in config.actions
        if moment in action.moments
    )


# --- arm -----------------------------------------------------------------------


def _arm(
    snapshot: SystemSnapshot,
    event: ArmRequest,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    scenario = config.scenario(event.scenario_id)
    if scenario is None:
        return _reject(snapshot, now, Reason.UNKNOWN_SCENARIO)

    if any(
        snapshot.area_states.get(area_id) is not AreaState.DISARMED
        for area_id in scenario.areas
    ):
        return _reject(snapshot, now, Reason.INVALID_STATE)

    if (reason := _code_check(config, Operation.ARM)) is not None:
        return _reject(snapshot, now, reason)

    # Arming preconditions (SPEC §5.4). Faults are checked first: a zone we
    # cannot see must never be mistaken for a closed one.
    zones = config.zones_in(scenario.areas)
    faulted = tuple(
        z.id for z in zones if is_fault(snapshot.entity_states.get(z.entity_id))
    )
    if faulted:
        return _reject(snapshot, now, Reason.ZONE_FAULT, faulted)

    # Phase 0 has no arm policies other than the default, `block`.
    open_zones = tuple(
        z.id for z in zones if is_triggered(z, snapshot.entity_states.get(z.entity_id))
    )
    if open_zones:
        return _reject(snapshot, now, Reason.ZONE_OPEN, open_zones)

    # No exit delay in Phase 0: with a delay of 0 `arming` is skipped (SPEC §5.2).
    areas = [a for a in config.areas if a.id in scenario.areas]
    return Decision(
        at=now,
        accepted=True,
        area_states={a.id: AreaState.ARMED for a in areas},
        active_scenario_id=scenario.id,
        moments=(Moment.ARMED,),
        actions=_intents(
            config,
            Moment.ARMED,
            {"area": ", ".join(a.name for a in areas), "scenario": scenario.name},
        ),
    )


# --- disarm --------------------------------------------------------------------


def _disarm(
    snapshot: SystemSnapshot,
    event: DisarmRequest,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    active = [
        a
        for a in config.areas
        if snapshot.area_states.get(a.id, AreaState.DISARMED) is not AreaState.DISARMED
    ]
    if not active:
        return _reject(snapshot, now, Reason.INVALID_STATE)

    if (reason := _code_check(config, Operation.DISARM)) is not None:
        return _reject(snapshot, now, reason)

    return Decision(
        at=now,
        accepted=True,
        area_states={a.id: AreaState.DISARMED for a in active},
        active_scenario_id=None,
        moments=(Moment.DISARMED,),
        actions=_intents(
            config, Moment.DISARMED, {"area": ", ".join(a.name for a in active)}
        ),
    )


# --- zone state changes --------------------------------------------------------


def _zone_changed(
    snapshot: SystemSnapshot,
    event: ZoneStateChanged,
    config: FoyerConfig,
    now: datetime,
) -> Decision:
    zones = [z for z in config.zones if z.entity_id == event.entity_id]
    previous = snapshot.entity_states.get(event.entity_id)
    area_states: dict[str, AreaState] = {}
    moments: list[Moment] = []
    actions: list[ActionIntent] = []

    for zone in zones:
        area = config.area(zone.area_id)
        if area is None:
            continue

        # Entering a fault is announced once, on the transition (INV-4). The
        # fault itself is an overlay: it does not change the area's state.
        if is_fault(event.new_state) and not is_fault(previous):
            moments.append(Moment.ZONE_FAULT)
            actions.extend(
                _intents(
                    config, Moment.ZONE_FAULT, {"zone": zone.name, "area": area.name}
                )
            )
            continue

        # Phase 0 has only instant semantics: an armed area goes straight to
        # triggered. Disarmed and already-triggered areas are unaffected.
        if snapshot.area_states.get(area.id) is AreaState.ARMED and is_triggered(
            zone, event.new_state
        ):
            area_states[area.id] = AreaState.TRIGGERED
            moments.append(Moment.TRIGGERED)
            actions.extend(
                _intents(
                    config, Moment.TRIGGERED, {"zone": zone.name, "area": area.name}
                )
            )

    return Decision(
        at=now,
        accepted=True,
        area_states=area_states,
        active_scenario_id=snapshot.active_scenario_id,
        moments=tuple(moments),
        actions=tuple(actions),
    )
