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
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from ..core.journal import config_row
from ..core.models import DeviceKind, DeviceTransport, FoyerConfig, User
from ..core.privacy import new_pseudonym
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
        # The stable opaque identifier a pseudonymised log row carries instead
        # of this name (§10.4). Not a credential and not a secret — it says
        # nothing about the person — and it travels with a backup on purpose:
        # a restore that minted new ones would detach every row already
        # pseudonymised from every row written afterwards.
        "pseudonym": user.pseudonym,
    }


def public_config(config: FoyerConfig) -> dict[str, Any]:
    """The configuration as the panel may see it: no hashes, ever (§8.1).

    A keypad's token hash goes the same way as a code's (§9.2.1): the panel
    is told whether one exists, never which.
    """
    document = config_to_dict(config)
    document["users"] = [public_user(u) for u in config.users]
    for device in document.get("devices", []):
        device["has_token"] = bool(device.pop("token_hash", None))
    return document


# What a backup never carries out, and never takes in. Both are credentials
# rather than settings: the acknowledgement webhook is an unauthenticated URL
# that stops an alarm, and the watchdog URL is the one address that can keep a
# dead installation looking alive. A backup is a file that leaves the machine
# (see this module's header), and a restore that could *choose* either of them
# would hand that choice to whoever wrote the file.
CREDENTIAL_SETTINGS = ("ack_webhook_id",)


def _without_credentials(document: dict[str, Any]) -> dict[str, Any]:
    settings = dict(document.get("settings") or {})
    for key in CREDENTIAL_SETTINGS:
        settings[key] = None
    document["settings"] = settings
    health = dict(document.get("health") or {})
    watchdog = dict(health.get("watchdog") or {})
    if watchdog:
        watchdog["url"] = ""
        health["watchdog"] = watchdog
        document["health"] = health
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
        "config": _without_credentials(public_config(config)),
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
    if not isinstance(document["config"], dict):
        return EditResult(None, (Problem("invalid", "config"),))
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
    except (ConfigError, KeyError, TypeError, ValueError, IndexError, AttributeError):
        # A hand-edited file puts a string where a list was, or a number
        # where a map was; any of these is "not a configuration", never a
        # traceback in the panel (third review).
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
    # A document that arrives with no pseudonym — hand-edited, or written by a
    # build that had none — would leave that person out of every sweep for
    # ever, silently, while the setting reported success. One that arrives
    # with the *same* pseudonym on two people is worse: the sweep stamps both
    # histories with one identifier, and an erasure or an export then crosses
    # between two people (both found in review). Either way a fresh one is
    # minted here.
    # The credentials are the installation's, never the document's: a
    # backup can neither carry them out (see `backup_document`) nor set them
    # coming in. `update_settings` has refused the webhook id since Phase 4 —
    # "the address of an unauthenticated URL can only ever be generated here"
    # — and this path did not go through it (found in review).
    config = replace(
        config,
        settings=replace(
            config.settings, ack_webhook_id=system.config.settings.ack_webhook_id
        ),
        health=replace(
            config.health,
            watchdog=replace(
                config.health.watchdog,
                url=system.config.health.watchdog.url,
                # The file says "enabled" and the URL stayed behind: on a
                # fresh install the restore was refused for a URL nobody
                # could type before restoring (third review). The watchdog
                # comes back once its URL is entered again.
                enabled=config.health.watchdog.enabled
                and bool(system.config.health.watchdog.url),
            ),
        ),
    )
    # A keypad's token is the installation's, like a code (§9.2.1): a backup
    # never carries one out, and a restore never sets one. The keypad this
    # installation already holds keeps its own, as long as the document
    # still puts it on the endpoint; anything else starts with none, and a
    # restored endpoint keypad waits for a token to be generated on page 8.
    config = replace(
        config,
        devices=tuple(
            replace(
                device,
                token_hash=(
                    held.token_hash
                    if (held := system.config.device(device.id)) is not None
                    and device.kind is DeviceKind.KEYPAD
                    and device.transport is DeviceTransport.HTTP
                    else None
                ),
            )
            for device in config.devices
        ),
    )
    # A zone this installation holds unconfirmed stays unconfirmed unless
    # the document changes its trigger: editing a backup to say `true` is
    # not somebody checking the sensor (INV-5, Phase 5 part 3). A changed
    # trigger is a different zone as far as the check is concerned, and the
    # document is trusted with it as it is trusted with every other zone.
    config = replace(
        config,
        zones=tuple(
            replace(zone, trigger_confirmed=False)
            if (held := system.config.zone(zone.id)) is not None
            and not held.trigger_confirmed
            and held.trigger == zone.trigger
            else zone
            for zone in config.zones
        ),
    )
    seen: set[str] = set()
    users = []
    for user in config.users:
        pseudonym = user.pseudonym
        if not pseudonym or pseudonym in seen:
            pseudonym = new_pseudonym(uuid.uuid4().hex)
        seen.add(pseudonym)
        users.append(replace(user, pseudonym=pseudonym))
    config = replace(config, users=tuple(users))
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
    if system.superseded:
        # This system has already written a newer configuration and is
        # waiting to be replaced by it. An edit built from the one it still
        # holds would write the old document back over the new — a revoked
        # token restored by somebody renaming a zone in the next second
        # (found in review). Refused, and the panel asks again once the
        # reload has happened.
        return {
            "success": False,
            "problems": [asdict(Problem("config_reloading", "config"))],
        }
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
    system.superseded = True
    await ConfigStore(hass).async_save(result.config)
    entry = next(iter(hass.config_entries.async_entries(DOMAIN)), None)
    if entry is not None:
        hass.config_entries.async_schedule_reload(entry.entry_id)
    return {"success": True, "id": result.id, "problems": []}
