import sys
from types import ModuleType

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager, generate_user_configs_yaml


class ExampleSettings(BaseSettings):
    """Example settings class for testing."""

    name: str = "default"
    value: int = 0


class TemplateItem(BaseModel):
    """Item model."""

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
    """Settings for HogeFuga service."""

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


def test_generate_user_configs_yaml_template() -> None:
    module = ModuleType("hoge.fuga._settings")
    module.settings_manager = SettingsManager(TemplateSettings)  # type: ignore[attr-defined]
    registered_modules = register_module_path("hoge.fuga._settings", module)

    try:
        yaml = generate_user_configs_yaml(["hoge.fuga._settings"])

        assert yaml == "\n".join(
            [
                "# Settings for HogeFuga service.",
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
        cleanup_modules(registered_modules)


def test_generate_user_configs_yaml_template_for_multi_mode() -> None:
    module = ModuleType("hoge.multi._settings")
    module.settings_manager = SettingsManager(TemplateSettings, multi=True)  # type: ignore[attr-defined]
    registered_modules = register_module_path("hoge.multi._settings", module)

    try:
        yaml = generate_user_configs_yaml(["hoge.multi._settings"])

        assert yaml == "\n".join(
            [
                "# Settings for HogeFuga service.",
                "hoge.multi:",
                "  # default: default",
                "  configs:",
                "    default:",
                "      # Hello Count",
                "      # Number of times to say hello",
                "      # hello_count: 1",
                "      #--------------------------------------------------",
                "      # API Key",
                "      # API key for accessing the service",
                "      api_key:",
                "      #--------------------------------------------------",
                "      # Metadata",
                "      # Additional metadata for the service",
                "      # metadata: {}",
                "      #--------------------------------------------------",
                "      # Hoge Items",
                "      # List of Hoge items",
                "      # hoge_items:",
                "      #   - name: default",
                "      #     value: 0",
                "      #   - name: example",
                "      #     value: 1",
                "  # aliases: {}",
            ]
        )

    finally:
        cleanup_modules(registered_modules)


def test_generate_user_configs_yaml_module_key_rules_and_order() -> None:
    first = ModuleType("hoge.fuga.settings")
    first.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]
    second = ModuleType("hoge.fuga._fire.settings")
    second.settings_manager = SettingsManager(ExampleSettings)  # type: ignore[attr-defined]

    registered_modules = [
        *register_module_path("hoge.fuga.settings", first),
        *register_module_path("hoge.fuga._fire.settings", second),
    ]

    try:
        yaml = generate_user_configs_yaml(["hoge.fuga.settings", "hoge.fuga._fire.settings"])

        assert yaml.splitlines() == [
            "# Example settings class for testing.",
            "hoge.fuga.settings:",
            "  # name: default",
            "  #--------------------------------------------------",
            "  # value: 0",
            "",
            "# Example settings class for testing.",
            "hoge.fuga:",
            "  # name: default",
            "  #--------------------------------------------------",
            "  # value: 0",
        ]

    finally:
        cleanup_modules(registered_modules)
