"""
Unified settings manager implementation.
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic_settings import BaseSettings

from .utils import NestedDict, nested_dict, update_dict

T = TypeVar("T", bound=BaseSettings)


class SettingsManager(Generic[T]):
    """
    A unified settings manager that can handle both single and multiple configurations.

    This manager internally uses a map-based approach for consistency, where:
    - For single mode (multi=False): uses a default key "default"
    - For multi mode (multi=True): allows multiple named configurations

    Type Parameters:
        T: A type that inherits from BaseSettings

    Example (Single mode):
        ```python
        from pydantic_settings import BaseSettings
        from pydantic_settings_manager import SettingsManager

        class MySettings(BaseSettings):
            name: str = "default"
            value: int = 0

        # Single settings manager (like old SingleSettingsManager)
        manager = SettingsManager(MySettings)

        # Set configuration
        manager.user_config = {"name": "app", "value": 42}

        # Override with CLI args
        manager.cli_args["value"] = 100

        settings = manager.settings
        assert settings.name == "app"
        assert settings.value == 100
        ```

    Example (Multi mode):
        ```python
        # Multi settings manager (like old MappedSettingsManager)
        manager = SettingsManager(MySettings, multi=True)

        # Set multiple configurations
        manager.user_config = {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100}
        }

        # Switch between configurations
        manager.set_active_key("dev")
        dev_settings = manager.settings

        manager.set_active_key("prod")
        prod_settings = manager.settings
        ```
    """

    def __init__(self, settings_cls: type[T], *, multi: bool = False):
        """
        Initialize the settings manager.

        Args:
            settings_cls: The settings class to manage
            multi: Whether to enable multi-configuration mode
        """
        self.settings_cls: type[T] = settings_cls
        """The settings class being managed"""

        self.multi: bool = multi
        """Whether multi-configuration mode is enabled"""

        self.cli_args: NestedDict = nested_dict()
        """Command line arguments (for single mode)"""

        self._user_config: dict[str, dict[str, Any]] = {}
        """Internal user configuration storage"""

        self._active_key: str = "default"
        """The currently active key"""

        self._map: dict[str, T] = {}
        """Settings map cache"""

        self._cache_valid: bool = False
        """Whether the cache is valid"""

    def _is_multi_config(self, value: dict[str, Any]) -> bool:
        """
        Check if the given value is a multi-configuration format.

        Args:
            value: The configuration value to check

        Returns:
            True if it's a multi-configuration format
        """
        # Check if all values are dictionaries (indicating multi-config format)
        return all(isinstance(v, dict) for v in value.values())

    @property
    def user_config(self) -> dict[str, Any]:
        """
        Get the user configuration.

        For single mode: returns the configuration for the default key
        For multi mode: returns all configurations

        Returns:
            The user configuration
        """
        if self.multi:
            # Multi mode: always return all configurations
            return dict(self._user_config)
        else:
            # Single mode: return default config
            return self._user_config.get("default", {})

    @user_config.setter
    def user_config(self, value: dict[str, Any]) -> None:
        """
        Set the user configuration.

        Args:
            value: The configuration to set. Can be:
                - Single mode: {"name": "app", "value": 42}
                - Multi mode bulk: {"dev": {"name": "dev"}, "prod": {"name": "prod"}}
                - Multi mode individual: {"name": "app"} (requires active_key to be set first)

        Raises:
            ValueError: If multi mode is used with single config format without explicit active_key
        """
        if self.multi:
            if self._is_multi_config(value):
                # Multi mode with bulk configuration
                self._user_config = dict(value)
            else:
                # Multi mode with individual configuration - require explicit active_key
                if self._active_key == "default" and not self._user_config:
                    raise ValueError(
                        "In multi mode, you must either:\n"
                        "1. Use bulk configuration: {'dev': {...}, 'prod': {...}}\n"
                        "2. Set active_key first, then set individual configuration"
                    )
                # Individual configuration for the active key
                self._user_config[self._active_key] = dict(value)
        else:
            # Single mode
            self._user_config[self._active_key] = dict(value)

        # Invalidate cache
        self.clear()

    def _rebuild_cache(self) -> None:
        """Rebuild the settings cache from current configuration."""
        if self.multi:
            # Multi mode: build from all configurations in _user_config
            self._map = {}

            for key, config in self._user_config.items():
                if isinstance(config, dict):
                    self._map[key] = self.settings_cls(**config)

            # Set active key to first available key if current key doesn't exist
            if self._map and self._active_key not in self._map:
                self._active_key = next(iter(self._map.keys()))
        else:
            # Single mode: create default entry from user_config and cli_args
            user_cfg = self._user_config.get("default", {})
            config = update_dict(user_cfg, self.cli_args)
            self._map = {"default": self.settings_cls(**config)}
            self._active_key = "default"

        self._cache_valid = True

    def _ensure_cache(self) -> None:
        """Ensure the cache is valid, rebuild if necessary."""
        if not self._cache_valid:
            self._rebuild_cache()

    @property
    def settings(self) -> T:
        """
        Get the current active settings.

        Returns:
            The current active settings object

        Raises:
            ValueError: If the active key does not exist in the settings map
        """
        self._ensure_cache()

        if self._active_key not in self._map:
            if self.multi:
                raise ValueError(
                    f"Active key '{self._active_key}' does not exist in settings map"
                )
            else:
                # For single mode, create default settings if not exists
                self._map["default"] = self.settings_cls()
                self._active_key = "default"

        return self._map[self._active_key]

    def set_active_key(self, key: str) -> None:
        """
        Set the active configuration key (multi mode only).

        Args:
            key: The key to make active

        Raises:
            ValueError: If called in single mode or key doesn't exist
        """
        if not self.multi:
            raise ValueError("set_active_key() is only available in multi mode")

        self._ensure_cache()

        if key not in self._map:
            raise ValueError(f"Key '{key}' does not exist in settings map")

        self._active_key = key

    def get_settings_by_key(self, key: str) -> T:
        """
        Get settings by specific key.

        Args:
            key: The key to get settings for

        Returns:
            The settings object for the specified key

        Raises:
            ValueError: If the key does not exist
        """
        self._ensure_cache()

        if key not in self._map:
            raise ValueError(f"Key '{key}' does not exist in settings map")

        return self._map[key]

    def get_user_config_by_key(self, key: str) -> dict[str, Any]:
        """
        Get user configuration by specific key.

        Args:
            key: The key to get user configuration for

        Returns:
            The user configuration dictionary for the specified key

        Raises:
            ValueError: If the key does not exist
        """
        if key not in self._user_config:
            raise ValueError(f"Key '{key}' does not exist in user configuration")

        return dict(self._user_config[key])

    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the settings map.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        self._ensure_cache()
        return key in self._map

    @property
    def active_key(self) -> str:
        """
        Get the active key.

        Returns:
            The active key
        """
        return self._active_key

    @active_key.setter
    def active_key(self, key: str) -> None:
        """
        Set the active key.

        Args:
            key: The key to make active

        Raises:
            ValueError: If called in single mode or key doesn't exist
        """
        if not self.multi:
            raise ValueError("Setting active_key is only available in multi mode")

        self._ensure_cache()

        if key not in self._map:
            raise ValueError(f"Key '{key}' does not exist in settings map")

        self._active_key = key

    @property
    def all_keys(self) -> list[str]:
        """
        Get all available keys.

        Returns:
            A list of all available keys
        """
        self._ensure_cache()
        return list(self._map.keys())

    @property
    def all_settings(self) -> dict[str, T]:
        """
        Get all settings.

        Returns:
            A dictionary mapping keys to settings objects
        """
        self._ensure_cache()
        return self._map.copy()

    def clear(self) -> None:
        """
        Clear the cached settings.
        This forces the next access to settings to rebuild the cache.
        """
        self._cache_valid = False
        self._map.clear()
