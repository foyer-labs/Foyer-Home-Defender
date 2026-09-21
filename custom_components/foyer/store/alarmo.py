"""Bringing an Alarmo configuration across into Foyer (SPEC §20.2). Pure.

**What this is, and what it is not.** It reads ``.storage/alarmo.storage``,
the file Alarmo keeps its configuration in. That file is Alarmo's internal
format, which its author may change in any release, without notice and without
fault — it was never offered as an interface to anybody. So this is a
best-effort tool that says what it could not convert, never a guaranteed
migration. It refuses a file whose version it has not been checked against,
by name, rather than parse it hopefully; it refuses a file whose shape is
wrong rather than bring half of it across; and every line of what it did not
do is in the report it returns, which the panel shows before anything is
written.

It lives in ``store/`` beside the migrations rather than in ``core/``: it is a
translation from one stored document to another, like them, and the engine
never needs it. It is pure for the same reason they are — the whole of it can
be tested without Home Assistant, and ``api/alarmo.py`` does the reading, the
permissions and the writing.

The document on disk
====================

Read from Alarmo's own source, not from its documentation: Alarmo 1.10.19
(released 2026-08-09), default branch at commit 47b31a6 (2026-09-14), whose
backend and storage code is identical to the release. Read on 2026-09-21.
``custom_components/alarmo/store.py`` is what writes it. If upstream changes
the shape, this is the paragraph to compare against.

Home Assistant's ``Store`` envelope, and nothing else carries a version::

    {"version": 6, "minor_version": 3, "key": "alarmo.storage", "data": {...}}

There is no Alarmo release number anywhere in the file. ``version`` and
``minor_version`` are the only markers, so they are what a refusal names.
Storage 6.1 was first written by Alarmo 1.9.5, 6.2 by 1.9.11 and 6.3 by 1.9.14;
the 1.10 series still writes 6.3 and added three sensor fields without a bump
(``entry_delay`` in 1.10.11, ``delay_on`` in 1.10.16, and the config flag
``ignore_blocking_sensors_after_trigger`` in 1.10.9), each of which may be
absent and defaults safely. 6.2 added ``config.code_mode_change_required``; 6.3
only de-duplicated group members. Anything below 6.1 renamed or moved fields
this module does not read, and is refused.

``data`` always has five lists and one object. Ids are epoch seconds as
strings, except sensors, which are keyed by their entity id::

    config:  {code_arm_required, code_mode_change_required, code_disarm_required,
              code_format: "number"|"text", disarm_after_trigger,
              ignore_blocking_sensors_after_trigger,
              master: {enabled, name},
              mqtt: {enabled, state_topic, state_payload, command_topic,
                     command_payload, require_code, event_topic}}
    areas:   [{area_id, name,
               modes: {<mode>: {enabled, exit_time, entry_time, trigger_time}}}]
    sensors: [{entity_id, type, modes: [<mode>], use_exit_delay, use_entry_delay,
               always_on, arm_on_close, allow_open, trigger_unavailable,
               auto_bypass, auto_bypass_modes: [<mode>], area, enabled,
               entry_delay: int|null, delay_on: int|null}]
    users:   [{user_id, name, enabled, code, can_arm, can_disarm,
               is_override_code, code_format, code_length, area_limit: [area_id]}]
    automations: [{automation_id, type: "notification"|"action", name, enabled,
                   triggers: [{event, area, modes} | {entity_id, state}],
                   actions: [{service, entity_id, data}]}]
    sensor_groups: [{group_id, name, entities: [entity_id], timeout, event_count}]

A mode is one of ``armed_away``, ``armed_home``, ``armed_night``,
``armed_vacation``, ``armed_custom_bypass``, and ``area.modes`` may hold only
some of them. A sensor type is ``door``, ``window``, ``motion``, ``tamper``,
``environmental`` or ``other``. A trigger's ``event`` is one of ``armed``,
``disarmed``, ``triggered``, ``untriggered``, ``arm_failure``, ``arming``,
``pending``; its ``area`` is an area id, or null or 0 for "any"; its ``modes``
of ``[]`` means any mode.

How Alarmo reads those fields, which is what the mapping below preserves:

* A sensor is violated when its state is ``on``, ``open`` or ``unlocked`` —
  one list for every domain and every sensor, which is exactly what INV-5
  exists to refuse. ``unavailable`` is safe unless ``trigger_unavailable``.
* The exit delay belongs to an area and a mode (``exit_time``). The entry
  delay is the sensor's ``entry_delay`` if set, else the area's ``entry_time``
  for the armed mode, and zero for an always-on sensor or one with
  ``use_entry_delay`` false. ``trigger_time`` is how long it stays triggered;
  0 means for ever.
* ``use_exit_delay`` false: the sensor must be closed when arming starts, and
  opening during the exit delay aborts it. ``allow_open``: may be open at
  arming. ``auto_bypass`` with ``auto_bypass_modes``: bypassed when open at
  arming in those modes. ``arm_on_close``: closing it during the exit delay
  arms five seconds later. ``delay_on``: must stay violated that long first.
* A group alarms when ``event_count`` of its sensors are violated within
  ``timeout`` seconds, and its members do not alarm on their own.
* ``code`` is ``base64(bcrypt(code))``. It is never read here (see below).

What it becomes
===============

The numbered decisions are in the session report of Phase 5 part 3; the short
form, so the code can be read against it:

* **Areas** follow Alarmo's areas, split by the modes a sensor is active in: in
  Foyer a scenario arms whole areas, so "the PIR only in Away, the doors in
  every mode" is two areas that Away arms together and Home arms one of.
* **Scenarios**, one per mode an area has enabled, arming every area that mode
  watches. An existing scenario reporting the same master state is extended
  instead of duplicated, or the master would refuse the mode (decision 41).
* **Zones** arrive switched off with ``trigger_confirmed`` false and Foyer's
  own proposal filled in (INV-5): nothing Alarmo believed about ``on`` is
  carried across. Technical and tamper sensors keep their channel.
* **Delays** take the longest wherever Alarmo had several and Foyer has room
  for one, because a delay too short locks somebody out of their own house
  with the siren going. Every such choice is a report line.
* **People** come across without a code, ever: a hash in a foreign format is
  not something this project can verify (INV-2, §8.1).
* **Actions**: sirens and switches only, and the rest is reported.
* **Groups** are reported, not created: a group needs enabled members, and
  every imported zone starts switched off.

Untrusted input
===============

Nothing in the file chooses an id, a hash, a webhook or a URL. Every id is
minted by the caller's ``new_id``; every field is type-checked before it is
used; a shape that does not match is refused whole, naming where. Names are
the only strings that travel, and they travel as names.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
import re
from typing import Any

from ..core.models import (
    MAX_ENTRY_DELAY,
    MAX_EXIT_DELAY,
    MAX_SIREN_DURATION,
    ActionKind,
    Area as FoyerArea,
    ArmPolicy,
    FoyerConfig,
    Moment,
    Permission,
    ProfileAction,
    ResponseProfile,
    Scenario,
    StateTrigger,
    User,
    Zone,
    ZoneType,
)
from ..core.presets import PRESETS
from ..core.privacy import new_pseudonym
from ..core.proposals import propose_trigger

SOURCE_KEY = "alarmo.storage"
# Storage versions whose shape this module was written against (see the
# module docstring). A version outside this set is refused by name.
READ_VERSIONS: frozenset[tuple[int, int]] = frozenset({(6, 1), (6, 2), (6, 3)})
# Alarmo's own order of modes, which is also the order scenarios are made in.
MODES: tuple[str, ...] = (
    "armed_away",
    "armed_home",
    "armed_night",
    "armed_vacation",
    "armed_custom_bypass",
)
SENSOR_TYPES = frozenset(
    {"door", "window", "motion", "tamper", "environmental", "other"}
)
EVENTS = frozenset(
    {
        "armed",
        "disarmed",
        "triggered",
        "untriggered",
        "arm_failure",
        "arming",
        "pending",
    }
)
# A generous ceiling: large enough for any house, small enough that a file
# built to exhaust memory is refused before it is walked.
MAX_ITEMS = 1000
MAX_NAME = 200
# The domains Alarmo's one list of "violated" states means anything for. A
# numeric sensor is never violated in Alarmo, so it is not a zone to bring.
SENSOR_DOMAINS = frozenset(
    {"binary_sensor", "cover", "lock", "switch", "input_boolean"}
)
_ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")

_SECTIONS = ("config", "areas", "sensors", "users", "automations", "sensor_groups")
_KNOWN: dict[str, frozenset[str]] = {
    "config": frozenset(
        {
            "code_arm_required",
            "code_mode_change_required",
            "code_disarm_required",
            "code_format",
            "disarm_after_trigger",
            "ignore_blocking_sensors_after_trigger",
            "master",
            "mqtt",
        }
    ),
    "areas": frozenset({"area_id", "name", "modes"}),
    "modes": frozenset({"enabled", "exit_time", "entry_time", "trigger_time"}),
    "sensors": frozenset(
        {
            "entity_id",
            "type",
            "modes",
            "use_exit_delay",
            "use_entry_delay",
            "always_on",
            "arm_on_close",
            "allow_open",
            "trigger_unavailable",
            "auto_bypass",
            "auto_bypass_modes",
            "area",
            "enabled",
            "entry_delay",
            "delay_on",
        }
    ),
    "users": frozenset(
        {
            "user_id",
            "name",
            "enabled",
            "code",
            "can_arm",
            "can_disarm",
            "is_override_code",
            "code_format",
            "code_length",
            "area_limit",
            # Dropped by Alarmo itself at load; older files still carry it.
            "is_admin",
        }
    ),
    "automations": frozenset(
        {"automation_id", "type", "name", "triggers", "actions", "enabled"}
    ),
    "sensor_groups": frozenset(
        {"group_id", "name", "entities", "timeout", "event_count"}
    ),
}


# --- the report --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Line:
    """One sentence of the report, as a stable code and its values.

    The backend writes no word a person reads: the panel turns ``code`` into
    a sentence from ``alarmo.line.<code>`` in its own language.
    """

    code: str
    params: Mapping[str, str | int] = field(default_factory=dict)


class Refused(Exception):
    """The file is not one this importer will bring across. Nothing was."""

    def __init__(self, code: str, **params: str | int) -> None:
        super().__init__(code)
        self.line = Line(code, params)


@dataclass(frozen=True, slots=True)
class Labels:
    """The words new things are named with, supplied by the panel.

    A scenario made for Alarmo's Away mode needs a name, and the backend writes
    no word a person reads — so the panel sends them, from its translations,
    in the language of whoever pressed the button. Missing or unusable, the
    importer falls back to Alarmo's own identifiers, which are not words.
    """

    modes: Mapping[str, str] = field(default_factory=dict)
    # "{area}" and "{modes}", for an Alarmo area that has to become several.
    split: str = "{area} ({modes})"
    # "{area}", for the response profile made for an Alarmo area's actions.
    profile: str = "{area} (Alarmo)"

    def mode(self, mode: str) -> str:
        return self.modes.get(mode) or mode

    @staticmethod
    def parse(data: Any) -> Labels:
        if not isinstance(data, Mapping):
            return Labels()
        modes = data.get("modes")
        clean = {
            m: v.strip()
            for m, v in (modes.items() if isinstance(modes, Mapping) else ())
            if m in MODES and isinstance(v, str) and 0 < len(v.strip()) <= 60
        }
        default = Labels()
        split = data.get("split")
        profile = data.get("profile")
        return Labels(
            modes=clean,
            split=split
            if isinstance(split, str)
            and "{area}" in split
            and "{modes}" in split
            and len(split) <= 80
            else default.split,
            profile=profile
            if isinstance(profile, str) and "{area}" in profile and len(profile) <= 80
            else default.profile,
        )


@dataclass(frozen=True, slots=True)
class EntityInfo:
    """What Home Assistant knows about an entity right now, for the proposal."""

    state: str | None = None
    name: str | None = None
    device_class: str | None = None


@dataclass(frozen=True, slots=True)
class ImportPlan:
    """The configuration an import would store, and what it could not do."""

    config: FoyerConfig
    lines: tuple[Line, ...]
    counts: Mapping[str, int]


# --- reading the file --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Mode:
    enabled: bool
    exit_time: int
    entry_time: int
    trigger_time: int  # 0: for ever


@dataclass(frozen=True, slots=True)
class _Area:
    id: str
    name: str
    modes: Mapping[str, _Mode]

    @property
    def enabled_modes(self) -> tuple[str, ...]:
        return tuple(m for m in MODES if m in self.modes and self.modes[m].enabled)


@dataclass(frozen=True, slots=True)
class _Sensor:
    entity_id: str
    type: str
    modes: tuple[str, ...]
    use_exit_delay: bool
    use_entry_delay: bool
    always_on: bool
    arm_on_close: bool
    allow_open: bool
    trigger_unavailable: bool
    auto_bypass: bool
    auto_bypass_modes: tuple[str, ...]
    area: str | None
    enabled: bool
    entry_delay: int | None
    delay_on: int | None


@dataclass(frozen=True, slots=True)
class _User:
    name: str
    enabled: bool
    can_arm: bool
    can_disarm: bool
    is_override_code: bool
    area_limit: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Trigger:
    event: str | None  # None: an entity trigger, which Foyer has no moment for
    area: str | None  # None: any area
    modes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Action:
    service: str
    entity_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Automation:
    name: str
    type: str
    enabled: bool
    triggers: tuple[_Trigger, ...]
    actions: tuple[_Action, ...]


@dataclass(frozen=True, slots=True)
class _Group:
    name: str
    entities: tuple[str, ...]
    timeout: int
    event_count: int


@dataclass(frozen=True, slots=True)
class Alarmo:
    """The file, checked. Only what the mapping reads is kept."""

    version: tuple[int, int]
    flags: Mapping[str, bool]
    mqtt_enabled: bool
    areas: tuple[_Area, ...]
    sensors: tuple[_Sensor, ...]
    users: tuple[_User, ...]
    automations: tuple[_Automation, ...]
    groups: tuple[_Group, ...]
    unknown_fields: tuple[str, ...]


class _Reader:
    """Type checks that name where they failed, and the unknown keys seen."""

    def __init__(self) -> None:
        self.unknown: set[str] = set()

    def fail(self, where: str) -> Refused:
        return Refused("invalid", where=where)

    def obj(self, value: Any, where: str, known: str | None = None) -> Mapping:
        if not isinstance(value, Mapping):
            raise self.fail(where)
        if known is not None:
            for key in value:
                if key not in _KNOWN[known]:
                    self.unknown.add(f"{known}.{key}")
        return value

    def items(self, value: Any, where: str) -> list:
        if not isinstance(value, list):
            raise self.fail(where)
        if len(value) > MAX_ITEMS:
            raise Refused("too_many", where=where, limit=MAX_ITEMS)
        return value

    def boolean(self, data: Mapping, key: str, where: str, default: bool) -> bool:
        value = data.get(key, default)
        if not isinstance(value, bool):
            raise self.fail(f"{where}.{key}")
        return value

    def number(self, data: Mapping, key: str, where: str) -> int | None:
        value = data.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise self.fail(f"{where}.{key}")
        return value

    def text(self, data: Mapping, key: str, where: str, default: str = "") -> str:
        value = data.get(key, default)
        if value is None:
            value = default
        if not isinstance(value, str) or len(value) > MAX_NAME:
            raise self.fail(f"{where}.{key}")
        return value

    def area_ref(self, value: Any, where: str) -> str | None:
        """An area id, or "any" — which Alarmo writes as null, "" or 0."""
        if value in (None, "", 0) and not isinstance(value, bool):
            return None
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        if not isinstance(value, str) or len(value) > MAX_NAME:
            raise self.fail(where)
        return value

    def modes(self, value: Any, where: str) -> tuple[str, ...]:
        # A mode this importer does not know is refused, not dropped: a
        # sensor that silently lost the mode it was armed in is a sensor
        # that silently stopped watching.
        return tuple(self._mode(m, where) for m in self.items(value or [], where))

    def _mode(self, mode: Any, where: str) -> str:
        if mode not in MODES:
            raise self.fail(where)
        return mode

    def entities(self, value: Any, where: str) -> tuple[str, ...]:
        if isinstance(value, str):
            value = [value]
        if value is None:
            return ()
        return tuple(self.entity(e, where) for e in self.items(value, where))

    def entity(self, value: Any, where: str) -> str:
        if not isinstance(value, str) or not _ENTITY_ID.match(value):
            raise self.fail(where)
        return value


def read(document: Any) -> Alarmo:
    """Check the whole file, or refuse it naming where. Never half of it."""
    r = _Reader()
    if not isinstance(document, Mapping) or document.get("key") != SOURCE_KEY:
        raise Refused("not_alarmo")
    major, minor = document.get("version"), document.get("minor_version", 1)
    if (
        isinstance(major, bool)
        or isinstance(minor, bool)
        or not isinstance(major, int)
        or not isinstance(minor, int)
    ):
        raise Refused("not_alarmo")
    if (major, minor) not in READ_VERSIONS:
        raise Refused("version_unsupported", version=f"{major}.{minor}")
    data = r.obj(document.get("data"), "data")
    for section in _SECTIONS:
        if section not in data:
            raise r.fail(section)

    config = r.obj(data["config"], "config", "config")
    flags = {
        key: r.boolean(config, key, "config", False)
        for key in (
            "code_arm_required",
            "code_mode_change_required",
            "code_disarm_required",
            "disarm_after_trigger",
            "ignore_blocking_sensors_after_trigger",
        )
    }
    mqtt = config.get("mqtt") or {}
    mqtt_enabled = r.boolean(
        r.obj(mqtt, "config.mqtt"), "enabled", "config.mqtt", False
    )

    areas = []
    for i, raw in enumerate(r.items(data["areas"], "areas")):
        where = f"areas[{i}]"
        a = r.obj(raw, where, "areas")
        area_id = r.area_ref(a.get("area_id"), f"{where}.area_id")
        if area_id is None:
            raise r.fail(f"{where}.area_id")
        modes = {}
        for mode, entry in r.obj(a.get("modes", {}), f"{where}.modes").items():
            here = f"{where}.modes.{mode}"
            if mode not in MODES:
                raise r.fail(here)
            m = r.obj(entry, here, "modes")
            modes[mode] = _Mode(
                enabled=r.boolean(m, "enabled", here, False),
                exit_time=r.number(m, "exit_time", here) or 0,
                entry_time=r.number(m, "entry_time", here) or 0,
                trigger_time=r.number(m, "trigger_time", here) or 0,
            )
        areas.append(
            _Area(id=area_id, name=r.text(a, "name", where).strip(), modes=modes)
        )

    sensors = []
    for i, raw in enumerate(r.items(data["sensors"], "sensors")):
        where = f"sensors[{i}]"
        s = r.obj(raw, where, "sensors")
        sensor_type = s.get("type", "other")
        if sensor_type not in SENSOR_TYPES:
            raise r.fail(f"{where}.type")
        sensors.append(
            _Sensor(
                entity_id=r.entity(s.get("entity_id"), f"{where}.entity_id"),
                type=sensor_type,
                modes=r.modes(s.get("modes"), f"{where}.modes"),
                use_exit_delay=r.boolean(s, "use_exit_delay", where, True),
                use_entry_delay=r.boolean(s, "use_entry_delay", where, True),
                always_on=r.boolean(s, "always_on", where, False),
                arm_on_close=r.boolean(s, "arm_on_close", where, False),
                allow_open=r.boolean(s, "allow_open", where, False),
                trigger_unavailable=r.boolean(s, "trigger_unavailable", where, False),
                auto_bypass=r.boolean(s, "auto_bypass", where, False),
                auto_bypass_modes=r.modes(
                    s.get("auto_bypass_modes"), f"{where}.auto_bypass_modes"
                ),
                area=r.area_ref(s.get("area"), f"{where}.area"),
                enabled=r.boolean(s, "enabled", where, True),
                entry_delay=r.number(s, "entry_delay", where),
                delay_on=r.number(s, "delay_on", where),
            )
        )

    users = []
    for i, raw in enumerate(r.items(data["users"], "users")):
        where = f"users[{i}]"
        u = r.obj(raw, where, "users")
        # The code is looked at only to be sure it is what it claims to be
        # — a string — and then never again (INV-2).
        r.text(u, "code", where)
        users.append(
            _User(
                name=r.text(u, "name", where).strip(),
                enabled=r.boolean(u, "enabled", where, True),
                can_arm=r.boolean(u, "can_arm", where, False),
                can_disarm=r.boolean(u, "can_disarm", where, False),
                is_override_code=r.boolean(u, "is_override_code", where, False),
                area_limit=tuple(
                    ref
                    for j, a in enumerate(
                        r.items(u.get("area_limit") or [], f"{where}.area_limit")
                    )
                    if (ref := r.area_ref(a, f"{where}.area_limit[{j}]")) is not None
                ),
            )
        )

    automations = []
    for i, raw in enumerate(r.items(data["automations"], "automations")):
        where = f"automations[{i}]"
        a = r.obj(raw, where, "automations")
        triggers = []
        for j, raw_t in enumerate(
            r.items(a.get("triggers") or [], f"{where}.triggers")
        ):
            here = f"{where}.triggers[{j}]"
            t = r.obj(raw_t, here)
            if "event" in t:
                event = t.get("event")
                if event not in EVENTS:
                    raise r.fail(f"{here}.event")
                triggers.append(
                    _Trigger(
                        event=event,
                        area=r.area_ref(t.get("area"), f"{here}.area"),
                        modes=r.modes(t.get("modes"), f"{here}.modes"),
                    )
                )
            else:
                triggers.append(_Trigger(event=None, area=None, modes=()))
        actions = []
        for j, raw_act in enumerate(
            r.items(a.get("actions") or [], f"{where}.actions")
        ):
            here = f"{where}.actions[{j}]"
            act = r.obj(raw_act, here)
            actions.append(
                _Action(
                    service=r.text(act, "service", here).strip(),
                    entity_ids=r.entities(act.get("entity_id"), f"{here}.entity_id"),
                )
            )
        kind = a.get("type")
        if kind not in ("notification", "action"):
            raise r.fail(f"{where}.type")
        automations.append(
            _Automation(
                name=r.text(a, "name", where).strip(),
                type=kind,
                enabled=r.boolean(a, "enabled", where, True),
                triggers=tuple(triggers),
                actions=tuple(actions),
            )
        )

    groups = []
    for i, raw in enumerate(r.items(data["sensor_groups"], "sensor_groups")):
        where = f"sensor_groups[{i}]"
        g = r.obj(raw, where, "sensor_groups")
        groups.append(
            _Group(
                name=r.text(g, "name", where).strip(),
                entities=r.entities(g.get("entities"), f"{where}.entities"),
                timeout=r.number(g, "timeout", where) or 0,
                event_count=r.number(g, "event_count", where) or 2,
            )
        )

    return Alarmo(
        version=(major, minor),
        flags=flags,
        mqtt_enabled=mqtt_enabled,
        areas=tuple(areas),
        sensors=tuple(sensors),
        users=tuple(users),
        automations=tuple(automations),
        groups=tuple(groups),
        unknown_fields=tuple(sorted(r.unknown)),
    )


# --- turning it into Foyer ---------------------------------------------------------

# Alarmo's automation events, as the moments of §6.1 that mean the same thing.
# `arming` has no moment of its own in Foyer (an exit delay starting is not a
# moment a profile answers), and `untriggered` — leaving `triggered`, by a
# disarm or by the siren time running out — is both of the moments that end
# an alarm. A switch turned off at either is what Alarmo users write to pair
# with the one they turned on.
_MOMENTS: Mapping[str, frozenset[Moment]] = {
    "armed": frozenset({Moment.ARMED}),
    "disarmed": frozenset({Moment.DISARMED}),
    "triggered": frozenset({Moment.TRIGGERED}),
    "untriggered": frozenset({Moment.SIREN_CUTOFF, Moment.DISARMED}),
    "arm_failure": frozenset({Moment.ARM_FAILED}),
    "pending": frozenset({Moment.ENTRY_STARTED}),
}


def _slug(name: str) -> str:
    # The same slug validation uses to refuse two names alike (they become
    # entity ids); a name that passes here passes there.
    return re.sub(r"[^0-9a-z]+", "_", name.casefold()).strip("_")


class _Names:
    """Hands out names no other area, scenario or zone already has."""

    def __init__(self, taken: list[str]) -> None:
        self.taken = {_slug(n) for n in taken}

    def claim(self, wanted: str) -> str:
        name, n = wanted, 1
        while not _slug(name) or _slug(name) in self.taken:
            n += 1
            name = f"{wanted} {n}"
        self.taken.add(_slug(name))
        return name


def _clamp(value: int, high: int) -> int:
    return max(0, min(value, high))


@dataclass
class _Draft:
    """A zone before its area exists: which Alarmo area, which modes."""

    sensor: _Sensor
    area: _Area
    modes: frozenset[str] | None  # None: always on, watched in every mode
    zone_type: ZoneType
    trigger: frozenset[str]
    name: str
    arm_policy: ArmPolicy


def plan(
    document: Any,
    config: FoyerConfig,
    entities: Mapping[str, EntityInfo],
    labels: Labels,
    new_id: Callable[[], str],
) -> ImportPlan:
    """What bringing this file across would store, and what it would not.

    Raises ``Refused`` for a file it will not read. Otherwise returns the
    configuration merged with what the file converts to — validated by the
    caller like every other edit — and the report, first line first.
    """
    alarmo = read(document)
    lines: list[Line] = []
    notes: list[Line] = []

    def note(code: str, **params: str | int) -> None:
        notes.append(Line(code, params))

    areas_by_id = {a.id: a for a in alarmo.areas}
    zone_names = _Names([z.name for z in config.zones])
    existing = {z.entity_id: z for z in config.zones}

    # 1. Sensors into drafts, each with the modes it is watched in.
    drafts: list[_Draft] = []
    seen: set[str] = set()
    for sensor in alarmo.sensors:
        entity = sensor.entity_id
        if entity in seen:
            note("sensor_duplicate", entity=entity)
            continue
        seen.add(entity)
        if entity in existing:
            note("sensor_exists", entity=entity, zone=existing[entity].name)
            continue
        if entity.split(".", 1)[0] not in SENSOR_DOMAINS:
            note("sensor_domain", entity=entity)
            continue
        area = areas_by_id.get(sensor.area) if sensor.area else None
        if area is None and sensor.area is None and len(alarmo.areas) == 1:
            area = alarmo.areas[0]
        if area is None:
            note("sensor_no_area", entity=entity)
            continue
        info = entities.get(entity) or EntityInfo()
        if sensor.type == "environmental":
            zone_type = ZoneType.TECHNICAL
        elif sensor.type == "tamper":
            zone_type = ZoneType.TAMPER
        elif sensor.always_on:
            zone_type = ZoneType.H24
        else:
            zone_type = None
        if zone_type in (ZoneType.TECHNICAL, ZoneType.TAMPER) and not sensor.always_on:
            note("sensor_made_always_on", entity=entity, type=sensor.type)
        modes: frozenset[str] | None = None
        if zone_type is None:
            modes = frozenset(sensor.modes) & frozenset(area.enabled_modes)
            if not modes:
                note("sensor_no_mode", entity=entity)
                continue
            delays = [_entry_delay(sensor, area, m) for m in modes]
            zone_type = ZoneType.DELAYED if any(delays) else ZoneType.INSTANT
            if sensor.entry_delay is None and len(set(delays)) > 1:
                note(
                    "entry_delay_varies",
                    entity=entity,
                    seconds=_clamp(max(delays), MAX_ENTRY_DELAY),
                )
        name = zone_names.claim((info.name or "").strip()[:MAX_NAME] or entity)
        if info.state is None and info.name is None:
            note("sensor_missing", entity=entity, zone=name)
        drafts.append(
            _Draft(
                sensor=sensor,
                area=area,
                modes=modes,
                zone_type=zone_type,
                trigger=_proposed_trigger(entity, info),
                name=name,
                arm_policy=_arm_policy(sensor, modes, note, name),
            )
        )
        if sensor.trigger_unavailable:
            note("trigger_unavailable", zone=name)
        if sensor.delay_on:
            note("delay_on", zone=name, seconds=sensor.delay_on)
        if not sensor.enabled:
            note("sensor_was_disabled", zone=name)
        if sensor.entry_delay is not None and sensor.entry_delay > MAX_ENTRY_DELAY:
            note(
                "delay_capped",
                item=name,
                seconds=sensor.entry_delay,
                max=MAX_ENTRY_DELAY,
            )

    # 2. Foyer areas: one per Alarmo area and set of modes (see the docstring).
    area_names = _Names([a.name for a in config.areas])
    new_areas: list[FoyerArea] = []
    area_modes: dict[str, frozenset[str]] = {}  # Foyer area id -> modes
    placed: dict[int, str] = {}  # id(draft) -> Foyer area id
    by_alarmo: dict[str, list[str]] = {}  # Alarmo area id -> Foyer area ids
    for area in alarmo.areas:
        mine = [d for d in drafts if d.area is area]
        if not mine:
            note("area_empty", area=area.name or area.id)
            continue
        full = frozenset(area.enabled_modes)
        if not full:
            # No mode to arm it in: nothing Foyer could make of it would
            # ever be armed, and an always-on zone still needs an area that
            # says which state it reports.
            note("area_no_modes", area=area.name or area.id)
            for d in mine:
                note("sensor_no_mode", entity=d.sensor.entity_id)
            continue
        sets = sorted(
            {d.modes for d in mine if d.modes is not None},
            key=lambda s: (-len(s), [MODES.index(m) for m in MODES if m in s]),
        )
        # Always-on zones care about no mode; they live with the area that
        # every mode arms, so they are shown where the house is.
        if any(d.modes is None for d in mine) and full not in sets:
            sets.insert(0, full)
        created = []
        for modes in sets:
            base = area.name or area.id
            wanted = (
                base
                if len(sets) == 1 or modes == full
                else labels.split.replace("{area}", base).replace(
                    "{modes}", ", ".join(labels.mode(m) for m in MODES if m in modes)
                )
            )
            name = area_names.claim(wanted)
            if name != wanted:
                note("renamed", kind="area", wanted=wanted, name=name)
            exits = [area.modes[m].exit_time for m in modes]
            entries = [area.modes[m].entry_time for m in modes]
            if len(set(exits)) > 1:
                note(
                    "exit_delay_varies",
                    area=name,
                    seconds=_clamp(max(exits), MAX_EXIT_DELAY),
                )
            if max(exits) > MAX_EXIT_DELAY:
                note("delay_capped", item=name, seconds=max(exits), max=MAX_EXIT_DELAY)
            if max(entries) > MAX_ENTRY_DELAY:
                note(
                    "delay_capped", item=name, seconds=max(entries), max=MAX_ENTRY_DELAY
                )
            foyer = FoyerArea(
                id=new_id(),
                name=name,
                ha_state_when_armed=next(m for m in MODES if m in modes),
                default_exit_delay=_clamp(max(exits), MAX_EXIT_DELAY),
                default_entry_delay=_clamp(max(entries), MAX_ENTRY_DELAY),
            )
            new_areas.append(foyer)
            area_modes[foyer.id] = modes
            created.append(foyer)
        by_alarmo[area.id] = [a.id for a in created]
        if len(created) > 1:
            note(
                "area_split",
                area=area.name or area.id,
                areas=", ".join(a.name for a in created),
            )
        home = next(a for a in created if area_modes[a.id] == sets[0])
        for d in mine:
            placed[id(d)] = (
                home.id
                if d.modes is None
                else next(a.id for a in created if area_modes[a.id] == d.modes)
            )

    # 3. The zones themselves, switched off and unconfirmed (INV-5).
    new_zones = []
    # Alarmo lets a sensor that uses the exit delay be open when arm is
    # pressed; Foyer's `block` refuses to start arming with it open (§5.4).
    # One line for all of them, not one per door.
    open_at_arming = 0
    for d in drafts:
        if id(d) not in placed:
            continue
        values = dict(PRESETS[d.zone_type])
        if d.zone_type in (ZoneType.INSTANT, ZoneType.DELAYED):
            values["arm_policy"] = d.arm_policy
            if d.arm_policy is ArmPolicy.BLOCK and d.sensor.use_exit_delay:
                open_at_arming += 1
        new_zones.append(
            Zone(
                id=new_id(),
                name=d.name,
                entity_id=d.sensor.entity_id,
                area_id=placed[id(d)],
                trigger=StateTrigger(states=d.trigger),
                type=d.zone_type,
                entry_delay=(
                    _clamp(d.sensor.entry_delay, MAX_ENTRY_DELAY)
                    if d.zone_type is ZoneType.DELAYED
                    and d.sensor.entry_delay is not None
                    else None
                ),
                enabled=False,
                trigger_confirmed=False,
                **values,
            )
        )

    if open_at_arming:
        note("arm_while_open", zones=open_at_arming)

    # 4. Scenarios: one per mode an imported area is armed in.
    scenario_names = _Names([s.name for s in config.scenarios])
    scenarios = list(config.scenarios)
    new_scenarios = extended = 0
    for mode in MODES:
        members = tuple(a.id for a in new_areas if mode in area_modes[a.id])
        if not members:
            if any(mode in a.enabled_modes for a in alarmo.areas):
                note("mode_unused", mode=mode)
            continue
        same = [s for s in scenarios if s.ha_master_state == mode]
        if len(same) == 1:
            target = same[0]
            scenarios[scenarios.index(target)] = replace(
                target, areas=(*target.areas, *members)
            )
            extended += 1
            note("scenario_extended", scenario=target.name, mode=mode)
            continue
        if len(same) > 1:
            note("scenario_mode_ambiguous", mode=mode)
        watching = [a for a in alarmo.areas if mode in a.enabled_modes]
        exits = [a.modes[mode].exit_time for a in watching]
        sirens = [a.modes[mode].trigger_time for a in watching]
        wanted = labels.mode(mode)
        name = scenario_names.claim(wanted)
        if name != wanted:
            note("renamed", kind="scenario", wanted=wanted, name=name)
        if len(set(exits)) > 1:
            note(
                "exit_delay_varies",
                area=name,
                seconds=_clamp(max(exits), MAX_EXIT_DELAY),
            )
        siren = max(sirens) if sirens and 0 not in sirens else 0
        if siren == 0 or siren > MAX_SIREN_DURATION:
            note(
                "siren_capped",
                scenario=name,
                seconds=siren,
                max=MAX_SIREN_DURATION,
            )
        scenarios.append(
            Scenario(
                id=new_id(),
                name=name,
                areas=members,
                ha_master_state=mode,
                exit_delay_override=_clamp(max(exits), MAX_EXIT_DELAY),
                siren_duration_override=(
                    MAX_SIREN_DURATION if siren == 0 else min(siren, MAX_SIREN_DURATION)
                ),
            )
        )
        new_scenarios += 1

    # 5. People, never with a code.
    known_people = {u.name.strip().casefold() for u in config.users}
    new_users = []
    for person in alarmo.users:
        if not person.name:
            note("person_unnamed")
            continue
        if person.name.casefold() in known_people:
            note("person_exists", person=person.name)
            continue
        known_people.add(person.name.casefold())
        permissions = set()
        if person.can_arm:
            permissions |= {Permission.ARM.value, Permission.CHANGE_SCENARIO.value}
        if person.can_disarm:
            permissions.add(Permission.DISARM.value)
        if person.is_override_code:
            permissions.add(Permission.FORCE_ARM.value)
            note("override_code", person=person.name)
        allowed = None
        if person.area_limit:
            allowed = tuple(
                a for ref in person.area_limit for a in by_alarmo.get(ref, ())
            )
            if not allowed:
                note("person_scope_empty", person=person.name)
        new_users.append(
            User(
                id=new_id(),
                name=person.name,
                permissions=frozenset(permissions),
                allowed_area_ids=allowed,
                enabled=person.enabled,
                pseudonym=new_pseudonym(new_id()),
            )
        )

    # 6. Sirens and switches, into a profile per Alarmo area.
    profiles, assignments = _profiles(
        alarmo,
        config=config,
        by_alarmo=by_alarmo,
        alarmo_area_ids={a.id for a in alarmo.areas},
        labels=labels,
        new_id=new_id,
        note=note,
    )
    new_areas = [
        replace(a, response_profile_id=assignments.get(a.id)) for a in new_areas
    ]

    # 7. What there is no place for.
    for group in alarmo.groups:
        note(
            "group_not_imported",
            group=group.name or "—",
            n=group.event_count,
            members=len(group.entities),
            seconds=group.timeout,
        )
    for flag, value in alarmo.flags.items():
        if value:
            note("setting_not_imported", setting=flag)
    if alarmo.mqtt_enabled:
        note("setting_not_imported", setting="mqtt")
    for name in alarmo.unknown_fields:
        note("unknown_field", field=name)

    new_config = replace(
        config,
        areas=(*config.areas, *new_areas),
        zones=(*config.zones, *new_zones),
        scenarios=tuple(scenarios),
        users=(*config.users, *new_users),
        profiles=(*config.profiles, *profiles),
    )

    # The report: the two things nobody may miss first, then the rest in the
    # order the file was read.
    if new_users:
        lines.append(Line("codes", {"people": len(new_users)}))
    else:
        lines.append(Line("codes_nobody"))
    if new_zones:
        lines.append(Line("zones_to_confirm", {"zones": len(new_zones)}))
        lines.append(Line("unavailable_is_fault"))
    lines.extend(notes)
    counts = {
        "areas": len(new_areas),
        "zones": len(new_zones),
        "scenarios": new_scenarios,
        "scenarios_extended": extended,
        "people": len(new_users),
        "profiles": len(profiles),
    }
    if not any(counts.values()):
        raise Refused("nothing_to_import")
    return ImportPlan(config=new_config, lines=tuple(lines), counts=counts)


def _entry_delay(sensor: _Sensor, area: _Area, mode: str) -> int:
    """Alarmo's own reading of a sensor's entry delay in one mode."""
    if sensor.always_on or not sensor.use_entry_delay:
        return 0
    if sensor.entry_delay is not None:
        return sensor.entry_delay
    return area.modes[mode].entry_time


def _proposed_trigger(entity_id: str, info: EntityInfo) -> frozenset[str]:
    """Foyer's proposal for this entity, never Alarmo's belief (INV-5).

    The proposal is what the zone wizard would offer; it stays a proposal,
    because the zone arrives unconfirmed and switched off.
    """
    proposal = propose_trigger(entity_id, info.state)
    return frozenset(proposal.proposed or ("on",))


def _arm_policy(
    sensor: _Sensor,
    modes: frozenset[str] | None,
    note: Callable[..., None],
    name: str,
) -> ArmPolicy:
    if modes is None:
        return ArmPolicy.BLOCK
    if sensor.arm_on_close:
        note("arm_on_close", zone=name)
        return ArmPolicy.ARM_AFTER_CLOSING
    if sensor.allow_open:
        return ArmPolicy.IGNORE
    if sensor.auto_bypass and sensor.auto_bypass_modes:
        if modes <= frozenset(sensor.auto_bypass_modes):
            return ArmPolicy.AUTO_BYPASS
        # Bypassed in some of its modes and not others: Foyer's policy is one
        # per zone, and the safe half is the one that refuses to arm.
        note("auto_bypass_partial", zone=name)
    return ArmPolicy.BLOCK


def _profiles(
    alarmo: Alarmo,
    *,
    config: FoyerConfig,
    by_alarmo: Mapping[str, list[str]],
    alarmo_area_ids: set[str],
    labels: Labels,
    new_id: Callable[[], str],
    note: Callable[..., None],
) -> tuple[list[ResponseProfile], dict[str, str]]:
    """Sirens and switches, each into the profile of the areas it served.

    A profile replaces the default for the areas it is assigned to, so it
    starts as a copy of the default: an imported area that answered with a
    siren and nothing else would be an alarm that notifies nobody, which is
    the worst failure there is (decision 63).
    """
    wanted: dict[str, list[ProfileAction]] = {}  # Alarmo area id -> actions
    used = {m for a in alarmo.areas for m in a.enabled_modes}
    siren_duration = config.settings.siren_duration
    for automation in alarmo.automations:
        label = automation.name or "—"
        if not automation.enabled:
            note("automation_disabled", automation=label)
            continue
        if automation.type == "notification":
            note("automation_notification", automation=label)
            continue
        if not automation.triggers or any(t.event is None for t in automation.triggers):
            note("automation_trigger", automation=label)
            continue
        if any(t.event not in _MOMENTS for t in automation.triggers):
            note("automation_trigger", automation=label)
            continue
        if any(t.modes and not used <= set(t.modes) for t in automation.triggers):
            note("automation_modes", automation=label)
            continue
        refs = {t.area for t in automation.triggers}
        if None in refs:
            scope = set(alarmo_area_ids)
        elif refs <= alarmo_area_ids:
            scope = {r for r in refs if r is not None}
        else:
            note("automation_trigger", automation=label)
            continue
        moments = frozenset().union(*(_MOMENTS[t.event] for t in automation.triggers))
        actions = []
        for action in automation.actions:
            converted = _action(action, moments, siren_duration, new_id)
            if converted is None and action.service == "siren.turn_off":
                # A disarm and the siren cutoff stop what a siren action
                # started (§6.2): the automation that did it is not needed.
                note("siren_off_not_needed", automation=label)
            elif converted is None:
                note("action_not_imported", automation=label, service=action.service)
            else:
                actions.append(converted)
        if not actions:
            continue
        note("automation_imported", automation=label)
        for area_id in sorted(scope):
            wanted.setdefault(area_id, []).extend(actions)

    default = next(
        (p for p in config.profiles if p.id == config.settings.default_profile_id),
        None,
    )
    names = _Names([p.name for p in config.profiles])
    profiles: list[ResponseProfile] = []
    assignments: dict[str, str] = {}
    for area in alarmo.areas:
        if area.id not in wanted or not by_alarmo.get(area.id):
            continue
        base = [replace(a, id=new_id()) for a in (default.actions if default else ())]
        # Each area's own copies: two profiles sharing an action id would be
        # one action edited from two places.
        own = [replace(a, id=new_id()) for a in wanted[area.id]]
        profile = ResponseProfile(
            id=new_id(),
            name=names.claim(labels.profile.replace("{area}", area.name or area.id)),
            severity=default.severity if default else 1,
            actions=(*base, *own),
        )
        profiles.append(profile)
        note("profile_created", profile=profile.name)
        for foyer_area in by_alarmo[area.id]:
            assignments[foyer_area] = profile.id
    return profiles, assignments


def _action(
    action: _Action,
    moments: frozenset[Moment],
    siren_duration: int,
    new_id: Callable[[], str],
) -> ProfileAction | None:
    """A siren or a switch, if that is what this is; anything else is None."""
    domain, _, service = action.service.partition(".")
    entities = action.entity_ids
    if not entities or any(e.split(".", 1)[0] != domain for e in entities):
        return None
    if domain == "siren" and service == "turn_on":
        return ProfileAction(
            id=new_id(),
            kind=ActionKind.SIREN,
            moments=moments,
            params={"entity_ids": list(entities), "duration": siren_duration},
        )
    if domain == "switch" and service in ("turn_on", "turn_off"):
        return ProfileAction(
            id=new_id(),
            kind=ActionKind.SWITCH,
            moments=moments,
            params={
                "entity_ids": list(entities),
                "state": "on" if service == "turn_on" else "off",
                "revert_after": None,
            },
        )
    return None


__all__ = [
    "READ_VERSIONS",
    "SOURCE_KEY",
    "Alarmo",
    "EntityInfo",
    "ImportPlan",
    "Labels",
    "Line",
    "Refused",
    "plan",
    "read",
]
