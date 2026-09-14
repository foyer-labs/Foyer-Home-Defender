"""Platform entry point. Home Assistant loads platforms from the package root."""

from .entity.scenario_select import async_setup_entry

__all__ = ["async_setup_entry"]
