from __future__ import annotations

from copilot_app.core.app import App
from copilot_app.cli.registry import CommandRegistry


def load_cli_environment(quiet=False) -> App:
    import logging

    # QUIET MODE MUST BE APPLIED BEFORE App() IS CREATED
    if quiet:
        # Remove ALL existing handlers so init_logging() can't re-enable INFO output
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Replace with a silent handler
        silent = logging.NullHandler()
        logging.root.addHandler(silent)

        # Set root logger to WARNING
        logging.getLogger().setLevel(logging.WARNING)
    # Ensures all CLI modules are imported once
    # Ensures registry is populated
    # Ensures app_context is available
    app = App()
    CommandRegistry.initialize()
    CommandRegistry.populate_default_commands()
    return app
