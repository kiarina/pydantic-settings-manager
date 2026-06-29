import sys
from collections.abc import Iterator
from types import ModuleType

import pytest
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager, UserConfigError


class SlackSettings(BaseSettings):
    """Slack integration settings."""

    bot_token: str = Field(default="", description="Bot token used to call the Slack API.")
    default_channel: str = Field(
        title="Default Slack Channel",
        description="The default channel to send messages to.",
    )


class ServerSettings(BaseSettings):
    """HTTP server settings."""

    port: int = Field(title="Port", description="Port to bind.")
    host: str = "0.0.0.0"


def _register(name: str, manager: SettingsManager, settings_cls: type) -> None:
    module = ModuleType(name)
    module.settings_manager = manager  # type: ignore[attr-defined]
    sys.modules[name] = module
    settings_cls.__module__ = name


@pytest.fixture
def slack_manager() -> Iterator[SettingsManager[SlackSettings]]:
    manager: SettingsManager[SlackSettings] = SettingsManager(SlackSettings, multi=True)
    _register("uc_slack", manager, SlackSettings)
    try:
        yield manager
    finally:
        del sys.modules["uc_slack"]


@pytest.fixture
def server_manager() -> Iterator[SettingsManager[ServerSettings]]:
    manager: SettingsManager[ServerSettings] = SettingsManager(ServerSettings)
    _register("uc_server", manager, ServerSettings)
    try:
        yield manager
    finally:
        del sys.modules["uc_server"]


def test_missing_required_field_multi(slack_manager: SettingsManager[SlackSettings]) -> None:
    slack_manager.user_config = {"configs": {"default": {"bot_token": "xoxb-..."}}}

    with pytest.raises(UserConfigError) as exc_info:
        _ = slack_manager.settings

    assert str(exc_info.value) == (
        "Failed to load user settings.\n"
        "\n"
        "uc_slack:\n"
        "  configs:\n"
        "    default:\n"
        "      #--------------------------------------------------\n"
        "      # Default Slack Channel: str\n"
        "      #   The default channel to send messages to.\n"
        "      #   required field is not set\n"
        "      default_channel:"
    )
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_invalid_value_echoes_input_single(server_manager: SettingsManager[ServerSettings]) -> None:
    server_manager.user_config = {"port": "not-a-number"}

    with pytest.raises(UserConfigError) as exc_info:
        _ = server_manager.settings

    message = str(exc_info.value)
    assert message.startswith("Failed to load user settings.\n\nuc_server:\n")
    assert "# Port: int" in message
    assert "#   Input should be a valid integer" in message
    assert message.endswith("  port: not-a-number")


def test_user_config_error_is_value_error(slack_manager: SettingsManager[SlackSettings]) -> None:
    slack_manager.user_config = {"configs": {"default": {}}}

    with pytest.raises(ValueError):
        _ = slack_manager.settings


def test_unresolvable_manager_raises_original_validation_error() -> None:
    class Orphan(BaseSettings):
        x: int = Field(title="X")

    # Not bound to any module attribute, so no friendly message can be built.
    manager: SettingsManager[Orphan] = SettingsManager(Orphan)

    with pytest.raises(ValidationError):
        _ = manager.settings
