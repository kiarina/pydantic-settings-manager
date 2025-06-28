# pydantic-settings-manager

A library for managing Pydantic settings objects.

## Features

- Two types of settings managers:
  - `SingleSettingsManager`: For managing a single settings object
  - `MappedSettingsManager`: For managing multiple settings objects mapped to keys
- Support for loading settings from multiple sources
- Command line argument overrides
- Settings validation through Pydantic
- Type hints and documentation

## Installation

```bash
pip install pydantic-settings-manager
```

## Quick Start

### Single Settings Manager

```python
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SingleSettingsManager

class MySettings(BaseSettings):
    name: str = "default"
    value: int = 0

# Create a settings manager
manager = SingleSettingsManager(MySettings)

# Update settings from a configuration file
manager.user_config = {"name": "from_file", "value": 42}

# Update settings from command line arguments
manager.cli_args = {"value": 100}

# Get the current settings (combines both sources)
settings = manager.settings
assert settings.name == "from_file"  # from user_config
assert settings.value == 100  # from cli_args (overrides user_config)
```

### Mapped Settings Manager

```python
from pydantic_settings import BaseSettings
from pydantic_settings_manager import MappedSettingsManager

class MySettings(BaseSettings):
    name: str = "default"
    value: int = 0

# Create a settings manager
manager = MappedSettingsManager(MySettings)

# Set up multiple configurations
manager.user_config = {
    "map": {
        "dev": {"name": "development", "value": 42},
        "prod": {"name": "production", "value": 100}
    }
}

# Select which configuration to use
manager.set_cli_args("dev")

# Get the current settings
settings = manager.settings
assert settings.name == "development"
assert settings.value == 42

# Switch to a different configuration
manager.set_cli_args("prod")
settings = manager.settings
assert settings.name == "production"
assert settings.value == 100
```

## Development

This project uses modern Python development tools:

- **ruff**: Fast linter and formatter (replaces black, isort, and flake8)
- **mypy**: Static type checking
- **pytest**: Testing framework with coverage reporting

### Setup

```bash
# Install dependencies
uv sync --dev

# Format code
uv run ruff check --fix .

# Run linting
uv run ruff check .
uv run mypy .

# Run tests
uv run pytest --cov=pydantic_settings_manager tests/

# Build and test everything
make build
```

## Documentation

For more detailed documentation, please see the [GitHub repository](https://github.com/kiarina/pydantic-settings-manager).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
