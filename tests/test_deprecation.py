"""
Tests for deprecation warnings
"""
import warnings

from pydantic_settings import BaseSettings

from pydantic_settings_manager import (
    BaseSettingsManager,
    MappedSettingsManager,
    SingleSettingsManager,
)


class ExampleSettings(BaseSettings):
    """Example settings class for testing"""
    name: str = "default"
    value: int = 0


def test_single_settings_manager_deprecation_warning() -> None:
    """Test that SingleSettingsManager shows deprecation warning"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        SingleSettingsManager(ExampleSettings)

        # Check that a warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "SingleSettingsManager is deprecated" in str(w[0].message)
        assert "SettingsManager instead" in str(w[0].message)
        assert "v2.0.0" in str(w[0].message)


def test_mapped_settings_manager_deprecation_warning() -> None:
    """Test that MappedSettingsManager shows deprecation warning"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        MappedSettingsManager(ExampleSettings)

        # Check that a warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "MappedSettingsManager is deprecated" in str(w[0].message)
        assert "SettingsManager(YourSettings, multi=True)" in str(w[0].message)
        assert "v2.0.0" in str(w[0].message)


def test_base_settings_manager_no_deprecation_warning() -> None:
    """Test that BaseSettingsManager does NOT show deprecation warning"""

    class TestManager(BaseSettingsManager[ExampleSettings]):
        def __init__(self, settings_cls: type[ExampleSettings]):
            super().__init__(settings_cls)

        @property
        def settings(self) -> ExampleSettings:
            return ExampleSettings()

        def clear(self) -> None:
            pass

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        TestManager(ExampleSettings)

        # Check that NO warning was issued
        assert len(w) == 0


def test_deprecated_classes_still_work() -> None:
    """Test that deprecated classes still function correctly"""

    # Test SingleSettingsManager functionality
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Ignore deprecation warnings for this test

        single_manager = SingleSettingsManager(ExampleSettings)
        single_manager.user_config = {"name": "test", "value": 42}

        settings = single_manager.settings
        assert settings.name == "test"
        assert settings.value == 42

    # Test MappedSettingsManager functionality
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Ignore deprecation warnings for this test

        mapped_manager = MappedSettingsManager(ExampleSettings)
        mapped_manager.user_config = {
            "map": {
                "dev": {"name": "development", "value": 42},
                "prod": {"name": "production", "value": 100}
            }
        }
        mapped_manager.set_cli_args("dev")

        settings = mapped_manager.settings
        assert settings.name == "development"
        assert settings.value == 42


def test_warning_includes_migration_guide_url() -> None:
    """Test that warnings include migration guide URL"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        SingleSettingsManager(ExampleSettings)

        assert len(w) == 1
        assert "migration-guide" in str(w[0].message)


def test_multiple_instantiations_show_warnings() -> None:
    """Test that each instantiation shows a warning"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Create multiple instances
        SingleSettingsManager(ExampleSettings)
        SingleSettingsManager(ExampleSettings)
        MappedSettingsManager(ExampleSettings)

        # Should have 3 warnings
        assert len(w) == 3
        assert all(issubclass(warning.category, DeprecationWarning) for warning in w)


def test_warning_stacklevel() -> None:
    """Test that warnings point to the correct location in user code"""
    def create_manager() -> SingleSettingsManager[ExampleSettings]:
        return SingleSettingsManager(ExampleSettings)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        create_manager()

        assert len(w) == 1
        # The warning should point to the create_manager function call,
        # not to the internal SingleSettingsManager.__init__
        assert w[0].filename == __file__
        # The line number should be the line where create_manager() is called
        # (This is a bit fragile but helps ensure stacklevel is correct)
