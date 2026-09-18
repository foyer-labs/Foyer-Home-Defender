"""Which device is asking, and whether it is one of ours (SPEC §9.3).

The gate in front of every channel that is not the Home Assistant UI: a
service call, an MQTT message, an adapter. It answers one question — is this
a device this installation has declared? — and builds the Actor that follows
from the answer.

Two rules, both narrow and both worth stating (part 2 decisions 1 and 4).

**An unknown device is refused**, code or no code. Page 8 is a white list. The
reason is not tidiness: the lockout of §8.4 counts per channel and device, so
a caller free to invent a device id is a caller who can try codes for ever
without a counter ever reaching its limit.

**The channel is the device's, never the message's.** A message saying
``channel: nfc`` would be buying the per-user exemption of §8.2 by typing a
word; a message saying ``channel: keypad`` would be choosing which lockout
counter to spend. So a channel that identifies, or that names a physical
thing, comes only from a registered device — and a caller with no device gets
the channel its transport actually is.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant

from ..const import CHANNEL_API, CHANNEL_AUTOMATION
from ..core.models import Actor, ArmingDevice, FoyerConfig, Reason
from . import codes

# The channels a caller may claim without a registered device behind it.
# Neither identifies anybody, so neither buys anything (§8.2).
DECLARABLE: frozenset[str] = frozenset({CHANNEL_API, CHANNEL_AUTOMATION})


@dataclass(frozen=True, slots=True)
class Requester:
    """Who is asking, once the device has been resolved.

    ``reason`` is set instead of ``actor`` when the request must be refused
    before the engine ever sees it: there is nothing for ``decide()`` to
    decide about a device this installation does not know.
    """

    actor: Actor | None = None
    device: ArmingDevice | None = None
    reason: Reason | None = None


async def async_requester(
    hass: HomeAssistant,
    config: FoyerConfig,
    *,
    transport: str,
    ref: str | None = None,
    code: str | None = None,
    channel: str | None = None,
    user_id: str | None = None,
) -> Requester:
    """Resolve one request arriving from a service call or a broker.

    ``ref`` is what the message calls itself — the ``device_id`` field of
    §9.1 and §9.2. ``user_id`` is honoured for **attribution only**: it says
    whose name goes in the log, and it buys nothing, because a channel that
    does not identify cannot be talked into identifying. The person's
    permissions and validity window still apply in full, which is the safe
    direction for a claim to travel: claiming to be somebody gets you their
    restrictions, never their exemptions.
    """
    device: ArmingDevice | None = None
    if ref is not None:
        device = config.device_by_ref(ref)
        if device is None:
            return Requester(reason=Reason.DEVICE_NOT_REGISTERED)
    elif channel is not None and channel not in DECLARABLE:
        # A physical or identifying channel with no device behind it. Refused
        # rather than quietly downgraded: a caller that asked to be a keypad
        # and was silently filed as an automation has been told nothing.
        return Requester(reason=Reason.DEVICE_NOT_REGISTERED)

    credential = await hass.async_add_executor_job(codes.identify, config.users, code)
    if device is not None and device.token:
        # Possession is the credential; nothing can be typed on it (§9.3).
        return Requester(
            actor=Actor(
                user_id=device.user_id,
                channel=device.channel,
                device_id=device.id,
                identified=True,
                token=True,
            ),
            device=device,
        )
    # The code wins over a claimed user, as it does everywhere else: somebody
    # typing their own code on the hall keypad is that person, whatever the
    # message says about who is holding it.
    resolved = credential.user.id if credential.user else (user_id or None)
    return Requester(
        actor=Actor(
            user_id=resolved,
            channel=device.channel if device else (channel or transport),
            device_id=device.id if device else None,
            code=credential.result,
            duress=credential.duress,
        ),
        device=device,
    )
