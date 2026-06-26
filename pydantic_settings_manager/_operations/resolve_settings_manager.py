from importlib import import_module

from .._models.settings_manager import SettingsManager


def resolve_settings_manager(module_name: str, manager_name: str) -> SettingsManager:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as e:
        if e.name == module_name or (e.name is not None and module_name.startswith(f"{e.name}.")):
            raise ModuleNotFoundError(
                f"Module not found: {module_name}",
                name=module_name,
            ) from e
        raise

    if not hasattr(module, manager_name):
        raise AttributeError(f"Module {module_name} does not have a '{manager_name}' attribute")

    settings_manager = getattr(module, manager_name)

    if not isinstance(settings_manager, SettingsManager):
        raise TypeError(
            f"'{manager_name}' in module {module_name} is not an instance of "
            f"SettingsManager (got {type(settings_manager).__name__})"
        )

    return settings_manager
