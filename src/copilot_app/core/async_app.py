from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..utils.config import get_config
from ..utils.logging_setup import init_logging
from ..persistence.database import init_db
from .router import run_command
from ..plugins.plugin_manager import PluginManager


class AsyncApp:
    """Async version of App using asyncio."""

    def __init__(self) -> None:
        # synchronous init pieces are still done here
        init_logging()
        init_db()
        self.config = get_config()
        self.plugin_manager = PluginManager()
        self.app_context: dict[str, Any] = {"app": self, "config": self.config, "plugin_manager": self.plugin_manager}

    async def init(self) -> None:
        # load plugins synchronously, then activate asynchronously
        self.plugin_manager.load_plugins()
        # plugins may perform blocking work; run activation in thread pool
        await asyncio.to_thread(self.plugin_manager.activate_all, self.app_context)
        logging.info("AsyncApp initialized with config: %s", dict(self.config.items("app")))

    async def run(self, command: str, args: list[str]) -> int:
        logging.info("Running async command: %s %s", command, args)
        try:
            # delegate to async router if needed
            from .async_router import AsyncRouter

            result = await AsyncRouter().run_command(command, *args, app_context=self.app_context)
            print(result)
            return 0
        except Exception as exc:
            logging.error("Async command execution failed: %s", exc)
            print(f"Error: {exc}")
            return 1
