from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic_settings_manager import SettingsManager


class SlackSettings(BaseSettings):
    """Sample Slack settings"""

    model_config = SettingsConfigDict(
        env_prefix="SLACK_",
        extra="ignore",
    )

    bot_token: SecretStr = Field(
        ...,
        title="Slack Bot Token",
        description="The bot token for the Slack integration.",
    )

    default_channel: str = Field(
        ...,
        title="Default Slack Channel",
        description="The default channel to send messages to.",
    )


# Specifying multi=True lets the manager hold multiple settings
settings_manager = SettingsManager(SlackSettings, multi=True)
