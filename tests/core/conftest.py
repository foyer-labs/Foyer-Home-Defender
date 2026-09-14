"""Fixtures for the pure test suite. Nothing here may import homeassistant."""

from __future__ import annotations

import pytest

from custom_components.foyer.core.models import FoyerConfig

from .helpers import World, make_house


@pytest.fixture
def config() -> FoyerConfig:
    return make_house()


@pytest.fixture
def world() -> World:
    return World()
