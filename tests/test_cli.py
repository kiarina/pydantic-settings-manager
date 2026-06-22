import sys
from types import ModuleType

import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager
from pydantic_settings_manager.cli import main


class CliSettings(BaseSettings):
    name: str = "default"
    api_key: str


def register_module_path(module_name: str, module: ModuleType) -> list[str]:
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


def cleanup_modules(module_names: list[str]) -> None:
    for module_name in reversed(module_names):
        sys.modules.pop(module_name, None)


def test_generate_user_configs_command_outputs_yaml(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = ModuleType("hoge.fuga._settings")
    module.settings_manager = SettingsManager(CliSettings)  # type: ignore[attr-defined]
    registered_modules = register_module_path("hoge.fuga._settings", module)

    try:
        exit_code = main(["generate-user-configs", "hoge.fuga._settings"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.err == ""
        assert captured.out.splitlines() == [
            "#--------------------------------------------------------------------------------",
            "#--------------------------------------------------------------------------------",
            "hoge.fuga:",
            "  # name: str",
            "  # name: default",
            "  #--------------------------------------------------",
            "  # api_key: str",
            "  api_key:",
        ]

    finally:
        cleanup_modules(registered_modules)


def test_generate_user_configs_command_supports_custom_manager_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = ModuleType("hoge.fuga.settings")
    module.app_manager = SettingsManager(CliSettings)  # type: ignore[attr-defined]
    registered_modules = register_module_path("hoge.fuga.settings", module)

    try:
        exit_code = main(
            [
                "generate-user-configs",
                "--manager-name",
                "app_manager",
                "hoge.fuga.settings",
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.err == ""
        assert captured.out.splitlines()[2] == "hoge.fuga.settings:"

    finally:
        cleanup_modules(registered_modules)


def test_generate_user_configs_command_writes_errors_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["generate-user-configs", "missing.module"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: Module not found: missing.module\n"
