"""Binary sensors and sensors (SPEC §13): zones, readiness, faults, countdown."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from ..const import DOMAIN
from ..core.models import Area, Channel, Radio, TimerKind, Zone
from ..runtime.system import FoyerSystem
from .common import FoyerEntity, area_device, hub_device

_COUNTDOWN_KINDS = (TimerKind.EXIT, TimerKind.HOLD, TimerKind.ENTRY)


async def async_setup_binary_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    entry_id = entry.entry_id
    areas = {a.id: a for a in system.config.areas}
    async_add_entities(
        [
            FoyerReadyToArm(system, entry_id, None),
            *(FoyerReadyToArm(system, entry_id, a) for a in system.config.areas),
            FoyerFault(system, entry_id),
            FoyerSystemHealth(system, entry_id),
            FoyerTechnicalAlarm(system, entry_id),
            *(
                FoyerRfInterference(system, entry_id, radio)
                for radio in system.config.health.radios
            ),
            *(
                FoyerZoneSensor(system, entry_id, z, areas[z.area_id])
                for z in system.config.zones
                if z.area_id in areas
            ),
        ]
    )


async def async_setup_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    system: FoyerSystem = entry.runtime_data
    async_add_entities(
        [
            FoyerOpenZones(system, entry.entry_id),
            *(FoyerCountdown(system, entry.entry_id, a) for a in system.config.areas),
            FoyerTechnicalCause(system, entry.entry_id),
            FoyerIncident(system, entry.entry_id),
            FoyerLastEvent(system, entry.entry_id),
            FoyerNextAutoAction(system, entry.entry_id),
        ]
    )


# --- binary sensors -------------------------------------------------------------


class FoyerZoneSensor(FoyerEntity, BinarySensorEntity):
    """The zone as Foyer reads it: ``on`` means triggered, whatever the entity
    says "open" with (INV-5). A fault is an attribute, never "off" (INV-4)."""

    _attr_name = None

    def __init__(self, system: FoyerSystem, entry_id: str, zone: Zone, area: Area):
        super().__init__(system)
        self._zone = zone
        self._attr_unique_id = f"{entry_id}_zone_{zone.id}"
        self.entity_id = f"binary_sensor.{DOMAIN}_zone_{slugify(zone.name)}"
        self._attr_device_info = area_device(entry_id, area)
        self._attr_name = zone.name

    @property
    def is_on(self) -> bool:
        return self._zone.id in self._system.state.active_zones

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bypass = self._system.state.bypassed.get(self._zone.id)
        return {
            "zone_id": self._zone.id,
            "source_entity": self._zone.entity_id,
            "type": self._zone.type.value,
            "bypassed": bypass.value if bypass else None,
            "fault": self._zone.id in self._system.state.faults,
            "enabled": self._zone.enabled,
        }


class FoyerReadyToArm(FoyerEntity, BinarySensorEntity):
    """Whether arming would succeed right now, for one area or for all."""

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area | None):
        super().__init__(system)
        self._area = area
        if area is None:
            self._attr_translation_key = "ready_to_arm"
            self._attr_unique_id = f"{entry_id}_ready_to_arm"
            self.entity_id = f"binary_sensor.{DOMAIN}_ready_to_arm"
            self._attr_device_info = hub_device(entry_id)
        else:
            self._attr_translation_key = "ready_to_arm"
            self._attr_unique_id = f"{entry_id}_ready_to_arm_{area.id}"
            self.entity_id = f"binary_sensor.{DOMAIN}_ready_to_arm_{slugify(area.name)}"
            self._attr_device_info = area_device(entry_id, area)

    def _area_ids(self) -> tuple[str, ...]:
        if self._area is not None:
            return (self._area.id,)
        return tuple(a.id for a in self._system.config.areas)

    @property
    def is_on(self) -> bool:
        faulted, open_ = self._system.blockers(self._area_ids())
        return not faulted and not open_

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        faulted, open_ = self._system.blockers(self._area_ids())
        names = {z.id: z.name for z in self._system.config.zones}
        return {
            "faulted_zones": [names[z] for z in faulted],
            "open_zones": [names[z] for z in open_],
        }


class FoyerFault(FoyerEntity, BinarySensorEntity):
    """Any zone in fault (INV-4)."""

    _attr_translation_key = "fault"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_fault"
        self.entity_id = f"binary_sensor.{DOMAIN}_fault"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return bool(self._system.state.faults)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        names = {z.id: z.name for z in self._system.config.zones}
        return {"zones": sorted(names[z] for z in self._system.state.faults)}


class FoyerSystemHealth(FoyerEntity, BinarySensorEntity):
    """Is anything wrong with the system itself? (SPEC §13, §12)

    One entity with the causes as attributes rather than five entities,
    because the question a dashboard asks is "is anything wrong" and the
    answer to "what" belongs on page 14, where there is room to say it
    properly. It overlaps binary_sensor.foyer_fault on purpose: that one
    answers "can I arm", this one answers "is Foyer still able to do its
    job", and a house whose only trouble is a removed Telegram integration
    lights exactly one of them.
    """

    _attr_translation_key = "system_health"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_system_health"
        self.entity_id = f"binary_sensor.{DOMAIN}_system_health"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return bool(self._system.health_status()["causes"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self._system.health_status()
        names = {z.id: z.name for z in self._system.config.zones}
        return {
            "causes": status["causes"],
            "faulted_zones": sorted(names.get(z, z) for z in status["faults"]),
            "mains_lost_since": status["mains"]["since"],
            "broken_channels": [
                f"{c['contact_name']} · {c['service']}"
                for c in status["channels"]
                if c["fault"]
            ],
            "watchdog_down_since": status["watchdog"]["down_since"],
            "radios_suspected": [r["name"] for r in status["radios"] if r["confirmed"]],
        }


class FoyerRfInterference(FoyerEntity, BinarySensorEntity):
    """Correlated silence on one radio, coordinator still answering (§12.5).

    One per radio, because a Zigbee outage says nothing about Z-Wave. The
    attributes carry the first line §12.5 asks for — how many zones, of how
    many, and whether the coordinator is still there — because those three
    numbers are what let somebody tell jamming from the four other things
    that produce exactly this signature.
    """

    _attr_translation_key = "rf_interference"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, system: FoyerSystem, entry_id: str, radio: Radio) -> None:
        super().__init__(system)
        self._radio = radio
        self._attr_unique_id = f"{entry_id}_rf_interference_{radio.id}"
        self.entity_id = f"binary_sensor.{DOMAIN}_rf_interference_{slugify(radio.name)}"
        self._attr_translation_placeholders = {"radio": radio.name}
        self._attr_device_info = hub_device(entry_id)

    def _status(self) -> dict[str, Any] | None:
        return next(
            (
                r
                for r in self._system.health_status()["radios"]
                if r["id"] == self._radio.id
            ),
            None,
        )

    @property
    def is_on(self) -> bool:
        status = self._status()
        return bool(status and status["confirmed"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self._status() or {}
        return {
            "radio": self._radio.name,
            "zones_quiet": status.get("quiet", 0),
            "zones_on_radio": status.get("zones", 0),
            "threshold": status.get("threshold"),
            "window": status.get("window"),
            "coordinator_entity_id": self._radio.coordinator_entity_id,
            "coordinator_answering": status.get("coordinator_down_since") is None,
            "suspected_since": status.get("suspected_since"),
        }


class FoyerTechnicalAlarm(FoyerEntity, BinarySensorEntity):
    """The technical channel (§5.5): on from the moment a technical zone fires
    until it is both acknowledged and back to normal. Never part of any
    alarm_control_panel, so HomeKit and voice assistants never hear "burglary"
    for a smoke detector."""

    _attr_translation_key = "technical_alarm"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_technical_alarm"
        self.entity_id = f"binary_sensor.{DOMAIN}_technical_alarm"
        self._attr_device_info = hub_device(entry_id)

    @property
    def is_on(self) -> bool:
        return bool(self._system.state.technical)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        alarms = self._system.technical_status()
        return {
            "zones": [a["name"] for a in alarms],
            "active": [a["name"] for a in alarms if a["active"]],
            "unacknowledged": [a["name"] for a in alarms if not a["acknowledged"]],
        }


# --- sensors ----------------------------------------------------------------------

# The state of a text sensor with nothing to report: a word, not "unknown",
# because "unknown" would say Foyer does not know (INV-4).
NONE = "none"


class FoyerTechnicalCause(FoyerEntity, SensorEntity):
    """Which technical zone is in alarm: the first to fire, all as attributes."""

    _attr_translation_key = "technical_cause"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_technical_cause"
        self.entity_id = f"sensor.{DOMAIN}_technical_cause"
        self._attr_device_info = hub_device(entry_id)

    @property
    def native_value(self) -> str:
        alarms = sorted(self._system.technical_status(), key=lambda a: a["since"])
        return alarms[0]["name"] if alarms else NONE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"zones": [a["name"] for a in self._system.technical_status()]}


class FoyerIncident(FoyerEntity, SensorEntity):
    """The open intrusion incident (§5.6, §13): its id, or "none"."""

    _attr_translation_key = "incident"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_incident"
        self.entity_id = f"sensor.{DOMAIN}_incident"
        self._attr_device_info = hub_device(entry_id)

    @property
    def native_value(self) -> str:
        incident = self._system.state.incident
        return incident.id if incident else NONE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        incident = self._system.state.incident
        if incident is None:
            return {"zones": [], "areas": [], "acknowledged": None, "severity": None}
        zones = {z.id: z.name for z in self._system.config.zones}
        areas = {a.id: a.name for a in self._system.config.areas}
        severities = [
            c.severity for c in incident.contributors if c.severity is not None
        ]
        return {
            "opened_at": incident.opened_at.isoformat(),
            "zones": [zones.get(z, z) for z in incident.zone_ids],
            "areas": [areas.get(a, a) for a in incident.area_ids],
            "acknowledged": incident.acknowledged,
            # The highest contributing profile severity: filled once response
            # profiles exist (Phase 1 part 3); None until then.
            "severity": max(severities, default=None),
        }


class FoyerLastEvent(FoyerEntity, SensorEntity):
    """The last significant thing in the log, for dashboards (§13).

    Significant, not last: zone activity is thousands of rows a day and would
    keep overwriting the event somebody actually wants to see. The row itself
    is in the panel's log page; this is the one line a dashboard shows.
    """

    _attr_translation_key = "last_event"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_last_event"
        self.entity_id = f"sensor.{DOMAIN}_last_event"
        self._attr_device_info = hub_device(entry_id)

    @property
    def native_value(self) -> str:
        row = self._system.last_row
        return row.event_type if row else NONE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        row = self._system.last_row
        if row is None:
            return {"category": None, "severity": None, "when": None}
        zones = {z.id: z.name for z in self._system.config.zones}
        areas = {a.id: a.name for a in self._system.config.areas}
        return {
            "category": str(row.category),
            "severity": str(row.severity),
            "when": row.ts.isoformat(),
            "area": areas.get(row.area_id) if row.area_id else None,
            "zone": zones.get(row.zone_id) if row.zone_id else None,
            "channel": row.channel,
            "outcome": row.outcome,
            "incident_id": row.incident_id,
        }


class FoyerOpenZones(FoyerEntity, SensorEntity):
    _attr_translation_key = "open_zones"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_open_zones"
        self.entity_id = f"sensor.{DOMAIN}_open_zones"
        self._attr_device_info = hub_device(entry_id)

    def _open(self) -> list[str]:
        """Open intrusion zones. A smoke detector in alarm is not an open zone:
        it is on the technical channel's own entities."""
        active = self._system.state.active_zones
        return [
            z.name
            for z in self._system.config.zones
            if z.id in active and z.channel is Channel.INTRUSION
        ]

    @property
    def native_value(self) -> int:
        return len(self._open())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"zones": self._open()}


