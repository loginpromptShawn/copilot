from __future__ import annotations

import importlib.util
import inspect
import logging
from pathlib import Path
from types import ModuleType
from typing import Dict, Optional

from .base_plugin import BasePlugin


logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, installed_dir: Optional[Path] = None) -> None:
        # by default, look for plugins in the package's installed/ directory
        if installed_dir is None:
            base = Path(__file__).resolve().parents[1]
            installed_dir = base / "installed"

        self.installed_dir: Path = Path(installed_dir)
        self.active_plugins: Dict[str, BasePlugin] = {}

    def _iter_plugin_files(self):
        if not self.installed_dir.exists():
            return
        for p in sorted(self.installed_dir.iterdir()):
            if p.suffix == ".py" and p.name != "__init__.py":
                yield p

    def load_plugins(self) -> None:
        """Scan installed directory and load plugin modules."""
        for p in self._iter_plugin_files():
            try:
                name = p.stem
                # Load as part of the installed package so relative imports work
                package_name = "copilot_app.plugins.installed"
                module_name = f"{package_name}.{name}"
                spec = importlib.util.spec_from_file_location(module_name, str(p))
                if spec is None or spec.loader is None:
                    logger.warning("Could not load plugin spec: %s", p)
                    continue
                mod = importlib.util.module_from_spec(spec)
                mod.__package__ = package_name
                loader = spec.loader
                assert loader is not None
                loader.exec_module(mod)  # type: ignore[arg-type]
                self._register_from_module(mod)
            except Exception:
                logger.exception("Failed loading plugin: %s", p)

    def _register_from_module(self, module: ModuleType) -> None:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                try:
                    inst: BasePlugin = obj()
                    self.active_plugins[inst.name] = inst
                    logger.info("Registered plugin: %s", inst.name)
                except Exception:
                    logger.exception("Failed to instantiate plugin: %s", obj)

    def activate_all(self, app_context: dict) -> None:
        for plugin in list(self.active_plugins.values()):
            try:
                plugin.activate(app_context)
                logger.info("Activated plugin: %s", plugin.name)
            except Exception:
                logger.exception("Failed to activate plugin: %s", plugin.name)

    def deactivate_all(self) -> None:
        for plugin in list(self.active_plugins.values()):
            try:
                plugin.deactivate()
                logger.info("Deactivated plugin: %s", plugin.name)
            except Exception:
                logger.exception("Failed to deactivate plugin: %s", plugin.name)

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.active_plugins.get(name)
