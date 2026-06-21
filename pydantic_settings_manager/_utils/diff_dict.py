from typing import Any


def diff_dict(base: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Return values from target that differ from base."""
    result = {}

    for key in target:
        if key not in base:
            result[key] = target[key]
        elif isinstance(target[key], dict) and isinstance(base[key], dict):
            nested = diff_dict(base[key], target[key])
            if nested:
                result[key] = nested
        elif target[key] != base[key]:
            result[key] = target[key]

    return result
