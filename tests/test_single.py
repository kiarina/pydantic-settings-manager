"""
Tests for SingleSettingsManager
"""
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SingleSettingsManager


class TestSettings(BaseSettings):
    """Test settings class"""

    name: str = "default"
    value: int = 0


def test_single_settings_manager_init() -> None:
    """Test initialization"""
    manager = SingleSettingsManager(TestSettings)
    assert isinstance(manager.settings, TestSettings)
    assert manager.settings.name == "default"
    assert manager.settings.value == 0


def test_single_settings_manager_user_config() -> None:
    """Test user configuration"""
    manager = SingleSettingsManager(TestSettings)
    manager.user_config = {"name": "from_file", "value": 42}

    assert manager.settings.name == "from_file"
    assert manager.settings.value == 42


def test_single_settings_manager_cli_args():
    """Test command line arguments"""
    manager = SingleSettingsManager(TestSettings)
    manager.cli_args = {"value": 100}

    assert manager.settings.name == "default"
    assert manager.settings.value == 100


def test_single_settings_manager_precedence():
    """Test settings precedence"""
    manager = SingleSettingsManager(TestSettings)
    manager.user_config = {"name": "from_file", "value": 42}
    manager.cli_args = {"value": 100}

    assert manager.settings.name == "from_file"  # from user_config
    assert manager.settings.value == 100  # from cli_args


def test_single_settings_manager_clear():
    """Test clear settings"""
    manager = SingleSettingsManager(TestSettings)
    manager.user_config = {"name": "from_file", "value": 42}

    # Get settings to cache them
    _ = manager.settings

    # Clear settings
    manager.clear()

    # Modify config
    manager.user_config = {"name": "new_name", "value": 100}

    # Check that new settings are used
    assert manager.settings.name == "new_name"
    assert manager.settings.value == 100