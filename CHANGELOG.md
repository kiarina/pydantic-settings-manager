# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [2.2.0] - 2025-09-08

### Added
- **Direct Configuration Format**: Multi-mode now supports direct configuration format `{"dev": {...}, "prod": {...}}` in addition to the existing structured format `{"key": "dev", "map": {...}}`
- Enhanced flexibility for multi-configuration setup with more intuitive API

### Changed
- `SettingsManager.user_config` setter in multi-mode now automatically detects configuration format
- Improved configuration format detection logic for better reliability
- Updated documentation and examples to showcase both configuration formats

### Fixed
- Simplified condition logic in configuration format detection
- Enhanced test coverage for both direct and structured configuration formats

## [2.1.0] - 2025-9-04

### Changed
- **API Enhancement**: `SettingsManager.get_settings_by_key()` now accepts `str | None` instead of just `str`
- When `None` is passed to `get_settings_by_key()`, it returns the current active settings (same behavior as empty string)
- Improved API consistency and flexibility for multi-mode configuration access

### Added
- Enhanced type annotations for better IDE support and type safety
- Additional test coverage for `None` parameter handling

## [2.0.0] - 2025-09-04

### Removed
- **BREAKING**: Removed deprecated classes as announced in v1.0.0:
  - `BaseSettingsManager`: Use `SettingsManager` instead
  - `SingleSettingsManager`: Use `SettingsManager(MySettings)` instead
  - `MappedSettingsManager`: Use `SettingsManager(MySettings, multi=True)` instead
- Removed internal implementation files: `base.py`, `single.py`, `mapped.py`, `deprecated.py`, `types.py`
- Removed `nested_dict` utility function (was only used by deprecated `SingleSettingsManager`)

### Changed
- Simplified package structure with only the unified `SettingsManager` class
- Reduced package size by removing deprecated code paths
- Cleaner API surface with only the recommended `SettingsManager` class

### Migration
- All functionality is available through the unified `SettingsManager` class
- No breaking changes for users already using `SettingsManager`
- See migration guide in README for upgrading from deprecated classes

## [1.0.3] - 2025-08-15

### Added
- Added support for Python 3.13
- Enhanced CI/CD pipeline to test against Python 3.13

### Changed
- Updated project classifiers to include Python 3.13 support
- Improved compatibility testing across all supported Python versions (3.9-3.13)

## [1.0.2] - 2025-08-15

### Fixed
- Fixed `get_settings_by_key` method to properly validate single mode usage
- Added proper error handling when `get_settings_by_key` is called in single mode
- Improved docstring for `get_settings_by_key` to clarify multi-mode requirement and empty key behavior
- Enhanced API consistency by restricting multi-mode specific methods to multi-mode only

## [1.0.1] - 2025-08-15

### Fixed
- Fixed BaseSettingsManager export to use original implementation instead of deprecated wrapper
- BaseSettingsManager no longer shows deprecation warning (only child classes do)
- Maintained backward compatibility for existing BaseSettingsManager usage

## [1.0.0] - 2025-08-15

### Added
- **NEW**: Unified `SettingsManager` class that replaces all previous managers
- Thread-safe operations with proper locking mechanisms
- Property-based API for more intuitive configuration management
- Support for both single mode (`SettingsManager(MySettings)`) and multi mode (`SettingsManager(MySettings, multi=True)`)
- Comprehensive migration guide in README
- New `active_key` property for cleaner multi-configuration switching
- Enhanced error messages with clear usage instructions
- Thread safety tests and stress testing examples

### Changed
- **BREAKING**: `BaseSettingsManager`, `SingleSettingsManager`, and `MappedSettingsManager` are now deprecated
- **BREAKING**: CLI args now use dict assignment (`manager.cli_args = {...}`) instead of dict access (`manager.cli_args[key] = value`)
- **BREAKING**: Multi-mode configuration no longer requires `"map"` wrapper
- Improved internal implementation with consistent map-based approach
- Enhanced type safety with better generic type handling
- Simplified API with property-based operations

### Deprecated
- `BaseSettingsManager`: Use `SettingsManager` instead (will be removed in v2.0.0)
- `SingleSettingsManager`: Use `SettingsManager(MySettings)` instead (will be removed in v2.0.0)
- `MappedSettingsManager`: Use `SettingsManager(MySettings, multi=True)` instead (will be removed in v2.0.0)

### Fixed
- Thread safety issues in concurrent environments
- Cache invalidation edge cases
- Memory leaks in long-running applications

## [0.2.2] - 2025-06-28

### Changed
- Version bump: 0.2.1 → 0.2.2
- Internal version sync in __init__.py
- docs: add section on pydantic-config-builder in README


## [0.2.1] - 2025-06-28

### Changed
- Version bump: 0.2.0 → 0.2.1
- Internal version sync in __init__.py

## [0.2.0] - 2025-06-28

### Changed
- **BREAKING**: Migrated from Poetry to uv for dependency management
- Modernized development toolchain with unified linting using ruff
- Updated to use PEP 621 compliant project metadata format
- Introduced PEP 735 dependency groups for flexible development environments
- Enhanced CI/CD pipeline to use uv instead of Poetry
- Improved type checking configuration with stricter MyPy settings
- Updated all development dependencies to latest versions

### Added
- Comprehensive development documentation in README
- Support for modular dependency groups (test, lint, dev)
- Enhanced linting rules including pyupgrade and flake8-comprehensions
- Migration guide for developers updating their local environment

### Removed
- Poetry configuration files (poetry.lock, pyproject.toml Poetry sections)
- Separate black, isort, and flake8 configurations (replaced by ruff)

## [0.1.2] - 2024-03-12

### Added
- Added py.typed file for better type checking support
- Improved package configuration and build process

## [0.1.1] - 2024-03-12

### Added
- Added detailed documentation in README.md
- Added example code for both SingleSettingsManager and MappedSettingsManager

### Fixed
- Improved type hints and documentation

## [0.1.0] - 2024-03-11

### Added
- Initial release
- Implemented SingleSettingsManager for managing single settings object
- Implemented MappedSettingsManager for managing multiple settings objects
- Support for loading settings from multiple sources
- Command line argument overrides
- Settings validation through Pydantic
