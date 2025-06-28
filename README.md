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

### Basic Usage

Let's start with a simple example you can try immediately:

```python
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SingleSettingsManager

# 1. Define your settings
class AppSettings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    max_connections: int = 100

# 2. Create a settings manager
settings_manager = SingleSettingsManager(AppSettings)

# 3. Use your settings
settings = settings_manager.settings
print(f"App: {settings.app_name}, Debug: {settings.debug}")
```

### Loading from Configuration Files

You can load settings from external sources:

```python
# Load from a dictionary (could be from JSON, YAML, etc.)
settings_manager.user_config = {
    "app_name": "ProductionApp",
    "debug": False,
    "max_connections": 500
}

settings = settings_manager.settings
print(f"App: {settings.app_name}")  # Output: App: ProductionApp
```

### Command Line Overrides

Override specific settings at runtime:

```python
# Simulate command line arguments
settings_manager.cli_args["debug"] = True
settings_manager.cli_args["max_connections"] = 50

# Clear cache to apply changes
settings_manager.clear()

settings = settings_manager.settings
print(f"Debug: {settings.debug}")  # Output: Debug: True
print(f"Connections: {settings.max_connections}")  # Output: Connections: 50
```

### Multiple Configurations (Mapped Settings)

For managing multiple environments or configurations:

```python
from pydantic_settings_manager import MappedSettingsManager

# Create a mapped settings manager
mapped_manager = MappedSettingsManager(AppSettings)

# Configure multiple environments
mapped_manager.user_config = {
    "map": {
        "development": {
            "app_name": "MyApp-Dev",
            "debug": True,
            "max_connections": 10
        },
        "production": {
            "app_name": "MyApp-Prod", 
            "debug": False,
            "max_connections": 1000
        }
    }
}

# Switch between configurations
mapped_manager.set_cli_args("development")
dev_settings = mapped_manager.settings
print(f"Dev: {dev_settings.app_name}, Debug: {dev_settings.debug}")

mapped_manager.set_cli_args("production")
prod_settings = mapped_manager.settings
print(f"Prod: {prod_settings.app_name}, Debug: {prod_settings.debug}")
```

## Advanced Usage

### Project Structure for Large Applications

For complex applications with multiple modules, you can organize your settings like this:

```
your_project/
├── hoge/
│   ├── __init__.py
│   ├── settings.py
│   ├── client.py
│   └── registry.py
├── fuga/
│   ├── __init__.py
│   ├── settings.py
│   ├── client.py
│   └── registry.py
├── bootstrap.py
├── __main__.py
└── config.yaml
```

### Module-based Settings Management

```python
# fuga/__init__.py
from .settings import settings_manager

__all__ = ["settings_manager"]
```

```python
# fuga/settings.py
from pydantic_settings import BaseSettings
from pydantic_settings_manager import MappedSettingsManager

class FugaSettings(BaseSettings):
    name: str = "default"
    api_key: str = "***"

settings_manager = MappedSettingsManager(FugaSettings)
```

```python
# fuga/client.py
from .settings import FugaSettings

class FugaClient:
    def __init__(self, settings: FugaSettings):
        self.settings = settings
```

```python
# fuga/registry.py
from .settings import settings_manager

def create_fuga_client(config_key: str = ""):
    settings = settings_manager.get_settings_by_key(config_key)
    return FugaClient(settings)
```

### Bootstrap

The bootstrap process loads configuration from external sources (like YAML files) and applies them to your settings managers. This allows you to centralize configuration management and easily switch between different environments.

```yaml
# config.yaml
hoge:
  name: "star"
  value: 7
fuga:
  key: first
  map:
    first:
      name: "first"
      api_key: "***"
    second:
      name: "second"
      api_key: "***"
```

```python
# bootstrap.py
import importlib
import yaml

from pydantic_settings_manager import BaseSettingsManager

def bootstrap():
    config = yaml.safe_load(open("/path/to/config.yaml"))

    for module_name, user_config in config.items():
        try:
            module = importlib.import_module(module_name)
            settings_manager = getattr(module, 'settings_manager', None)

            if isinstance(settings_manager, BaseSettingsManager):
                settings_manager.user_config = user_config
                settings_manager.clear()
```

### CLI Integration

You can integrate command-line arguments to override specific settings at runtime. This is useful for debugging, testing different configurations, or providing runtime flexibility without modifying configuration files.

```python
# __main__.py
import click

from .bootstrap import bootstrap
from .hoge import settings_manager as hoge_settings_manager
from .fuga import settings_manager as fuga_settings_manager

@click.command
@click.option("--name", type=str, default="", help="Name of the Hoge")
@click.option("--key", type=str, default="", help="Key for Fuga settings")
def main(name: str, key: str):
    bootstrap()

    if name:
        hoge_settings_manager.cli_args["name"] = name
        hoge_settings_manager.clear()

    if key:
        fuga_settings_manager.cli_args["key"] = key
        fuga_settings_manager.clear()

    # ...
```

## Related Tools

### pydantic-config-builder

For complex projects with multiple configuration files, you might want to use [`pydantic-config-builder`](https://github.com/kiarina/pydantic-config-builder) to merge and build your YAML configuration files:

```bash
pip install pydantic-config-builder
```

This tool allows you to:
- Merge multiple YAML files into a single configuration
- Use base configurations with overlay files
- Build different configurations for different environments
- Support glob patterns and recursive merging

Example workflow:
```yaml
# pydantic_config_builder.yml
development:
  input:
    - base/*.yaml
    - dev-overrides.yaml
  output:
    - config/dev.yaml

production:
  input:
    - base/*.yaml
    - prod-overrides.yaml
  output:
    - config/prod.yaml
```

Then use the generated configurations with your settings manager:
```python
import yaml
from your_app import settings_manager

# Load the built configuration
with open("config/dev.yaml") as f:
    config = yaml.safe_load(f)

settings_manager.user_config = config
```

## Development

This project uses modern Python development tools with flexible dependency groups:

- **ruff**: Fast linter and formatter (replaces black, isort, and flake8)
- **mypy**: Static type checking
- **pytest**: Testing framework with coverage reporting
- **uv**: Fast Python package manager with PEP 735 dependency groups support

### Setup

```bash
# Install all development dependencies
uv sync --group dev

# Or install specific dependency groups
uv sync --group test    # Testing tools only
uv sync --group lint    # Linting tools only

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

### Development Workflow

```bash
# Quick setup for testing
uv sync --group test
make test

# Quick setup for linting
uv sync --group lint
make lint

# Full development environment
uv sync --group dev
make build
```

## Documentation

For more detailed documentation, please see the [GitHub repository](https://github.com/kiarina/pydantic-settings-manager).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
