# pydantic-settings-manager

A modern, thread-safe library for managing Pydantic settings with support for multiple configurations and runtime overrides.

## Features

- **Bootstrap Pattern**: Centralized configuration loading for multi-module applications
- **Unified API**: Single `SettingsManager` class handles both simple and complex configurations
- **Thread-safe**: Built-in thread safety for concurrent applications
- **Type-safe**: Full type hints and Pydantic validation
- **Flexible**: Support for single settings or multiple named configurations
- **Runtime overrides**: Command-line arguments and dynamic configuration changes
- **Easy migration**: Simple upgrade path from configuration files and environment variables

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Single Module (Simple Projects)](#single-module-simple-projects)
  - [Runtime Overrides](#runtime-overrides)
- [**Bootstrap Pattern (Recommended for Production)**](#bootstrap-pattern-recommended-for-production) ⭐
  - [Why Bootstrap Pattern?](#why-bootstrap-pattern)
  - [Project Structure](#project-structure)
  - [Quick Example](#quick-example)
  - [Configuration File Structure](#configuration-file-structure)
  - [Custom Manager Names](#custom-manager-names)
  - [Frequently Asked Questions](#frequently-asked-questions)
- [Multiple Configurations](#multiple-configurations)
- [Advanced Usage](#advanced-usage)
  - [Thread Safety](#thread-safety)
  - [Dynamic Configuration Updates](#dynamic-configuration-updates)
- [CLI Integration](#cli-integration)
- [Related Tools](#related-tools)
- [Development](#development)
- [API Reference](#api-reference)
- [License](#license)

## Installation

```bash
pip install pydantic-settings-manager
```

## Quick Start

### Single Module (Simple Projects)

```python
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

# 1. Define your settings
class AppSettings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    max_connections: int = 100

# 2. Create a settings manager
manager = SettingsManager(AppSettings)

# 3. Load configuration
manager.user_config = {
    "app_name": "ProductionApp",
    "debug": False,
    "max_connections": 500
}

# 4. Use your settings
settings = manager.settings
print(f"App: {settings.app_name}")  # Output: App: ProductionApp
```

### Runtime Overrides

```python
# Override settings at runtime (e.g., from command line)
manager.cli_args = {"debug": True, "max_connections": 50}

settings = manager.settings
print(f"Debug: {settings.debug}")  # Output: Debug: True
print(f"Connections: {settings.max_connections}")  # Output: Connections: 50
```

## Bootstrap Pattern (Recommended for Production)

**For multi-module applications, use the bootstrap pattern with `load_user_configs()`.** This is the recommended approach for production applications.

### Why Bootstrap Pattern?

- **Centralized Configuration**: Load all module settings from a single configuration file
- **Automatic Discovery**: No need to manually import and configure each module
- **Environment Management**: Easy switching between development, staging, and production
- **Clean Separation**: Configuration files separate from application code

### Project Structure

```
your_project/
├── settings/
│   ├── __init__.py
│   └── app.py                    # app_settings_manager
├── modules/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── settings.py           # auth_settings_manager
│   │   └── service.py
│   └── billing/
│       ├── __init__.py
│       ├── settings.py           # billing_settings_manager
│       └── service.py
├── config/
│   ├── base.yaml                 # Shared configuration
│   ├── development.yaml          # Dev overrides
│   └── production.yaml           # Prod overrides
├── bootstrap.py                  # Bootstrap logic
└── main.py                       # Application entry point
```

### Quick Example

```python
# 1. Define settings in each module
# settings/app.py
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

class AppSettings(BaseSettings):
    name: str = "MyApp"
    debug: bool = False
    secret_key: str = "dev-secret"

settings_manager = SettingsManager(AppSettings)

# modules/auth/settings.py
class AuthSettings(BaseSettings):
    jwt_secret: str = "jwt-secret"
    token_expiry: int = 3600

settings_manager = SettingsManager(AuthSettings)

# modules/billing/settings.py
class BillingSettings(BaseSettings):
    currency: str = "USD"
    stripe_api_key: str = ""

settings_manager = SettingsManager(BillingSettings)
```

```yaml
# config/base.yaml (shared across all environments)
settings.app:
  name: "MyApp"

modules.auth.settings:
  token_expiry: 3600

modules.billing.settings:
  currency: "USD"

# config/production.yaml (prod-specific overrides)
settings.app:
  debug: false
  secret_key: "${SECRET_KEY}"

modules.auth.settings:
  jwt_secret: "${JWT_SECRET}"

modules.billing.settings:
  stripe_api_key: "${STRIPE_API_KEY}"
```

```python
# bootstrap.py - RECOMMENDED IMPLEMENTATION
import os
import yaml
from pathlib import Path
from pydantic_settings_manager import load_user_configs, update_dict

def bootstrap(environment: str | None = None) -> None:
    """
    Bootstrap all settings managers with environment-specific configuration.
    
    Args:
        environment: Environment name (e.g., "development", "production").
                    If None, uses ENVIRONMENT env var or defaults to "development".
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    config_dir = Path("config")
    
    # Load base configuration (optional)
    base_file = config_dir / "base.yaml"
    if base_file.exists():
        with open(base_file) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Load environment-specific configuration
    env_file = config_dir / f"{environment}.yaml"
    if env_file.exists():
        with open(env_file) as f:
            env_config = yaml.safe_load(f) or {}
            # Deep merge configurations (environment overrides base)
            config = update_dict(config, env_config)
    
    # This single line configures ALL your settings managers!
    load_user_configs(config)
    
    print(f"✓ Loaded configuration for '{environment}' environment")

# main.py
from bootstrap import bootstrap
from settings.app import settings_manager as app_settings_manager
from modules.auth.settings import settings_manager as auth_settings_manager
from modules.billing.settings import settings_manager as billing_settings_manager

def main():
    # Bootstrap all settings with one line
    bootstrap("production")
    
    # All settings are now configured and ready to use!
    app = app_settings_manager.settings
    auth = auth_settings_manager.settings
    billing = billing_settings_manager.settings
    
    print(f"App: {app.name}, Debug: {app.debug}")
    print(f"JWT Expiry: {auth.token_expiry}")
    print(f"Currency: {billing.currency}")

if __name__ == "__main__":
    main()
```

### Configuration File Structure

The configuration file structure maps directly to your module structure:

```yaml
# Key = module path (e.g., "settings.app" → settings/app.py)
# Value = configuration for that module's settings manager

settings.app:
  name: "MyApp-Production"
  debug: false
  secret_key: "${SECRET_KEY}"  # Pydantic will read from environment

modules.auth.settings:
  jwt_secret: "${JWT_SECRET}"
  token_expiry: 3600

modules.billing.settings:
  currency: "USD"
  stripe_api_key: "${STRIPE_API_KEY}"
```

### Custom Manager Names

By default, `load_user_configs()` looks for `settings_manager` in each module. You can customize this:

```python
# settings/app.py
app_manager = SettingsManager(AppSettings)  # Custom name

# bootstrap.py
load_user_configs(config, manager_name="app_manager")
```

### Frequently Asked Questions

**Q: Do I need `multi=True` for bootstrap pattern?**

A: No! Bootstrap pattern works with both single and multi mode:
- **Single mode** (recommended): One configuration per module
- **Multi mode**: Multiple configurations per module (e.g., dev/staging/prod in same manager)

```python
# Single mode (simpler, recommended for most cases)
settings_manager = SettingsManager(AppSettings)

# Multi mode (when you need multiple configs per module)
settings_manager = SettingsManager(AppSettings, multi=True)
```

**Q: How are environment variables like `${SECRET_KEY}` handled?**

A: Pydantic Settings automatically reads from environment variables. The `${VAR}` syntax in YAML is just documentation - you can use any value:

```yaml
# config/production.yaml
settings.app:
  secret_key: "placeholder"  # Will be overridden by SECRET_KEY env var
```

Pydantic will automatically use `os.getenv("SECRET_KEY")` if the environment variable is set.

**Q: When should I use manual configuration instead of `load_user_configs`?**

A: Only when you need module-specific logic:
- Custom validation per module
- Conditional configuration based on module state  
- Dynamic module discovery

For 99% of cases, use `load_user_configs()`.

**Q: Can I use bootstrap pattern with a single module?**

A: Yes, but it's overkill. For single-module projects, just use:

```python
manager = SettingsManager(AppSettings)
manager.user_config = yaml.safe_load(open("config.yaml"))
```

## Multiple Configurations

For applications that need different settings for different environments or contexts:

```python
# Enable multi-configuration mode
manager = SettingsManager(AppSettings, multi=True)

# Configure multiple environments (direct format)
manager.user_config = {
    "development": {
        "app_name": "MyApp-Dev",
        "debug": True,
        "max_connections": 10
    },
    "production": {
        "app_name": "MyApp-Prod", 
        "debug": False,
        "max_connections": 1000
    },
    "testing": {
        "app_name": "MyApp-Test",
        "debug": True,
        "max_connections": 5
    }
}

# Alternative: structured format (useful when you want to set active_key in config)
# manager.user_config = {
#     "key": "production",  # Set active configuration
#     "map": {
#         "development": {"app_name": "MyApp-Dev", "debug": True, "max_connections": 10},
#         "production": {"app_name": "MyApp-Prod", "debug": False, "max_connections": 1000},
#         "testing": {"app_name": "MyApp-Test", "debug": True, "max_connections": 5}
#     }
# }

# Switch between configurations
manager.active_key = "development"
dev_settings = manager.settings
print(f"Dev: {dev_settings.app_name}, Debug: {dev_settings.debug}")

manager.active_key = "production"
prod_settings = manager.settings
print(f"Prod: {prod_settings.app_name}, Debug: {prod_settings.debug}")

# Get all configurations
all_settings = manager.all_settings
for env, settings in all_settings.items():
    print(f"{env}: {settings.app_name}")
```

## Advanced Usage

### Thread Safety

The `SettingsManager` is fully thread-safe and can be used in multi-threaded applications:

```python
import threading
from concurrent.futures import ThreadPoolExecutor

manager = SettingsManager(AppSettings, multi=True)
manager.user_config = {
    "worker1": {"app_name": "Worker1", "max_connections": 10},
    "worker2": {"app_name": "Worker2", "max_connections": 20}
}

def worker_function(worker_id: int):
    # Each thread can safely switch configurations
    manager.active_key = f"worker{worker_id}"
    settings = manager.settings
    print(f"Worker {worker_id}: {settings.app_name}")

# Run multiple workers concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(worker_function, i) for i in range(1, 3)]
    for future in futures:
        future.result()
```

### Dynamic Configuration Updates

```python
# Update individual CLI arguments
manager.set_cli_args("debug", True)
manager.set_cli_args("nested.value", "test")  # Supports nested keys

# Update entire CLI args
manager.cli_args = {"debug": False, "max_connections": 200}

# Get specific settings by key (multi mode)
dev_settings = manager.get_settings_by_key("development")
prod_settings = manager.get_settings_by_key("production")
```

## CLI Integration

Integrate with command-line tools for runtime configuration:

```python
# cli.py
import click
from bootstrap import bootstrap_settings
from settings.app import app_settings_manager

@click.command()
@click.option("--environment", "-e", default="development", 
              help="Environment to run in")
@click.option("--debug/--no-debug", default=None, 
              help="Override debug setting")
@click.option("--max-connections", type=int, 
              help="Override max connections")
def main(environment: str, debug: bool, max_connections: int):
    """Run the application with specified settings"""
    
    # Bootstrap with environment
    bootstrap_settings(environment)
    
    # Apply CLI overrides
    cli_overrides = {}
    if debug is not None:
        cli_overrides["debug"] = debug
    if max_connections is not None:
        cli_overrides["max_connections"] = max_connections
    
    if cli_overrides:
        app_settings_manager.cli_args = cli_overrides
    
    # Run application
    settings = app_settings_manager.settings
    print(f"Running {settings.name} in {environment} mode")
    print(f"Debug: {settings.debug}")

if __name__ == "__main__":
    main()
```

Usage:
```bash
# Run with defaults
python cli.py

# Run in production with debug enabled
python cli.py --environment production --debug

# Override specific settings
python cli.py --max-connections 500
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

This project uses modern Python development tools:

- **uv**: Fast Python package manager with PEP 735 dependency groups support
- **ruff**: Fast linter and formatter (replaces black, isort, and flake8)
- **mypy**: Static type checking
- **pytest**: Testing framework with coverage reporting

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

## API Reference

### SettingsManager

The main class for managing Pydantic settings.

```python
class SettingsManager(Generic[T]):
    def __init__(self, settings_cls: type[T], *, multi: bool = False)
```

#### Parameters
- `settings_cls`: The Pydantic settings class to manage
- `multi`: Whether to enable multi-configuration mode (default: False)

#### Properties
- `settings: T` - Get the current active settings
- `all_settings: dict[str, T]` - Get all settings (multi mode)
- `user_config: dict[str, Any]` - Get/set user configuration
- `cli_args: dict[str, Any]` - Get/set CLI arguments
- `active_key: str | None` - Get/set active key (multi mode only)

#### Methods
- `clear() -> None` - Clear cached settings
- `get_settings_by_key(key: str) -> T` - Get settings by specific key
- `set_cli_args(target: str, value: Any) -> None` - Set individual CLI argument

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Documentation

For more detailed documentation and examples, please see the [GitHub repository](https://github.com/kiarina/pydantic-settings-manager).
