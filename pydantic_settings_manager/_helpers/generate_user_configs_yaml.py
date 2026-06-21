from typing import Any

from pydantic import BaseModel

from .._constants.default_key import DEFAULT_KEY
from .._operations.resolve_settings_manager import resolve_settings_manager


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

    lines: list[str] = []
    doc = settings_cls.__doc__
    if doc:
        for doc_line in _clean_doc_lines(doc):
            lines.append(f"# {doc_line}" if doc_line else "#")

    lines.append(f"{_module_config_key(import_path)}:")
    if settings_manager.multi:
        lines.append(f"  # default: {DEFAULT_KEY}")
        lines.append("  configs:")
        lines.append(f"    {DEFAULT_KEY}:")
        lines.extend(_generate_settings_fields_yaml_lines(settings_cls, indent=6))
        lines.append("  # aliases: {}")
        return "\n".join(lines)

    lines.extend(_generate_settings_fields_yaml_lines(settings_cls, indent=2))
    return "\n".join(lines)


def _generate_settings_fields_yaml_lines(
    settings_cls: type[BaseModel],
    *,
    indent: int,
) -> list[str]:
    comment_prefix = " " * indent
    separator = f"{comment_prefix}#--------------------------------------------------"
    lines: list[str] = []

    fields = list(settings_cls.model_fields.items())
    for index, (field_name, field_info) in enumerate(fields):
        if index:
            lines.append(separator)

        if field_info.title:
            lines.append(f"{comment_prefix}# {field_info.title}")
        if field_info.description:
            for description_line in _clean_doc_lines(field_info.description):
                if description_line:
                    lines.append(f"{comment_prefix}# {description_line}")
                else:
                    lines.append(f"{comment_prefix}#")

        if field_info.is_required():
            lines.append(f"{comment_prefix}{field_name}:")
            continue

        default_value = field_info.get_default(call_default_factory=True)
        rendered_lines = _render_yaml_key_value(
            field_name,
            _to_yaml_value(default_value),
            indent=indent,
        )
        lines.extend(f"{comment_prefix}# {line[indent:]}" for line in rendered_lines)

    return lines


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
