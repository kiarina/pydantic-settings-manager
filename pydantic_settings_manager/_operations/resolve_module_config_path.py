from __future__ import annotations

import sys
from importlib import import_module

from .._models.settings_manager import SettingsManager


def resolve_module_config_path(
    manager: SettingsManager,
    *,
    manager_name: str = "settings_manager",
) -> str | None:
    """Resolve the shallowest public module path that re-exports ``manager``.

    Walks the dotted prefixes of the settings class' module (shallowest first)
    so a re-export at ``app`` wins over ``app.slack``. Falls back to scanning
    all imported modules when the settings class lives outside the manager's own
    package. Returns ``None`` when no module re-exports the manager.
    """
    module_name = getattr(manager.settings_cls, "__module__", None)
    if isinstance(module_name, str) and module_name:
        parts = module_name.split(".")
        for depth in range(1, len(parts) + 1):
            candidate = ".".join(parts[:depth])
            module = sys.modules.get(candidate)
            if module is None:
                try:
                    module = import_module(candidate)
                except Exception:
                    continue
            if getattr(module, manager_name, None) is manager:
                return candidate

    return _scan_imported_modules(manager, manager_name)


def _scan_imported_modules(manager: SettingsManager, manager_name: str) -> str | None:
    best: str | None = None
    for name, module in list(sys.modules.items()):
        if module is None or not name:
            continue
        try:
            value = getattr(module, manager_name, None)
        except Exception:
            continue
        if value is manager and (best is None or _path_rank(name) < _path_rank(best)):
            best = name
    return best


def _path_rank(name: str) -> tuple[int, int, str]:
    parts = name.split(".")
    private_segments = sum(1 for part in parts if part.startswith("_"))
    return (private_segments, len(parts), name)
