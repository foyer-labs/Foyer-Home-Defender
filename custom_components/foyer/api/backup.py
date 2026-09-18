"""Reading the configuration out, and putting one back (SPEC §15.1, §14.1).

Shared by the panel's WebSocket commands and by the ``foyer.*`` services,
because there must be exactly one answer to "what does a backup contain" and
one path that writes a configuration. Two would eventually disagree, and the
one that disagreed would be the one that dropped an alarm setting.

What a backup never contains is a hash (§8.1). It is a file that leaves the
machine; a code hash in it is an offline guessing exercise waiting to happen.
A restore therefore keeps the codes of the people already here under the same
id, and nothing in a file can ever set one.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from ..core.journal import config_row
from ..core.models import FoyerConfig, User
from ..core.validation import Problem, edit_conflicts, validate
from ..runtime.system import FoyerSystem
from ..store.config_store import ConfigStore
from ..store.editing import EditResult, config_diff
from ..store.migrations import MigrationError, migrate
from ..store.schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    ConfigError,
    config_from_dict,
    config_to_dict,
)

# What marks a file as ours, so a JSON document picked by mistake is refused
# with a sentence rather than half-imported.
BACKUP_MAGIC = "foyer.config"


def public_user(user: User) -> dict[str, Any]:
    """A person as any API may see them: whether a code exists, never which."""
    return {
        "id": user.id,
        "name": user.name,
        "has_code": bool(user.code_hash),
        "has_duress_code": bool(user.duress_code_hash),
        "ha_user_id": user.ha_user_id,
        "permissions": sorted(user.permissions),
        "allowed_area_ids": (
            None if user.allowed_area_ids is None else list(user.allowed_area_ids)
        ),
        "allowed_scenario_ids": (
            None
            if user.allowed_scenario_ids is None
            else list(user.allowed_scenario_ids)
        ),
        "valid_from": user.valid_from.isoformat() if user.valid_from else None,
        "valid_until": user.valid_until.isoformat() if user.valid_until else None,
        "code_exempt_when_identified": user.code_exempt_when_identified,
        "enabled": user.enabled,
    }


def public_config(config: FoyerConfig) -> dict[str, Any]:
    """The configuration as the panel may see it: no hashes, ever (§8.1)."""
    document = config_to_dict(config)
    document["users"] = [public_user(u) for u in config.users]
    return document


def backup_document(config: FoyerConfig) -> dict[str, Any]:
    """The stored document with its schema version (§15.1).

    The version travels with the document because an import must migrate it,
    not guess at it — and must refuse one written by a newer major version.
    """
    return {
        "foyer": BACKUP_MAGIC,
        "version": [STORAGE_VERSION, STORAGE_MINOR_VERSION],
        "created": dt_util.now().isoformat(),
        "config": public_config(config),
    }


def backup_filename(kind: str, extension: str = "json") -> str:
    return f"foyer-{kind}-{dt_util.now().strftime('%Y%m%d-%H%M')}.{extension}"


def restore(system: FoyerSystem, document: dict[str, Any]) -> EditResult:
    """Migrate, validate, then check what is armed. Never around those three.

    A document written by an older version is brought up to date by the same
    steps a real upgrade uses; one written by a newer major version is refused,
    because silently dropping fields it does not understand could drop an alarm
    setting; and a restore that would change an armed area is refused like any
    other edit.
    """
    if document.get("foyer") != BACKUP_MAGIC or "config" not in document:
        return EditResult(None, (Problem("not_a_foyer_backup", "config"),))
    version = document.get("version") or [STORAGE_VERSION, STORAGE_MINOR_VERSION]
    try:
        data = migrate(
            (int(version[0]), int(version[1])),
            (STORAGE_VERSION, STORAGE_MINOR_VERSION),
            document["config"],
        )
        config = config_from_dict(data)
    except MigrationError:
        return EditResult(None, (Problem("backup_version_unsupported", "config"),))
    except (ConfigError, KeyError, TypeError, ValueError, IndexError):
        return EditResult(None, (Problem("invalid", "config"),))

    config = replace(
        config,
        users=tuple(
            replace(
                user,
                code_hash=(k.code_hash if (k := system.config.user(user.id)) else None),
                duress_code_hash=(k.duress_code_hash if k else None),
            )
            for user in config.users
        ),
    )
    problems = validate(config) + edit_conflicts(system.config, config, system.state)
    return EditResult(None if problems else config, tuple(problems))


async def async_write(
    hass: HomeAssistant,
    system: FoyerSystem,
    result: EditResult,
    *,
    operation: str,
    kind: str,
    channel: str,
    user_id: str | None,
    user_name: str | None,
) -> dict[str, Any]:
    """Store an accepted edit, record who made it, and reload the entry.

    The row is written before the reload, which replaces this system with a
    new one; the entities follow the configuration, and the alarm state is
    saved on unload and restored on setup (INV-3).
    """
    if result.config is None:
        return {"success": False, "problems": [asdict(p) for p in result.problems]}
    system.async_record(
        (
            config_row(
                dt_util.utcnow(),
                operation=operation,
                kind=kind,
                item_id=result.id,
                user_id=user_id,
                user_name=user_name,
                channel=channel,
                changes=config_diff(system.config, result.config),
            ),
        )
    )
    await ConfigStore(hass).async_save(result.config)
    entry = next(iter(hass.config_entries.async_entries(DOMAIN)), None)
    if entry is not None:
        hass.config_entries.async_schedule_reload(entry.entry_id)
    return {"success": True, "id": result.id, "problems": []}
