"""
Tests for SettingsManager (unified settings manager)
"""

import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import DEFAULT_KEY, SettingsManager


class ExampleSettings(BaseSettings):
    """Example settings class for testing"""

    name: str = "default"
    value: int = 0
    debug: bool = False


# Single Mode Tests


def test_init_single_mode() -> None:
    """Test initialization in single mode"""
    manager = SettingsManager(ExampleSettings)
    assert not manager.multi
    assert isinstance(manager.settings, ExampleSettings)
    assert manager.settings.name == "default"
    assert manager.settings.value == 0
    assert manager.settings.debug is False


def test_user_config_single_mode() -> None:
    """Test user configuration in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "from_file", "value": 42, "debug": True}

    assert manager.settings.name == "from_file"
    assert manager.settings.value == 42
    assert manager.settings.debug is True


def test_cli_args_single_mode() -> None:
    """Test CLI arguments in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.cli_args = {"value": 100, "debug": True}

    assert manager.settings.name == "default"
    assert manager.settings.value == 100
    assert manager.settings.debug is True


def test_precedence_single_mode() -> None:
    """Test settings precedence in single mode (CLI args override user config)"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "from_file", "value": 42, "debug": False}
    manager.cli_args = {"value": 100, "debug": True}

    assert manager.settings.name == "from_file"  # from user_config
    assert manager.settings.value == 100  # from cli_args (overrides)
    assert manager.settings.debug is True  # from cli_args (overrides)


def test_clear_single_mode() -> None:
    """Test clear cache in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "initial", "value": 42}

    # Get settings to cache them
    initial_settings = manager.settings
    assert initial_settings.name == "initial"

    # Clear and modify config
    manager.clear()
    manager.user_config = {"name": "updated", "value": 100}

    # Check that new settings are used
    updated_settings = manager.settings
    assert updated_settings.name == "updated"
    assert updated_settings.value == 100


def test_all_settings_single_mode() -> None:
    """Test all_settings property in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "test", "value": 42}

    all_settings = manager.all_settings
    assert len(all_settings) == 1
    assert DEFAULT_KEY in all_settings
    assert all_settings[DEFAULT_KEY].name == "test"
    assert all_settings[DEFAULT_KEY].value == 42


def test_active_key_error_single_mode() -> None:
    """Test that active_key raises error in single mode"""
    manager = SettingsManager(ExampleSettings)

    with pytest.raises(ValueError, match="Getting active_key is only available in multi mode"):
        _ = manager.active_key

    with pytest.raises(ValueError, match="Setting active_key is only available in multi mode"):
        manager.active_key = "test"


def test_get_settings_single_mode() -> None:
    """Test get_settings in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "test", "value": 42}

    # Should return current settings when no key is provided
    settings = manager.get_settings()
    assert settings.name == "test"
    assert settings.value == 42

    # Should raise error when key is provided in single mode
    with pytest.raises(ValueError, match="Getting settings by key is only available in multi mode"):
        manager.get_settings("some_key")


# Multi Mode Validation Tests (v3.0.0+)


def test_multi_mode_requires_configs() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Multi configuration requires `configs`"):
        manager.user_config = {
            "default": "development",
        }


def test_old_key_map_format_rejected() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Invalid multi configuration keys"):
        manager.user_config = {
            "key": "production",
            "map": {
                "production": {"debug": False},
            },
        }


def test_unknown_toplevel_key_rejected() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Invalid multi configuration keys"):
        manager.user_config = {
            "default": "production",
            "configs": {
                "production": {"debug": False},
            },
            "foo": "bar",
        }


def test_invalid_default_rejected() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Default configuration 'missing'"):
        manager.user_config = {
            "default": "missing",
            "configs": {
                "production": {"debug": False},
            },
        }


def test_alias_target_must_exist() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Alias 'dev' resolved to 'development'"):
        manager.user_config = {
            "configs": {
                "production": {"debug": False},
            },
            "aliases": {
                "dev": "development",
            },
        }


def test_circular_alias_setter() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    with pytest.raises(ValueError, match="Circular alias reference detected: a -> b -> a"):
        manager.user_config = {
            "configs": {
                "production": {"debug": False},
            },
            "aliases": {
                "a": "b",
                "b": "a",
            },
        }


def test_no_default_and_no_active_key_returns_default_settings() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "configs": {
            "development": {"debug": True},
            "production": {"debug": False},
        },
    }
    # Should automatically fall back to generated DEFAULT_KEY
    settings = manager.settings
    assert settings.name == "default"
    assert settings.debug is False


def test_no_default_falls_back_to_default_key() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "configs": {
            "default": {"debug": True},
            "production": {"debug": False},
        },
    }
    # Should fallback to DEFAULT_KEY ("default")
    assert manager.settings.debug is True


# Multi Mode Tests


