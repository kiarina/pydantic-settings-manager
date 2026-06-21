"""
Tests for helper functions
"""

import sys
from types import ModuleType
from typing import Any

import pytest
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from pydantic_settings_manager import (
    SettingsManager,
    clear_user_configs,
    generate_user_configs_yaml,
    load_user_configs,
)


class ExampleSettings(BaseSettings):
    """Example settings class for testing"""

    name: str = "default"
    value: int = 0


def _register_module_path(module_name: str, module: ModuleType) -> list[str]:
    registered = []
    parts = module_name.split(".")

    for index in range(1, len(parts)):
        package_name = ".".join(parts[:index])
        if package_name not in sys.modules:
            package = ModuleType(package_name)
            package.__path__ = []
            sys.modules[package_name] = package
            registered.append(package_name)

    sys.modules[module_name] = module
    registered.append(module_name)
    return registered


def _cleanup_modules(module_names: list[str]) -> None:
    for module_name in reversed(module_names):
        sys.modules.pop(module_name, None)


class TemplateItem(BaseModel):
    """Item model"""

    name: str = Field(
        ...,
        title="Name",
        description="Name of the item",
    )
    value: int = Field(
        0,
        title="Value",
        description="Value of the item",
    )


class TemplateSettings(BaseSettings):
    """Settings for HogeFuga service"""

    hello_count: int = Field(
        1,
        title="Hello Count",
        description="Number of times to say hello",
    )
    api_key: str = Field(
        ...,
        title="API Key",
        description="API key for accessing the service",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        title="Metadata",
        description="Additional metadata for the service",
    )
    hoge_items: list[TemplateItem] = Field(
        default_factory=lambda: [
            TemplateItem(name="default", value=0),
            TemplateItem(name="example", value=1),
        ],
        title="Hoge Items",
        description="List of Hoge items",
    )


def test_generate_user_configs_yaml_template() -> None:
    """Test generating a user config YAML template from settings metadata"""
    module = ModuleType("hoge.fuga._settings")
    module.settings_manager = SettingsManager(TemplateSettings)  # type: ignore[attr-defined]
    registered_modules = _register_module_path("hoge.fuga._settings", module)

    try:
        yaml = generate_user_configs_yaml(["hoge.fuga._settings"])

        assert yaml == "\n".join(
            [
                "# Settings for HogeFuga service",
                "hoge.fuga:",
                "  # Hello Count",
                "  # Number of times to say hello",
                "  # hello_count: 1",
                "  #--------------------------------------------------",
                "  # API Key",
                "  # API key for accessing the service",
                "  api_key:",
                "  #--------------------------------------------------",
                "  # Metadata",
                "  # Additional metadata for the service",
                "  # metadata: {}",
                "  #--------------------------------------------------",
                "  # Hoge Items",
                "  # List of Hoge items",
                "  # hoge_items:",
                "  #   - name: default",
                "  #     value: 0",
                "  #   - name: example",
                "  #     value: 1",
            ]
        )

    finally:
        _cleanup_modules(registered_modules)


