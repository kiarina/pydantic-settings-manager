"""
pydantic-settings-manager
========================

A library for managing Pydantic settings objects.

This library provides a unified SettingsManager class that can handle both single
and multiple settings configurations:

- SettingsManager: Unified settings manager (recommended)
  - Single mode: SettingsManager(MySettings)
  - Multi mode: SettingsManager(MySettings, multi=True)

DEPRECATED CLASSES (will be removed in v2.0.0):
- BaseSettingsManager: Use SettingsManager instead
- SingleSettingsManager: Use SettingsManager instead
- MappedSettingsManager: Use SettingsManager(MySettings, multi=True) instead

Features:
- Loading settings from multiple sources
- Command line argument overrides
- Settings validation through Pydantic
- Thread-safe operations
- Type-safe configuration management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Import the original base class (not deprecated)
from .base import BaseSettingsManager

# Import deprecated classes with warnings
from .deprecated import MappedSettingsManager, SingleSettingsManager

# Import the unified manager and related components
from .manager import DEFAULT_KEY, SettingsManager
from .mapped import SettingsMap

__version__ = "1.0.3"

__all__ = [
    # Constants
    "DEFAULT_KEY",
    # Re-exports from pydantic_settings
    "BaseSettings",
    # Base class (not deprecated - used for inheritance)
    "BaseSettingsManager",        # DEPRECATED: Use SettingsManager instead
    "MappedSettingsManager",      # DEPRECATED: Use SettingsManager(MySettings, multi=True) instead
    "SettingsConfigDict",
    # Unified settings manager (RECOMMENDED)
    "SettingsManager",
    # Supporting classes
    "SettingsMap",
    "SingleSettingsManager",      # DEPRECATED: Use SettingsManager(MySettings) instead
]
