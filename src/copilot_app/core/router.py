from typing import Callable, Optional
import inspect
import asyncio

from ..cli.registry import CommandRegistry
from ..cli.router import get_auth_command_handler
from ..core.errors import CommandNotFoundError
from .async_router import AsyncRouter


def run_command(command: str, args: list[str], app_context: Optional[dict] = None) -> str:
    # Use CommandRegistry as the single source of truth
    cmd_obj = CommandRegistry.get(command)
    if cmd_obj is None:
        handler = get_auth_command_handler(command)
        if handler is None:
            raise CommandNotFoundError(command)
        # Auth commands are sync; execute directly
        return handler(*args)
    else:
        handler = cmd_obj.handler

    # if async command, delegate to AsyncRouter and run in event loop
    if getattr(cmd_obj, "is_async", False):
        return asyncio.run(AsyncRouter().run_command(command, *args, app_context=app_context))

    # if handler expects app_context, pass it as a keyword arg
    try:
        sig = inspect.signature(handler)
        if "app_context" in sig.parameters:
            return handler(*args, app_context=app_context)
    except Exception:
        pass

    return handler(*args)
