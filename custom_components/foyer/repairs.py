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
trace anywhere a person was going to look. Confirming dismisses the card;
the problem coming back raises it again.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .core.models import ChannelFault

# One translation key per kind of problem; the issue id carries which zone,
# channel or radio it is about, and the placeholders carry the names. A key
# per zone would be a translation file that changes when somebody renames a
# door.
ZONE_UNREACHABLE = "zone_unreachable"
CHANNEL_BROKEN = "channel_broken"
WATCHDOG_NEVER_WORKED = "watchdog_never_worked"
WATCHDOG_UNREACHABLE = "watchdog_unreachable"
RF_INTERFERENCE = "rf_interference"
COORDINATOR_DOWN = "coordinator_down"
MAINS_LOST = "mains_lost"

# How long the two conditions that can right themselves have to last before
# they are worth a card in Settings. A power cut of five minutes and a
# coordinator rebooting are not repairs; an hour of either is.
TRANSIENT_GRACE = 3600


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """Every Foyer issue is confirmed rather than repaired from here.

    There is nothing Home Assistant can do about a jammed radio or a removed
    integration, and a flow that pretended otherwise would be a button that
    does nothing. What it offers is the honest thing: "I have seen this".
    """
    return ConfirmRepairFlow()


def reconcile(hass: HomeAssistant, entry_id: str, status: dict[str, Any]) -> None:
    """Raise what is true now and withdraw what is not. Idempotent.

    Called periodically rather than on every decision: these are problems
    measured in hours and days, and re-registering an issue every time a
    door opens would be work nobody asked for.
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
        wanted[f"{CHANNEL_BROKEN}_{channel['key'].replace(':', '_')}"] = {
            "translation_key": CHANNEL_BROKEN,
            "severity": ir.IssueSeverity.ERROR,
            "placeholders": {
                "contact": channel["contact_name"],
                "service": channel["service"],
                "cause": channel["fault"],
                # Said in the card as well as in the notification, because
                # the two are read by different people at different times.
                "detail": (
                    "missing"
                    if channel["fault"] == ChannelFault.MISSING_SERVICE.value
                    else "failing"
                ),
            },
        }

    watchdog = status["watchdog"]
    if watchdog["enabled"] and watchdog["down_since"]:
        key = WATCHDOG_NEVER_WORKED if not watchdog["ever_ok"] else WATCHDOG_UNREACHABLE
        wanted[key] = {
            "translation_key": key,
            "severity": ir.IssueSeverity.ERROR,
            "placeholders": {
                "url": watchdog["url"],
                "error": watchdog["last_error"] or "-",
            },
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


def _is_health_issue(issue_id: str) -> bool:
    """Only withdraw what this module raises, never somebody else's issue."""
    return issue_id.startswith(
        (
            ZONE_UNREACHABLE,
            CHANNEL_BROKEN,
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
