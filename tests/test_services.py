from copilot_app.services.user_service import greet_user
from copilot_app.services.system_service import get_system_info


def test_greet_user():
    assert greet_user("Shawn") == "Hello, Shawn from macOS! Your home directory is /Users/bong." 


def test_get_system_info():
    output = get_system_info()
    assert "System:" in output
    assert "Home: /Users/bong" in output
