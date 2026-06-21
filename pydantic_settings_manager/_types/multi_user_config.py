from typing import Any, NotRequired, TypedDict


class MultiUserConfig(TypedDict):
    """User configuration format for multi-configuration managers."""

    configs: dict[str, dict[str, Any]]
    default: NotRequired[str | None]
    aliases: NotRequired[dict[str, str]]
