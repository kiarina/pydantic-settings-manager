# pydantic-settings-manager

[![PyPI](https://img.shields.io/pypi/v/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![Python](https://img.shields.io/pypi/pyversions/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![CI](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/kiarina/pydantic-settings-manager/branch/main/graph/badge.svg)](https://codecov.io/gh/kiarina/pydantic-settings-manager)
[![License](https://img.shields.io/pypi/l/pydantic-settings-manager.svg)](https://github.com/kiarina/pydantic-settings-manager/blob/main/LICENSE)

[English](README.md) | **日本語**

## Summary

pydantic-settings-manager は、pydantic-settings を、下記のように利用するためのライブラリです。
- 設定クラスを、単一責任の原則に従ってモジュールごとに分割して定義できる
- 分割された設定クラスを、アプリケーション全体で統合して扱える

> [!NOTE]
> pydantic-settings-manager は、[Crystal Architecture](https://github.com/kiarina/crystal-architecture) を実現するためのライブラリの一部です。

## Features

- [Pydantic Settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/) で設定クラスを定義できる
- 設定クラスに、環境変数・設定ファイル・コマンドライン引数の 3 つのソースから設定値を読み込める
- 複数の設定クラスを、アプリケーションレベルで 1 つに統合して扱える
- 1 つの設定クラスに、複数の設定を持たせて、切り替えながら使える

## Quick Start

pydantic-settings-manager のスタンダードな使い方を紹介します。

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

**プロジェクトを初期化:**
```sh
uv init
uv add pydantic-settings-manager pyyaml click
```

**シングルモードの設定クラスを定義:**
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

**コマンドライン引数・ユーザー設定を反映した設定クラスの読み込み:**
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

        # ユーザー設定を全設定マネージャーに反映
        load_user_configs(user_configs_dict)

    # CLI 引数を設定マネージャーに反映
    if verbose is not None:
        cli.settings_manager.set_cli_args("verbose", verbose)

        # ネストしたキーに対応する場合は、ドット区切りで指定できます
        # cli.settings_manager.set_cli_args("nested.value", "test")

        # CLI args 全体を更新する場合は、辞書で指定できます
        # cli.settings_manager.cli_args = {"verbose": True, "nested.value": "test

    # CLI 引数 > ユーザー設定 > 環境変数の優先順位で反映された設定クラスを取得
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

**マルチモードの設定クラスを定義:**
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

# multi=True を指定することで、複数の設定を持たせることができる
settings_manager = SettingsManager(SlackSettings, multi=True)

#--------------------------------------------------
# app/slack/_helpers/send_slack_message.py
from .._settings import settings_manager

def send_slack_message(
    message: str,
    channel: str | None = None,
    slack_settings_key: str | None = None,
) -> None:
    # キーを指定して設定クラスを取得
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

**環境変数を指定して実行:**
```sh
> SLACK_API_KEY=xoxb-...tmp SLACK_DEFAULT_CHANNEL=C...tmp uv run python -m app hello
Sending message to Slack channel 'C...tmp': hello
```

**設定クラスからユーザー設定の雛形を生成:**
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
> デフォルト値を持つフィールドはコメントアウトされ、必須フィールドは有効な状態で出力されます。

**ユーザー設定を反映して実行:**
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
- 環境変数よりも、ユーザー設定が優先されます

**CLI 引数を反映して実行:**
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

ユーザー設定を、各モジュールが公開する設定マネージャーに反映します。
`user_configs` のキー（モジュール名）から `manager_name` の属性を解決し、その `user_config` を更新します。

**Parameters**

- `user_configs` (`UserConfigs`): モジュール名から、そのモジュールのユーザー設定へのマッピング。
- `manager_name` (`str`): 各モジュールで設定マネージャーを公開している属性名。
- `update_policy` (`ConfigUpdatePolicy`): `"replace"` は既存のユーザー設定を置き換え、`"merge"` は既存のユーザー設定に深くマージします。
- `missing_module_policy` (`MissingModulePolicy`): モジュールが見つからない場合の挙動。`"error"` は例外を送出し、`"warn"` は警告して継続し、`"ignore"` は無視して継続します。

**Raises**

- `ValueError`: `update_policy` または `missing_module_policy` の値が不正な場合。
- `TypeError`: あるモジュールのユーザー設定が辞書でない場合。
- `ModuleNotFoundError`: モジュールが見つからず、`missing_module_policy` が `"error"` の場合。

#### `clear_user_configs`

```python
def clear_user_configs(
    user_configs: UserConfigs,
    *,
    manager_name: str = "settings_manager",
) -> None: ...
```

`user_configs` に含まれる各モジュールの設定マネージャーのユーザー設定をリセットします。
内部では各設定マネージャーの `reset_user_config()` を呼び出します。

**Parameters**

- `user_configs` (`UserConfigs`): リセット対象のモジュールを含むマッピング。値の内容は参照されず、キー（モジュール名）のみが使用されます。
- `manager_name` (`str`): 各モジュールで設定マネージャーを公開している属性名。

#### `generate_user_configs_yaml`

```python
def generate_user_configs_yaml(
    import_paths: list[str],
    *,
    manager_name: str = "settings_manager",
) -> str: ...
```

設定クラスから、コメント付きのユーザー設定 YAML テンプレートを生成します。
デフォルト値を持つフィールドはコメントアウトされ、必須フィールドは有効な状態で出力されます。

**Parameters**

- `import_paths` (`list[str]`): 設定マネージャーを公開するモジュールの import path のリスト。
- `manager_name` (`str`): 各モジュールで設定マネージャーを公開している属性名。

**Returns**

- `str`: 各モジュールのブロックを連結した YAML テンプレート文字列。

#### `update_dict`

```python
def update_dict(
    base: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]: ...
```

`base` を `update` で深く更新したコピーを返します。`base` は変更されません。
両方の値が辞書であるキーは再帰的にマージされ、それ以外は `update` の値で上書きされます。

**Parameters**

- `base` (`dict[str, Any]`): ベースとなる辞書。
- `update` (`dict[str, Any]`): 上書き・マージする辞書。

**Returns**

- `dict[str, Any]`: 深くマージされた新しい辞書。

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

単一・複数いずれの設定も扱える設定マネージャーです。
シングルモード（`multi=False`）では 1 つの設定を、マルチモード（`multi=True`）では名前付きの複数の設定を保持します。
内部処理はスレッドセーフです。

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

- `settings_cls` (`type[T]`): 管理対象の `BaseSettings` サブクラス。
- `multi` (`bool`): `True` で複数の名前付き設定を扱うマルチモードになります。

##### `settings_cls`

```python
settings_cls: type[T]
```

管理対象の設定クラス。

##### `multi`

```python
multi: bool
```

マルチモードかどうか。

##### `all_settings`

```python
@property
def all_settings(self) -> dict[str, T]: ...
```

すべてのキーに対する設定インスタンスのコピーを返します。

##### `settings`

```python
@property
def settings(self) -> T: ...
```

現在アクティブな設定インスタンスを返します。
マルチモードでは `active_key`、未設定の場合は `default` キーで解決されます。

**Raises**

- `ValueError`: 解決されたキーが設定マップに存在しない場合。

##### `user_config`

```python
@property
def user_config(self) -> dict[str, Any]: ...
@user_config.setter
def user_config(self, value: dict[str, Any]) -> None: ...
```

ユーザー設定を取得・設定します。
シングルモードでは設定フィールドの辞書、マルチモードでは `{"default": ..., "configs": {...}, "aliases": {...}}` 形式（[`UserConfig`](#userconfig) 参照）になります。

**Raises**

- `ValueError`: マルチモードで未知のキーが含まれる、`configs` が無い、またはエイリアス・デフォルトキーの解決先が存在しない場合。
- `TypeError`: マルチモードで `configs`・`aliases`・`default` の型が不正な場合。

##### `active_key`

```python
@property
def active_key(self) -> SettingsKey | None: ...
@active_key.setter
def active_key(self, key: SettingsKey | None) -> None: ...
```

マルチモードでアクティブにする設定キーを取得・設定します。

**Raises**

- `ValueError`: シングルモードで呼び出した場合。

##### `cli_args`

```python
@property
def cli_args(self) -> dict[str, Any]: ...
@cli_args.setter
def cli_args(self, value: dict[str, Any]) -> None: ...
```

設定に対して最優先で適用される CLI 引数の辞書を取得・設定します。

##### `set_cli_args`

```python
def set_cli_args(self, target: str, value: Any) -> None: ...
```

CLI 引数を 1 件設定します。`target` にドット区切りのパスを渡すと、ネストしたキーを設定できます。

**Parameters**

- `target` (`str`): 設定先のキー。ドット区切りでネストを指定できます（例: `"nested.value"`）。
- `value` (`Any`): 設定する値。

**Raises**

- `ValueError`: `target` のパスの途中が辞書でない場合。

##### `get_settings`

```python
def get_settings(self, key: SettingsKey | None = None) -> T: ...
```

設定インスタンスを取得します。マルチモードでは `key` を指定して任意の設定を取得できます。
`key` を省略した場合は [`settings`](#settings) と同じ結果を返します。

**Parameters**

- `key` (`SettingsKey | None`): 取得する設定のキー（エイリアス可）。

**Returns**

- `T`: 解決されたキーに対応する設定インスタンス。

**Raises**

- `ValueError`: シングルモードで `key` を指定した場合、または解決されたキーが存在しない場合。

##### `reset_user_config`

```python
def reset_user_config(self) -> None: ...
```

ユーザー設定・エイリアス・デフォルトキー・アクティブキーをすべて初期状態に戻します。

##### `clear`

```python
def clear(self) -> None: ...
```

内部キャッシュを無効化し、次回アクセス時に設定を再構築させます。

#### `UserConfig`

```python
type UserConfig = SingleUserConfig | MultiUserConfig

type SingleUserConfig = dict[str, Any]

class MultiUserConfig(TypedDict):
    configs: dict[str, dict[str, Any]]
    default: NotRequired[str | None]
    aliases: NotRequired[dict[str, str]]
```

単一・複数いずれかのモードのユーザー設定を表す型エイリアスです。
シングルモードでは設定フィールドの辞書、マルチモードでは `configs`・`default`・`aliases` を持つ辞書になります。

**Fields**(`MultiUserConfig`)

- `configs` (`dict[str, dict[str, Any]]`): 設定名から、その設定フィールドの辞書へのマッピング。
- `default` (`NotRequired[str | None]`): キー未指定時に使うデフォルトの設定名。
- `aliases` (`NotRequired[dict[str, str]]`): エイリアス名から実際の設定名へのマッピング。

#### `UserConfigs`

```python
type UserConfigs = dict[ModuleName, UserConfig]
```

モジュール名から、そのモジュールの [`UserConfig`](#userconfig) へのマッピングです。

#### `ConfigUpdatePolicy`

```python
type ConfigUpdatePolicy = Literal["replace", "merge"]
```

既存の設定マネージャーへ設定を適用する際の挙動。`"replace"` は置き換え、`"merge"` は深いマージです。

#### `MissingModulePolicy`

```python
type MissingModulePolicy = Literal["error", "warn", "ignore"]
```

設定対象のモジュールが存在しない場合の挙動。`"error"` は例外、`"warn"` は警告して継続、`"ignore"` は無視して継続です。

#### `ModuleName`

```python
type ModuleName = str
```

設定ヘルパーが扱う、完全修飾のモジュール名。

#### `SettingsKey`

```python
type SettingsKey = str
```

設定マネージャーのキー。

#### `DEFAULT_KEY`

```python
DEFAULT_KEY: str = "default"
```

シングルモードで内部的に使用されるデフォルトキー。
