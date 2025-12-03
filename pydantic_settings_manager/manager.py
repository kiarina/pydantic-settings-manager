from __future__ import annotations

import threading
from typing import Any

from pydantic_settings import BaseSettings

from .types import SettingsKey
from .utils import update_dict

DEFAULT_KEY = "default"
"""
Default key for single mode
"""


class SettingsManager[T: BaseSettings]:
    """
    A unified settings manager that can handle both single and multiple configurations.

    This manager internally uses a map-based approach for consistency, where:
    - For single mode (multi=False): uses a default key DEFAULT_KEY
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
        manager.cli_args = {"value": 100}

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
            "key": "dev",
            "map": {
                "dev": {"name": "development", "value": 42},
                "prod": {"name": "production", "value": 100}
            }
        }

        # Switch between configurations
        manager.active_key = "dev"
        dev_settings = manager.settings

        manager.active_key = "prod"
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

        self._user_config: dict[str, dict[str, Any]] = {}
        """Internal user configuration storage"""

        self._aliases: dict[str, str] = {}
        """Configuration key aliases"""

        self._active_key: SettingsKey | None = None
        """The currently active key"""

        self._cli_args: dict[str, Any] = {}
        """Command line arguments"""

        self._cache: dict[str, T] = {}
        """Settings map cache"""

        self._cache_valid: bool = False
        """Whether the cache is valid"""

        # Use RLock (reentrant lock) instead of Lock because some methods may call
        # other methods that also acquire the lock, requiring reentrancy to avoid deadlocks.
        self._lock: threading.RLock = threading.RLock()
        """Thread synchronization lock"""

    @property
    def all_settings(self) -> dict[str, T]:
        """
        Get all settings.

        Returns:
            A dictionary mapping keys to settings objects
        """
        with self._lock:
            self._ensure_cache()
            return self._cache.copy()

    @property
    def settings(self) -> T:
        """
        Get the current active settings.

        Returns:
            The current active settings object

        Raises:
            ValueError: If the active key does not exist in the settings map,
                or circular alias reference is detected
        """
        with self._lock:
            self._ensure_cache()

            if not self.multi:
                return self._cache[DEFAULT_KEY]

            if self._active_key:
                # Resolve alias if active_key is an alias
                resolved_key = self._resolve_alias(self._active_key)

                if resolved_key not in self._cache:
                    # Show both original and resolved key in error message if different
                    if self._active_key != resolved_key:
                        raise ValueError(
                            f"Active key '{self._active_key}' (resolved to '{resolved_key}') "
                            f"does not exist in settings map"
                        )
                    else:
                        raise ValueError(
                            f"Active key '{self._active_key}' does not exist in settings map"
                        )

                return self._cache[resolved_key]

            if self._cache:
                return self._cache[next(iter(self._cache.keys()))]

            return self.settings_cls(**update_dict({}, self._cli_args))

    @property
    def user_config(self) -> dict[str, Any]:
        """
        Get the user configuration.

        Returns:
            A deep copy of the user configuration to prevent external modification
        """
        import copy

        with self._lock:
            if self.multi:
                # Deep copy to prevent external modification
                return copy.deepcopy(self._user_config)
            else:
                return copy.deepcopy(self._user_config.get(DEFAULT_KEY, {}))

    @user_config.setter
    def user_config(self, value: dict[str, Any]) -> None:
        """
        Set the user configuration.

        Args:
            value: The configuration to set. Can be:
                Single mode:
                    `{"name": "app", "value": 42}`
                Multi mode (Structured format):
                    `{"key": "dev", "map": {"dev": {"name": ".."}}, "aliases": {"hoge": "dev"}}`
                Multi mode (Direct format):
                    `{"dev": {"name": ".."}, "stg": {"name": ".."}}`
        """
        with self._lock:
            if self.multi:
                if set(value.keys()).issubset({"key", "map", "aliases"}):
                    # Structured format
                    if "key" in value:
                        self._active_key = value["key"]
                    if "map" in value:
                        self._user_config = dict(value["map"])
                    if "aliases" in value:
                        self._aliases = dict(value["aliases"])
                else:
                    # Direct format
                    self._user_config = dict(value)

            else:
                self._user_config[DEFAULT_KEY] = dict(value)

            self._cache_valid = False

    @property
    def active_key(self) -> SettingsKey | None:
        """
        Get the active key.

        Returns:
            The active key
        """
        if not self.multi:
            raise ValueError("Getting active_key is only available in multi mode")

        with self._lock:
            return self._active_key

    @active_key.setter
    def active_key(self, key: SettingsKey | None) -> None:
        """
        Set the active key.

        Args:
            key: The key to make active

        Raises:
            ValueError: If called in single mode or key doesn't exist
        """
        if not self.multi:
            raise ValueError("Setting active_key is only available in multi mode")

        with self._lock:
            self._active_key = key

    @property
    def cli_args(self) -> dict[str, Any]:
        """
        Get command line arguments.
        """
        with self._lock:
            return dict(self._cli_args)  # Return a copy to prevent external modification

    @cli_args.setter
    def cli_args(self, value: dict[str, Any]) -> None:
        """
        Set command line arguments.
        """
        with self._lock:
            self._cli_args = dict(value)  # Create a copy
            self._cache_valid = False

    def set_cli_args(self, target: str, value: Any) -> None:
        """
        Set command line arguments.

        Args:
            target: The target argument name
            value: The value to set for the target argument
        """
        with self._lock:
            keys = target.split(".")
            d = self._cli_args

            for key in keys[:-1]:
                if not isinstance(d, dict):
                    raise ValueError(f"Invalid target path: {target}")

                d = d.setdefault(key, {})

            d[keys[-1]] = value

            self._cache_valid = False

    def get_settings(self, key: SettingsKey | None = None) -> T:
        """
        Get settings by key or return current active settings.

        This is a convenience method that combines the functionality of:
        - `settings` property (when key=None)
        - Key-based access (when key is specified in multi mode)

        Args:
            key: Configuration key (multi mode only).
                If None, returns current active settings.

        Returns:
            Settings object for the specified key or current active settings.

        Raises:
            ValueError: If key is specified in single mode, or key doesn't exist,
                or circular alias reference is detected.

        Examples:
            ```python
            # Single mode
            manager = SettingsManager(MySettings)
            settings = manager.get_settings()  # Same as manager.settings

            # Multi mode
            manager = SettingsManager(MySettings, multi=True)
            dev = manager.get_settings("dev")
            current = manager.get_settings()  # Current active settings
            ```
        """
        if not self.multi:
            if key:
                raise ValueError("Getting settings by key is only available in multi mode")

            return self.settings

        if not key:
            return self.settings

        with self._lock:
            self._ensure_cache()

            resolved_key = self._resolve_alias(key)

            if resolved_key not in self._cache:
                if key != resolved_key:
                    raise ValueError(
                        f"Key '{key}' (resolved to '{resolved_key}') does not exist in settings map"
                    )
                else:
                    raise ValueError(f"Key '{key}' does not exist in settings map")

            return self._cache[resolved_key]

    def get_settings_by_key(self, key: str | None) -> T:
        """
        Get settings by specific key.

        .. deprecated:: 2.3.0
            Use :meth:`get_settings` instead.
            This method will be removed in version 3.0.0.

        This method is only available in multi mode (multi=True).

        Args:
            key: The key to get settings for. If None or empty, returns the current active settings.

        Returns:
            The settings object for the specified key

        Raises:
            ValueError: If called in single mode, or if the key does not exist in multi mode
        """
        import warnings

        warnings.warn(
            "get_settings_by_key() is deprecated and will be removed in version 3.0.0. "
            "Use get_settings() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_settings(key)

    def clear(self) -> None:
        """
        Clear the cached settings.
        This forces the next access to settings to rebuild the cache.
        """
        with self._lock:
            self._cache_valid = False

    def _resolve_alias(self, key: str, *, _visited: set[str] | None = None) -> str:
        """
        Resolve alias to actual key.

        Supports multi-level aliases (alias of alias).
        Prevents infinite loops with visited set.

        Args:
            key: The key to resolve
            _visited: Internal set to track visited keys (for loop detection)

        Returns:
            The resolved key

        Raises:
            ValueError: If circular alias reference is detected
        """
        if not self._aliases:
            return key

        if _visited is None:
            _visited = set()

        if key in _visited:
            chain = " -> ".join(_visited) + f" -> {key}"
            raise ValueError(f"Circular alias reference detected: {chain}")

        if key not in self._aliases:
            return key

        _visited.add(key)
        target = self._aliases[key]
        return self._resolve_alias(target, _visited=_visited)

    def _ensure_cache(self) -> None:
        """
        Ensure the cache is valid, rebuild if necessary.
        """
        # Note: This method is called from within other locked methods,
        # so we don't add another lock here to avoid deadlock
        if not self._cache_valid:
            self._rebuild_cache()

    def _rebuild_cache(self) -> None:
        """
        Rebuild the settings cache from current configuration.
        """
        # Note: This method is called from _ensure_cache which is called
        # from within other locked methods, so we don't add another lock here
        if self.multi:
            self._cache = {}

            for key, user_config in self._user_config.items():
                if isinstance(user_config, dict):
                    self._cache[key] = self.settings_cls(**update_dict(user_config, self._cli_args))

        else:
            self._cache = {
                DEFAULT_KEY: self.settings_cls(
                    **update_dict(self._user_config.get(DEFAULT_KEY, {}), self._cli_args)
                )
            }

        self._cache_valid = True
