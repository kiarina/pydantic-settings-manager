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

from importlib.metadata import version

from pydantic_settings import BaseSettings, SettingsConfigDict

from .helpers import load_user_configs
from .manager import DEFAULT_KEY, SettingsManager
from .types import SettingsKey
from .utils import update_dict

__version__ = version("pydantic-settings-manager")

__all__ = [
    "DEFAULT_KEY",
    "BaseSettings",
    "SettingsConfigDict",
    "SettingsKey",
    "SettingsManager",
    "load_user_configs",
    "update_dict",
]
