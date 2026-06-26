import warnings
from typing import cast

from .._operations.resolve_settings_manager import resolve_settings_manager
from .._types.config_update_policy import ConfigUpdatePolicy
from .._types.missing_module_policy import MissingModulePolicy
from .._types.user_configs import UserConfigs
from .._utils.update_dict import update_dict


def load_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
    update_policy: ConfigUpdatePolicy = "replace",
    missing_module_policy: MissingModulePolicy = "error",
) -> None:
    """Load user configurations into their respective settings managers."""
    if update_policy not in {"replace", "merge"}:
        raise ValueError("update_policy must be 'replace' or 'merge'")
    if missing_module_policy not in {"error", "warn", "ignore"}:
        raise ValueError("missing_module_policy must be 'error', 'warn', or 'ignore'")

    for module_name, user_config in user_configs.items():
        if not isinstance(user_config, dict):
            raise TypeError(
                f"Configuration for module {module_name} must be a dictionary, "
                f"got {type(user_config).__name__}"
            )

        try:
            settings_manager = resolve_settings_manager(module_name, manager_name)
        except ModuleNotFoundError as e:
            if e.name != module_name or missing_module_policy == "error":
                raise
            if missing_module_policy == "warn":
                warnings.warn(str(e), stacklevel=2)
            continue

        config_dict = cast(dict, user_config)

        if update_policy == "merge":
            settings_manager.user_config = update_dict(settings_manager.user_config, config_dict)
        else:
            settings_manager.user_config = config_dict
