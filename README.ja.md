# pydantic-settings-manager

言語: [English](README.md) | [日本語](README.ja.md)

[![PyPI](https://img.shields.io/pypi/v/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![Python](https://img.shields.io/pypi/pyversions/pydantic-settings-manager.svg)](https://pypi.org/project/pydantic-settings-manager/)
[![CI](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/kiarina/pydantic-settings-manager/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/kiarina/pydantic-settings-manager/branch/main/graph/badge.svg)](https://codecov.io/gh/kiarina/pydantic-settings-manager)
[![License](https://img.shields.io/pypi/l/pydantic-settings-manager.svg)](https://github.com/kiarina/pydantic-settings-manager/blob/main/LICENSE)

複数の設定と実行時の上書きに対応した、Pydantic settings 向けのモダンでスレッドセーフな管理ライブラリです。

## Features

- **Bootstrap パターン**: 複数モジュールのアプリケーション向けに設定読み込みを一元化
- **統一 API**: 単一の `SettingsManager` クラスで、シンプルな設定と複雑な設定の両方を扱える
- **スレッドセーフ**: 並行実行されるアプリケーション向けのスレッド安全性を内蔵
- **型安全**: 完全な型ヒントと Pydantic バリデーション
- **柔軟**: 単一設定にも、名前付きの複数設定にも対応
- **実行時の上書き**: コマンドライン引数や動的な設定変更に対応
- **移行しやすい**: 設定ファイルや環境変数からの移行が簡単

## Table of Contents

- [pydantic-settings-manager](#pydantic-settings-manager)
  - [Features](#features)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
    - [Single Module (Simple Projects)](#single-module-simple-projects)
    - [Runtime Overrides](#runtime-overrides)
  - [Bootstrap Pattern (Recommended for Production)](#bootstrap-pattern-recommended-for-production)
    - [Why Bootstrap Pattern?](#why-bootstrap-pattern)
    - [Project Structure](#project-structure)
    - [Quick Example](#quick-example)
    - [Configuration File Structure](#configuration-file-structure)
    - [User Configuration Templates](#user-configuration-templates)
    - [Custom Manager Names](#custom-manager-names)
    - [Frequently Asked Questions](#frequently-asked-questions)
  - [Multiple Configurations](#multiple-configurations)
  - [Migration Guide (v2.x to v3.0.0)](#migration-guide-v2x-to-v300)
    - [Configuration Aliases](#configuration-aliases)
  - [Advanced Usage](#advanced-usage)
    - [Thread Safety](#thread-safety)
    - [Dynamic Configuration Updates](#dynamic-configuration-updates)
  - [CLI Integration](#cli-integration)
  - [Related Tools](#related-tools)
    - [pydantic-config-builder](#pydantic-config-builder)
  - [Development](#development)
    - [Quick Start](#quick-start-1)
    - [Common Tasks](#common-tasks)
    - [Technology Stack](#technology-stack)
  - [API Reference](#api-reference)
    - [SettingsManager](#settingsmanager)
      - [Parameters](#parameters)
      - [Properties](#properties)
      - [Methods](#methods)
    - [Helper Functions](#helper-functions)
  - [Migration from v2 to v3](#migration-from-v2-to-v3)
    - [Direct format migration](#direct-format-migration)
    - [Old structured format migration](#old-structured-format-migration)
    - [`get_settings_by_key()` migration](#get_settings_by_key-migration)
  - [License](#license)
  - [Contributing](#contributing)
  - [Documentation](#documentation)

## Installation

```bash
pip install pydantic-settings-manager
```

## Quick Start

### Single Module (Simple Projects)

```python
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

# 1. 設定を定義する
class AppSettings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    max_connections: int = 100

# 2. settings manager を作成する
manager = SettingsManager(AppSettings)

# 3. 設定を読み込む
manager.user_config = {
    "app_name": "ProductionApp",
    "debug": False,
    "max_connections": 500
}

# 4. 設定を使う
settings = manager.settings
print(f"App: {settings.app_name}")  # Output: App: ProductionApp
```

### Runtime Overrides

```python
# 実行時に設定を上書きする（例: コマンドラインから）
manager.cli_args = {"debug": True, "max_connections": 50}

settings = manager.settings
print(f"Debug: {settings.debug}")  # Output: Debug: True
print(f"Connections: {settings.max_connections}")  # Output: Connections: 50
```

## Bootstrap Pattern (Recommended for Production)

**複数モジュールのアプリケーションでは、`load_user_configs()` を使った bootstrap パターンを使ってください。** 本番アプリケーションではこの方法を推奨します。

### Why Bootstrap Pattern?

- **設定の一元化**: すべてのモジュール設定を 1 つの設定ファイルから読み込める
- **自動検出**: 各モジュールを手動で import して設定する必要がない
- **環境管理**: development、staging、production の切り替えが簡単
- **関心の分離**: 設定ファイルをアプリケーションコードから分離できる

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
│   ├── base.yaml                 # 共通設定
│   ├── development.yaml          # 開発環境の上書き
│   └── production.yaml           # 本番環境の上書き
├── bootstrap.py                  # Bootstrap ロジック
└── main.py                       # アプリケーションのエントリポイント
```

### Quick Example

```python
# 1. 各モジュールで設定を定義する
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
# config/base.yaml（すべての環境で共有）
settings.app:
  name: "MyApp"

modules.auth.settings:
  token_expiry: 3600

modules.billing.settings:
  currency: "USD"

# config/production.yaml（本番固有の上書き）
settings.app:
  debug: false
  secret_key: "${SECRET_KEY}"

modules.auth.settings:
  jwt_secret: "${JWT_SECRET}"

modules.billing.settings:
  stripe_api_key: "${STRIPE_API_KEY}"
```

```python
# bootstrap.py - 推奨実装
import os
import yaml
from pathlib import Path
from pydantic_settings_manager import load_user_configs, update_dict

def bootstrap(environment: str | None = None) -> None:
    """
    環境ごとの設定で、すべての settings manager を bootstrap する。

    Args:
        environment: 環境名（例: "development", "production"）。
                    None の場合は ENVIRONMENT 環境変数を使い、
                    未設定なら "development" を使う。
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    config_dir = Path("config")

    # 基本設定を読み込む（任意）
    base_file = config_dir / "base.yaml"
    if base_file.exists():
        with open(base_file) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # 環境ごとの設定を読み込む
    env_file = config_dir / f"{environment}.yaml"
    if env_file.exists():
        with open(env_file) as f:
            env_config = yaml.safe_load(f) or {}
            # 設定を deep merge する（環境設定が base を上書き）
            config = update_dict(config, env_config)

    # この 1 行で、すべての settings manager を設定できる
    load_user_configs(config)

    print(f"✓ Loaded configuration for '{environment}' environment")

# main.py
from bootstrap import bootstrap
from settings.app import settings_manager as app_settings_manager
from modules.auth.settings import settings_manager as auth_settings_manager
from modules.billing.settings import settings_manager as billing_settings_manager

def main():
    # 1 行ですべての設定を bootstrap する
    bootstrap("production")

    # すべての設定は構成済みで、すぐ使える
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

設定ファイルの構造は、モジュール構造に直接対応します。

```yaml
# Key = モジュールパス（例: "settings.app" → settings/app.py）
# Value = そのモジュールの settings manager に渡す設定

settings.app:
  name: "MyApp-Production"
  debug: false
  secret_key: "${SECRET_KEY}"  # Pydantic が環境変数から読み込む

modules.auth.settings:
  jwt_secret: "${JWT_SECRET}"
  token_expiry: 3600

modules.billing.settings:
  currency: "USD"
  stripe_api_key: "${STRIPE_API_KEY}"
```

### User Configuration Templates

`generate_user_configs_yaml()` を使うと、既存の settings manager から `user_settings.yaml` の雛形を生成できます。

```python
from pydantic_settings_manager import generate_user_configs_yaml

yaml_text = generate_user_configs_yaml(
    [
        "settings.app",
        "modules.auth.settings",
        "modules.billing.settings",
    ]
)
```

同じ雛形はコマンドラインからも生成できます。

```bash
pydantic-settings-manager generate-user-configs \
  settings.app \
  modules.auth.settings \
  modules.billing.settings \
  > user_settings.yaml
```

デフォルト値を持つフィールドはコメントアウトされ、必須フィールドは有効な状態で出力されます。

```yaml
# Settings for the application
settings.app:
  # Application Name
  # app_name: MyApp
  #--------------------------------------------------
  # Secret Key
  secret_key:
```

`SettingsManager(..., multi=True)` の場合、生成される雛形は構造化された multi configuration 形式になります。

```yaml
# Settings for the application
settings.app:
  # default: default
  configs:
    default:
      # Application Name
      # app_name: MyApp
      #--------------------------------------------------
      # Secret Key
      secret_key:
  # aliases: {}
```

private な settings module segment は、生成される設定 key から省略されます。たとえば、`hoge.fuga._settings` と `hoge.fuga._fire.settings` はどちらも `hoge.fuga` を生成します。

### Custom Manager Names

デフォルトでは、`load_user_configs()` は各モジュール内の `settings_manager` を探します。名前はカスタマイズできます。

```python
# settings/app.py
app_manager = SettingsManager(AppSettings)  # カスタム名

# bootstrap.py
load_user_configs(config, manager_name="app_manager")
```

template generator CLI でもカスタム manager 名を指定できます。

```bash
pydantic-settings-manager generate-user-configs --manager-name app_manager settings.app
```

### Frequently Asked Questions

**Q: bootstrap パターンに `multi=True` は必要ですか？**

A: いいえ。bootstrap パターンは single mode と multi mode の両方で動作します。
- **Single mode**（推奨）: モジュールごとに 1 つの設定
- **Multi mode**: モジュールごとに複数の設定（例: 同じ manager 内に dev/staging/prod）

```python
# Single mode（よりシンプルで、多くのケースで推奨）
settings_manager = SettingsManager(AppSettings)

# Multi mode（モジュールごとに複数設定が必要な場合）
settings_manager = SettingsManager(AppSettings, multi=True)
```

**Q: `${SECRET_KEY}` のような環境変数はどのように扱われますか？**

A: Pydantic Settings が環境変数から自動的に読み込みます。YAML 内の `${VAR}` 構文はドキュメント用途です。任意の値を指定できます。

```yaml
# config/production.yaml
settings.app:
  secret_key: "placeholder"  # SECRET_KEY 環境変数で上書きされる
```

環境変数が設定されている場合、Pydantic は `os.getenv("SECRET_KEY")` を自動的に使います。

**Q: `load_user_configs` ではなく手動設定を使うべきなのはいつですか？**

A: モジュール固有のロジックが必要な場合だけです。
- モジュールごとのカスタムバリデーション
- モジュール状態に応じた条件付き設定
- 動的なモジュール検出

99% のケースでは `load_user_configs()` を使ってください。

**Q: 単一モジュールでも bootstrap パターンを使えますか？**

A: はい。ただし過剰です。単一モジュールのプロジェクトでは、次のように使うだけで十分です。

```python
manager = SettingsManager(AppSettings)
manager.user_config = yaml.safe_load(open("config.yaml"))
```

## Multiple Configurations

環境やコンテキストごとに異なる設定が必要なアプリケーション向けです。

```python
# 複数設定モードを有効にする
manager = SettingsManager(AppSettings, multi=True)

# 複数環境を設定する（構造化形式）
manager.user_config = {
    "default": "production",
    "configs": {
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
    },
    "aliases": {
        "dev": "development",
        "prod": "production",
    }
}

# default が production なので、settings は production を返す
settings = manager.settings
print(f"Prod: {settings.app_name}, Debug: {settings.debug}")

# 設定を動的に切り替える
manager.active_key = "development"
dev_settings = manager.settings
print(f"Dev: {dev_settings.app_name}, Debug: {dev_settings.debug}")

# alias で特定の設定を取得する
dev_settings = manager.get_settings("dev")
print(f"Dev alias: {dev_settings.app_name}, Debug: {dev_settings.debug}")

# すべての設定を取得する
all_settings = manager.all_settings
for env, settings in all_settings.items():
    print(f"{env}: {settings.app_name}")
```

- `default` は、`active_key` が未設定のときに `manager.settings` が使う設定を選びます。`active_key` も `default` も明示的に設定されていない場合、`manager.settings` は自動的に `"default"` という設定キーにフォールバックします。
- `configs` には名前付き設定を入れます。各エントリは Pydantic Settings クラスに渡されます。
- `aliases` は別名を実際の設定名へマッピングします。alias は別の alias を指すこともできますが、循環参照は拒否されます。

## Migration Guide (v2.x to v3.0.0)

古い `user_config` 辞書形式（環境ごとのフラットな辞書）を使っていた場合、その形式は非推奨です。上記の構造化形式へ移行してください。

**旧形式（非推奨）:**
```python
manager.user_config = {
    "development": {...},
    "production": {...}
}
```

**新形式（v3.0+）:**
設定を `configs` キーの中へ移動するだけです。
```python
manager.user_config = {
    "configs": {
        "development": {...},
        "production": {...}
    }
}
```

### Configuration Aliases

multi mode では、同じ設定を別のキーで参照する alias を定義できます。次のような場合に便利です。
- **短い名前**: `dev` → `development`、`prod` → `production`
- **サービス固有のキー**: 複数サービスで同じ環境設定を共有する
- **移行**: 新しいキー名へ移行しながら、古いキー名を維持する

```python
manager = SettingsManager(AppSettings, multi=True)

# 構造化形式で alias を定義する
manager.user_config = {
    "default": "development",
    "aliases": {
        # 短い名前
        "dev": "development",
        "stg": "staging",
        "prod": "production",

        # サービス固有の alias（同じ環境を共有）
        "account_service": "staging",
        "data_service": "staging",
        "analytics_service": "staging",

        # 多段 alias（alias の alias）
        "d": "dev",  # d → dev → development
    },
    "configs": {
        "development": {
            "app_name": "MyApp-Dev",
            "debug": True,
            "max_connections": 10
        },
        "staging": {
            "app_name": "MyApp-Staging",
            "debug": False,
            "max_connections": 50
        },
        "production": {
            "app_name": "MyApp-Prod",
            "debug": False,
            "max_connections": 1000
        }
    }
}

# これらはすべて同じ設定を返す
dev_settings = manager.get_settings("development")
dev_settings = manager.get_settings("dev")
dev_settings = manager.get_settings("d")

# サービス固有のキーはすべて staging に解決される
account_settings = manager.get_settings("account_service")
data_settings = manager.get_settings("data_service")
# どちらも同じ staging 設定を返す
```

**YAML 設定例:**

```yaml
# config/production.yaml
settings.app:
  default: production
  aliases:
    # 便利な短い名前
    dev: development
    stg: staging
    prod: production

    # サービス固有の alias
    account_service: staging
    data_service: staging

  configs:
    development:
      app_name: "MyApp-Dev"
      debug: true
      max_connections: 10
    staging:
      app_name: "MyApp-Staging"
      debug: false
      max_connections: 50
    production:
      app_name: "MyApp-Prod"
      debug: false
      max_connections: 1000
```

**メリット:**
- **DRY 原則**: 同じ設定値の重複を避けられる
- **柔軟性**: コードを変えずに、あとから設定を分割しやすい
- **明確さ**: コードでは説明的な名前を使い、設定ファイルは簡潔に保てる

## Advanced Usage

### Thread Safety

`SettingsManager` は完全にスレッドセーフで、マルチスレッドアプリケーションでも利用できます。

```python
import threading
from concurrent.futures import ThreadPoolExecutor

manager = SettingsManager(AppSettings, multi=True)
manager.user_config = {
    "default": "worker1",
    "configs": {
        "worker1": {"app_name": "Worker1", "max_connections": 10},
        "worker2": {"app_name": "Worker2", "max_connections": 20}
    }
}

def worker_function(worker_id: int):
    # 各スレッドは安全に設定を切り替えられる
    manager.active_key = f"worker{worker_id}"
    settings = manager.settings
    print(f"Worker {worker_id}: {settings.app_name}")

# 複数 worker を並行実行する
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(worker_function, i) for i in range(1, 3)]
    for future in futures:
        future.result()
```

### Dynamic Configuration Updates

```python
# 個別の CLI 引数を更新する
manager.set_cli_args("debug", True)
manager.set_cli_args("nested.value", "test")  # ネストしたキーに対応

# CLI args 全体を更新する
manager.cli_args = {"debug": False, "max_connections": 200}

# key を指定して設定を取得する（multi mode）
dev_settings = manager.get_settings("development")
prod_settings = manager.get_settings("production")
```

## CLI Integration

コマンドラインツールと連携して、実行時に設定できます。

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

    # environment を指定して bootstrap する
    bootstrap_settings(environment)

    # CLI の上書きを適用する
    cli_overrides = {}
    if debug is not None:
        cli_overrides["debug"] = debug
    if max_connections is not None:
        cli_overrides["max_connections"] = max_connections

    if cli_overrides:
        app_settings_manager.cli_args = cli_overrides

    # アプリケーションを実行する
    settings = app_settings_manager.settings
    print(f"Running {settings.name} in {environment} mode")
    print(f"Debug: {settings.debug}")

if __name__ == "__main__":
    main()
```

使い方:
```bash
# デフォルト設定で実行
python cli.py

# production で debug を有効にして実行
python cli.py --environment production --debug

# 特定の設定を上書き
python cli.py --max-connections 500
```

## Related Tools

### pydantic-config-builder

複数の設定ファイルを持つ複雑なプロジェクトでは、YAML 設定ファイルのマージとビルドに [`pydantic-config-builder`](https://github.com/kiarina/pydantic-config-builder) を使うと便利です。

```bash
pip install pydantic-config-builder
```

このツールでできること:
- 複数の YAML ファイルを 1 つの設定へマージ
- base 設定と overlay ファイルの利用
- 環境ごとに異なる設定のビルド
- glob パターンと再帰的マージのサポート

ワークフロー例:
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

生成された設定を settings manager で使います。
```python
import yaml
from your_app import settings_manager

# ビルド済み設定を読み込む
with open("config/dev.yaml") as f:
    config = yaml.safe_load(f)

settings_manager.user_config = config
```

## Development

このプロジェクトでは、開発環境の管理に [mise](https://mise.jdx.dev/) を使っています。

### Quick Start

```bash
# mise をインストールする（macOS）
brew install mise

# clone してセットアップする
git clone https://github.com/kiarina/pydantic-settings-manager.git
cd pydantic-settings-manager
mise run setup

# すべてが動くことを確認する
mise run ci
```

### Common Tasks

```bash
# 日々の開発（自動修正 + test）
mise run

# commit 前（フル CI チェック）
mise run ci

# test を実行
mise run test
mise run test -v          # verbose
mise run test -c          # coverage 付き

# コード品質
mise run format           # format code
mise run lint             # check issues
mise run lint-fix         # auto-fix issues
mise run typecheck        # type check

# 依存関係
mise run upgrade          # upgrade dependencies
mise run upgrade --sync   # upgrade and sync

# release（詳細は docs/how_to_release.md を参照）
mise run version 2.3.0
mise run update-changelog 2.3.0
mise run ci
git add . && git commit -m "chore: release v2.3.0"
git tag v2.3.0 && git push origin main --tags
```

### Technology Stack

- **[mise](https://mise.jdx.dev/)**: 開発環境とタスクランナー
- **[uv](https://github.com/astral-sh/uv)**: 高速な Python パッケージマネージャ
- **[ruff](https://github.com/astral-sh/ruff)**: 高速な linter / formatter
- **[mypy](https://mypy-lang.org/)**: 静的型チェック
- **[pytest](https://pytest.org/)**: テストフレームワーク

詳しいドキュメント:
- 利用できるタスク: `mise tasks`
- リリース手順: `docs/how_to_release.md`

## API Reference

### SettingsManager

Pydantic settings を管理するメインクラスです。

```python
class SettingsManager(Generic[T]):
    def __init__(self, settings_cls: type[T], *, multi: bool = False)
```

#### Parameters
- `settings_cls`: 管理対象の Pydantic settings クラス
- `multi`: 複数設定モードを有効にするかどうか（デフォルト: False）

#### Properties
- `settings: T` - 現在有効な設定を取得する
- `all_settings: dict[str, T]` - すべての設定を取得する（multi mode）
- `user_config: dict[str, Any]` - ユーザー設定を取得・設定する
- `cli_args: dict[str, Any]` - CLI 引数を取得・設定する
- `active_key: str | None` - 有効な key を取得・設定する（multi mode のみ）

#### Methods
- `get_settings(key: str | None = None) -> T` - key または現在有効な設定を取得する
- `clear() -> None` - キャッシュ済み設定をクリアする
- `set_cli_args(target: str, value: Any) -> None` - 個別の CLI 引数を設定する
- `reset_user_config() -> None` - ユーザー設定と状態を空にリセットする

### Helper Functions

- `load_user_configs(user_configs, *, manager_name="settings_manager", policy="replace") -> None` - settings manager にユーザー設定を読み込む
- `clear_user_configs(user_configs, *, manager_name="settings_manager") -> None` - settings manager からユーザー設定をクリアする
- `generate_user_configs_yaml(import_paths, *, manager_name="settings_manager") -> str` - settings manager から YAML の雛形を生成する

## Migration from v2 to v3

### Direct format migration

変更前:
```python
manager.user_config = {
    "development": {...},
    "production": {...},
}
```

変更後:
```python
manager.user_config = {
    "default": "production",
    "configs": {
        "development": {...},
        "production": {...},
    },
}
```

### Old structured format migration

変更前:
```python
manager.user_config = {
    "key": "production",
    "map": {
        "development": {...},
        "production": {...},
    },
}
```

変更後:
```python
manager.user_config = {
    "default": "production",
    "configs": {
        "development": {...},
        "production": {...},
    },
}
```

### `get_settings_by_key()` migration

変更前:
```python
settings = manager.get_settings_by_key("production")
```

変更後:
```python
settings = manager.get_settings("production")
```

## License

このプロジェクトは MIT License のもとで公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## Contributing

コントリビューションを歓迎します。ぜひ Pull Request を送ってください。

## Documentation

より詳しいドキュメントと例は、[GitHub repository](https://github.com/kiarina/pydantic-settings-manager) を参照してください。
