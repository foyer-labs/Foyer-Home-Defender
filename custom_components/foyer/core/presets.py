"""Zone type presets (SPEC §4.3): UI sugar over explicit properties.

A preset fills the properties a zone type implies. The engine never reads the
type; every property stays editable afterwards (decision 2, 2026-09-14).
"""

from __future__ import annotations

from typing import Any

from .models import AlarmKind, ArmPolicy, Channel, EntryMode, ZoneType

_INTRUSION: dict[str, Any] = {
    "channel": Channel.INTRUSION,
    "entry_mode": EntryMode.INSTANT,
    "alarm_kind": AlarmKind.INTRUSION,
    "always_on": False,
    "arm_policy": ArmPolicy.BLOCK,
    "bypassable": True,
    # SPEC §4.3: only panic makes a point of it, but every zone may be set to
    # respond without the sounders the global silent list names (§4.2).
    "silent": False,
}

PRESETS: dict[ZoneType, dict[str, Any]] = {
    ZoneType.INSTANT: {**_INTRUSION},
    ZoneType.DELAYED: {**_INTRUSION, "entry_mode": EntryMode.DELAYED},
    ZoneType.FOLLOWER: {**_INTRUSION, "entry_mode": EntryMode.FOLLOWER},
    ZoneType.H24: {**_INTRUSION, "always_on": True, "bypassable": False},
    ZoneType.TAMPER: {
        **_INTRUSION,
        "alarm_kind": AlarmKind.TAMPER,
        "always_on": True,
        "bypassable": False,
    },
    ZoneType.PANIC: {
        **_INTRUSION,
        "alarm_kind": AlarmKind.PANIC,
        "always_on": True,
        "bypassable": False,
    },
    ZoneType.TECHNICAL: {
        **_INTRUSION,
        "channel": Channel.TECHNICAL,
        "always_on": True,
        "bypassable": False,
    },
    ZoneType.KEY: {
        **_INTRUSION,
        "channel": Channel.KEY,
        "arm_policy": ArmPolicy.IGNORE,
        "bypassable": False,
    },
}

# Types whose channel is not implemented yet. None since the technical
# channel (§5.5) landed in Phase 1 part 2; kept so a future type can be
# refused the same way rather than stored and never acted on.
UNAVAILABLE_TYPES: frozenset[ZoneType] = frozenset()


def preset(zone_type: ZoneType) -> dict[str, Any]:
    """The property values a type implies, as plain JSON values."""
    return {
        k: (v.value if hasattr(v, "value") else v)
        for k, v in PRESETS[zone_type].items()
    }
