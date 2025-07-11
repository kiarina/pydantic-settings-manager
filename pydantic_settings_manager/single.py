"""
Single settings manager implementation.
"""
from typing import Any, Union

from .base import BaseSettingsManager, T
from .utils import NestedDict, nested_dict, update_dict


class SingleSettingsManager(BaseSettingsManager[T]):
    """
    A settings manager that manages a single settings object.

    This manager is useful when you need to manage a single configuration that can be
    updated from multiple sources (e.g., command line arguments, configuration files).

    Type Parameters:
        T: A type that inherits from BaseSettings

    Example:
        ```python
        from pydantic_settings import BaseSettings
        from pydantic_settings_manager import SingleSettingsManager

        class MySettings(BaseSettings):
            name: str = "default"
            value: int = 0

        # Create a settings manager
        manager = SingleSettingsManager(MySettings)

        # Update settings from a configuration file
        manager.user_config = {"name": "from_file", "value": 42}

        # Update settings from command line arguments
        manager.cli_args = {"value": 100}

        # Get the current settings (combines both sources)
        settings = manager.settings
        assert settings.name == "from_file"  # from user_config
        assert settings.value == 100  # from cli_args (overrides user_config)
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

        self.cli_args: NestedDict = nested_dict()
        """Command line arguments"""

        self.user_config: dict[str, Any] = {}
        """User configuration"""

        self._settings: Union[T, None] = None
        """Cached settings"""

    @property
    def settings(self) -> T:
        """
        Get the current settings.

        The settings are created by combining the user configuration and command line
        arguments, with command line arguments taking precedence.

        Returns:
            The current settings object
        """
        if not self._settings:
            self._settings = self._get_settings()

        return self._settings

    def _get_settings(self) -> T:
        """
        Create a new settings object.

        Returns:
            A new settings object
        """
        config = update_dict(self.user_config, self.cli_args)
        return self.settings_cls(**config)

    def clear(self) -> None:
        """
        Clear the cached settings.

        This forces the next access to settings to create a new settings object.
        """
        self._settings = None
