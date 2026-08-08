"""Allow running the package as a module: python -m copilot_app."""

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())