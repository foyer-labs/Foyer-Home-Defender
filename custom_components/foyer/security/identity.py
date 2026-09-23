"""Turning a request into an Actor: who is asking, with what (SPEC §8.2).

One place, used by the WebSocket API and by the entities, so the panel, the
card, a service call and an automation cannot each grow their own idea of who
somebody is. It resolves three things and nothing else:

* the **person** — the code identifies them if one arrived, otherwise the Home
  Assistant account does, if a Foyer user is linked to it;
* the **channel**, which decides whether the per-user exemption of §8.2 can
  apply at all and which lockout counter a failure belongs to;
* whether this is the **admin path**, which is never locked out (§8.4).

The code is compared here, in an executor thread, and goes no further: what
travels on is a CodeResult (INV-2).
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..const import CHANNEL_AUTOMATION, CHANNEL_HA_UI
from ..core.models import Actor, FoyerConfig
from . import codes


async def async_actor(
    hass: HomeAssistant,
    config: FoyerConfig,
    *,
    ha_user_id: str | None = None,
    code: str | None = None,
    channel: str | None = None,
    device_id: str | None = None,
    is_admin: bool | None = None,
) -> Actor:
    """Identify whoever is behind one request.

    When a code and a signed-in account disagree, the code wins: somebody
    typing their own code on a tablet signed in as another member of the
    household is that person, and the log has to say so. ``identified`` is
    true only when the two agree, because that is exactly what the exemption
    of §8.2 rests on — the channel knowing who this is without being told.
    """
    linked = config.user_of_ha(ha_user_id)
    credential = await hass.async_add_executor_job(codes.identify, config.users, code)
    user = credential.user or linked
    if is_admin is None and ha_user_id is not None:
        account = await hass.auth.async_get_user(ha_user_id)
        is_admin = bool(account and account.is_admin)
    return Actor(
        user_id=user.id if user else None,
        channel=channel or (CHANNEL_HA_UI if ha_user_id else CHANNEL_AUTOMATION),
        device_id=device_id,
        code=credential.result,
        identified=linked is not None and user is linked,
        duress=credential.duress,
        is_admin=bool(is_admin),
        account=ha_user_id,
    )
