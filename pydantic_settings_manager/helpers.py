from importlib import import_module
from typing import Any

from .manager import SettingsManager


def load_user_configs(
    user_configs: dict[str, Any],
    *,
    manager_name: str = "settings_manager",
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
    for module_name, user_config in user_configs.items():
        # Validate config type early
        if not isinstance(user_config, dict):
            raise TypeError(
                f"Configuration for module {module_name} must be a dictionary, "
                f"got {type(user_config).__name__}"
            )

        try:
            module = import_module(module_name)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(f"Module not found: {module_name}") from e

        # Check if attribute exists
        if not hasattr(module, manager_name):
            raise AttributeError(f"Module {module_name} does not have a '{manager_name}' attribute")

        settings_manager = getattr(module, manager_name)

        # Validate manager type
        if not isinstance(settings_manager, SettingsManager):
            raise TypeError(
                f"'{manager_name}' in module {module_name} is not an instance of "
                f"SettingsManager (got {type(settings_manager).__name__})"
            )

        settings_manager.user_config = user_config
