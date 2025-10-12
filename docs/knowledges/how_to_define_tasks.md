---
title: How to Define Tasks
description: Tasks are defined as mise File Tasks.
---

Tasks are defined as mise File Tasks under `mise-tasks/`.

You can check the current list of tasks with `mise tasks`.

```sh
> mise tasks
Name               Description
build              Build package
ci                 Run CI checks (format, lint, typecheck, test, build)
clean              Clean build artifacts and cache files
default            Run format, lint-fix, typecheck, and test
extract-changelog  Extract changelog section for a specific version
format             Format
lint               Lint code (ruff check + format check)
lint-fix           Lint auto-fix (ruff check --fix)
publish            Publish package to PyPI
setup              Setup development environment
test               Run tests
typecheck          Type check with mypy
update-changelog   Update CHANGELOG.md with version entry
version            Update version in pyproject.toml
```
