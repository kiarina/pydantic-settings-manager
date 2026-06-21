# AGENTS.md

このリポジトリで作業するエージェント向けのガイドラインです。

## 作業前に読むもの

あらゆるタスクを開始する前に、下記を必ず把握してください。
- `pyproject.toml`
- `README.md`
- `mise-tasks/`
- `Makefile`
- `pydantic_settings_manager/`

リリースする際は、作業前に下記を把握してください。
- docs/how_to_release.md

## README の運用

- `README.md` と `README.ja.md` は、言語違いの完全なミラーとして維持してください。
- 対応箇所を見出しで追いやすくするため、`README.ja.md` の `#`, `##`, `###`, `####` などの見出しは `README.md` と同じ英語に必ず一致させてください。

## 変更後の確認

コードを変更した場合は、`make` を実行して、build が通るか確認してください。

```bash
make
```
