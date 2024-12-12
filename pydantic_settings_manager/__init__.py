"""
pydantic-settings-manager
========================

A library for managing Pydantic settings objects.

This library provides two types of settings managers:

1. SingleSettingsManager: For managing a single settings object
2. MappedSettingsManager: For managing multiple settings objects mapped to keys

Both managers support:
- Loading settings from multiple sources
- Command line argument overrides
- Settings validation through Pydantic
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import BaseSettingsManager
from .mapped import MappedSettingsManager, SettingsMap
from .single import SingleSettingsManager

__version__ = "0.1.0"

__all__ = [
    # Re-exports from pydantic_settings
    "BaseSettings",
    "SettingsConfigDict",
    # Base manager
    "BaseSettingsManager",
    # Single settings manager
    "SingleSettingsManager",
    # Mapped settings manager
    "MappedSettingsManager",
    "SettingsMap",
]
