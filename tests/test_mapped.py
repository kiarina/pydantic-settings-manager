"""
Tests for MappedSettingsManager
"""
import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import MappedSettingsManager


class TestSettings(BaseSettings):
    """Test settings class"""

    name: str = "default"
    value: int = 0


def test_mapped_settings_manager_init():
    """Test initialization"""
    manager = MappedSettingsManager(TestSettings)
    assert isinstance(manager.settings, TestSettings)
    assert manager.settings.name == "default"
    assert manager.settings.value == 0


def test_mapped_settings_manager_user_config():
    """Test user configuration"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        }
    }

    # Without setting a key, it should use the first configuration
    assert manager.settings.name == "development"
    assert manager.settings.value == 42


def test_mapped_settings_manager_cli_args():
    """Test command line arguments"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        }
    }

    # Set active configuration through CLI args
    manager.set_cli_args("prod")

    assert manager.settings.name == "production"
    assert manager.settings.value == 100


def test_mapped_settings_manager_invalid_key():
    """Test invalid key"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
        }
    }

    # Try to set an invalid key
    manager.set_cli_args("invalid")

    with pytest.raises(ValueError):
        _ = manager.settings


def test_mapped_settings_manager_get_by_key():
    """Test get settings by key"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        }
    }

    # Get settings by key
    dev_settings = manager.get_settings_by_key("dev")
    assert dev_settings.name == "development"
    assert dev_settings.value == 42

    prod_settings = manager.get_settings_by_key("prod")
    assert prod_settings.name == "production"
    assert prod_settings.value == 100


def test_mapped_settings_manager_has_key():
    """Test has key"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
        }
    }

    assert manager.has_key("dev")
    assert not manager.has_key("prod")


def test_mapped_settings_manager_active_key():
    """Test active key"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        }
    }

    assert manager.active_key == ""

    manager.set_cli_args("dev")
    assert manager.active_key == "dev"


def test_mapped_settings_manager_all_settings():
    """Test all settings"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        }
    }

    all_settings = manager.all_settings
    assert len(all_settings) == 2
    assert all_settings["dev"].name == "development"
    assert all_settings["dev"].value == 42
    assert all_settings["prod"].name == "production"
    assert all_settings["prod"].value == 100


def test_mapped_settings_manager_clear():
    """Test clear settings"""
    manager = MappedSettingsManager(TestSettings)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 42},
        }
    }

    # Get settings to cache them
    _ = manager.settings

    # Clear settings
    manager.clear()

    # Modify config
    manager.user_config = {
        "map": {
            "dev": {"name": "new_development", "value": 100},
        }
    }

    # Check that new settings are used
    assert manager.settings.name == "new_development"
    assert manager.settings.value == 100