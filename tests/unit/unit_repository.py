import pytest

from copilot_app.persistence.database import init_db
from copilot_app.persistence.repository import UserRepository, SystemInfoRepository


@pytest.fixture(autouse=True)
def setup_db(temp_db):
    init_db()
    yield


def unit_create_and_list_user():
    ur = UserRepository()
    u = ur.create_user("Shawn")
    assert u.id is not None
    users = ur.list_users()
    assert any(x.name == "Shawn" for x in users)


def unit_save_and_get_system_info():
    sr = SystemInfoRepository()
    info = sr.save_system_info("Darwin", "20.6.0")
    assert info.id is not None
    latest = sr.get_latest_system_info()
    assert latest is not None
    assert latest.os == "Darwin"
