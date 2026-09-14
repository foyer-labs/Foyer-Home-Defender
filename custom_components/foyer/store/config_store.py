"""Configuration storage in ``.storage/foyer.config`` (SPEC §3.2)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..core.models import FoyerConfig
from .migrations import migrate
from .schema import (
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    config_from_dict,
    config_to_dict,
)

STORAGE_KEY = "foyer.config"


class _VersionedStore(Store[dict[str, Any]]):
    """A Store whose version changes are routed through store/migrations."""

    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        return migrate(
            (old_major_version, old_minor_version),
            (STORAGE_VERSION, STORAGE_MINOR_VERSION),
            old_data,
        )


class ConfigStore:
    """Loads and saves the Foyer configuration."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = _VersionedStore(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
            minor_version=STORAGE_MINOR_VERSION,
        )

    async def async_load(self) -> FoyerConfig | None:
        data = await self._store.async_load()
        return None if data is None else config_from_dict(data)

    async def async_save(self, config: FoyerConfig) -> None:
        await self._store.async_save(config_to_dict(config))

    async def async_remove(self) -> None:
        await self._store.async_remove()
