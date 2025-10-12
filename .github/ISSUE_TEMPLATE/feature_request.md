---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Is your feature request related to a problem? Please describe.
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

## Describe the solution you'd like
A clear and concise description of what you want to happen.

## Describe alternatives you've considered
A clear and concise description of any alternative solutions or features you've considered.

## Use case
Describe your use case and how this feature would help you.

```python
# Example of how you'd like to use this feature
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

class MySettings(BaseSettings):
    name: str = "default"
    value: int = 0

manager = SettingsManager(MySettings)
# Your desired usage
```

## Additional context
Add any other context or screenshots about the feature request here.
