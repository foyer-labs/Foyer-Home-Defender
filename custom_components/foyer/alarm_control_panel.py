"""Platform entry point. Home Assistant loads platforms from the package root."""

from .entity.alarm_panel import async_setup_entry

__all__ = ["async_setup_entry"]
