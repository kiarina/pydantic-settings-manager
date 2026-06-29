import sys
from types import ModuleType

from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager
from pydantic_settings_manager._operations.resolve_module_config_path import (
    resolve_module_config_path,
)


class SampleSettings(BaseSettings):
    name: str = "default"


def _register_module(name: str, **attrs: object) -> ModuleType:
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def test_resolves_module_that_re_exports_manager() -> None:
    manager: SettingsManager = SettingsManager(SampleSettings)
    _register_module("rmcp_pkg")
    _register_module("rmcp_pkg.app", settings_manager=manager)
    manager.settings_cls.__module__ = "rmcp_pkg.app"

    try:
        assert resolve_module_config_path(manager) == "rmcp_pkg.app"
    finally:
        del sys.modules["rmcp_pkg"]
        del sys.modules["rmcp_pkg.app"]


def test_prefers_shallowest_public_re_export() -> None:
    manager: SettingsManager = SettingsManager(SampleSettings)
    # Manager is re-exported both at the public package root and the private submodule.
    _register_module("rmcp_shallow", settings_manager=manager)
    _register_module("rmcp_shallow._internal", settings_manager=manager)
    manager.settings_cls.__module__ = "rmcp_shallow._internal"

    try:
        assert resolve_module_config_path(manager) == "rmcp_shallow"
    finally:
        del sys.modules["rmcp_shallow"]
        del sys.modules["rmcp_shallow._internal"]


def test_uses_custom_manager_name() -> None:
    manager: SettingsManager = SettingsManager(SampleSettings)
    _register_module("rmcp_custom", my_manager=manager)
    manager.settings_cls.__module__ = "rmcp_custom"

    try:
        assert resolve_module_config_path(manager, manager_name="my_manager") == "rmcp_custom"
        assert resolve_module_config_path(manager, manager_name="settings_manager") is None
    finally:
        del sys.modules["rmcp_custom"]


def test_falls_back_to_scanning_imported_modules() -> None:
    manager: SettingsManager = SettingsManager(SampleSettings)
    # The settings class lives in a module that does not re-export the manager,
    # so the prefix walk misses and the fallback scan must find the binding.
    _register_module("rmcp_defines_only")
    manager.settings_cls.__module__ = "rmcp_defines_only"
    _register_module("rmcp_a.b.c", settings_manager=manager)
    _register_module("rmcp_short", settings_manager=manager)

    try:
        # Among the bindings, the shallowest public path wins.
        assert resolve_module_config_path(manager) == "rmcp_short"
    finally:
        del sys.modules["rmcp_defines_only"]
        del sys.modules["rmcp_a.b.c"]
        del sys.modules["rmcp_short"]


def test_returns_none_when_manager_not_re_exported() -> None:
    manager: SettingsManager = SettingsManager(SampleSettings)
    _register_module("rmcp_orphan")
    manager.settings_cls.__module__ = "rmcp_orphan"

    try:
        assert resolve_module_config_path(manager) is None
    finally:
        del sys.modules["rmcp_orphan"]
