# AGENTS.md

このリポジトリで作業するエージェント向けのガイドラインです。

## 作業前に読むもの

あらゆるタスクを開始する前に、下記を必ず把握してください。
- `pyproject.toml`
- `README.md`
- `.mise/tasks/`
- `Makefile`
- `pydantic_settings_manager/`

コードの設計・追加・編集を行う場合、下記も先に把握してください。
- https://github.com/kiarina/crystal-architecture

リリースする際は、作業前に下記を把握してください。
- docs/how_to_release.md

## README の運用

- `README.md` と `README.ja.md` は、言語違いの完全なミラーとして維持してください。
- 対応箇所を見出しで追いやすくするため、`README.ja.md` の `#`, `##`, `###`, `####` などの見出しは `README.md` と同じ英語に必ず一致させてください。

## 変更後の確認

コードを修正した場合は、commit 前に `CHANGELOG.md` の `Unreleased` セクションに変更内容を追記してください。

コードを変更した場合は、`make` を実行して、build が通るか確認してください。

```bash
make
```

## テスト方針

- **フレームワーク**: `pytest` を使用します。
- **配置場所**: `tests/` ディレクトリ以下に配置します。
- **構造**: `pydantic_settings_manager/` ディレクトリの構造をそのままミラーリングします。
  - 例: `pydantic_settings_manager/_helpers/load_user_configs.py` のテストは `tests/_helpers/test_load_user_configs.py` に配置します。
- **特定のユースケースのテスト**: `tests/use_cases/` ディレクトリを作成し、特定のユースケースに対するテストコードを配置します。
  - 例: `tests/use_cases/test_thread_safety.py`
- **命名規則**:
  - 各ディレクトリには `__init__.py` を配置し、同名のテストファイル（例: `test_common.py`）が衝突しないようにします。
  - テストコードはクラス（`unittest.TestCase`）ではなく、関数（`def test_...():`）ベースで記述します。
- **実行方法**: `make test`
