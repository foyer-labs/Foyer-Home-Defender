"""The Home Assistant notifications Foyer puts up, and how they come down.

Two places create one: the ``persistent_notification`` action of §6.2, which
is what Phase 0 did and what every installation upgrading from it still has
(decision 71), and the refusal of an unregistered arming device (§9.3), which
has to reach somebody who does not open the Foyer panel.

They are created through here rather than directly so that leaving can take
them with it (§16). A persistent notification lives in memory and not on
disk, so the only ones that exist when somebody removes the integration are
the ones this process put up — which is exactly the set kept here. There is no
supported way to ask Home Assistant which notifications belong to whom, and
reaching into its private storage to find out is the kind of thing that breaks
silently two releases later.
"""

from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant, callback

from ..const import DOMAIN

_KEY = f"{DOMAIN}_notifications"


@callback
def async_create(
    hass: HomeAssistant,
    message: str,
    *,
    title: str | None,
    notification_id: str,
) -> None:
    ids: set[str] = hass.data.setdefault(_KEY, set())
    ids.add(notification_id)
    persistent_notification.async_create(
        hass, message, title=title, notification_id=notification_id
    )


@callback
def async_dismiss_all(hass: HomeAssistant) -> int:
    """Take down everything Foyer put up. Called when the integration goes."""
    ids: set[str] = hass.data.pop(_KEY, set())
    for notification_id in ids:
        persistent_notification.async_dismiss(hass, notification_id)
    return len(ids)
