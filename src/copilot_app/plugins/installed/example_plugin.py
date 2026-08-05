import logging

from ..base_plugin import BasePlugin


logger = logging.getLogger(__name__)


class ExamplePlugin(BasePlugin):
    name = "example"
    version = "1.0"
    description = "Example plugin for macOS Copilot project"

    def __init__(self) -> None:
        super().__init__()
        self.activated = False

    def activate(self, app_context: dict) -> None:
        self.activated = True
        logger.info("ExamplePlugin activated with app: %s", app_context.get("app"))

    def deactivate(self) -> None:
        self.activated = False
        logger.info("ExamplePlugin deactivated")
