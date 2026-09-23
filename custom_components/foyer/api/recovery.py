"""Getting an administrator back in, loudly (SPEC §8.2, decisions 109, 110).

Decision 101 asks a Home Assistant administrator for the code like anybody
else. That leaves two people with no way back: the administrator who holds no
code in a house where others do, and the one whose own Foyer user was
disabled or has run past its validity window. INV-6 already says an
administrator can do anything to this integration, so a way back exists —
from the integration's Configure step, which Home Assistant opens to
administrators only — and it is never the quiet way round a code: a
`security` row, a Home Assistant notification, and a message to every
enabled contact, each naming the account.

Home Assistant does not tell an integration who opened the step, so the step
asks for which account. Choosing another administrator's buys nothing INV-6
does not already give.
"""

from __future__ import annotations

from dataclasses import replace
from functools import partial

from homeassistant.core import HomeAssistant

from .. import i18n
from ..core.models import Actor, CodeAttempt, CodeResult, Permission
from ..runtime.system import FoyerSystem
from ..security import codes
from ..store.editing import upsert
from ..store.schema import user_to_dict
from .backup import async_write

# What the step answers with instead of doing it, as translation keys under
# `options.error`.
UNKNOWN_ACCOUNT = "unknown_account"
INVALID_CODE = "invalid_code"
CODE_IN_USE = "code_in_use"
INVALID = "invalid"
RELOADING = "reloading"


async def async_accounts(hass: HomeAssistant) -> dict[str, str]:
    """The administrators' accounts: the recovery is an administrator's own
    access (decisions 109, 110). Anybody else is given a way in from the
    Users page, with the permissions that takes."""
    users = [
        u
        for u in await hass.auth.async_get_users()
        if u.is_active and not u.system_generated and u.is_admin
    ]
    users.sort(key=lambda u: (u.name or "").casefold())
    return {u.id: u.name or u.id for u in users}


async def async_recover(
    hass: HomeAssistant, system: FoyerSystem, account_id: str, code: str
) -> str | None:
    """Recover access for this account with this code, or say why not."""
    account = await hass.auth.async_get_user(account_id)
    if (
        account is None
        or account.system_generated
        or not account.is_active
        or not account.is_admin
    ):
        return UNKNOWN_ACCOUNT
    config = system.config
    try:
        codes.validate(code, config.settings.security.code_length)
    except codes.CodeError:
        return INVALID_CODE
    linked = config.user_of_ha(account.id)
    # §8.1: codes are unique across people, and the answer never says whose.
    if await hass.async_add_executor_job(
        partial(
            codes.collides,
            config.users,
            code,
            ignore_user_id=linked.id if linked else None,
        )
    ) or (
        # Nor the person's own duress code: the ordinary hash would match
        # first and the silent alarm could never fire.
        linked is not None
        and await hass.async_add_executor_job(
            codes.matches, code, linked.duress_code_hash
        )
    ):
        # A collision is an oracle over somebody else's code (§8.1), so it
        # is spent like a wrong one: the same counter, the same row, the
        # same moment a profile can answer (second review decision 5, third
        # review). The admin path is never locked out, but it is counted.
        await system.async_handle(
            CodeAttempt(
                operation=None,
                actor=Actor(
                    channel="ha_config",
                    code=CodeResult.INVALID,
                    is_admin=True,
                    account=account.id,
                ),
            )
        )
        return CODE_IN_USE
    hashed = await hass.async_add_executor_job(codes.hash_code, code)
    if linked is not None:
        item = user_to_dict(
            replace(
                linked,
                enabled=True,
                valid_from=None,
                valid_until=None,
                code_hash=hashed,
            )
        )
    else:
        item = {
            "name": account.name or account.id,
            "ha_user_id": account.id,
            "permissions": sorted(p.value for p in Permission),
            "code_hash": hashed,
            "enabled": True,
        }
    result = upsert(config, system.state, "user", item)
    if result.config is None:
        return INVALID
    person = result.config.user(result.id)
    strings = await hass.async_add_executor_job(i18n.load_strings, system.language)
    # Announced once the write has been tried, whatever it answered: a
    # recovery announced and then not written would tell the household about
    # a code that does not exist (review), and one written and not announced
    # would be the quiet way round a code.
    try:
        answer = await async_write(
            hass,
            system,
            result,
            operation="recover",
            kind="user",
            channel="ha_config",
            user_id=None,
            user_name=None,
        )
    except Exception:
        system.access_recovered(
            strings,
            account=account.name or account.id,
            user_id=result.id,
            user_name=person.name if person else None,
            created=linked is None,
            written=False,
        )
        raise
    written = bool(answer.get("success"))
    system.access_recovered(
        strings,
        account=account.name or account.id,
        user_id=result.id,
        user_name=person.name if person else None,
        created=linked is None,
        written=written,
    )
    return None if written else RELOADING
