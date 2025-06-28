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

### Project Structure

Here's an example project structure for using pydantic-settings-manager:

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

### Single Settings Manager

`SingleSettingsManager` is ideal when you have a single configuration that needs to be loaded from multiple sources (config files, environment variables, CLI arguments). It automatically merges these sources with CLI arguments taking the highest precedence.

```python
# hoge/__init__.py
from .settings import settings_manager

__all__ = ["settings_manager"]
```

```python
# hoge/settings.py
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SingleSettingsManager

class HogeSettings(BaseSettings):
    name: str = "default"
    value: int = 0

settings_manager = SingleSettingsManager(HogeSettings)
```

```python
# hoge/client.py
from .settings import HogeSettings

class HogeClient:
    def __init__(self, settings: HogeSettings):
        self.settings = settings
```

```python
# hoge/registry.py
from .settings import settings_manager

def create_hoge_client():
    return HogeClient(settings_manager.settings)
```

### Mapped Settings Manager

`MappedSettingsManager` is perfect when you need to manage multiple configurations (e.g., different environments like dev/staging/prod, or multiple API clients). You can switch between configurations at runtime using keys.

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
