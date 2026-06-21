from importlib import import_module
from typing import Any

from pydantic import BaseModel

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


def generate_user_configs_yaml(
    import_paths: list[str],
    *,
    manager_name: str = "settings_manager",
) -> str:
    """
    Generate a commented YAML template for user configuration files.

    Args:
        import_paths: Module import paths that contain settings managers.
        manager_name: The name of the SettingsManager attribute in each module.
            Defaults to "settings_manager".

    Returns:
        A YAML string with required fields enabled and fields with defaults
        commented out.

    Raises:
        ModuleNotFoundError: If a specified module cannot be imported.
        AttributeError: If a module doesn't have the specified manager attribute.
        TypeError: If the manager attribute is not a SettingsManager instance.
    """
    blocks = [
        _generate_user_config_yaml_block(import_path, manager_name=manager_name)
        for import_path in import_paths
    ]
    return "\n\n".join(blocks)


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


def _generate_user_config_yaml_block(import_path: str, *, manager_name: str) -> str:
    settings_manager = _resolve_settings_manager(import_path, manager_name)
    settings_cls = settings_manager.settings_cls

    lines: list[str] = []
    doc = settings_cls.__doc__
    if doc:
        for doc_line in _clean_doc_lines(doc):
            lines.append(f"# {doc_line}" if doc_line else "#")

    lines.append(f"{_module_config_key(import_path)}:")

    fields = list(settings_cls.model_fields.items())
    for index, (field_name, field_info) in enumerate(fields):
        if index:
            lines.append("  #--------------------------------------------------")

        if field_info.title:
            lines.append(f"  # {field_info.title}")
        if field_info.description:
            for description_line in _clean_doc_lines(field_info.description):
                lines.append(f"  # {description_line}" if description_line else "  #")

        if field_info.is_required():
            lines.append(f"  {field_name}:")
            continue

        default_value = field_info.get_default(call_default_factory=True)
        rendered_lines = _render_yaml_key_value(field_name, _to_yaml_value(default_value), indent=2)
        lines.extend(f"  # {line[2:]}" for line in rendered_lines)

    return "\n".join(lines)


def _module_config_key(import_path: str) -> str:
    parts = []
    for part in import_path.split("."):
        if part.startswith("_"):
            break
        parts.append(part)
    return ".".join(parts)


def _clean_doc_lines(value: str) -> list[str]:
    return [line.strip() for line in value.strip().splitlines()]


def _to_yaml_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _to_yaml_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_yaml_value(item) for item in value]
    if isinstance(value, tuple):
        return [_to_yaml_value(item) for item in value]
    return value


def _render_yaml_key_value(key: str, value: Any, *, indent: int) -> list[str]:
    spaces = " " * indent
    if _is_scalar(value):
        return [f"{spaces}{key}: {_format_scalar(value)}"]

    if isinstance(value, dict) and not value:
        return [f"{spaces}{key}: {{}}"]

    if isinstance(value, list) and not value:
        return [f"{spaces}{key}: []"]

    lines = [f"{spaces}{key}:"]
    lines.extend(_render_yaml_value(value, indent=indent + 2))
    return lines


def _render_yaml_value(value: Any, *, indent: int) -> list[str]:
    spaces = " " * indent

    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            lines.extend(_render_yaml_key_value(str(key), item, indent=indent))
        return lines

    if isinstance(value, list):
        lines = []
        for item in value:
            if _is_scalar(item):
                lines.append(f"{spaces}- {_format_scalar(item)}")
            elif isinstance(item, dict):
                if not item:
                    lines.append(f"{spaces}- {{}}")
                    continue

                first_key = True
                for key, nested_item in item.items():
                    rendered = _render_yaml_key_value(str(key), nested_item, indent=indent + 2)
                    if first_key:
                        lines.append(f"{spaces}- {rendered[0].lstrip()}")
                        lines.extend(rendered[1:])
                        first_key = False
                    else:
                        lines.extend(rendered)
            else:
                lines.append(f"{spaces}-")
                lines.extend(_render_yaml_value(item, indent=indent + 2))
        return lines

    return [f"{spaces}{_format_scalar(value)}"]


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _format_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if not value:
            return '""'
        if _is_plain_yaml_string(value):
            return value
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(value)


def _is_plain_yaml_string(value: str) -> bool:
    if value.strip() != value or "\n" in value or ": " in value:
        return False
    if value in {"null", "Null", "NULL", "true", "True", "TRUE", "false", "False", "FALSE"}:
        return False
    return all(char.isalnum() or char in "_-./${}" for char in value)
