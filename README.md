# pydantic-settings-manager

A modern, thread-safe library for managing Pydantic settings with support for multiple configurations and runtime overrides.

## Features

- **Unified API**: Single `SettingsManager` class handles both simple and complex configurations
- **Thread-safe**: Built-in thread safety for concurrent applications
- **Type-safe**: Full type hints and Pydantic validation
- **Flexible**: Support for single settings or multiple named configurations
- **Runtime overrides**: Command-line arguments and dynamic configuration changes
- **Easy migration**: Simple upgrade path from configuration files and environment variables

## Installation

```bash
pip install pydantic-settings-manager
```

## Quick Start

### Basic Usage

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

# 3. Use your settings
settings = manager.settings
print(f"App: {settings.app_name}, Debug: {settings.debug}")
# Output: App: MyApp, Debug: False
```

### Loading from Configuration

```python
# Load from a dictionary (JSON, YAML, etc.)
manager.user_config = {
    "app_name": "ProductionApp",
    "debug": False,
    "max_connections": 500
}

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

### Complex Settings with Nested Configuration

```python
from typing import Dict, List
from pydantic import Field

class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    username: str = "user"
    password: str = "password"

class APISettings(BaseSettings):
    base_url: str = "https://api.example.com"
    timeout: int = 30
    retries: int = 3

class AppSettings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    features: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

manager = SettingsManager(AppSettings, multi=True)
manager.user_config = {
    "development": {
        "app_name": "MyApp-Dev",
        "debug": True,
        "database": {
            "host": "dev-db.example.com",
            "port": 5433
        },
        "api": {
            "base_url": "https://dev-api.example.com",
            "timeout": 10
        },
        "features": ["debug_toolbar", "hot_reload"],
        "metadata": {"environment": "dev", "version": "1.0.0-dev"}
    },
    "production": {
        "app_name": "MyApp-Prod",
        "debug": False,
        "database": {
            "host": "prod-db.example.com",
            "port": 5432,
            "username": "prod_user"
        },
        "api": {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "retries": 5
        },
        "features": ["monitoring", "caching"],
        "metadata": {"environment": "prod", "version": "1.0.0"}
    }
}

# Use nested configuration
manager.active_key = "development"
settings = manager.settings
print(f"DB Host: {settings.database.host}")
print(f"API URL: {settings.api.base_url}")
print(f"Features: {settings.features}")
```

## Project Structure for Large Applications

For complex applications with multiple modules:

```
your_project/
├── settings/
│   ├── __init__.py
│   ├── app.py
│   ├── database.py
│   └── api.py
├── modules/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── service.py
│   └── billing/
│       ├── __init__.py
│       ├── settings.py
│       └── service.py
├── config/
│   ├── base.yaml
│   ├── development.yaml
│   └── production.yaml
├── bootstrap.py
└── main.py
```

### Module-based Settings

```python
# settings/app.py
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

class AppSettings(BaseSettings):
    name: str = "MyApp"
    debug: bool = False
    secret_key: str = "dev-secret"

app_settings_manager = SettingsManager(AppSettings, multi=True)

# modules/auth/settings.py
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

class AuthSettings(BaseSettings):
    jwt_secret: str = "jwt-secret"
    token_expiry: int = 3600
    max_login_attempts: int = 5

auth_settings_manager = SettingsManager(AuthSettings, multi=True)
```

### Bootstrap Configuration

```python
# bootstrap.py
import yaml
import importlib
from pathlib import Path
from pydantic_settings_manager import SettingsManager

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path) as f:
        return yaml.safe_load(f)

def bootstrap_settings(environment: str = "development"):
    """Bootstrap all settings managers with configuration"""
    
    # Load base configuration
    base_config = load_config("config/base.yaml")
    env_config = load_config(f"config/{environment}.yaml")
    
    # Merge configurations (env overrides base)
    config = {**base_config, **env_config}
    
    # Configure each module's settings manager
    settings_managers = [
        ("settings.app", "app_settings_manager"),
        ("modules.auth.settings", "auth_settings_manager"),
        ("modules.billing.settings", "billing_settings_manager"),
    ]
    
    for module_name, manager_name in settings_managers:
        try:
            module = importlib.import_module(module_name)
            manager = getattr(module, manager_name, None)
            
            if isinstance(manager, SettingsManager):
                # Set configuration for this module
                if module_name.split('.')[-1] in config:
                    manager.user_config = config[module_name.split('.')[-1]]
                    manager.active_key = environment
                    
        except ImportError:
            print(f"Warning: Could not import {module_name}")

# main.py
from bootstrap import bootstrap_settings
from settings.app import app_settings_manager
from modules.auth.settings import auth_settings_manager

def main():
    # Bootstrap all settings
    bootstrap_settings("production")
    
    # Use settings throughout the application
    app_settings = app_settings_manager.settings
    auth_settings = auth_settings_manager.settings
    
    print(f"App: {app_settings.name}")
    print(f"JWT Expiry: {auth_settings.token_expiry}")

if __name__ == "__main__":
    main()
```

### Configuration Files

```yaml
# config/base.yaml
app:
  name: "MyApp"
  debug: false

auth:
  token_expiry: 3600
  max_login_attempts: 5

billing:
  currency: "USD"
  tax_rate: 0.08
```

```yaml
# config/development.yaml
app:
  debug: true
  secret_key: "dev-secret-key"

auth:
  jwt_secret: "dev-jwt-secret"
  token_expiry: 7200  # Longer expiry for development

billing:
  mock_payments: true
```

```yaml
# config/production.yaml
app:
  secret_key: "${SECRET_KEY}"  # From environment variable

auth:
  jwt_secret: "${JWT_SECRET}"
  max_login_attempts: 3  # Stricter in production

billing:
  mock_payments: false
  stripe_api_key: "${STRIPE_API_KEY}"
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
