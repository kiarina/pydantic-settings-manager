from pydantic_settings_manager._utils.update_dict import update_dict


def test_update_dict() -> None:
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    update = {"b": {"d": 5}, "e": 6}

    result = update_dict(base, update)
    assert result == {"a": 1, "b": {"c": 2, "d": 5}, "e": 6}


def test_update_dict_new_key() -> None:
    base = {"a": 1}
    update = {"b": 2}

    result = update_dict(base, update)
    assert result == {"a": 1, "b": 2}


def test_update_dict_nested() -> None:
    base = {"a": {"b": {"c": 1}}}
    update = {"a": {"b": {"d": 2}}}

    result = update_dict(base, update)
    assert result == {"a": {"b": {"c": 1, "d": 2}}}
