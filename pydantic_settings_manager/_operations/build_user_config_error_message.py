from pydantic import BaseModel
from pydantic_core import ErrorDetails

from .._models.settings_manager import SettingsManager
from .generate_settings_fields_yaml_lines import (
    FieldError,
    generate_settings_fields_yaml_lines,
)
from .resolve_module_config_path import resolve_module_config_path


def build_user_config_error_message(
    manager: SettingsManager,
    config_key: str,
    errors: list[ErrorDetails],
) -> str | None:
    """Build a user-friendly message for a failed config validation.

    Returns ``None`` when the manager has no resolvable public module path or no
    renderable top-level field error, signalling that the original
    ``ValidationError`` should be raised instead.
    """
    module_config_key = resolve_module_config_path(manager)
    if module_config_key is None:
        return None

    field_errors = _collect_field_errors(manager.settings_cls, errors)
    if not field_errors:
        return None

    indent = 6 if manager.multi else 2
    field_lines = generate_settings_fields_yaml_lines(
        manager.settings_cls,
        indent=indent,
        field_errors=field_errors,
        lead_separator=True,
    )

    lines = [f"{module_config_key}:"]
    if manager.multi:
        lines.append("  configs:")
        lines.append(f"    {config_key}:")
    lines.extend(field_lines)

    return "Failed to load user settings.\n\n" + "\n".join(lines)


def _collect_field_errors(
    settings_cls: type[BaseModel],
    errors: list[ErrorDetails],
) -> dict[str, FieldError]:
    model_fields = settings_cls.model_fields
    result: dict[str, FieldError] = {}

    for error in errors:
        loc = error.get("loc") or ()
        if not loc:
            continue

        field_name = loc[0]
        if not isinstance(field_name, str) or field_name not in model_fields:
            continue
        if field_name in result:
            continue

        message = str(error.get("msg", "invalid value"))

        if len(loc) > 1:
            sub_path = ".".join(str(part) for part in loc[1:])
            result[field_name] = FieldError(message=f"{sub_path}: {message}")
        elif error.get("type") == "missing":
            # For a missing field the reported input is the whole config dict,
            # not a value for this field, so it is intentionally not echoed back.
            result[field_name] = FieldError(message="required field is not set")
        else:
            result[field_name] = FieldError(message=message, input=error["input"])

    return result
