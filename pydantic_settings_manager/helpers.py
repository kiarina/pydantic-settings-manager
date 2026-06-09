from importlib import import_module

from .manager import SettingsManager
from .types import ConfigPolicy, UserConfigs
from .utils import update_dict


def load_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
    policy: ConfigPolicy = "replace",
) -> None:
    """
    Load user configurations into their respective settings managers.

    This function dynamically imports modules and sets their settings manager's
    user_config property. It's useful for bulk configuration loading across
    multiple modules.

    Args:
        user_configs: A dictionary mapping module names to their configuration.
            Keys are module names (e.g., "myapp.settings", "myapp.auth.settings").
            Values are configuration dictionaries to be passed to each manager's
            user_config property.
        manager_name: The name of the SettingsManager attribute in each module.
            Defaults to "settings_manager".
        policy: How to apply the configuration to each manager. Defaults to "replace".
            - "replace": replace the existing user_config entirely.
            - "merge": deep-merge into the existing user_config. Dicts are merged
              recursively; all other types (None, bool, int, float, str, list) are
              replaced. Useful when calling load_user_configs multiple times on the
              same manager, e.g. applying a global config first and then
              environment-specific overrides.

    Raises:
        ModuleNotFoundError: If a specified module cannot be imported.
        AttributeError: If a module doesn't have the specified manager attribute.
        TypeError: If the manager attribute is not a SettingsManager instance,
            or if a config value is not a dictionary.

    Example:
        ```python
        # Module structure:
        # myapp/
        #   settings.py  (contains: settings_manager = SettingsManager(...))
        #   auth/
        #     settings.py  (contains: settings_manager = SettingsManager(...))

        configs = {
            "myapp.settings": {
                "app_name": "MyApp",
                "debug": True
            },
            "myapp.auth.settings": {
                "jwt_secret": "secret",
                "token_expiry": 3600
            }
        }

        load_user_configs(configs)
        ```
    """
    if policy not in {"replace", "merge"}:
        raise ValueError("policy must be 'replace' or 'merge'")

    for module_name, user_config in user_configs.items():
        # Validate config type early
        if not isinstance(user_config, dict):
            raise TypeError(
                f"Configuration for module {module_name} must be a dictionary, "
                f"got {type(user_config).__name__}"
            )

        settings_manager = _resolve_settings_manager(module_name, manager_name)

        from typing import cast

        config_dict = cast(dict, user_config)

        if policy == "merge":
            settings_manager.user_config = update_dict(settings_manager.user_config, config_dict)
        else:
            settings_manager.user_config = config_dict


def clear_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
) -> None:
    """
    Clear user configurations from their respective settings managers.

    This function dynamically imports modules and resets their settings manager's
    user_config property to an empty dictionary.

    Args:
        user_configs: A dictionary mapping module names to their configuration.
            Keys are module names used to locate each target settings manager.
            Values are ignored by this function.
        manager_name: The name of the SettingsManager attribute in each module.
            Defaults to "settings_manager".

    Raises:
        ModuleNotFoundError: If a specified module cannot be imported.
        AttributeError: If a module doesn't have the specified manager attribute.
        TypeError: If the manager attribute is not a SettingsManager instance.
    """
    for module_name in user_configs:
        settings_manager = _resolve_settings_manager(module_name, manager_name)
        settings_manager.reset_user_config()


def _resolve_settings_manager(module_name: str, manager_name: str) -> SettingsManager:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Module not found: {module_name}") from e

    if not hasattr(module, manager_name):
        raise AttributeError(f"Module {module_name} does not have a '{manager_name}' attribute")

    settings_manager = getattr(module, manager_name)

    if not isinstance(settings_manager, SettingsManager):
        raise TypeError(
            f"'{manager_name}' in module {module_name} is not an instance of "
            f"SettingsManager (got {type(settings_manager).__name__})"
        )

    return settings_manager
