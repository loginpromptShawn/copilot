import pytest

from copilot_app.core.router import run_command
from copilot_app.core.errors import CommandNotFoundError
from copilot_app.persistence.database import init_db


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_run_command_greet():
    result = run_command("greet", ["Shawn"])
    assert "Hello, Shawn from macOS" in result


def test_run_command_sysinfo():
    result = run_command("sysinfo", [])
    assert "System:" in result


def test_run_command_not_found():
    with pytest.raises(CommandNotFoundError):
        run_command("unknown", [])
