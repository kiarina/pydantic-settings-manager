from typing import Any


def update_dict(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-updated copy of base."""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = update_dict(result[key], value)
        else:
            result[key] = value

    return result
