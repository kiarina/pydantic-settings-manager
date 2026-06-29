import inspect
from dataclasses import dataclass
from types import NoneType, UnionType
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel

_MISSING_INPUT = object()


@dataclass(frozen=True)
class FieldError:
    message: str
    # _MISSING_INPUT means there is no rejected value to echo back.
    input: Any = _MISSING_INPUT


def generate_settings_fields_yaml_lines(
    settings_cls: type[BaseModel],
    *,
    indent: int,
    field_errors: dict[str, FieldError] | None = None,
    lead_separator: bool = False,
) -> list[str]:
    """Render commented YAML lines for ``settings_cls`` fields.

    When ``field_errors`` is given, only those fields are rendered, each with an
    extra comment line for the error and the rejected value as the field value.
    """
    comment_prefix = " " * indent
    separator = f"{comment_prefix}#--------------------------------------------------"
    lines: list[str] = []

    fields = [
        (name, info)
        for name, info in settings_cls.model_fields.items()
        if field_errors is None or name in field_errors
    ]
    for index, (field_name, field_info) in enumerate(fields):
        if index or lead_separator:
            lines.append(separator)

        field_title = field_info.title or field_name
        field_type = _format_type_annotation(field_info.annotation)
        lines.append(f"{comment_prefix}# {field_title}: {field_type}")

        if field_info.description:
            for description_line in _clean_doc_lines(field_info.description):
                if description_line:
                    lines.append(f"{comment_prefix}#   {description_line}")
                else:
                    lines.append(f"{comment_prefix}#")

        field_error = field_errors.get(field_name) if field_errors else None
        if field_error is not None:
            lines.append(f"{comment_prefix}# ERROR: {field_error.message}")
            if field_error.input is _MISSING_INPUT:
                lines.append(f"{comment_prefix}{field_name}:")
            else:
                lines.extend(
                    _render_yaml_key_value(
                        field_name,
                        _to_yaml_value(field_error.input),
                        indent=indent,
                    )
                )
            continue

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


def _clean_doc_lines(value: str) -> list[str]:
    return inspect.cleandoc(value).splitlines()


def _format_type_annotation(annotation: Any) -> str:
    if annotation is Any:
        return "Any"
    if annotation is None:
        return "Any"
    if annotation is NoneType:
        return "None"

    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        if args:
            return _format_type_annotation(args[0])

    if origin is Literal:
        args = get_args(annotation)
        return f"Literal[{', '.join(repr(arg) for arg in args)}]"

    if origin in {Union, UnionType}:
        args = get_args(annotation)
        return " | ".join(_format_type_annotation(arg) for arg in args)

    if origin is not None:
        args = get_args(annotation)
        origin_name = _format_type_name(origin)
        if args:
            return f"{origin_name}[{', '.join(_format_type_annotation(arg) for arg in args)}]"
        return origin_name

    return _format_type_name(annotation)


def _format_type_name(annotation: Any) -> str:
    if isinstance(annotation, str):
        return annotation

    name = getattr(annotation, "__name__", None)
    if isinstance(name, str):
        return name

    name = getattr(annotation, "_name", None)
    if isinstance(name, str):
        return name

    return str(annotation).removeprefix("typing.").removeprefix("collections.abc.")


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
