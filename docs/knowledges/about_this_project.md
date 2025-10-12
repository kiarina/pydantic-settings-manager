---
title: About this project
description: >-
  Information about the pydantic-settings-manager project.
---

## Why

Pydantic Settings provides excellent configuration management, but lacks built-in support for:
- Managing multiple environment configurations (dev/staging/prod)
- Runtime configuration overrides (CLI arguments)
- Centralized configuration loading across multiple modules

This library fills these gaps with a unified, thread-safe settings manager.

## Design Philosophy

- **Simplicity First**: Single `SettingsManager` class handles both simple and complex use cases
- **Type Safety**: Full type hints and Pydantic validation throughout
- **Thread Safety**: Built-in locking for concurrent applications
- **Zero Magic**: Explicit configuration over implicit behavior
- **Bootstrap Pattern**: Centralized configuration loading for production applications

## Tech Stack

- language: Python 3.9+
- runtime management: mise
- dependency / environment management: uv
- code formatting: ruff
- linting: ruff
- typecheck: mypy
- testing: pytest
- task runner: mise (File Tasks)
