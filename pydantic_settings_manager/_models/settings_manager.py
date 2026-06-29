from __future__ import annotations

import threading
from typing import Any

from pydantic_settings import BaseSettings

from .._constants.default_key import DEFAULT_KEY
from .._types.settings_key import SettingsKey
from .._utils.update_dict import update_dict


class SettingsManager[T: BaseSettings]:
    """
    A unified settings manager that can handle both single and multiple configurations.

    This manager internally uses a map-based approach for consistency, where:
    - For single mode (multi=False): uses a default key DEFAULT_KEY
    - For multi mode (multi=True): allows multiple named configurations
    """

    def __init__(self, settings_cls: type[T], *, multi: bool = False):
        self.settings_cls: type[T] = settings_cls
        self.multi: bool = multi
        self._user_config: dict[str, dict[str, Any]] = {}
        self._aliases: dict[str, str] = {}
        self._default_key: str | None = None
        self._active_key: SettingsKey | None = None
        self._cli_args: dict[str, Any] = {}
        self._cache: dict[str, T] = {}
        self._cache_valid: bool = False
        self._lock: threading.RLock = threading.RLock()

    @property
    def all_settings(self) -> dict[str, T]:
        with self._lock:
            self._ensure_cache()
            return self._cache.copy()

    @property
    def settings(self) -> T:
        with self._lock:
            self._ensure_cache()

            if not self.multi:
                return self._cache[DEFAULT_KEY]

            target_key = self._active_key if self._active_key is not None else self._default_key

            if target_key is None:
                target_key = DEFAULT_KEY

            resolved_key = self._resolve_alias(target_key)

            if resolved_key not in self._cache:
                if target_key != resolved_key:
                    raise ValueError(
                        f"Key '{target_key}' (resolved to '{resolved_key}') "
                        f"does not exist in settings map"
                    )
                raise ValueError(f"Key '{target_key}' does not exist in settings map")

            return self._cache[resolved_key]

    @property
    def user_config(self) -> dict[str, Any]:
        import copy

        with self._lock:
            if self.multi:
                result: dict[str, Any] = {"configs": copy.deepcopy(self._user_config)}
                if self._default_key is not None:
                    result["default"] = self._default_key
                if self._aliases:
                    result["aliases"] = copy.deepcopy(self._aliases)
                return result

            return copy.deepcopy(self._user_config.get(DEFAULT_KEY, {}))

    @user_config.setter
    def user_config(self, value: dict[str, Any]) -> None:
        with self._lock:
            if self.multi:
                allowed_multi_keys = {"default", "configs", "aliases"}
                unknown_keys = set(value) - allowed_multi_keys
                if unknown_keys:
                    raise ValueError(
                        f"Invalid multi configuration keys: {sorted(unknown_keys)}. "
                        "Allowed keys are: default, configs, aliases."
                    )

                if "configs" not in value:
                    raise ValueError(
                        "Multi configuration requires `configs`. "
                        "Use {'default': ..., 'configs': {...}, 'aliases': {...}}."
                    )

                configs = value["configs"]
                if not isinstance(configs, dict):
                    raise TypeError("`configs` must be a dictionary.")

                normalized_configs: dict[str, dict[str, Any]] = {}
                for key, config in configs.items():
                    if not isinstance(key, str):
                        raise TypeError("All config names in `configs` must be strings.")
                    if not isinstance(config, dict):
                        raise TypeError(f"Config '{key}' must be a dictionary.")
                    normalized_configs[key] = dict(config)

                aliases_value = value.get("aliases", {})
                if aliases_value is None:
                    aliases_value = {}

                if not isinstance(aliases_value, dict):
                    raise TypeError("`aliases` must be a dictionary.")

                aliases: dict[str, str] = {}
                for alias, target in aliases_value.items():
                    if not isinstance(alias, str) or not isinstance(target, str):
                        raise TypeError("All alias names and targets must be strings.")
                    aliases[alias] = target

                default = value.get("default", None)
                if default is not None and not isinstance(default, str):
                    raise TypeError("`default` must be a string or None.")

                self._user_config = normalized_configs
                self._aliases = aliases
                self._default_key = default
                self._active_key = None
                self._validate_aliases()
                self._validate_default_key()

            else:
                self._user_config[DEFAULT_KEY] = dict(value)

            self._cache_valid = False

    def _validate_aliases(self) -> None:
        for alias in self._aliases:
            resolved = self._resolve_alias(alias)
            if resolved not in self._user_config:
                raise ValueError(
                    f"Alias '{alias}' resolved to '{resolved}', but it does not exist in `configs`."
                )

    def _validate_default_key(self) -> None:
        if self._default_key is None:
            return

        resolved = self._resolve_alias(self._default_key)
        if resolved not in self._user_config:
            raise ValueError(
                f"Default configuration '{self._default_key}' "
                f"resolved to '{resolved}', but it does not exist in `configs`."
            )

    @property
    def active_key(self) -> SettingsKey | None:
        if not self.multi:
            raise ValueError("Getting active_key is only available in multi mode")

        with self._lock:
            return self._active_key

    @active_key.setter
    def active_key(self, key: SettingsKey | None) -> None:
        if not self.multi:
            raise ValueError("Setting active_key is only available in multi mode")

        with self._lock:
            self._active_key = key

    @property
    def cli_args(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._cli_args)

    @cli_args.setter
    def cli_args(self, value: dict[str, Any]) -> None:
        with self._lock:
            self._cli_args = dict(value)
            self._cache_valid = False

    def set_cli_args(self, target: str, value: Any) -> None:
        with self._lock:
            keys = target.split(".")
            d = self._cli_args

            for key in keys[:-1]:
                if not isinstance(d, dict):
                    raise ValueError(f"Invalid target path: {target}")

                d = d.setdefault(key, {})

            d[keys[-1]] = value
            self._cache_valid = False

    def get_settings(self, key: SettingsKey | None = None) -> T:
        if not self.multi:
            if key:
                raise ValueError("Getting settings by key is only available in multi mode")

            return self.settings

        if not key:
            return self.settings

        with self._lock:
            self._ensure_cache()

            resolved_key = self._resolve_alias(key)

            if resolved_key not in self._cache:
                if key != resolved_key:
                    raise ValueError(
                        f"Key '{key}' (resolved to '{resolved_key}') does not exist in settings map"
                    )
                raise ValueError(f"Key '{key}' does not exist in settings map")

            return self._cache[resolved_key]

    def reset_user_config(self) -> None:
        with self._lock:
            self._user_config = {}
            self._aliases = {}
            self._default_key = None
            self._active_key = None
            self._cache_valid = False

    def clear(self) -> None:
        with self._lock:
            self._cache_valid = False

    def _resolve_alias(self, key: str, *, _chain: list[str] | None = None) -> str:
        if not self._aliases:
            return key

        if _chain is None:
            _chain = []

        if key in _chain:
            chain = " -> ".join([*_chain, key])
            raise ValueError(f"Circular alias reference detected: {chain}")

        if key not in self._aliases:
            return key

        return self._resolve_alias(self._aliases[key], _chain=[*_chain, key])

    def _ensure_cache(self) -> None:
        if not self._cache_valid:
            self._rebuild_cache()

    def _rebuild_cache(self) -> None:
        if self.multi:
            self._cache = {}

            for key, user_config in self._user_config.items():
                if isinstance(user_config, dict):
                    self._cache[key] = self.settings_cls(**update_dict(user_config, self._cli_args))

            if self._default_key is None and DEFAULT_KEY not in self._cache:
                self._cache[DEFAULT_KEY] = self.settings_cls(**self._cli_args)

        else:
            self._cache = {
                DEFAULT_KEY: self.settings_cls(
                    **update_dict(self._user_config.get(DEFAULT_KEY, {}), self._cli_args)
                )
            }

        self._cache_valid = True
