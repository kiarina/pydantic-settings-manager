from typing import Literal

type MissingModulePolicy = Literal["error", "warn", "ignore"]
"""Behavior when a configured module does not exist."""
