import sys
from types import ModuleType

from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager, clear_user_configs, load_user_configs


class ExampleSettings(BaseSettings):
    """Example settings class for testing."""

    name: str = "default"
    value: int = 0


def test_clear_user_configs_success() -> None:
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
