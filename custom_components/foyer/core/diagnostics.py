"""Live zone diagnostics: what every zone is doing right now (SPEC §11.1).

The most common question after an installation is not "is my configuration
elegant" — it is *am I looking at the right sensor, and does it work*. This
module answers it for every mapped zone: the entity behind it, the state that
entity is in, whether Foyer would count that as triggered, when it last
moved, whether it is reachable, what its battery and radio say, and whether
it is stopping the house being armed.

Pure, like everything in ``core``: it is given a snapshot and a clock and
looks nothing up (INV-1). Two consequences that are the point of putting it
here rather than in the runtime:

- the **trigger evaluation column is the engine's own** ``is_active``, not a
  second reading of the trigger spec. INV-5 exists because a zone that
  declares ``off`` as its alarm state is invisible until the night it does
  not fire, and a diagnostics page that evaluated triggers its own way would
  agree with the configuration and disagree with the alarm;
- the **"blocks arming" column is the engine's own** ``arm_blockers``, for
  the same reason: a table that says "ready" where arming refuses is worse
  than no table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .engine import arm_blockers
from .models import (
    ArmingDevice,
    EntityState,
    EventTrigger,
    FoyerConfig,
    SystemSnapshot,
    Zone,
)
from .triggers import (
    battery_level,
    battery_low,
    fault_cause,
    is_active,
    is_unavailable,
    supervision_due,
)

# Attributes a Home Assistant integration puts a radio measurement in. There
# is no standard one, so this is a list of what the common integrations
# actually use — Zigbee2MQTT's link quality, Z-Wave JS and deCONZ's RSSI —
# and a zone whose entity exposes none of them simply has no column to fill.
# Guessing at an unknown attribute would be worse: a number with no unit,
# presented as signal strength, is a diagnostic that misleads.
SIGNAL_ATTRIBUTES: tuple[tuple[str, str], ...] = (
    ("linkquality", "lqi"),
    ("link_quality", "lqi"),
    ("lqi", "lqi"),
    ("rssi", "dbm"),
    ("signal_strength", "dbm"),
)


@dataclass(frozen=True, slots=True)
class Signal:
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class ZoneDiagnostics:
    """One row of §11.1's table."""

    zone_id: str
    name: str
    area_id: str
    entity_id: str
    enabled: bool
    # The entity's raw state, exactly as Home Assistant holds it. None means
    # the entity does not exist at all, which is different from unavailable
    # and is the commonest mistake of all: a renamed entity.
    state: str | None
    # Would Foyer count this as triggered right now (INV-5)? It is resolved
    # through the zone's own trigger, which is the whole reason the column
    # exists: ``off`` is an alarm for a normally-closed contact.
    triggered: bool
    # An event or tag zone is momentary and is never "open": there is no
    # state to be in, only scans that have happened.
    momentary: bool
    available: bool
    last_changed: datetime | None
    last_reported: datetime | None
    fault: str | None
    supervision_timeout: int | None
    supervision_due: datetime | None
    battery_entity_id: str | None
    battery_level: float | None
    battery_low: bool
    signal: Signal | None
    bypassed: str | None
    blocks_arming: bool
    # Which of the two §5.4 reasons it blocks for, when it blocks: the table
    # says "fix the fault" or "close the window", not just "blocks".
    blocks_because: str | None


@dataclass(frozen=True, slots=True)
class DeviceDiagnostics:
    """One row of the arming devices table, below the zones.

    A keypad is not a zone and cannot block arming, so it is a table of its
    own rather than rows with half their columns struck through (part 1
    decision 3). But "the keypad by the door is dead" is exactly the kind of
    thing §11.1 exists to surface, and the watcher already follows the entity
    a tag arrives on.
    """

    device_id: str
    name: str
    kind: str
    enabled: bool
    entity_id: str | None
    state: str | None
    available: bool
    last_changed: datetime | None
    # A keypad has no entity at all: it speaks over MQTT or a service call,
    # so there is nothing to be available or unavailable. The table says so
    # rather than showing it as healthy, which would be a claim.
    watchable: bool


@dataclass(frozen=True, slots=True)
class Diagnostics:
    at: datetime
    zones: tuple[ZoneDiagnostics, ...] = ()
    devices: tuple[DeviceDiagnostics, ...] = ()
    # Entities named by a zone or a device that Home Assistant does not have.
    # Collected separately because it is one answer to several rows and it is
    # the first thing to check after a rename.
    missing_entities: tuple[str, ...] = field(default=())


def signal_of(entity: EntityState) -> Signal | None:
    """The radio measurement the entity exposes, if it exposes one."""
    for key, unit in SIGNAL_ATTRIBUTES:
        raw = entity.attributes.get(key)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            return Signal(float(raw), unit)
        except (TypeError, ValueError):
            continue
    return None