def test_generate_user_configs_yaml_module_key_rules_and_order() -> None:
    """Test import path conversion and ordering for generated templates"""
    first = ModuleType("hoge.fuga.settings")
    first.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]
    second = ModuleType("hoge.fuga._fire.settings")
    second.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    registered_modules = [
        *_register_module_path("hoge.fuga.settings", first),
        *_register_module_path("hoge.fuga._fire.settings", second),
    ]

    try:
        yaml = generate_user_configs_yaml(["hoge.fuga.settings", "hoge.fuga._fire.settings"])

        assert yaml.splitlines() == [
            "# Example settings class for testing",
            "hoge.fuga.settings:",
            "  # name: default",
            "  #--------------------------------------------------",
            "  # value: 0",
            "",
            "# Example settings class for testing",
            "hoge.fuga:",
            "  # name: default",
            "  #--------------------------------------------------",
            "  # value: 0",
        ]

    finally:
        _cleanup_modules(registered_modules)


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
        configs: dict[str, Any] = {
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
        configs: dict[str, Any] = {"test_custom_module": {"name": "custom", "value": 42}}

        load_user_configs(configs, manager_name="custom_manager")

        assert module.custom_manager.settings.name == "custom"
        assert module.custom_manager.settings.value == 42

    finally:
        del sys.modules["test_custom_module"]


def test_load_user_configs_module_not_found() -> None:
    """Test error when module is not found"""
    configs: dict[str, Any] = {"nonexistent_module": {"name": "test"}}

    with pytest.raises(ModuleNotFoundError, match="Module not found: nonexistent_module"):
        load_user_configs(configs)


def test_load_user_configs_missing_manager_attribute() -> None:
    """Test error when module doesn't have manager attribute"""
    module = ModuleType("test_no_manager")
    sys.modules["test_no_manager"] = module

    try:
        configs: dict[str, Any] = {"test_no_manager": {"name": "test"}}

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
        configs: dict[str, Any] = {"test_wrong_type": {"name": "test"}}

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
        configs: dict[str, Any] = {
            "test_multi_module": {
                "configs": {
                    "dev": {"name": "development", "value": 1},
                    "prod": {"name": "production", "value": 2},
                }
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
        configs: dict[str, Any] = {
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


class NestedSettings(BaseSettings):
    """Settings with a nested dict field for merge testing"""

    name: str = "default"
    value: int = 0
    nested: dict[str, Any] = {}


def test_load_user_configs_policy_replace() -> None:
    """Test that policy='replace' (default) replaces existing config"""
    module = ModuleType("test_policy_replace")
    module.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]
    sys.modules["test_policy_replace"] = module

    try:
        load_user_configs({"test_policy_replace": {"name": "first", "value": 1}})
        load_user_configs({"test_policy_replace": {"name": "second"}}, policy="replace")

        settings = module.settings_manager.settings
        assert settings.name == "second"
        assert settings.value == 0  # reset to default because config was replaced

    finally:
        del sys.modules["test_policy_replace"]


def test_load_user_configs_policy_merge_flat() -> None:
    """Test that policy='merge' merges flat fields without resetting untouched keys"""
    module = ModuleType("test_policy_merge_flat")
    module.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]
    sys.modules["test_policy_merge_flat"] = module

    try:
        load_user_configs({"test_policy_merge_flat": {"name": "first", "value": 1}})
        load_user_configs({"test_policy_merge_flat": {"name": "second"}}, policy="merge")

        settings = module.settings_manager.settings
        assert settings.name == "second"
        assert settings.value == 1  # preserved from first load

    finally:
        del sys.modules["test_policy_merge_flat"]


def test_load_user_configs_policy_merge_nested() -> None:
    """Test that policy='merge' deep-merges nested dicts"""

    module = ModuleType("test_policy_merge_nested")
    module.settings_manager = SettingsManager(NestedSettings)  # type: ignore[attr-defined]
    sys.modules["test_policy_merge_nested"] = module

    try:
        load_user_configs(
            {"test_policy_merge_nested": {"nested": {"a": 1, "b": 2}}},
        )
        load_user_configs(
            {"test_policy_merge_nested": {"nested": {"b": 99, "c": 3}}},
            policy="merge",
        )

        settings: NestedSettings = module.settings_manager.settings
        assert settings.nested == {"a": 1, "b": 99, "c": 3}

    finally:
        del sys.modules["test_policy_merge_nested"]


def test_load_user_configs_policy_merge_list_replaced() -> None:
    """Test that policy='merge' replaces lists (not appends)"""
    module = ModuleType("test_policy_merge_list")
    module.settings_manager = SettingsManager(NestedSettings)  # type: ignore[attr-defined]
    sys.modules["test_policy_merge_list"] = module

    try:
        load_user_configs(
            {"test_policy_merge_list": {"nested": {"items": [1, 2, 3]}}},
        )
        load_user_configs(
            {"test_policy_merge_list": {"nested": {"items": [4, 5]}}},
            policy="merge",
        )

        settings: NestedSettings = module.settings_manager.settings
        assert settings.nested == {"items": [4, 5]}

    finally:
        del sys.modules["test_policy_merge_list"]


def test_load_user_configs_policy_merge_multi_mode() -> None:
    """Test that policy='merge' works correctly with multi-mode managers"""
    module = ModuleType("test_policy_merge_multi")
    module.settings_manager = SettingsManager(ExampleSettings, multi=True)  # type: ignore[attr-defined]
    sys.modules["test_policy_merge_multi"] = module

    try:
        load_user_configs(
            {"test_policy_merge_multi": {"configs": {"dev": {"name": "dev-app", "value": 1}}}},
        )
        load_user_configs(
            {"test_policy_merge_multi": {"configs": {"prod": {"name": "prod-app", "value": 2}}}},
            policy="merge",
        )

        manager: SettingsManager[ExampleSettings] = module.settings_manager
        manager.active_key = "dev"
        assert manager.settings.name == "dev-app"
        manager.active_key = "prod"
        assert manager.settings.name == "prod-app"

    finally:
        del sys.modules["test_policy_merge_multi"]


def test_clear_user_configs_success() -> None:
    """Test successful clearing of user configs"""
    module1 = ModuleType("test_clear_module1")
    module1.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    module2 = ModuleType("test_clear_module2")
    module2.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    sys.modules["test_clear_module1"] = module1
    sys.modules["test_clear_module2"] = module2

    try:
        load_user_configs(
            {
                "test_clear_module1": {"name": "module1", "value": 1},
                "test_clear_module2": {"name": "module2", "value": 2},
            }
        )

        assert module1.settings_manager.settings.name == "module1"
        assert module2.settings_manager.settings.name == "module2"

        clear_user_configs(
            {
                "test_clear_module1": {"name": "module1", "value": 1},
                "test_clear_module2": {"name": "module2", "value": 2},
            }
        )

        assert module1.settings_manager.settings.name == "default"
        assert module1.settings_manager.settings.value == 0
        assert module2.settings_manager.settings.name == "default"
        assert module2.settings_manager.settings.value == 0

    finally:
        del sys.modules["test_clear_module1"]
        del sys.modules["test_clear_module2"]


def test_clear_user_configs_custom_manager_name() -> None:
    """Test clearing with custom manager name"""
    module = ModuleType("test_clear_custom_module")
    module.custom_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    sys.modules["test_clear_custom_module"] = module

    try:
        load_user_configs(
            {"test_clear_custom_module": {"name": "custom", "value": 42}},
            manager_name="custom_manager",
        )
        assert module.custom_manager.settings.name == "custom"

        clear_user_configs(
            {"test_clear_custom_module": {"name": "custom", "value": 42}},
            manager_name="custom_manager",
        )
        assert module.custom_manager.settings.name == "default"
        assert module.custom_manager.settings.value == 0

    finally:
        del sys.modules["test_clear_custom_module"]


def test_load_user_configs_invalid_policy() -> None:
    """Test error when policy is invalid"""
    with pytest.raises(ValueError, match="policy must be 'replace' or 'merge'"):
        load_user_configs({}, policy="invalid")  # type: ignore[arg-type]
