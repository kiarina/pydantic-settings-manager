"""
Base classes for settings managers.
"""
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseSettings)


class BaseSettingsManager(ABC, Generic[T]):
    """
    Base class for settings managers.

    This abstract class defines the interface that all settings managers must implement.
    It provides a generic way to manage Pydantic settings objects.

    Type Parameters:
        T: A type that inherits from BaseSettings
    """

    @abstractmethod
    def __init__(self, settings_cls: type[T]):
        """
        Initialize the settings manager.

        Args:
            settings_cls: The settings class to manage
        """
        self.settings_cls = settings_cls
        """The settings class being managed"""

        self.user_config: dict[str, Any] = {}
        """User configuration dictionary"""

    @property
    @abstractmethod
    def settings(self) -> T:
        """
        Get the current settings.

        Returns:
            The current settings object
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Clear the current settings.
        This typically involves clearing any cached settings.
        """
