from pathlib import Path
import pytest

from copilot_app.persistence import database
from copilot_app.persistence.repository import UserRepository, SystemInfoRepository

DB = Path("/Users/bong/VSCode/copilot/copilot.db")


@pytest.fixture(autouse=True)
def setup_db():
    # ensure a clean db for each test
    if DB.exists():
        DB.unlink()
    database.init_db()
    yield
    if DB.exists():
        DB.unlink()


def test_create_and_list_user():
    ur = UserRepository()
    u = ur.create_user("Shawn")
    assert u.id is not None
    users = ur.list_users()
    assert any(x.name == "Shawn" for x in users)


def test_save_and_get_system_info():
    sr = SystemInfoRepository()
    info = sr.save_system_info("Darwin", "20.6.0")
    assert info.id is not None
    latest = sr.get_latest_system_info()
    assert latest is not None
    assert latest.os == "Darwin"
