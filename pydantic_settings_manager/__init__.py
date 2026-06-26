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

from ._constants.default_key import DEFAULT_KEY
from ._helpers.clear_user_configs import clear_user_configs
from ._helpers.generate_user_configs_yaml import generate_user_configs_yaml
from ._helpers.load_user_configs import load_user_configs
from ._models.settings_manager import SettingsManager
from ._types.config_update_policy import ConfigUpdatePolicy
from ._types.missing_module_policy import MissingModulePolicy
from ._types.module_name import ModuleName
from ._types.settings_key import SettingsKey
from ._types.user_config import UserConfig
from ._types.user_configs import UserConfigs
from ._utils.update_dict import update_dict

__version__ = version("pydantic-settings-manager")

__all__ = [
    "DEFAULT_KEY",
    "BaseSettings",
    "ConfigUpdatePolicy",
    "MissingModulePolicy",
    "ModuleName",
    "SettingsConfigDict",
    "SettingsKey",
    "SettingsManager",
    "UserConfig",
    "UserConfigs",
    "clear_user_configs",
    "generate_user_configs_yaml",
    "load_user_configs",
    "update_dict",
]