class FoyerCountdown(FoyerEntity, SensorEntity):
    """Seconds left on an exit, hold or entry timer; 0 when none is running.

    Ticks once a second only while a countdown runs, so the recorder does not
    hear from it the rest of the day.
    """

    _attr_translation_key = "countdown"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, system: FoyerSystem, entry_id: str, area: Area) -> None:
        super().__init__(system)
        self._area = area
        self._attr_unique_id = f"{entry_id}_countdown_{area.id}"
        self.entity_id = f"sensor.{DOMAIN}_countdown_{slugify(area.name)}"
        self._attr_device_info = area_device(entry_id, area)
        self._unsub_tick: CALLBACK_TYPE | None = None

    def _timer(self):
        timer = self._system.state.area(self._area.id).timer
        return timer if timer is not None and timer.kind in _COUNTDOWN_KINDS else None

    @property
    def native_value(self) -> int:
        timer = self._timer()
        if timer is None:
            return 0
        return max(0, round((timer.due - dt_util.utcnow()).total_seconds()))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        timer = self._timer()
        return {
            "kind": timer.kind.value if timer else None,
            "due": timer.due.isoformat() if timer else None,
        }

    @callback
    def _on_change(self) -> None:
        running = self._timer() is not None
        if running and self._unsub_tick is None:
            self._unsub_tick = async_track_time_interval(
                self.hass, self._tick, timedelta(seconds=1)
            )
        elif not running and self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None
        super()._on_change()

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._on_change()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None


