import sys
import argparse
import asyncio

from copilot_app.core.errors import CommandNotFoundError
from copilot_app.core.async_router import AsyncRouter
from copilot_app.cli.bootstrap import load_cli_environment
from copilot_app.cli.registry import CommandRegistry


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
    # --- QUIET FLAG HANDLING (must come first) ---
    quiet = False
    if argv and "--quiet" in argv:
        quiet = True
        argv = [a for a in argv if a != "--quiet"]
    # ------------------------------------------------

    parser = create_parser()
    args = parser.parse_args(argv)

    if args.version:
        print("copilot 0.1.0 (macOS CLI)")
        return 0

    if args.command is None:
        parser.print_help()
        return 1

    # Lazy app initialization: only boot the full app when a real command is given
    app = load_cli_environment(quiet=quiet)

    command = args.command
    raw_args = args.args or []
    cmd_args = [arg for arg in raw_args if arg != "--"]

    cmd_obj = CommandRegistry.get(command)
    if cmd_obj is None:
        print(f"Unknown command: {command}")
        return 1

    if getattr(cmd_obj, "is_async", False):
        result = asyncio.run(
            AsyncRouter().run_command(command, *cmd_args, app_context=app.app_context)
        )
        print(result)
        return 0

    result = app.run(command, cmd_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
