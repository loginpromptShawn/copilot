from typing import Callable, Dict, Optional
import inspect
import asyncio

from ..cli import commands as cmd_mod
from ..core.errors import CommandNotFoundError
from .async_router import AsyncRouter


COMMAND_MAP: Dict[str, Callable[..., str]] = {cmd.name: cmd.handler for cmd in cmd_mod.COMMANDS}


def run_command(command: str, args: list[str], app_context: Optional[dict] = None) -> str:
    # if command not known
    cmd_obj = next((c for c in cmd_mod.COMMANDS if c.name == command), None)
    if cmd_obj is None:
        raise CommandNotFoundError(command)

    # if async command, delegate to AsyncRouter and run in event loop
    if getattr(cmd_obj, "is_async", False):
        return asyncio.run(AsyncRouter().run_command(command, *args, app_context=app_context))

    handler = COMMAND_MAP[command]
    # if handler expects app_context, pass it as a keyword arg
    try:
        sig = inspect.signature(handler)
        if "app_context" in sig.parameters:
            return handler(*args, app_context=app_context)
    except Exception:
        # fall back to calling without app_context
        pass

    return handler(*args)
