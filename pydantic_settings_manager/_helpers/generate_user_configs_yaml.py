import inspect

from .._constants.default_key import DEFAULT_KEY
from .._operations.generate_settings_fields_yaml_lines import generate_settings_fields_yaml_lines
from .._operations.resolve_settings_manager import resolve_settings_manager

_IMPORT_PATH_SEPARATOR = "#" + "-" * 80


def generate_user_configs_yaml(
    import_paths: list[str],
    *,
    manager_name: str = "settings_manager",
) -> str:
    """Generate a commented YAML template for user configuration files."""
    blocks = [
        _generate_user_config_yaml_block(import_path, manager_name=manager_name)
        for import_path in import_paths
    ]
    return "\n\n".join(blocks)


def _generate_user_config_yaml_block(import_path: str, *, manager_name: str) -> str:
    settings_manager = resolve_settings_manager(import_path, manager_name)
    settings_cls = settings_manager.settings_cls

    lines: list[str] = [_IMPORT_PATH_SEPARATOR]
    doc = settings_cls.__doc__
    if doc:
        for doc_line in inspect.cleandoc(doc).splitlines():
            lines.append(f"# {doc_line}" if doc_line else "#")

    lines.append(_IMPORT_PATH_SEPARATOR)
    lines.append(f"{_module_config_key(import_path)}:")
    if settings_manager.multi:
        lines.append(f"  # default: {DEFAULT_KEY}")
        lines.append("  configs:")
        lines.append(f"    {DEFAULT_KEY}:")
        lines.extend(generate_settings_fields_yaml_lines(settings_cls, indent=6))
        lines.append("  # aliases: {}")
        return "\n".join(lines)

    lines.extend(generate_settings_fields_yaml_lines(settings_cls, indent=2))
    return "\n".join(lines)


def _module_config_key(import_path: str) -> str:
    parts = []
    for part in import_path.split("."):
        if part.startswith("_"):
            break
        parts.append(part)
    return ".".join(parts)
