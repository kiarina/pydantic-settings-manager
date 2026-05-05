from typing import Any, Literal

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

type UserConfig = dict[str, Any]
"""
Type alias for user configuration dictionaries.

Represents a configuration dictionary to be passed to a SettingsManager's user_config property.
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
