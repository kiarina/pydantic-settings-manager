---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Describe the bug
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:

```python
# Minimal reproducible example
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

class MySettings(BaseSettings):
    name: str = "default"
    value: int = 0

manager = SettingsManager(MySettings)
# Your code here that demonstrates the bug
```

## Expected behavior
A clear and concise description of what you expected to happen.

## Actual behavior
What actually happened.

## Environment
- pydantic-settings-manager version: [e.g., 2.2.0]
- Python version: [e.g., 3.12.0]
- pydantic version: [e.g., 2.10.0]
- pydantic-settings version: [e.g., 2.7.0]
- OS: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]

## Additional context
Add any other context about the problem here.

## Logs/Output
```
Paste relevant logs or error messages here
```
