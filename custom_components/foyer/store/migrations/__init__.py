"""Schema migrations for the stored configuration.

Home Assistant's Store calls ``migrate`` whenever the version on disk differs
from the version in code. Each step upgrades one (major, minor) version to the
next and is a pure function over the JSON document, so it can be tested without
Home Assistant.
"""

from __future__ import annotations

from collections.abc import Callable
import copy
from typing import Any

Document = dict[str, Any]
Version = tuple[int, int]


def _v1_1_to_v2_1(data: Document) -> Document:
    """Phase 0 → Phase 1: every new property, chosen to change nothing.

    A Phase 0 installation keeps behaving exactly as it did: its one zone
    becomes an explicit instant intrusion zone with the ``block`` policy, and
    its area gets exit and entry delays of 0 s, because Phase 0 armed at once.
    The new defaults (30 s) apply only to areas created from now on.

    Two notifications are added to the existing action, because the spec
    requires them rather than leaving them to taste: a failed arming (someone
    left believing the house was armed) and an automatic bypass (§5.4 says
    "notify").
    """
    out = copy.deepcopy(data)
    for area in out["areas"]:
        area.setdefault("default_entry_delay", 0)
        area.setdefault("default_exit_delay", 0)
    for zone in out["zones"]:
        zone.update(
            {
                "type": "instant",
                "channel": "intrusion",
                "entry_mode": "instant",
                "alarm_kind": "intrusion",
                "always_on": False,
                "entry_delay": None,
                "arm_policy": "block",
                "arm_hold_timeout": None,
                "allow_arm_when_faulted": False,
                "bypassable": True,
                "supervision_timeout": None,
                "enabled": True,
                "key": None,
            }
        )
    for scenario in out["scenarios"]:
        scenario.update(
            {"icon": None, "exit_delay_override": None, "siren_duration_override": None}
        )
    for action in out["actions"]:
        action["moments"] = sorted({*action["moments"], "arm_failed", "zone_bypassed"})
    out["code_policy"] = {
        "arm": bool(out["code_policy"]["arm"]),
        "disarm": bool(out["code_policy"]["disarm"]),
        # No codes until Phase 2, and no code for these until then (decision 7).
        "force_arm": False,
        "change_scenario": False,
    }
    out["settings"] = {"siren_duration": 180, "arm_hold_timeout": 300}
    return out


def _v2_1_to_v2_2(data: Document) -> Document:
    """0.1.0-alpha.1 → alpha.2: followers can follow delayed zones in other
    areas. An empty list is exactly the 2.1 behaviour (own area only)."""
    out = copy.deepcopy(data)
    for zone in out["zones"]:
        zone.setdefault("follows", [])
    return out


def _v2_2_to_v2_3(data: Document) -> Document:
    """0.1.0-alpha.3 → Phase 1 part 2: technical channel, incidents,
    verification groups, cross-zone, trigger counting and chime.

    Every new setting is chosen to change nothing that already works: no
    groups, no cross-zone, one activation to alarm, no chime anywhere (the
    chime block has no targets), and acknowledgement needs no code, as
    nothing does before Phase 2.

    One behaviour is added on purpose (part 2 decision 10): a technical alarm
    gets the persistent notification every existing action already sends for
    faults. Without it a smoke detector would fire in an empty house and say
    nothing until response profiles exist.
    """
    out = copy.deepcopy(data)
    for zone in out["zones"]:
        zone.setdefault("chime", False)
        zone.setdefault("cross_zone_id", None)
        zone.setdefault("cross_zone_window", 60)
        zone.setdefault("trigger_count", 1)
        zone.setdefault("trigger_window", 60)
    out.setdefault("groups", [])
    out["code_policy"].setdefault("acknowledge", False)
    out.setdefault(
        "chime",
        {
            "targets": [],
            "mode": "sound",
            "sound": None,
            "tts_entity": None,
            "volume": None,
            "quiet_start": None,
            "quiet_end": None,
            "during_exit": False,
        },
    )
    for action in out["actions"]:
        action["moments"] = sorted({*action["moments"], "technical_raised"})
    return out


# (from_major, from_minor) -> (step, (to_major, to_minor))
STEPS: dict[Version, tuple[Callable[[Document], Document], Version]] = {
    (1, 1): (_v1_1_to_v2_1, (2, 1)),
    (2, 1): (_v2_1_to_v2_2, (2, 2)),
    (2, 2): (_v2_2_to_v2_3, (2, 3)),
}


class MigrationError(Exception):
    """The stored document cannot be brought to the current version."""


def migrate(
    from_version: Version,
    to_version: Version,
    data: Document,
    steps: dict[Version, tuple[Callable[[Document], Document], Version]] | None = None,
) -> Document:
    """Upgrade ``data`` from ``from_version`` to ``to_version``, one step at a time.

    A newer *minor* version of the same major is additive by contract and is
    read as is. A newer *major* version is refused rather than guessed at: a
    downgrade that silently drops fields could drop an alarm setting. Every
    older version needs an explicit step; there is no silent pass-through.
    """
    steps = STEPS if steps is None else steps
    if from_version[0] > to_version[0]:
        raise MigrationError(
            f"configuration was written by a newer version {from_version}; "
            f"this version understands up to {to_version}"
        )

    version = from_version
    while version < to_version:
        if version not in steps:
            raise MigrationError(f"no migration step from version {version}")
        step, next_version = steps[version]
        if next_version <= version:
            raise MigrationError(f"migration step from {version} does not advance")
        data = step(data)
        version = next_version
    return data
