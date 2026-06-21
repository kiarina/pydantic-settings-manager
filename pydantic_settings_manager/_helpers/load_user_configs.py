from typing import cast

from .._operations.resolve_settings_manager import resolve_settings_manager
from .._types.config_policy import ConfigPolicy
from .._types.user_configs import UserConfigs
from .._utils.update_dict import update_dict


def load_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
    policy: ConfigPolicy = "replace",
) -> None:
    """Load user configurations into their respective settings managers."""
    if policy not in {"replace", "merge"}:
        raise ValueError("policy must be 'replace' or 'merge'")

    for module_name, user_config in user_configs.items():
        if not isinstance(user_config, dict):
            raise TypeError(
                f"Configuration for module {module_name} must be a dictionary, "
                f"got {type(user_config).__name__}"
            )

        settings_manager = resolve_settings_manager(module_name, manager_name)
        config_dict = cast(dict, user_config)

        if policy == "merge":
            settings_manager.user_config = update_dict(settings_manager.user_config, config_dict)
        else:
            settings_manager.user_config = config_dict
