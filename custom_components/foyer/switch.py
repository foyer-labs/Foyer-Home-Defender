"""Platform entry point. Home Assistant loads platforms from the package root."""

from .entity.switches import async_setup_switches as async_setup_entry

__all__ = ["async_setup_entry"]