def _zone_row(
    zone: Zone,
    snapshot: SystemSnapshot,
    config: FoyerConfig,
    now: datetime,
    blocking: dict[str, str],
) -> ZoneDiagnostics:
    entity = snapshot.entity(zone.entity_id)
    battery = snapshot.entity(zone.battery_entity_id or "")
    was_active = zone.id in snapshot.state.active_zones
    bypassed = snapshot.state.bypassed.get(zone.id)
    return ZoneDiagnostics(
        zone_id=zone.id,
        name=zone.name,
        area_id=zone.area_id,
        entity_id=zone.entity_id,
        enabled=zone.enabled,
        state=entity.state,
        # The engine's own reading, with the engine's own memory of what the
        # zone was: a numeric trigger inside its hysteresis band and an
        # entity in fault both keep whatever they were, and a table that
        # forgot that would disagree with the alarm twice a day.
        triggered=is_active(zone, entity, was_active),
        momentary=isinstance(zone.trigger, EventTrigger),
        available=not is_unavailable(entity),
        last_changed=entity.last_changed,
        last_reported=entity.last_reported,
        fault=fault_cause(zone, entity, now, battery) if zone.enabled else None,
        supervision_timeout=zone.supervision_timeout,
        supervision_due=supervision_due(zone, entity),
        battery_entity_id=zone.battery_entity_id,
        battery_level=battery_level(battery) if zone.battery_entity_id else None,
        battery_low=battery_low(zone, battery, config.settings.low_battery_threshold),
        bypassed=bypassed.value if bypassed is not None else None,
        blocks_arming=zone.id in blocking,
        blocks_because=blocking.get(zone.id),
        signal=signal_of(entity),
    )


def _device_row(device: ArmingDevice, snapshot: SystemSnapshot) -> DeviceDiagnostics:
    entity = snapshot.entity(device.entity_id or "")
    watchable = bool(device.entity_id)
    return DeviceDiagnostics(
        device_id=device.id,
        name=device.name,
        kind=device.kind.value,
        enabled=device.enabled,
        entity_id=device.entity_id,
        state=entity.state if watchable else None,
        available=watchable and not is_unavailable(entity),
        last_changed=entity.last_changed if watchable else None,
        watchable=watchable,
    )


def diagnose(
    snapshot: SystemSnapshot, config: FoyerConfig, now: datetime
) -> Diagnostics:
    """Every mapped zone, and every declared arming device (SPEC §11.1)."""
    blocking: dict[str, str] = {}
    for area in config.areas:
        faulted, open_ = arm_blockers(snapshot, config, (area.id,), now)
        blocking.update(dict.fromkeys(faulted, "fault"))
        blocking.update(dict.fromkeys(open_, "open"))

    zones = tuple(
        _zone_row(zone, snapshot, config, now, blocking) for zone in config.zones
    )
    devices = tuple(_device_row(device, snapshot) for device in config.devices)
    named = [z.entity_id for z in config.zones]
    named += [z.battery_entity_id for z in config.zones if z.battery_entity_id]
    named += [d.entity_id for d in config.devices if d.entity_id]
    missing = tuple(
        sorted({e for e in named if e and snapshot.entity(e).state is None})
    )
    return Diagnostics(at=now, zones=zones, devices=devices, missing_entities=missing)


def as_dict(diagnostics: Diagnostics) -> dict[str, Any]:
    """The table as the panel receives it. Identifiers, never sentences: the
    panel translates every word a person reads (§15.2)."""

    def when(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    return {
        "at": diagnostics.at.isoformat(),
        "zones": [
            {
                "zone_id": z.zone_id,
                "name": z.name,
                "area_id": z.area_id,
                "entity_id": z.entity_id,
                "enabled": z.enabled,
                "state": z.state,
                "triggered": z.triggered,
                "momentary": z.momentary,
                "available": z.available,
                "last_changed": when(z.last_changed),
                "last_reported": when(z.last_reported),
                "fault": z.fault,
                "supervision_timeout": z.supervision_timeout,
                "supervision_due": when(z.supervision_due),
                "battery_entity_id": z.battery_entity_id,
                "battery_level": z.battery_level,
                "battery_low": z.battery_low,
                "signal": (
                    None
                    if z.signal is None
                    else {"value": z.signal.value, "unit": z.signal.unit}
                ),
                "bypassed": z.bypassed,
                "blocks_arming": z.blocks_arming,
                "blocks_because": z.blocks_because,
            }
            for z in diagnostics.zones
        ],
        "devices": [
            {
                "device_id": d.device_id,
                "name": d.name,
                "kind": d.kind,
                "enabled": d.enabled,
                "entity_id": d.entity_id,
                "state": d.state,
                "available": d.available,
                "last_changed": when(d.last_changed),
                "watchable": d.watchable,
            }
            for d in diagnostics.devices
        ],
        "missing_entities": list(diagnostics.missing_entities),
    }
