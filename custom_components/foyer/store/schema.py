"""Conversion between the stored JSON document and the core dataclasses.

Pure: no Home Assistant imports, so the round trip is testable on its own.
"""

from __future__ import annotations

from typing import Any

from ..core.models import (
    Area,
    CodePolicy,
    FoyerConfig,
    Moment,
    NotificationAction,
    Scenario,
    StateTrigger,
    Zone,
)

# Bump STORAGE_VERSION (breaking) or STORAGE_MINOR_VERSION (additive) together
# with a step in store/migrations. Home Assistant's Store calls the hook.
STORAGE_VERSION = 1
STORAGE_MINOR_VERSION = 1


class ConfigError(ValueError):
    """The stored document does not describe a valid configuration."""


def config_from_dict(data: dict[str, Any]) -> FoyerConfig:
    try:
        return FoyerConfig(
            areas=tuple(
                Area(
                    id=a["id"],
                    name=a["name"],
                    ha_state_when_armed=a["ha_state_when_armed"],
                )
                for a in data["areas"]
            ),
            zones=tuple(
                Zone(
                    id=z["id"],
                    name=z["name"],
                    entity_id=z["entity_id"],
                    area_id=z["area_id"],
                    trigger=_trigger_from_dict(z["trigger"]),
                )
                for z in data["zones"]
            ),
            scenarios=tuple(
                Scenario(
                    id=s["id"],
                    name=s["name"],
                    areas=tuple(s["areas"]),
                    ha_master_state=s["ha_master_state"],
                )
                for s in data["scenarios"]
            ),
            actions=tuple(
                NotificationAction(
                    id=a["id"], moments=frozenset(Moment(m) for m in a["moments"])
                )
                for a in data["actions"]
            ),
            code_policy=CodePolicy(
                arm=bool(data["code_policy"]["arm"]),
                disarm=bool(data["code_policy"]["disarm"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as err:
        raise ConfigError(f"invalid Foyer configuration: {err!r}") from err


def config_to_dict(config: FoyerConfig) -> dict[str, Any]:
    return {
        "areas": [
            {"id": a.id, "name": a.name, "ha_state_when_armed": a.ha_state_when_armed}
            for a in config.areas
        ],
        "zones": [
            {
                "id": z.id,
                "name": z.name,
                "entity_id": z.entity_id,
                "area_id": z.area_id,
                "trigger": {"kind": "state", "states": sorted(z.trigger.states)},
            }
            for z in config.zones
        ],
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "areas": list(s.areas),
                "ha_master_state": s.ha_master_state,
            }
            for s in config.scenarios
        ],
        "actions": [
            {
                "id": a.id,
                "kind": "notification",
                "moments": sorted(m.value for m in a.moments),
            }
            for a in config.actions
        ],
        "code_policy": {
            "arm": config.code_policy.arm,
            "disarm": config.code_policy.disarm,
        },
    }


def _trigger_from_dict(data: dict[str, Any]) -> StateTrigger:
    if data.get("kind") != "state":
        raise ConfigError(f"unsupported trigger kind: {data.get('kind')!r}")
    return StateTrigger(states=frozenset(data["states"]))
