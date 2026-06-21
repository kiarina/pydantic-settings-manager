from pydantic_settings_manager._utils.diff_dict import diff_dict


def test_diff_dict() -> None:
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    target = {"a": 1, "b": {"c": 2, "d": 5}, "e": 6}

    diff = diff_dict(base, target)
    assert diff == {"b": {"d": 5}, "e": 6}


def test_diff_dict_new_key() -> None:
    base = {"a": 1}
    target = {"a": 1, "b": 2}

    diff = diff_dict(base, target)
    assert diff == {"b": 2}


def test_diff_dict_nested() -> None:
    base = {"a": {"b": {"c": 1}}}
    target = {"a": {"b": {"c": 2}}}

    diff = diff_dict(base, target)
    assert diff == {"a": {"b": {"c": 2}}}
