"""CLI layer for copilot_app."""


def __getattr__(name):
    if name == "main":
        from .cli import main
        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["main"]
