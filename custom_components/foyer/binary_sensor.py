"""Platform entry point. Home Assistant loads platforms from the package root."""

from .entity.sensors import async_setup_binary_sensors as async_setup_entry

__all__ = ["async_setup_entry"]
