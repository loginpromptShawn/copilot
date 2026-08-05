import argparse
import sys
import asyncio

from ..core.app import App
from ..core.errors import CommandNotFoundError
from ..core.async_router import AsyncRouter
from .commands import COMMANDS


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="copilot",
        description="macOS-friendly modular Copilot CLI tool.",
    )
    parser.add_argument("--version", action="store_true", help="print version information")
    parser.add_argument("command", nargs="?", help="command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="arguments for the command")
    return parser


def main(argv=None) -> int:
    app = App()
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.version:
        print("copilot 0.1.0 (macOS modular CLI)")
        return 0

    if args.command is None:
        parser.print_help()
        return 1

    command = args.command
    raw_args = args.args or []
    cmd_args = [arg for arg in raw_args if arg != "--"]
    cmd_obj = next((c for c in COMMANDS if c.name == command), None)
    if cmd_obj is None:
        print(f"Unknown command: {command}")
        return 1

    if getattr(cmd_obj, "is_async", False):
        result = asyncio.run(AsyncRouter().run_command(command, *cmd_args, app_context=app.app_context))
        print(result)
        return 0

    result = app.run(command, cmd_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
