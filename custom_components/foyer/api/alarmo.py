"""The Alarmo importer's Home Assistant half (SPEC §20.2).

``store/alarmo.py`` does the translation and is pure; this reads the file
from this installation's own ``.storage``, reads what Home Assistant knows
about the sensors it names, and hands the result to the same validation and
armed-area guard every edit goes through. The panel's two commands — a
preview, then an apply — are in ``websocket.py`` beside the other
configuration commands, and call this.

There is no upload. The file is read from the installation the panel is
talking to, so the importer is pointed at *this* house's Alarmo and at
nothing a browser chose.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any
import uuid

from homeassistant.core import HomeAssistant

from ..core.models import FoyerConfig
from ..core.validation import edit_conflicts, validate
from ..runtime.system import FoyerSystem
from ..store.alarmo import (
    SENSOR_DOMAINS,
    SOURCE_KEY,
    EntityInfo,
    ImportPlan,
    Labels,
    Line,
    Refused,
    plan,
)
from ..store.schema import config_to_dict

# Alarmo's configuration for a house with a hundred sensors is tens of
# kilobytes. A file far past that is not one this importer is for.
MAX_BYTES = 4 * 1024 * 1024


def _read(path: Path) -> tuple[bytes, Any]:
    """Blocking, parsing included; run in an executor."""
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except FileNotFoundError:
        raise Refused("not_found") from None
    except OSError:
        raise Refused("unreadable") from None
    if len(raw) > MAX_BYTES:
        raise Refused("too_large")
    try:
        return raw, json.loads(raw)
    except (ValueError, RecursionError):
        raise Refused("not_json") from None


async def _load(hass: HomeAssistant) -> tuple[bytes, Any]:
    path = Path(hass.config.path(".storage", SOURCE_KEY))
    return await hass.async_add_executor_job(_read, path)


def _named(document: Any) -> set[str]:
    """The entities the file names, which are the only ones the plan reads."""
    data = document.get("data") if isinstance(document, dict) else None
    sensors = data.get("sensors") if isinstance(data, dict) else None
    if not isinstance(sensors, list):
        return set()
    return {
        s["entity_id"]
        for s in sensors
        if isinstance(s, dict) and isinstance(s.get("entity_id"), str)
    }


def _entities(hass: HomeAssistant) -> dict[str, EntityInfo]:
    """What Home Assistant knows about every entity a sensor could be."""
    found = {}
    for state in hass.states.async_all(tuple(SENSOR_DOMAINS)):
        name = state.attributes.get("friendly_name")
        device_class = state.attributes.get("device_class")
        found[state.entity_id] = EntityInfo(
            state=state.state,
            name=name if isinstance(name, str) else None,
            device_class=device_class if isinstance(device_class, str) else None,
        )
    return found


def _fingerprint(
    raw: bytes,
    config: FoyerConfig,
    entities: dict[str, EntityInfo],
    labels: Labels,
) -> str:
    """Everything the plan was computed from, so the apply can be refused
    when any of it changed after the preview was shown.

    The preview is what the person agreed to. Applying something computed
    from a different file, a configuration somebody edited in another tab,
    or a sensor renamed meanwhile would store what nobody looked at — and
    the names it would create come from the labels, so they count too.
    """
    digest = hashlib.sha256(raw)
    digest.update(json.dumps(asdict(labels), sort_keys=True).encode())
    digest.update(
        json.dumps(config_to_dict(config), sort_keys=True, default=str).encode()
    )
    # What the plan reads of each entity the file names: its name and
    # whether it exists — never its state, which a motion sensor changes
    # every time somebody walks past and which would refuse every apply in a
    # house anybody is living in.
    digest.update(
        json.dumps(
            {e: [i.name, i.state is not None] for e, i in sorted(entities.items())}
        ).encode()
    )
    return digest.hexdigest()


def _line(line: Line) -> dict[str, Any]:
    return {"code": line.code, "params": dict(line.params)}


def _names(before: FoyerConfig, after: FoyerConfig) -> dict[str, list[str]]:
    """What would be created or extended, by name, for the preview."""

    def added(old, new) -> list[str]:
        known = {i.id for i in old}
        return [i.name for i in new if i.id not in known]

    old_scenarios = {s.id: s for s in before.scenarios}
    return {
        "areas": added(before.areas, after.areas),
        "scenarios": added(before.scenarios, after.scenarios),
        "extended": [
            s.name
            for s in after.scenarios
            if s.id in old_scenarios and s != old_scenarios[s.id]
        ],
        "people": added(before.users, after.users),
        "profiles": added(before.profiles, after.profiles),
    }


async def async_plan(
    hass: HomeAssistant, system: FoyerSystem, labels: Any
) -> tuple[ImportPlan | None, dict[str, Any]]:
    """Read and translate, and describe the outcome as the panel shows it.

    Returns the plan (None when refused) and the answer for the panel: the
    refusal, or the report, what would be created, the problems validation
    and the armed-area guard would raise, and the fingerprint to apply with.
    """
    words = Labels.parse(labels)
    try:
        raw, document = await _load(hass)
        named = _named(document)
        entities = {e: i for e, i in _entities(hass).items() if e in named}
        result = plan(
            document,
            system.config,
            entities,
            words,
            lambda: uuid.uuid4().hex,
        )
    except Refused as refused:
        return None, {"success": False, "refused": _line(refused.line)}
    problems = validate(result.config) + edit_conflicts(
        system.config, result.config, system.state
    )
    return result, {
        "success": not problems,
        "lines": [_line(line) for line in result.lines],
        "counts": dict(result.counts),
        "created": _names(system.config, result.config),
        "problems": [asdict(p) for p in problems],
        "fingerprint": _fingerprint(raw, system.config, entities, words),
    }
