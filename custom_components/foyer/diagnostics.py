"""Home Assistant's own download-diagnostics button (SPEC §12.4).

The dump itself is built in ``core.dump``, which is pure and has a test
asserting what is not in it. This file is the plumbing: Home Assistant asks,
Foyer answers with the anonymised document plus the few facts about the
installation that make it answerable — the version, the schema, and whether
the log opened at all.

Access is Home Assistant's own: the button is in the integration's page and
Home Assistant shows it to administrators. Foyer adds no gate of its own
here and adds one on the *panel* instead (page 14 is gated on ``view_log``),
because the two surfaces answer to different things — one is Home
Assistant's, one is Foyer's.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .core.dump import anonymised
from .runtime.system import FoyerSystem
from .store.schema import STORAGE_MINOR_VERSION, STORAGE_VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    system: FoyerSystem = entry.runtime_data
    return {
        "integration": {
            "config_schema": f"{STORAGE_VERSION}.{STORAGE_MINOR_VERSION}",
            "entry_version": f"{entry.version}.{entry.minor_version}",
            "log_open": system.log is not None,
            "settling": system.settling,
            "language": system.language,
        },
        # No names, no codes, no hashes, no URLs, no entity ids (§12.4).
        "config": anonymised(system.config, system.state, system.snapshot()),
    }
