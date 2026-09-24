"""Home Assistant repair issues for persistent problems (SPEC §12.4).

The point of this file is *where* it puts things, not what it knows. A zone
that has been unreachable for two days, a notification channel that was
removed in an update and a watchdog that has never once succeeded are all
already in the log, on page 14 and on ``binary_sensor.foyer_system_health``
— and all three are invisible to somebody who does not open the Foyer panel.
Settings ▸ Repairs is where Home Assistant users look when something is
wrong, so that is where these go.

Every issue Foyer raises is fixable, and what the flow does is confirm that
somebody has seen it (part 1 decision 10). That is deliberate and it is the
one place system health does ask for an acknowledgement: the state itself
never does — it clears when the cause clears — but an issue that vanished on
its own would mean a zone could drop off for a week, come back, and leave no
trace anywhere a person was going to look.

The acknowledgement is *persisted*, and that is not a detail. Home
Assistant's own confirm flow only deletes the issue, and this module
reconciles every five minutes — so without a record the card a person
dismissed would be back before they had closed the page, and back again
after every restart. An id is forgotten as soon as its problem clears, so
the next occurrence raises the card again.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import TYPE_CHECKING, Any

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir
import voluptuous as vol

from .const import CONF_DISCLAIMER, DISCLAIMER_VERSION, DOMAIN
from .core.models import ChannelFault

if TYPE_CHECKING:
    from .runtime.system import FoyerSystem

# One translation key per kind of problem; the issue id carries which zone,
# channel or radio it is about, and the placeholders carry the names. A key
# per zone would be a translation file that changes when somebody renames a
# door.
ZONE_UNREACHABLE = "zone_unreachable"
CHANNEL_BROKEN = "channel_broken"
CHANNEL_FAILING = "channel_failing"
WATCHDOG_NEVER_WORKED = "watchdog_never_worked"
WATCHDOG_UNREACHABLE = "watchdog_unreachable"
RF_INTERFERENCE = "rf_interference"
COORDINATOR_DOWN = "coordinator_down"
MAINS_LOST = "mains_lost"
# Not a health problem: the disclaimer of SPEC §20.4, for an installation set
# up before it was asked for, or before its current version (decision 152).
DISCLAIMER = "disclaimer"

# How long the two conditions that can right themselves have to last before
# they are worth a card in Settings. A power cut of five minutes and a
# coordinator rebooting are not repairs; an hour of either is.
TRANSIENT_GRACE = 3600


class SeenRepairFlow(RepairsFlow):
    """Confirm that somebody has seen this, and remember that they did.

    There is nothing Home Assistant can do about a jammed radio or a removed
    integration, and a flow that pretended otherwise would be a button that
    does nothing. What this offers is the honest thing — "I have seen
    this" — and then records it, so the card stays dismissed until the
    problem has cleared and come back.
    """

    def __init__(self, hass: HomeAssistant, issue_id: str) -> None:
        self.hass = hass
        self.issue_id = issue_id

    async def async_step_init(self, user_input: dict[str, str] | None = None):
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        if user_input is not None:
            system: FoyerSystem | None = self.hass.data.get(DOMAIN)
            if system is not None:
                await system.async_acknowledge_issue(self.issue_id)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


class DisclaimerRepairFlow(RepairsFlow):
    """Accept the disclaimer from Settings ▸ Repairs (SPEC §20.4).

    The same text and the same tick as the config flow, for an installation
    that never went through it. Nothing waits on it: the alarm keeps working
    until somebody accepts, because an alarm switched off by an update to its
    documentation would be a worse outcome than the one the text warns about.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("accept_disclaimer"):
                await async_accept_disclaimer(self.hass)
                return self.async_create_entry(data={})
            errors["accept_disclaimer"] = "disclaimer_not_accepted"
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {vol.Required("accept_disclaimer", default=False): bool}
            ),
            errors=errors,
        )


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    if issue_id == DISCLAIMER:
        return DisclaimerRepairFlow(hass)
    return SeenRepairFlow(hass, issue_id)


def disclaimer_accepted(data: Mapping[str, Any]) -> bool:
    """Whether a config entry's data holds an acceptance of the current text."""
    accepted = data.get(CONF_DISCLAIMER)
    return isinstance(accepted, Mapping) and (
        accepted.get("version", 0) >= DISCLAIMER_VERSION
    )


def sync_disclaimer(hass: HomeAssistant, entry_data: Mapping[str, Any]) -> None:
    """Raise the disclaimer card while the current text is unaccepted."""
    if disclaimer_accepted(entry_data):
        ir.async_delete_issue(hass, DOMAIN, DISCLAIMER)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        DISCLAIMER,
        is_fixable=True,
        is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=DISCLAIMER,
    )


async def async_accept_disclaimer(hass: HomeAssistant) -> None:
    """Record the acceptance on the entry and in the log, and drop the card.

    The entry's data is updated in place: Foyer registers no update
    listener, so this reloads nothing and leaves the alarm as it is.
    """
    from homeassistant.util import dt as dt_util

    now = dt_util.utcnow()
    for entry in hass.config_entries.async_entries(DOMAIN):
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_DISCLAIMER: {
                    "version": DISCLAIMER_VERSION,
                    "accepted_at": now.isoformat(),
                },
            },
        )
    system: FoyerSystem | None = hass.data.get(DOMAIN)
    if system is not None:
        system.async_record((disclaimer_row(now),))
    ir.async_delete_issue(hass, DOMAIN, DISCLAIMER)