def test_init_multi_mode() -> None:
    """Test initialization in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    assert manager.multi
    assert manager.active_key is None


def test_user_config_multi_mode() -> None:
    """Test user configuration in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "dev",
        "configs": {
            "dev": {"name": "development", "value": 42, "debug": True},
            "prod": {"name": "production", "value": 100, "debug": False},
        },
    }

    # Should use default configuration
    settings = manager.settings
    assert settings.name == "development"
    assert settings.value == 42
    assert settings.debug is True


def test_active_key_property() -> None:
    """Test active_key property in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    assert manager.active_key is None

    manager.active_key = "dev"
    assert manager.active_key == "dev"

    manager.active_key = "prod"
    assert manager.active_key == "prod"


def test_active_key_overrides_default() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "production",
        "configs": {
            "development": {"debug": True},
            "production": {"debug": False},
        },
    }

    assert manager.settings.debug is False
    manager.active_key = "development"
    assert manager.settings.debug is True


def test_active_key_none_falls_back_to_default() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "production",
        "configs": {
            "development": {"debug": True},
            "production": {"debug": False},
        },
    }

    manager.active_key = "development"
    manager.active_key = None
    assert manager.settings.debug is False


def test_cli_args_multi_mode() -> None:
    """Test CLI arguments in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "dev",
        "configs": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        },
    }
    manager.active_key = "dev"
    manager.cli_args = {"value": 999, "debug": True}

    settings = manager.settings
    assert settings.name == "development"  # from user_config
    assert settings.value == 999  # from cli_args (overrides)
    assert settings.debug is True  # from cli_args


def test_set_cli_args_method() -> None:
    """Test set_cli_args method"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {"configs": {"dev": {"name": "development", "value": 42}}}

    manager.set_cli_args("value", 999)
    manager.active_key = "dev"

    settings = manager.settings
    assert settings.value == 999


def test_set_cli_args_nested() -> None:
    """Test set_cli_args with nested keys"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {"configs": {"dev": {"name": "development", "value": 42}}}

    # Test nested key setting
    manager.set_cli_args("nested.key", "test_value")
    cli_args = manager.cli_args
    assert cli_args["nested"]["key"] == "test_value"


def test_all_settings_multi_mode() -> None:
    """Test all_settings property in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "configs": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        },
        "aliases": {"development": "dev"},
    }

    all_settings = manager.all_settings
    assert set(all_settings.keys()) == {"default", "dev", "prod"}
    assert all_settings["dev"].name == "development"
    assert all_settings["dev"].value == 42
    assert all_settings["prod"].name == "production"
    assert all_settings["prod"].value == 100


def test_invalid_active_key() -> None:
    """Test invalid active key"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {"configs": {"dev": {"name": "development", "value": 42}}}
    manager.active_key = "nonexistent"

    with pytest.raises(ValueError, match="Key 'nonexistent' does not exist"):
        _ = manager.settings


def test_clear_multi_mode() -> None:
    """Test clear cache in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {"configs": {"dev": {"name": "initial", "value": 42}}}
    manager.active_key = "dev"

    # Get settings to cache them
    initial_settings = manager.settings
    assert initial_settings.name == "initial"

    # Clear and modify config
    manager.clear()
    manager.user_config = {"configs": {"dev": {"name": "updated", "value": 100}}}
    manager.active_key = "dev"

    # Check that new settings are used
    updated_settings = manager.settings
    assert updated_settings.name == "updated"
    assert updated_settings.value == 100


# Edge Cases Tests


def test_empty_config_single_mode() -> None:
    """Test empty configuration in single mode"""
    manager = SettingsManager(ExampleSettings)
    settings = manager.settings
    assert settings.name == "default"
    assert settings.value == 0


def test_user_config_getter_single_mode() -> None:
    """Test user_config getter in single mode"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "test", "value": 42}

    config = manager.user_config
    assert config == {"name": "test", "value": 42}

    # Modifying returned dict should not affect internal state
    config["name"] = "modified"
    assert manager.user_config["name"] == "test"


def test_user_config_getter_multi_mode() -> None:
    """Test user_config getter in multi mode"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "prod",
        "configs": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        },
        "aliases": {"production": "prod"},
    }

    config = manager.user_config
    expected = {
        "default": "prod",
        "configs": {
            "dev": {"name": "development", "value": 42},
            "prod": {"name": "production", "value": 100},
        },
        "aliases": {"production": "prod"},
    }
    assert config == expected

    # The implementation returns a deep copy,
    # so modifying nested dictionaries should not affect the internal state.
    config["configs"]["dev"]["name"] = "modified"
    # The internal state should not be affected due to deep copy
    assert manager.user_config["configs"]["dev"]["name"] == "development"


def test_cli_args_getter() -> None:
    """Test cli_args getter returns copy"""
    manager = SettingsManager(ExampleSettings)
    manager.cli_args = {"value": 42, "debug": True}

    cli_args = manager.cli_args
    assert cli_args == {"value": 42, "debug": True}

    # Modifying returned dict should not affect internal state
    cli_args["value"] = 999
    assert manager.cli_args["value"] == 42


def test_cache_invalidation_on_config_change() -> None:
    """Test that cache is invalidated when configuration changes"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "initial", "value": 42}

    # Get settings to build cache
    settings1 = manager.settings
    assert settings1.name == "initial"

    # Change user_config
    manager.user_config = {"name": "updated", "value": 100}

    # Should get new settings without explicit clear
    settings2 = manager.settings
    assert settings2.name == "updated"
    assert settings2.value == 100


