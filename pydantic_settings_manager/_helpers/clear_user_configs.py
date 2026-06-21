from .._operations.resolve_settings_manager import resolve_settings_manager
from .._types.user_configs import UserConfigs


def clear_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
) -> None:
    """Clear user configurations from their respective settings managers."""
    for module_name in user_configs:
        settings_manager = resolve_settings_manager(module_name, manager_name)
        settings_manager.reset_user_config()
