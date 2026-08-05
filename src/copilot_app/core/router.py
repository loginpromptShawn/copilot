from typing import Callable, Dict, Optional
import inspect
import asyncio

from ..cli import commands as cmd_mod
from ..cli.router import get_auth_command_handler
from ..core.errors import CommandNotFoundError
from .async_router import AsyncRouter


COMMAND_MAP: Dict[str, Callable[..., str]] = {cmd.name: cmd.handler for cmd in cmd_mod.COMMANDS}


def run_command(command: str, args: list[str], app_context: Optional[dict] = None) -> str:
    # if command not known, allow CLI auth router fallback
    cmd_obj = next((c for c in cmd_mod.COMMANDS if c.name == command), None)
    if cmd_obj is None:
        handler = get_auth_command_handler(command)
        if handler is None:
            raise CommandNotFoundError(command)
        cmd_obj = None
    else:
        handler = COMMAND_MAP[command]

    # if async command, delegate to AsyncRouter and run in event loop
    if cmd_obj is not None and getattr(cmd_obj, "is_async", False):
        return asyncio.run(AsyncRouter().run_command(command, *args, app_context=app_context))

    # if handler expects app_context, pass it as a keyword arg
    try:
        sig = inspect.signature(handler)
        if "app_context" in sig.parameters:
            return handler(*args, app_context=app_context)
    except Exception:
        pass

    return handler(*args)
