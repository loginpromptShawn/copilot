from pathlib import Path

import pytest

from copilot_app.persistence.database import init_db
from copilot_app.services.user_service import greet_user
from copilot_app.services.system_service import get_system_info


@pytest.fixture(autouse=True)
def setup_db(temp_db):
    init_db()
    yield


def unit_greet_user():
    assert greet_user("Shawn") == f"Hello, Shawn from macOS! Your home directory is {Path.home()}."


def unit_get_system_info():
    output = get_system_info()
    assert "System:" in output
    assert f"Home: {Path.home()}" in output
