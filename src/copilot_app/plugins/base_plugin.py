from __future__ import annotations

import abc
from typing import Any


class BasePlugin(abc.ABC):
    """Abstract base class for plugins."""

    name: str
    version: str
    description: str

    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def activate(self, app_context: dict[str, Any]) -> None:
        """Called when the plugin is activated/loaded."""

    @abc.abstractmethod
    def deactivate(self) -> None:
        """Called when the plugin is deactivated/unloaded."""


class ExampleBasePlugin(BasePlugin):
    """A simple example plugin class for reference inside this module."""

    name = "example_base"
    version = "0.0"
    description = "Reference example plugin class inside base_plugin.py"

    def __init__(self) -> None:
        super().__init__()
        self.activated = False

    def activate(self, app_context: dict[str, Any]) -> None:
        self.activated = True

    def deactivate(self) -> None:
        self.activated = False
