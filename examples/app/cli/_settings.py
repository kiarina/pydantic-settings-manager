from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic_settings_manager import SettingsManager


class CLISettings(BaseSettings):
    """Sample CLI settings"""

    model_config = SettingsConfigDict(
        env_prefix="CLI_",
        extra="ignore",
    )

    verbose: bool = Field(
        default=False,
        title="Verbose Mode",
        description="Enable verbose output for debugging purposes.",
    )


settings_manager = SettingsManager(CLISettings)
