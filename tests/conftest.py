import pytest

from copilot_app.persistence import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """Use a temporary database for every test to avoid touching the production DB."""
    original_db_path = database.DB_PATH
    database.DB_PATH = tmp_path / "test_copilot.db"
    yield
    database.DB_PATH = original_db_path