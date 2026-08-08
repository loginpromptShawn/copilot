import asyncio
import pytest

from copilot_app.core.async_router import AsyncRouter
from copilot_app.cli.registry import CommandRegistry, Command
from copilot_app.services.async_user_service import greet_user as async_greet_user
from copilot_app.services.async_system_service import get_system_info as async_get_system_info


async def _async_handler(name: str, app_context=None) -> str:
    return f"hello {name}"


async def _async_no_app_context(name: str) -> str:
    return f"hi {name}"


def _sync_handler(name: str, app_context=None) -> str:
    return f"hey {name}"


def _run(router, command_name, *args, app_context=None):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(router.run_command(command_name, *args, app_context=app_context))
    finally:
        loop.close()


def unit_async_router_runs_async_command():
    router = AsyncRouter()
    cmd = Command("test-async", "desc", _async_handler, is_async=True)
    CommandRegistry.initialize()
    original = CommandRegistry._commands.get("test-async")
    CommandRegistry._commands["test-async"] = cmd
    try:
        result = _run(router, "test-async", "world", app_context={})
        assert result == "hello world"
    finally:
        if original is None:
            CommandRegistry._commands.pop("test-async", None)
        else:
            CommandRegistry._commands["test-async"] = original


def unit_async_router_runs_sync_command_in_thread():
    router = AsyncRouter()
    cmd = Command("test-sync", "desc", _sync_handler, is_async=False)
    CommandRegistry.initialize()
    original = CommandRegistry._commands.get("test-sync")
    CommandRegistry._commands["test-sync"] = cmd
    try:
        result = _run(router, "test-sync", "world", app_context={})
        assert result == "hey world"
    finally:
        if original is None:
            CommandRegistry._commands.pop("test-sync", None)
        else:
            CommandRegistry._commands["test-sync"] = original


def unit_async_router_unknown_command():
    router = AsyncRouter()
    with pytest.raises(SystemExit):
        _run(router, "missing-cmd")


class _ExpectSystemExit(Exception):
    pass


def _expect_system_exit():
    # helper context manager-ish via pytest.raises not available here; inline try/except instead
    import contextlib

    @contextlib.contextmanager
    def ctx():
        try:
            yield
        except SystemExit:
            return
        raise AssertionError("SystemExit not raised")

    return ctx()


def unit_async_router_validates_app_context_parameter():
    router = AsyncRouter()
    cmd = Command("test-bad", "desc", _async_no_app_context, is_async=True)
    CommandRegistry.initialize()
    original = CommandRegistry._commands.get("test-bad")
    CommandRegistry._commands["test-bad"] = cmd
    try:
        with pytest.raises(RuntimeError, match="must accept app_context"):
            _run(router, "test-bad", app_context={})
    finally:
        if original is None:
            CommandRegistry._commands.pop("test-bad", None)
        else:
            CommandRegistry._commands["test-bad"] = original
