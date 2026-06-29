# pydantic-settings-manager

[![PyPI](https://img.shields.io/pypi/v/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![Python](https://img.shields.io/pypi/pyversions/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![CI](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/kiarina/pydantic-settings-manager/branch/main/graph/badge.svg)](https://codecov.io/gh/kiarina/pydantic-settings-manager)
[![License](https://img.shields.io/pypi/l/pydantic-settings-manager.svg)](https://github.com/kiarina/pydantic-settings-manager/blob/main/LICENSE)

**English** | [日本語](README.ja.md)

## Summary

pydantic-settings-manager is a library for using pydantic-settings in the following ways:
- Define settings classes split per module, following the single-responsibility principle
- Treat the split settings classes in an integrated way across the whole application

> [!NOTE]
> pydantic-settings-manager is part of the libraries that realize [Crystal Architecture](https://github.com/kiarina/crystal-architecture).

## Features

- Define settings classes with [Pydantic Settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
- Load settings values into a settings class from three sources: environment variables, configuration files, and command-line arguments
- Integrate multiple settings classes into one at the application level
- Hold multiple settings in a single settings class and switch between them

## Quick Start

This section introduces the standard way to use pydantic-settings-manager.

```sh
> tree .
.
├── app
│   ├── __main__.py
│   ├── cli
│   │   ├── __init__.py
│   │   ├── _settings.py
│   │   └── cli.py
│   └── slack
│       ├── __init__.py
│       ├── _helpers
│       │   └── send_slack_message.py
│       └── _settings.py
├── pyproject.toml
└── uv.lock
```

**Initialize the project:**
```sh
uv init
uv add pydantic-settings-manager pyyaml click
```

**Define a single-mode settings class:**
```python
# app/cli/_settings.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager

class CLISettings(BaseSettings):
    """Sample CLI settings"""

    model_config = SettingsConfigDict(
        env_prefix="CLI_",
        extra="ignore",
    )

    verbose: bool = Field(
        default=False,
        title="Verbose Mode",
        description="Enable verbose output for debugging purposes.",
    )

settings_manager = SettingsManager(CLISettings)
```

**Load a settings class with command-line arguments and user configs applied:**
```python
# app/cli/__init__.py
from ._settings import settings_manager

__all__ = ["settings_manager"]

# app/cli/cli.py
from pathlib import Path

import click
import yaml
from pydantic_settings_manager import load_user_configs

from app import cli, slack

@click.command()
@click.argument("message", type=str)
@click.option("--channel", type=str, default=None)
@click.option("--slack-settings-key", type=str, default=None)
@click.option("--verbose", is_flag=True, default=None)
def main(
    message: str,
    channel: str | None,
    slack_settings_key: str | None,
    verbose: bool | None,
):
    user_configs_path = Path(__file__).parent.parent.parent / "settings.yaml"

    if user_configs_path.exists():
        with user_configs_path.open("r") as f:
            user_configs_dict = yaml.safe_load(f)

        # Apply user configs to all settings managers
        load_user_configs(user_configs_dict)

    # Apply CLI arguments to the settings manager
    if verbose is not None:
        cli.settings_manager.set_cli_args("verbose", verbose)

        # For nested keys, you can specify a dot-separated path
        # cli.settings_manager.set_cli_args("nested.value", "test")

        # To update the whole CLI args at once, pass a dict
        # cli.settings_manager.cli_args = {"verbose": True, "nested.value": "test

    # Get the settings class with the priority: CLI args > user configs > environment variables
    settings = cli.settings_manager.get_settings()

    if settings.verbose:
        print("Verbose mode is enabled.")

    slack.send_slack_message(
        message, channel=channel, slack_settings_key=slack_settings_key
    )

# app/__main__.py
from app.cli.cli import main

if __name__ == "__main__":
    main()
```

**Define a multi-mode settings class:**
```python
#--------------------------------------------------
# app/slack/_settings.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager

class SlackSettings(BaseSettings):
    """Sample Slack settings"""

    model_config = SettingsConfigDict(
        env_prefix="SLACK_",
        extra="ignore",
    )

    bot_token: SecretStr = Field(
        ...,
        title="Slack Bot Token",
        description="The bot token for the Slack integration.",
    )

    default_channel: str = Field(
        ...,
        title="Default Slack Channel",
        description="The default channel to send messages to.",
    )

# Specifying multi=True lets the manager hold multiple settings
settings_manager = SettingsManager(SlackSettings, multi=True)

#--------------------------------------------------
# app/slack/_helpers/send_slack_message.py
from .._settings import settings_manager

def send_slack_message(
    message: str,
    channel: str | None = None,
    slack_settings_key: str | None = None,
) -> None:
    # Get the settings class by key
    settings = settings_manager.get_settings(slack_settings_key)

    if channel is None:
        channel = settings.default_channel

    print(f"Sending message to Slack channel '{channel}': {message}")

#--------------------------------------------------
# app/slack/__init__.py
from ._helpers.send_slack_message import send_slack_message
from ._settings import settings_manager

__all__ = [
    "send_slack_message",
    "settings_manager",
]
```

**Run with environment variables:**
```sh
> SLACK_API_KEY=xoxb-...tmp SLACK_DEFAULT_CHANNEL=C...tmp uv run python -m app hello
Sending message to Slack channel 'C...tmp': hello
```

**Generate a user-config template from the settings classes:**
```sh
> uv run python -m pydantic_settings_manager generate-user-configs app.cli app.slack
#--------------------------------------------------------------------------------
# Sample CLI settings
#--------------------------------------------------------------------------------
app.cli:
  # Verbose Mode: bool
  #   Enable verbose output for debugging purposes.
  # verbose: false

#--------------------------------------------------------------------------------
# Sample Slack settings
#--------------------------------------------------------------------------------
app.slack:
  # default: default
  configs:
    default:
      # Slack Bot Token: SecretStr
      #   The bot token for the Slack integration.
      bot_token:
      #--------------------------------------------------
      # Default Slack Channel: str
      #   The default channel to send messages to.
      default_channel:
  # aliases: {}
```

> [!NOTE]
> Fields with default values are commented out, while required fields are emitted in an active state.

**Run with user configs applied:**
```yaml
# settings.yaml
app.cli:
  verbose: true

app.slack:
  default: group2
  aliases:
    hotline: group1
  configs:
    group1:
      bot_token: "xoxb-...(group1)"
      default_channel: "C...(group1)"
    group2:
      bot_token: "xoxb-...(group2)"
      default_channel: "C...(group2)"
```
```sh
> SLACK_API_KEY=xoxb-tmp SLACK_DEFAULT_CHANNEL=C...tmp uv run python -m app hello
Verbose mode is enabled.
Sending message to Slack channel 'C...(group2)': hello
```
- User configs take priority over environment variables

**Run with CLI arguments applied:**
```sh
> SLACK_API_KEY=xoxb-tmp SLACK_DEFAULT_CHANNEL=C...tmp uv run python -m app --slack-settings-key hotline hello
Verbose mode is enabled.
Sending message to Slack channel 'C...(group1)': hello
```

## API Reference

### `pydantic_settings_manager`

```python
from pydantic_settings_manager import (
    DEFAULT_KEY,
    ConfigUpdatePolicy,
    MissingModulePolicy,
    ModuleName,
    SettingsKey,
    SettingsManager,
    UserConfig,
    UserConfigError,
    UserConfigs,
    clear_user_configs,
    generate_user_configs_yaml,
    load_user_configs,
    update_dict,
)
```

#### `load_user_configs`

```python
def load_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
    update_policy: ConfigUpdatePolicy = "replace",
    missing_module_policy: MissingModulePolicy = "error",
) -> None: ...
```

Applies user configs to the settings managers exposed by each module.
It resolves the `manager_name` attribute from each key (module name) in `user_configs` and updates its `user_config`.

**Parameters**

- `user_configs` (`UserConfigs`): A mapping from module name to that module's user config.
- `manager_name` (`str`): The attribute name under which each module exposes its settings manager.
- `update_policy` (`ConfigUpdatePolicy`): `"replace"` replaces the existing user config, while `"merge"` deeply merges into the existing user config.
- `missing_module_policy` (`MissingModulePolicy`): Behavior when a module is not found. `"error"` raises an exception, `"warn"` warns and continues, and `"ignore"` silently continues.

**Raises**

- `ValueError`: When the value of `update_policy` or `missing_module_policy` is invalid.
- `TypeError`: When a module's user config is not a dict.
- `ModuleNotFoundError`: When a module is not found and `missing_module_policy` is `"error"`.

#### `clear_user_configs`

```python
def clear_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
) -> None: ...
```

Resets the user configs of the settings managers for each module contained in `user_configs`.
Internally, it calls `reset_user_config()` on each settings manager.

**Parameters**

- `user_configs` (`UserConfigs`): A mapping containing the modules to reset. The values are not referenced; only the keys (module names) are used.
- `manager_name` (`str`): The attribute name under which each module exposes its settings manager.

#### `generate_user_configs_yaml`

```python
def generate_user_configs_yaml(
    import_paths: list[str],
    *,
    manager_name: str = "settings_manager",
) -> str: ...
```

Generates a commented user-config YAML template from the settings classes.
Fields with default values are commented out, while required fields are emitted in an active state.

**Parameters**

- `import_paths` (`list[str]`): A list of import paths of the modules that expose a settings manager.
- `manager_name` (`str`): The attribute name under which each module exposes its settings manager.

**Returns**

- `str`: A YAML template string concatenating the block for each module.

#### `update_dict`

```python
def update_dict(
    base: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]: ...
```

Returns a copy of `base` deeply updated with `update`. `base` is not modified.
Keys whose values are both dicts are merged recursively; otherwise the value from `update` overwrites.

**Parameters**

- `base` (`dict[str, Any]`): The base dict.
- `update` (`dict[str, Any]`): The dict to overwrite/merge.

**Returns**

- `dict[str, Any]`: A new deeply merged dict.

#### `SettingsManager`

```python
class SettingsManager[T: BaseSettings]:
    def __init__(
        self,
        settings_cls: type[T],
        *,
        multi: bool = False,
    ) -> None: ...

    settings_cls: type[T]
    multi: bool

    @property
    def all_settings(self) -> dict[str, T]: ...

    @property
    def settings(self) -> T: ...

    @property
    def user_config(self) -> dict[str, Any]: ...
    @user_config.setter
    def user_config(self, value: dict[str, Any]) -> None: ...

    @property
    def active_key(self) -> SettingsKey | None: ...
    @active_key.setter
    def active_key(self, key: SettingsKey | None) -> None: ...

    @property
    def cli_args(self) -> dict[str, Any]: ...
    @cli_args.setter
    def cli_args(self, value: dict[str, Any]) -> None: ...

    def set_cli_args(self, target: str, value: Any) -> None: ...

    def get_settings(self, key: SettingsKey | None = None) -> T: ...

    def reset_user_config(self) -> None: ...

    def clear(self) -> None: ...
```

A settings manager that can handle both single and multiple settings.
In single mode (`multi=False`) it holds one setting; in multi mode (`multi=True`) it holds multiple named settings.
Its internal processing is thread-safe.

##### `__init__`

```python
def __init__(
    self,
    settings_cls: type[T],
    *,
    multi: bool = False,
) -> None: ...
```

**Parameters**

- `settings_cls` (`type[T]`): The `BaseSettings` subclass to manage.
- `multi` (`bool`): `True` enables multi mode, which handles multiple named settings.

##### `settings_cls`

```python
settings_cls: type[T]
```

The settings class being managed.

##### `multi`

```python
multi: bool
```

Whether the manager is in multi mode.

##### `all_settings`

```python
@property
def all_settings(self) -> dict[str, T]: ...
```

Returns copies of the settings instances for all keys.

##### `settings`

```python
@property
def settings(self) -> T: ...
```

Returns the currently active settings instance.
In multi mode it is resolved by `active_key`, or by the `default` key when unset.

**Raises**

- `ValueError`: When the resolved key does not exist in the settings map.

##### `user_config`

```python
@property
def user_config(self) -> dict[str, Any]: ...
@user_config.setter
def user_config(self, value: dict[str, Any]) -> None: ...
```

Gets/sets the user config.
In single mode it is a dict of settings fields; in multi mode it is in the form `{"default": ..., "configs": {...}, "aliases": {...}}` (see [`UserConfig`](#userconfig)).

**Raises**

- `ValueError`: When, in multi mode, an unknown key is included, `configs` is missing, or an alias/default key resolves to a non-existent target.
- `TypeError`: When, in multi mode, the types of `configs`/`aliases`/`default` are invalid.

##### `active_key`

```python
@property
def active_key(self) -> SettingsKey | None: ...
@active_key.setter
def active_key(self, key: SettingsKey | None) -> None: ...
```

Gets/sets the settings key to activate in multi mode.

**Raises**

- `ValueError`: When called in single mode.

##### `cli_args`

```python
@property
def cli_args(self) -> dict[str, Any]: ...
@cli_args.setter
def cli_args(self, value: dict[str, Any]) -> None: ...
```

Gets/sets the dict of CLI arguments, which are applied to the settings with the highest priority.

##### `set_cli_args`

```python
def set_cli_args(self, target: str, value: Any) -> None: ...
```

Sets a single CLI argument. Passing a dot-separated path to `target` lets you set a nested key.

**Parameters**

- `target` (`str`): The destination key. You can specify nesting with a dot-separated path (e.g. `"nested.value"`).
- `value` (`Any`): The value to set.

**Raises**

- `ValueError`: When an intermediate node along the `target` path is not a dict.

##### `get_settings`

```python
def get_settings(self, key: SettingsKey | None = None) -> T: ...
```

Gets a settings instance. In multi mode you can specify `key` to get any setting.
When `key` is omitted, it returns the same result as [`settings`](#settings).

**Parameters**

- `key` (`SettingsKey | None`): The key of the setting to get (aliases allowed).

**Returns**

- `T`: The settings instance corresponding to the resolved key.

**Raises**

- `ValueError`: When `key` is specified in single mode, or when the resolved key does not exist.

##### `reset_user_config`

```python
def reset_user_config(self) -> None: ...
```

Resets the user config, aliases, default key, and active key all back to their initial state.

##### `clear`

```python
def clear(self) -> None: ...
```

Invalidates the internal cache so that the settings are rebuilt on the next access.

#### `UserConfig`

```python
type UserConfig = SingleUserConfig | MultiUserConfig

type SingleUserConfig = dict[str, Any]

class MultiUserConfig(TypedDict):
    configs: dict[str, dict[str, Any]]
    default: NotRequired[str | None]
    aliases: NotRequired[dict[str, str]]
```

A type alias representing a user config in either single or multi mode.
In single mode it is a dict of settings fields; in multi mode it is a dict with `configs`, `default`, and `aliases`.

**Fields** (`MultiUserConfig`)

- `configs` (`dict[str, dict[str, Any]]`): A mapping from config name to that config's dict of settings fields.
- `default` (`NotRequired[str | None]`): The default config name to use when no key is specified.
- `aliases` (`NotRequired[dict[str, str]]`): A mapping from alias name to the actual config name.

#### `UserConfigs`

```python
type UserConfigs = dict[ModuleName, UserConfig]
```

A mapping from module name to that module's [`UserConfig`](#userconfig).

#### `ConfigUpdatePolicy`

```python
type ConfigUpdatePolicy = Literal["replace", "merge"]
```

Behavior when applying settings to an existing settings manager. `"replace"` replaces, `"merge"` deeply merges.

#### `MissingModulePolicy`

```python
type MissingModulePolicy = Literal["error", "warn", "ignore"]
```

Behavior when a target module does not exist. `"error"` raises an exception, `"warn"` warns and continues, and `"ignore"` silently continues.

#### `ModuleName`

```python
type ModuleName = str
```

A fully-qualified module name handled by the settings helpers.

#### `SettingsKey`

```python
type SettingsKey = str
```

A settings manager key.

#### `DEFAULT_KEY`

```python
DEFAULT_KEY: str = "default"
```

The default key used internally in single mode.

#### `UserConfigError`

```python
class UserConfigError(ValueError): ...
```

Raised when a user configuration fails to validate while the settings cache is built (for example, a required field is missing). Instead of a raw `pydantic.ValidationError`, the message points at the offending fields in the same commented-YAML format as [`generate_user_configs_yaml`](#generate_user_configs_yaml), with a comment describing each error and the rejected input value when available:

```text
Failed to load user settings.

app.slack:
  configs:
    default:
      #--------------------------------------------------
      # Default Slack Channel: str
      #   The default channel to send messages to.
      #   required field is not set
      default_channel:
```

The module path is resolved to the public location that re-exports the settings manager. The original `pydantic.ValidationError` is preserved as `__cause__`. When the manager cannot be located by its public module path, the raw `ValidationError` is raised instead. Because `UserConfigError` subclasses `ValueError`, existing `except ValueError` handlers keep working.
