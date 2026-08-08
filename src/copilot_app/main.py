"""Application entry point for copilot_app."""

import sys


def main(argv: list[str] | None = None) -> int:
    """Main entry point that delegates to the CLI."""
    from copilot_app.cli import main as cli_main
    return cli_main(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
