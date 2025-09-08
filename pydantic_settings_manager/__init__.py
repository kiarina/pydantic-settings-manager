"""
pydantic-settings-manager
========================

A library for managing Pydantic settings objects.

This library provides a unified SettingsManager class that can handle both single
and multiple settings configurations:

- SettingsManager: Unified settings manager
  - Single mode: SettingsManager(MySettings)
  - Multi mode: SettingsManager(MySettings, multi=True)

Features:
- Loading settings from multiple sources
- Command line argument overrides
- Settings validation through Pydantic
- Thread-safe operations
- Type-safe configuration management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Import the unified manager and related components
from .manager import DEFAULT_KEY, SettingsManager

__version__ = "2.2.0"

__all__ = [
    # Constants
    "DEFAULT_KEY",
    # Re-exports from pydantic_settings
    "BaseSettings",
    "SettingsConfigDict",
    # Unified settings manager
    "SettingsManager",
]
