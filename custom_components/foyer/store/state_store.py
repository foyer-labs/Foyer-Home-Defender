"""Runtime state in ``.storage/foyer.state`` (INV-3).

Saved immediately on every change, never on a delay: an alarm that loses the
last few seconds of state across a crash can come back disarmed. A heartbeat
also records ``alive_at`` periodically, so that after a crash the restart gap
starts at the last moment Foyer is known to have been running rather than at
the last state change, which may be days old. The gap it reports is therefore
at most one heartbeat too long, never too short: the log must never imply the
house was covered when it was not.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..core.models import FoyerConfig, RuntimeState
from .schema import (
    STATE_MINOR_VERSION,
    STATE_VERSION,
    state_from_dict,
    state_to_dict,
)

STATE_KEY = "foyer.state"


@dataclass(frozen=True, slots=True)
class StoredState:
    state: RuntimeState
    alive_at: datetime | None


class StateStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STATE_VERSION, STATE_KEY, minor_version=STATE_MINOR_VERSION
        )

    async def async_load(self, config: FoyerConfig) -> StoredState | None:
        data = await self._store.async_load()
        if data is None:
            return None
        alive = data.get("alive_at")
        return StoredState(
            state=state_from_dict(data.get("state", {}), config),
            alive_at=datetime.fromisoformat(alive) if alive else None,
        )

    async def async_save(self, state: RuntimeState, alive_at: datetime) -> None:
        await self._store.async_save(
            {"state": state_to_dict(state), "alive_at": alive_at.isoformat()}
        )

    async def async_remove(self) -> None:
        await self._store.async_remove()
