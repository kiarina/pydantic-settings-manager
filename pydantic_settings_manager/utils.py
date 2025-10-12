from typing import Any


def diff_dict(base: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """
    Get the difference between two dictionaries.
    Only includes keys where the values are different.
    """
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


def update_dict(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """
    Update a dictionary with another dictionary.
    Performs a deep update.
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = update_dict(result[key], value)
        else:
            result[key] = value

    return result