def disclaimer_row(at):
    """The log's row for an accepted disclaimer (category ``config``)."""
    from .core.journal import config_row

    return config_row(
        at,
        operation="disclaimer_accepted",
        kind="disclaimer",
        channel="ha_config",
        changes={"version": DISCLAIMER_VERSION},
    )


def reconcile(
    hass: HomeAssistant,
    entry_id: str,
    status: dict[str, Any],
    acknowledged: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Raise what is true now and withdraw what is not. Idempotent.

    Called periodically rather than on every decision: these are problems
    measured in hours and days, and re-registering an issue every time a
    door opens would be work nobody asked for.

    Returns the acknowledgements still worth keeping — an id whose problem
    has cleared is forgotten, so the next occurrence raises its card again.
    """
    wanted: dict[str, dict[str, Any]] = {}

    for zone in status.get("unreachable_zones", []):
        wanted[f"{ZONE_UNREACHABLE}_{zone['id']}"] = {
            "translation_key": ZONE_UNREACHABLE,
            "severity": ir.IssueSeverity.WARNING,
            "placeholders": {"zone": zone["name"], "days": str(zone["days"])},
        }

    for channel in status["channels"]:
        if not channel["fault"]:
            continue
        missing = channel["fault"] == ChannelFault.MISSING_SERVICE.value
        # Two keys rather than one with a word in it: a placeholder Foyer
        # fills with "missing" puts an English word in the middle of an
        # Italian sentence, and the backend writes no word a person reads.
        key = CHANNEL_BROKEN if missing else CHANNEL_FAILING
        wanted[f"{key}_{_slug(channel['key'])}"] = {
            "translation_key": key,
            "severity": ir.IssueSeverity.ERROR,
            "placeholders": {
                "contact": channel["contact_name"],
                "service": channel["service"],
            },
        }

    watchdog = status["watchdog"]
    if watchdog["enabled"] and watchdog["down_since"]:
        key = WATCHDOG_NEVER_WORKED if not watchdog["ever_ok"] else WATCHDOG_UNREACHABLE
        wanted[key] = {
            "translation_key": key,
            "severity": ir.IssueSeverity.ERROR,
            # Never the URL: it is the credential, and a repair card is a
            # page somebody screenshots into an issue thread.
            "placeholders": {"error": watchdog["last_error"] or "-"},
        }

    for radio in status["radios"]:
        if radio["confirmed"]:
            wanted[f"{RF_INTERFERENCE}_{radio['id']}"] = {
                "translation_key": RF_INTERFERENCE,
                "severity": ir.IssueSeverity.ERROR,
                "placeholders": {
                    "radio": radio["name"],
                    "count": str(radio["quiet"]),
                    "of": str(radio["zones"]),
                },
            }
        if _older_than(radio["coordinator_down_since"], status["now"], TRANSIENT_GRACE):
            wanted[f"{COORDINATOR_DOWN}_{radio['id']}"] = {
                "translation_key": COORDINATOR_DOWN,
                "severity": ir.IssueSeverity.ERROR,
                "placeholders": {
                    "radio": radio["name"],
                    "entity_id": radio["coordinator_entity_id"] or "-",
                },
            }

    if _older_than(status["mains"]["since"], status["now"], TRANSIENT_GRACE):
        wanted[MAINS_LOST] = {
            "translation_key": MAINS_LOST,
            "severity": ir.IssueSeverity.ERROR,
            "placeholders": {"entity_id": status["mains"]["entity_id"] or "-"},
        }

    registry = ir.async_get(hass)
    existing = {
        issue_id
        for (domain, issue_id) in registry.issues
        if domain == DOMAIN and _is_health_issue(issue_id)
    }
    for issue_id, issue in wanted.items():
        if issue_id in acknowledged:
            # Somebody has seen this one. It comes back when the problem
            # does, not five minutes after they dismissed it.
            continue
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["placeholders"],
            data={"entry_id": entry_id},
        )
    for issue_id in existing - wanted.keys():
        ir.async_delete_issue(hass, DOMAIN, issue_id)
    return acknowledged & wanted.keys()


def async_forget_all(hass: HomeAssistant) -> None:
    """Withdraw every card Foyer raised. For an integration being removed.

    Issues are registered against the domain rather than the config entry,
    so Home Assistant does not take them away with the entry: without this,
    removing Foyer leaves a card in Settings for ever, pointing at an
    integration that is not there to fix it.
    """
    registry = ir.async_get(hass)
    for domain, issue_id in list(registry.issues):
        if domain == DOMAIN and (_is_health_issue(issue_id) or issue_id == DISCLAIMER):
            ir.async_delete_issue(hass, DOMAIN, issue_id)


def _slug(key: str) -> str:
    """A collision-free suffix for a contact channel.

    ``contact:channel`` cannot go into an issue id as it is, and flattening
    the separator to an underscore makes ``luca_home`` + ``sms`` and
    ``luca`` + ``home_sms`` the same card. A short digest cannot collide by
    accident, and the card's words come from the translation anyway.
    """
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def _is_health_issue(issue_id: str) -> bool:
    """Only withdraw what this module raises, never somebody else's issue."""
    return issue_id.startswith(
        (
            ZONE_UNREACHABLE,
            CHANNEL_BROKEN,
            CHANNEL_FAILING,
            WATCHDOG_NEVER_WORKED,
            WATCHDOG_UNREACHABLE,
            RF_INTERFERENCE,
            COORDINATOR_DOWN,
            MAINS_LOST,
        )
    )


def _older_than(since: str | None, now: str, seconds: int) -> bool:
    from datetime import datetime

    if not since:
        return False
    return (
        datetime.fromisoformat(now) - datetime.fromisoformat(since)
    ).total_seconds() >= seconds
