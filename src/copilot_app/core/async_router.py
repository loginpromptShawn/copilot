from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any

from ..cli.registry import CommandRegistry

logger = logging.getLogger(__name__)


class AsyncRouter:
    async def run_command(self, command_name: str, *args: str, app_context: dict | None = None) -> str:
        metadata = CommandRegistry.get(command_name)
        if metadata is None:
            logger.error("Unknown async command: %s", command_name)
            raise SystemExit(f"Unknown command: {command_name}")

        handler = metadata.handler
        if metadata.is_async:
            signature = inspect.signature(handler)
            if "app_context" not in signature.parameters:
                logger.error(
                    "Async command '%s' handler '%s' does not accept app_context",
                    command_name,
                    handler.__name__,
                )
                raise RuntimeError(
                    f"Async handler for '{command_name}' must accept app_context"
                )

        # if coroutine function, await it and pass app_context
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, app_context=app_context)

        # else run in thread to avoid blocking event loop
        return await asyncio.to_thread(lambda: handler(*args, **({} if app_context is None else {"app_context": app_context})))
