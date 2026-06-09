from typing import Any, Literal, NotRequired, TypedDict

type SettingsKey = str
"""
Type alias for settings manager keys.

This is a type alias for documentation and clarity purposes.
"""

type ModuleName = str
"""
Type alias for module names used in load_user_configs.

Represents a fully qualified module name (e.g., "myapp.settings", "myapp.auth.settings").
"""


class MultiUserConfig(TypedDict):
    """
    Type definition for multi-configuration format (v3.0.0).
    """

    configs: dict[str, dict[str, Any]]
    default: NotRequired[str | None]
    aliases: NotRequired[dict[str, str]]


type SingleUserConfig = dict[str, Any]
"""
Type alias for single configuration dictionary.
"""

type UserConfig = SingleUserConfig | MultiUserConfig
"""
Type alias for user configuration.

Can be a direct dictionary for single mode, or a structured dictionary for multi mode.
"""

type UserConfigs = dict[ModuleName, UserConfig]
"""
Type alias for multiple user configurations.

Maps module names to their respective configuration dictionaries.
Used in load_user_configs function.
"""

type ConfigPolicy = Literal["replace", "merge"]
"""
Type alias for configuration merge policy.

- "replace": replace the existing user_config entirely (default)
- "merge": deep-merge into the existing user_config (dicts are merged recursively,
  all other types are replaced)
"""
