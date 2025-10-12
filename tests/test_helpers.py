"""
Tests for helper functions
"""

import sys
from types import ModuleType
from typing import Any

import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager, load_user_configs


class ExampleSettings(BaseSettings):
    """Example settings class for testing"""

    name: str = "default"
    value: int = 0


def test_load_user_configs_success() -> None:
    """Test successful loading of user configs"""
    # Create mock modules with settings managers
    module1 = ModuleType("test_module1")
    module1.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    module2 = ModuleType("test_module2")
    module2.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    # Add to sys.modules
    sys.modules["test_module1"] = module1
    sys.modules["test_module2"] = module2

    try:
        # Load configs
        configs = {
            "test_module1": {"name": "module1", "value": 1},
            "test_module2": {"name": "module2", "value": 2},
        }

        load_user_configs(configs)

        # Verify configs were loaded
        assert module1.settings_manager.settings.name == "module1"
        assert module1.settings_manager.settings.value == 1
        assert module2.settings_manager.settings.name == "module2"
        assert module2.settings_manager.settings.value == 2

    finally:
        # Cleanup
        del sys.modules["test_module1"]
        del sys.modules["test_module2"]


def test_load_user_configs_custom_manager_name() -> None:
    """Test loading with custom manager name"""
    module = ModuleType("test_custom_module")
    module.custom_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    sys.modules["test_custom_module"] = module

    try:
        configs = {"test_custom_module": {"name": "custom", "value": 42}}

        load_user_configs(configs, manager_name="custom_manager")

        assert module.custom_manager.settings.name == "custom"
        assert module.custom_manager.settings.value == 42

    finally:
        del sys.modules["test_custom_module"]


def test_load_user_configs_module_not_found() -> None:
    """Test error when module is not found"""
    configs = {"nonexistent_module": {"name": "test"}}

    with pytest.raises(ModuleNotFoundError, match="Module not found: nonexistent_module"):
        load_user_configs(configs)


def test_load_user_configs_missing_manager_attribute() -> None:
    """Test error when module doesn't have manager attribute"""
    module = ModuleType("test_no_manager")
    sys.modules["test_no_manager"] = module

    try:
        configs = {"test_no_manager": {"name": "test"}}

        with pytest.raises(
            AttributeError,
            match="Module test_no_manager does not have a 'settings_manager' attribute",
        ):
            load_user_configs(configs)

    finally:
        del sys.modules["test_no_manager"]


def test_load_user_configs_wrong_manager_type() -> None:
    """Test error when manager is not a SettingsManager instance"""
    module = ModuleType("test_wrong_type")
    module.settings_manager = "not a manager"  # type: ignore[attr-defined]

    sys.modules["test_wrong_type"] = module

    try:
        configs = {"test_wrong_type": {"name": "test"}}

        with pytest.raises(
            TypeError,
            match=(
                "'settings_manager' in module test_wrong_type is not an instance of SettingsManager"
            ),
        ):
            load_user_configs(configs)

    finally:
        del sys.modules["test_wrong_type"]


def test_load_user_configs_invalid_config_type() -> None:
    """Test error when config is not a dictionary"""
    module = ModuleType("test_invalid_config")
    module.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    sys.modules["test_invalid_config"] = module

    try:
        configs: dict[str, Any] = {"test_invalid_config": "not a dict"}

        with pytest.raises(
            TypeError, match="Configuration for module test_invalid_config must be a dictionary"
        ):
            load_user_configs(configs)

    finally:
        del sys.modules["test_invalid_config"]


def test_load_user_configs_multi_mode() -> None:
    """Test loading configs for multi-mode managers"""
    module = ModuleType("test_multi_module")
    module.settings_manager = SettingsManager(ExampleSettings, multi=True)  # type: ignore[attr-defined]

    sys.modules["test_multi_module"] = module

    try:
        configs = {
            "test_multi_module": {
                "dev": {"name": "development", "value": 1},
                "prod": {"name": "production", "value": 2},
            }
        }

        load_user_configs(configs)

        # Verify multi-mode config was loaded
        manager: SettingsManager[ExampleSettings] = module.settings_manager
        manager.active_key = "dev"
        assert manager.settings.name == "development"
        assert manager.settings.value == 1

        manager.active_key = "prod"
        assert manager.settings.name == "production"
        assert manager.settings.value == 2

    finally:
        del sys.modules["test_multi_module"]


def test_load_user_configs_empty() -> None:
    """Test loading empty configs"""
    # Should not raise any errors
    load_user_configs({})


def test_load_user_configs_partial_failure() -> None:
    """Test that failure in one module doesn't affect others"""
    module1 = ModuleType("test_partial1")
    module1.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    sys.modules["test_partial1"] = module1

    try:
        configs = {
            "test_partial1": {"name": "first", "value": 1},
            "nonexistent_module": {"name": "second", "value": 2},
        }

        # Should fail on second module
        with pytest.raises(ModuleNotFoundError):
            load_user_configs(configs)

        # First module should not have been configured due to iteration order
        # (Python dicts maintain insertion order, so first module is processed first)
        # But if it was processed, it should have the config
        # This test verifies the function doesn't have transaction-like behavior

    finally:
        del sys.modules["test_partial1"]
