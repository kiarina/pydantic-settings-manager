"""
Tests for utility functions
"""

from pydantic_settings_manager.utils import diff_dict, update_dict


def test_diff_dict() -> None:
    """Test diff_dict function"""
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    target = {"a": 1, "b": {"c": 2, "d": 5}, "e": 6}

    diff = diff_dict(base, target)
    assert diff == {"b": {"d": 5}, "e": 6}


def test_diff_dict_new_key() -> None:
    """Test diff_dict function with new key"""
    base = {"a": 1}
    target = {"a": 1, "b": 2}

    diff = diff_dict(base, target)
    assert diff == {"b": 2}


def test_diff_dict_nested() -> None:
    """Test diff_dict function with nested dictionaries"""
    base = {"a": {"b": {"c": 1}}}
    target = {"a": {"b": {"c": 2}}}

    diff = diff_dict(base, target)
    assert diff == {"a": {"b": {"c": 2}}}


def test_update_dict() -> None:
    """Test update_dict function"""
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    update = {"b": {"d": 5}, "e": 6}

    result = update_dict(base, update)
    assert result == {"a": 1, "b": {"c": 2, "d": 5}, "e": 6}


def test_update_dict_new_key() -> None:
    """Test update_dict function with new key"""
    base = {"a": 1}
    update = {"b": 2}

    result = update_dict(base, update)
    assert result == {"a": 1, "b": 2}


def test_update_dict_nested() -> None:
    """Test update_dict function with nested dictionaries"""
    base = {"a": {"b": {"c": 1}}}
    update = {"a": {"b": {"d": 2}}}

    result = update_dict(base, update)
    assert result == {"a": {"b": {"c": 1, "d": 2}}}
