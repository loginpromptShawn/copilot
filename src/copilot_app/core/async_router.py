from __future__ import annotations

import asyncio
import inspect
from typing import Any

from ..cli import commands as cmd_mod


class AsyncRouter:
    async def run_command(self, command_name: str, *args: str, app_context: dict | None = None) -> str:
        # find handler
        handler = None
        for c in cmd_mod.COMMANDS:
            if c.name == command_name:
                handler = c.handler
                break
        if handler is None:
            raise RuntimeError(f"Command not found: {command_name}")

        # if coroutine function, await it
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, app_context=app_context)

        # else run in thread to avoid blocking event loop
        return await asyncio.to_thread(lambda: handler(*args, **({} if app_context is None else {"app_context": app_context})))
