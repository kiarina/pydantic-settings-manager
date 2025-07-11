"""
Mapped settings manager implementation.
"""
from __future__ import annotations

from typing import Any, Generic

from pydantic import BaseModel, Field
from pydantic.main import create_model

from .base import BaseSettingsManager, T
from .utils import diff_dict, update_dict


class SettingsMap(BaseModel, Generic[T]):
    """
    A model that maps keys to settings objects.

    This model is used by MappedSettingsManager to store multiple settings objects
    and track which one is currently active.

    Type Parameters:
        T: A type that inherits from BaseSettings

    Attributes:
        key: The key of the currently active settings
        map: A dictionary mapping keys to settings objects
    """

    key: str = ""
    """The key of the currently active settings"""

    map: dict[str, T] = Field(default_factory=dict)
    """A dictionary mapping keys to settings objects"""


class MappedSettingsManager(BaseSettingsManager[T]):
    """
    A settings manager that manages multiple settings objects mapped to keys.

    This manager is useful when you need to switch between different configurations
    at runtime. Each configuration is identified by a unique key.

    Type Parameters:
        T: A type that inherits from BaseSettings

    Example:
        ```python
        from pydantic_settings import BaseSettings
        from pydantic_settings_manager import MappedSettingsManager

        class MySettings(BaseSettings):
            name: str = "default"
            value: int = 0

        # Create a settings manager
        manager = MappedSettingsManager(MySettings)

        # Set up multiple configurations
        manager.user_config = {
            "map": {
                "dev": {"name": "development", "value": 42},
                "prod": {"name": "production", "value": 100}
            }
        }

        # Select which configuration to use
        manager.set_cli_args("dev")

        # Get the current settings
        settings = manager.settings
        assert settings.name == "development"
        assert settings.value == 42

        # Switch to a different configuration
        manager.set_cli_args("prod")
        settings = manager.settings
        assert settings.name == "production"
        assert settings.value == 100
        ```
    """

    def __init__(self, settings_cls: type[T]):
        """
        Initialize the settings manager.

        Args:
            settings_cls: The settings class to manage
        """
        self.settings_cls: type[T] = settings_cls
        """The settings class being managed"""

        self.cli_args: SettingsMap[T] = SettingsMap[T]()
        """Command line arguments"""

        self.user_config: dict[str, Any] = {}
        """User configuration"""

        self.system_settings: T = settings_cls()
        """System settings"""

        self._map_settings: SettingsMap[T] | None = None
        """Cached settings map"""

    @property
    def settings_cls_name(self) -> str:
        """
        Get the name of the settings class.

        Returns:
            The name of the settings class
        """
        return self.settings_cls.__name__

    def set_cli_args(self, key: str, value: T | None = None) -> None:
        """
        Set the command line arguments.

        Args:
            key: The key to make active
            value: Optional settings to associate with the key
        """
        self.cli_args.key = key

        if value:
            self.cli_args.map[key] = value

        self.clear()

    @property
    def _cli_args_config(self) -> dict[str, Any]:
        """
        Get the command line arguments as a dictionary.

        Returns:
            The command line arguments
        """
        vanilla = SettingsMap[T]()

        for k, _ in self.cli_args.map.items():
            vanilla.map[k] = self.settings_cls()

        base = vanilla.model_dump()
        target = self.cli_args.model_dump()

        return diff_dict(base, target)

    @property
    def _system_settings_config(self) -> dict[str, Any]:
        """
        Get the system settings as a dictionary.

        Returns:
            The system settings
        """
        base = self.settings_cls().model_dump()
        target = self.system_settings.model_dump()
        return diff_dict(base, target)

    @property
    def map_settings(self) -> SettingsMap[T]:
        """
        Get the settings map.

        Returns:
            The settings map
        """
        if not self._map_settings:
            self._map_settings = self._get_map_settings()

        return self._map_settings

    def _get_map_settings(self) -> SettingsMap[T]:
        """
        Create a new settings map.

        Returns:
            A new settings map
        """
        DynamicMapSettings = create_model(
            "DynamicMapSettings",
            key=(str, ""),
            map=(dict[str, self.settings_cls], {}),  # type: ignore[name-defined]
            __base__=SettingsMap[T],
        )

        # Merge user configuration and command line arguments
        config = update_dict(self.user_config, self._cli_args_config)

        # Merge system settings into each configuration
        if "map" in config:
            for key, value in config["map"].items():
                config["map"][key] = update_dict(value, self._system_settings_config)

        return DynamicMapSettings(**config)

    def clear(self) -> None:
        """
        Clear the cached settings map.
        """
        self._map_settings = None

    @property
    def settings(self) -> T:
        """
        Get the current settings.

        Returns:
            The current settings object

        Raises:
            ValueError: If the active key does not exist in the settings map
        """
        if not self.map_settings.key:
            if not self.map_settings.map:
                settings = self.settings_cls(**self.system_settings.model_dump())
            else:
                key = next(iter(self.map_settings.map.keys()))
                settings = self.map_settings.map[key]
        else:
            if self.map_settings.key not in self.map_settings.map:
                raise ValueError(
                    f"Key does not exist in settings map: "
                    f"{self.settings_cls_name}, {self.map_settings.key}"
                )
            else:
                settings = self.map_settings.map[self.map_settings.key]

        return settings

    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the settings map.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self.map_settings.map

    def get_settings_by_key(self, key: str = "") -> T:
        """
        Get settings by key.

        Args:
            key: The key to get settings for. If empty, returns the active settings.

        Returns:
            The settings object for the specified key

        Raises:
            ValueError: If the specified key does not exist in the settings map
        """
        if not key:
            return self.settings

        if not self.has_key(key):
            raise ValueError(f"Key does not exist in settings map: {key}")

        return self.map_settings.map[key]

    @property
    def active_key(self) -> str:
        """
        Get the active key.

        Returns:
            The active key
        """
        return self.map_settings.key

    @property
    def all_settings(self) -> dict[str, T]:
        """
        Get all settings.

        Returns:
            A dictionary mapping keys to settings objects
        """
        return self.map_settings.map
