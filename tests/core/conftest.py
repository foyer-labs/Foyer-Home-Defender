"""Fixtures for the pure test suite. Nothing here may import homeassistant."""

from __future__ import annotations

import pytest

from custom_components.foyer.core.models import FoyerConfig

from .helpers import make_config


@pytest.fixture
def config() -> FoyerConfig:
    return make_config()
