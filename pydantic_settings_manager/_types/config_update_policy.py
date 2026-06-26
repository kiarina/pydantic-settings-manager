from typing import Literal

type ConfigUpdatePolicy = Literal["replace", "merge"]
"""Behavior when applying configuration to an existing settings manager."""
