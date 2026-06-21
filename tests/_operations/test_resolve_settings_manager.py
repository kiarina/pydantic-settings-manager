import sys
from types import ModuleType

import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager
from pydantic_settings_manager._operations.resolve_settings_manager import resolve_settings_manager


class ExampleSettings(BaseSettings):
    """Example settings class for testing."""

    name: str = "default"
    value: int = 0


def test_resolve_settings_manager_success() -> None:
    module = ModuleType("test_resolve_settings_manager_success")
    module.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]
    sys.modules["test_resolve_settings_manager_success"] = module

    try:
        assert (
            resolve_settings_manager(
                "test_resolve_settings_manager_success",
                "settings_manager",
            )
            is module.settings_manager
        )

    finally:
        del sys.modules["test_resolve_settings_manager_success"]


def test_resolve_settings_manager_module_not_found() -> None:
    with pytest.raises(ModuleNotFoundError, match="Module not found: missing_module"):
        resolve_settings_manager("missing_module", "settings_manager")


def test_resolve_settings_manager_missing_attribute() -> None:
    module = ModuleType("test_resolve_settings_manager_missing_attribute")
    sys.modules["test_resolve_settings_manager_missing_attribute"] = module

    try:
        with pytest.raises(
            AttributeError,
            match=(
                "Module test_resolve_settings_manager_missing_attribute "
                "does not have a 'settings_manager' attribute"
            ),
        ):
            resolve_settings_manager(
                "test_resolve_settings_manager_missing_attribute",
                "settings_manager",
            )

    finally:
        del sys.modules["test_resolve_settings_manager_missing_attribute"]


def test_resolve_settings_manager_wrong_type() -> None:
    module = ModuleType("test_resolve_settings_manager_wrong_type")
    module.settings_manager = object()  # type: ignore[attr-defined]
    sys.modules["test_resolve_settings_manager_wrong_type"] = module

    try:
        with pytest.raises(
            TypeError,
            match=(
                "'settings_manager' in module test_resolve_settings_manager_wrong_type "
                "is not an instance of SettingsManager"
            ),
        ):
            resolve_settings_manager(
                "test_resolve_settings_manager_wrong_type",
                "settings_manager",
            )

    finally:
        del sys.modules["test_resolve_settings_manager_wrong_type"]
