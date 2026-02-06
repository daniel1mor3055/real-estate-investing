"""Adapters for external interfaces and persistence."""

from .config_loader import ConfigLoader, get_config_value
from .repository import DealRepository

__all__ = [
    "ConfigLoader",
    "get_config_value",
    "DealRepository",
]