class FoyerNextAutoAction(FoyerEntity, SensorEntity):
    """``sensor.foyer_next_auto_action`` (§9.4, §13): what happens next.

    The state is the **action** — `arm`, `disarm`, `switch`, or `idle` when
    nothing is scheduled — because that is a closed set an automation can
    trigger on and a panel can translate, and because a rule's name is free
    text that changes when somebody renames it (part 2 decision 10). When it
    happens, which rule, and any suspension covering it are attributes.

    It reports what is **scheduled**, not what will certainly happen: the
    guards are evaluated at the moment the rule acts. Predicting them here
    would be a second code path able to contradict the Decision (INV-1), and
    "it said it would arm and then did not" is exactly the mistrust §9.4's
    logging exists to prevent — the row under `system` is where the answer
    lives.
    """

    _attr_translation_key = "next_auto_action"
    IDLE = "idle"

    def __init__(self, system: FoyerSystem, entry_id: str) -> None:
        super().__init__(system)
        self._attr_unique_id = f"{entry_id}_next_auto_action"
        self.entity_id = f"sensor.{DOMAIN}_next_auto_action"
        self._attr_device_info = hub_device(entry_id)

    def _next(self) -> dict[str, Any] | None:
        return self._system.auto_status()["next"]

    @property
    def native_value(self) -> str:
        upcoming = self._next()
        return upcoming["action"] if upcoming else self.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        upcoming = self._next()
        if upcoming is None:
            return {
                "rule": None,
                "at": None,
                "scenario": None,
                "areas": [],
                "counting_down": False,
                "suspension": None,
                "enabled": self._system.state.auto_arming,
            }
        scenarios = {s.id: s.name for s in self._system.config.scenarios}
        areas = {a.id: a.name for a in self._system.config.areas}
        suspension = upcoming["suspension"]
        return {
            "rule": upcoming["rule_name"],
            "rule_id": upcoming["rule_id"],
            "at": upcoming["at"],
            "scenario": scenarios.get(upcoming["scenario_id"] or ""),
            "areas": [areas.get(a, a) for a in upcoming["area_ids"]],
            # Whether the countdown is already running, which is the one
            # state in which somebody can still stop it.
            "counting_down": upcoming["pending_id"] is not None,
            "suspension": (suspension or {}).get("name")
            or (suspension["kind"] if suspension else None),
            "enabled": self._system.state.auto_arming,
        }