def test_cache_invalidation_on_cli_args_change() -> None:
    """Test that cache is invalidated when CLI args change"""
    manager = SettingsManager(ExampleSettings)
    manager.user_config = {"name": "test", "value": 42}

    # Get settings to build cache
    settings1 = manager.settings
    assert settings1.value == 42

    # Change cli_args
    manager.cli_args = {"value": 999}

    # Should get new settings without explicit clear
    settings2 = manager.settings
    assert settings2.value == 999


def test_thread_safety_properties() -> None:
    """Test that properties return copies for thread safety"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {"configs": {"dev": {"name": "development", "value": 42}}}
    manager.cli_args = {"debug": True}

    # Get properties multiple times
    config1 = manager.user_config
    config2 = manager.user_config
    cli_args1 = manager.cli_args
    cli_args2 = manager.cli_args
    all_settings1 = manager.all_settings
    all_settings2 = manager.all_settings

    # Should be equal but not the same object
    assert config1 == config2
    assert config1 is not config2
    assert cli_args1 == cli_args2
    assert cli_args1 is not cli_args2
    assert all_settings1.keys() == all_settings2.keys()
    assert all_settings1 is not all_settings2


# Alias Tests


def test_alias_basic() -> None:
    """Test basic alias functionality"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "aliases": {
            "dev": "development",
            "stg": "staging",
        },
        "configs": {
            "development": {"name": "dev_name", "value": 1},
            "staging": {"name": "stg_name", "value": 2},
        },
    }

    # Access via alias
    dev_settings = manager.get_settings("dev")
    assert dev_settings.name == "dev_name"
    assert dev_settings.value == 1

    # Access via original key
    dev_settings_direct = manager.get_settings("development")
    assert dev_settings_direct.name == "dev_name"
    assert dev_settings_direct.value == 1

    # Access via another alias
    stg_settings = manager.get_settings("stg")
    assert stg_settings.name == "stg_name"
    assert stg_settings.value == 2


def test_alias_multi_level() -> None:
    """Test multi-level alias (alias of alias)"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "aliases": {
            "a": "b",
            "b": "c",
            "c": "target",
        },
        "configs": {
            "target": {"name": "final", "value": 42},
        },
    }

    # All aliases should resolve to the same target
    assert manager.get_settings("a").name == "final"
    assert manager.get_settings("b").name == "final"
    assert manager.get_settings("c").name == "final"
    assert manager.get_settings("target").name == "final"


def test_alias_with_active_key() -> None:
    """Test alias with active_key property"""
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "aliases": {"dev": "development"},
        "configs": {
            "development": {"name": "dev_name", "value": 1},
            "production": {"name": "prod_name", "value": 2},
        },
    }

    # Set active_key to alias
    manager.active_key = "dev"

    # .settings should resolve the alias
    settings = manager.settings
    assert settings.name == "dev_name"
    assert settings.value == 1

    # get_settings() should also work
    settings2 = manager.get_settings()
    assert settings2.name == "dev_name"
    assert settings2.value == 1

    # get_settings("dev") should also work
    settings3 = manager.get_settings("dev")
    assert settings3.name == "dev_name"
    assert settings3.value == 1


def test_alias_active_key_nonexistent_target() -> None:
    """Test active_key with alias pointing to non-existent target"""
    manager = SettingsManager(ExampleSettings, multi=True)
    # The setter validates this now, so we need to bypass or test setter
    with pytest.raises(ValueError, match="Alias 'dev' resolved to 'nonexistent'"):
        manager.user_config = {
            "aliases": {"dev": "nonexistent"},
            "configs": {"staging": {"name": "stg", "value": 1}},
        }


def test_default_can_be_alias() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "default": "prod",
        "configs": {
            "production": {"debug": False},
        },
        "aliases": {
            "prod": "production",
        },
    }
    assert manager.settings.debug is False


def test_get_settings_explicit_key_works_without_default() -> None:
    manager = SettingsManager(ExampleSettings, multi=True)
    manager.user_config = {
        "configs": {
            "development": {"debug": True},
            "production": {"debug": False},
        },
    }
    assert manager.get_settings("development").debug is True
