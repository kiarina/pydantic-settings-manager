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

TODO
