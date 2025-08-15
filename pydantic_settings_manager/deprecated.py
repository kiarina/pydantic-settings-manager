"""
Deprecated classes with migration warnings.

These classes are deprecated and will be removed in v2.0.0.
Use the unified SettingsManager class instead.
"""
import warnings
from typing import TypeVar

from pydantic_settings import BaseSettings

from .mapped import MappedSettingsManager as _MappedSettingsManager
from .single import SingleSettingsManager as _SingleSettingsManager

T = TypeVar("T", bound=BaseSettings)


class SingleSettingsManager(_SingleSettingsManager[T]):
    """
    DEPRECATED: Use SettingsManager instead.

    This class will be removed in v2.0.0.

    Migration guide:
    ```python
    # Old way
    from pydantic_settings_manager import SingleSettingsManager
    manager = SingleSettingsManager(MySettings)
    manager.user_config = {"name": "app", "value": 42}
    manager.cli_args["value"] = 100
    settings = manager.settings

    # New way
    from pydantic_settings_manager import SettingsManager
    manager = SettingsManager(MySettings)  # multi=False is default
    manager.user_config = {"name": "app", "value": 42}
    manager.cli_args = {"value": 100}
    settings = manager.settings
    ```
    """

    def __init__(self, settings_cls: type[T]):
        warnings.warn(
            "SingleSettingsManager is deprecated and will be removed in v2.0.0. "
            "Use SettingsManager instead. "
            "Migration: SettingsManager(YourSettings) replaces "
            "SingleSettingsManager(YourSettings). "
            "See migration guide: https://github.com/kiarina/pydantic-settings-manager#migration-guide",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(settings_cls)


class MappedSettingsManager(_MappedSettingsManager[T]):
    """
    DEPRECATED: Use SettingsManager with multi=True instead.

    This class will be removed in v2.0.0.

    Migration guide:
    ```python
    # Old way
    from pydantic_settings_manager import MappedSettingsManager
    manager = MappedSettingsManager(MySettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100}
        }
    }
    manager.set_cli_args("dev")
    settings = manager.settings

    # New way
    from pydantic_settings_manager import SettingsManager
    manager = SettingsManager(MySettings, multi=True)
    manager.user_config = {
        "dev": {"name": "development", "value": 42},
        "prod": {"name": "production", "value": 100}
    }
    manager.active_key = "dev"
    settings = manager.settings
    ```
    """

    def __init__(self, settings_cls: type[T]):
        warnings.warn(
            "MappedSettingsManager is deprecated and will be removed in v2.0.0. "
            "Use SettingsManager(YourSettings, multi=True) instead. "
            "See migration guide: https://github.com/kiarina/pydantic-settings-manager#migration-guide",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(settings_cls)
