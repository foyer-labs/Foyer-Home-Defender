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

**One transport per keypad** (decision 98). A keypad on the device endpoint
is its token, and its name is refused everywhere else — over the broker and
through a service call — or whoever knows the name reaches the house around
the token. The refusal answers exactly as an unknown device does, so the
broker learns nothing about which names are real; the row and the
notification say what actually happened.

**The channel is the device's, never the message's.** A message saying
``channel: nfc`` would be buying the per-user exemption of §8.2 by typing a
word; a message saying ``channel: keypad`` would be choosing which lockout
counter to spend. So a channel that identifies, or that names a physical
thing, comes only from a registered device — and a caller with no device gets
the channel its transport actually is.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets

from homeassistant.core import HomeAssistant

from ..const import CHANNEL_API, CHANNEL_AUTOMATION
from ..core.models import (
    Actor,
    ArmingDevice,
    DeviceKind,
    DeviceTransport,
    FoyerConfig,
    Reason,
)
from . import codes

# The transport a request to the device endpoint arrives on (§9.2.1).
TRANSPORT_HTTP = "http"

# 32 random bytes (§9.2.1), written URL-safe so it survives a keypad's
# firmware, a YAML file and a header without quoting.
TOKEN_BYTES = 32

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
    # The name was a real keypad's, and this is not its transport (decision
    # 98). The caller is answered exactly as for an unknown device; the row
    # and the notification say this instead.
    wrong_transport: bool = False


def new_token() -> tuple[str, str]:
    """A fresh token and the hash that is stored in its place (§9.2.1).

    The token is shown once and never kept: what the configuration holds is
    its SHA-256, which is enough for a random secret — a slow hash exists to
    slow down guessing a code somebody chose, and nobody chose this.
    """
    token = secrets.token_urlsafe(TOKEN_BYTES)
    return token, token_hash(token)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def device_by_token(config: FoyerConfig, token: str | None) -> ArmingDevice | None:
    """The keypad this token belongs to, or None (§9.2.1).

    Compared in constant time against every keypad on the endpoint, and every
    one is compared whether or not an earlier one matched, so how long the
    answer takes says nothing about how close a guess came. A disabled keypad
    answers to nothing, as a disabled device does on every other path.
    """
    if not token:
        return None
    offered = token_hash(token).encode("ascii")
    found: ArmingDevice | None = None
    for device in config.devices:
        if (
            device.kind is not DeviceKind.KEYPAD
            or device.transport is not DeviceTransport.HTTP
            or not device.token_hash
        ):
            continue
        if hmac.compare_digest(offered, device.token_hash.encode("ascii")):
            found = found or device
    if found is None or not found.enabled:
        return None
    return found


async def async_requester(
    hass: HomeAssistant,
    config: FoyerConfig,
    *,
    transport: str,
    ref: str | None = None,
    code: str | None = None,
    channel: str | None = None,
    user_id: str | None = None,
    device: ArmingDevice | None = None,
    encrypted: bool | None = None,
    account: str | None = None,
    locked_address: str | None = None,
) -> Requester:
    """Resolve one request arriving from a service call or a broker.

    ``ref`` is what the message calls itself — the ``device_id`` field of
    §9.1 and §9.2. ``user_id`` is honoured for **attribution only**: it says
    whose name goes in the log, and it buys nothing, because a channel that
    does not identify cannot be talked into identifying. The person's
    permissions and validity window still apply in full, which is the safe
    direction for a claim to travel: claiming to be somebody gets you their
    restrictions, never their exemptions.

    ``locked_address`` is the device endpoint's alone: the address a right
    token came from while that address is locked out for wrong tokens
    (§9.2.1, decision 135), carried to every row the request causes.
    """
    if device is not None:
        # Already established by a token (§9.2.1): the device endpoint is the
        # one caller that knows the device before it reads the message, and
        # a `device_id` the message carries anyway is ignored.
        if transport != TRANSPORT_HTTP:
            raise ValueError("only the device endpoint names a device by token")
    elif ref is not None:
        device = config.device_by_ref(ref)
        if device is None:
            return Requester(reason=Reason.DEVICE_NOT_REGISTERED)
        if device.transport is DeviceTransport.HTTP:
            # Its name, over a path that is not its own (decision 98).
            return Requester(
                reason=Reason.DEVICE_NOT_REGISTERED,
                device=device,
                wrong_transport=True,
            )
    elif channel is not None and channel not in DECLARABLE:
        # A physical or identifying channel with no device behind it. Refused
        # rather than quietly downgraded: a caller that asked to be a keypad
        # and was silently filed as an automation has been told nothing.
        return Requester(reason=Reason.DEVICE_NOT_REGISTERED)

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
    # After the token branch, which discards it: every stored hash is checked
    # twice per code, and a tag carries no code to check (second review).
    credential = await hass.async_add_executor_job(codes.identify, config.users, code)
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
            encrypted=encrypted,
            locked_address=locked_address,
            # Only for a request with no device: a keypad's failures count
            # against the keypad, whoever's automation relayed them.
            account=None if device is not None else account,
            # Nothing established this person: the message said so. The log
            # records the difference rather than flattening it.
            claimed=credential.user is None and bool(resolved),
        ),
        device=device,
    )
