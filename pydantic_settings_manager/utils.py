"""
Utility functions for dictionary operations.
"""
from collections import defaultdict
from typing import Any, Dict

from .types import NestedDict


def diff_dict(base: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
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


def update_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
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


def nested_dict() -> NestedDict:
    """
    ネストした dict を作成する
    """
    return defaultdict(nested_dict)
