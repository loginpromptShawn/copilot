import time

import pytest
from fastapi.testclient import TestClient

from copilot_app.api.routes import app as api_app
from copilot_app.auth.service import AuthService
from copilot_app.auth.tokens import hash_password, verify_password, token_expiry
from copilot_app.core.errors import AuthError
from copilot_app.persistence.database import init_db


@pytest.fixture(autouse=True)
def setup_db(temp_db):
    init_db()
    yield


def integration_hash_and_verify_password():
    hashed = hash_password("MySecret123")
    assert verify_password("MySecret123", hashed) is True
    assert verify_password("WrongPass", hashed) is False


def integration_token_expiry_returns_future_timestamp():
    expiry = token_expiry(hours=1)
    assert expiry > time.time()


def integration_register_user_and_authenticate():
    auth_service = AuthService()
    user = auth_service.register_user("alice", "Password123")
    assert user.id is not None
    assert user.username == "alice"
    session = auth_service.authenticate("alice", "Password123")
    assert session.token
    assert session.expires_at > time.time()


def integration_validate_token_and_revoke_session():
    auth_service = AuthService()
    auth_service.register_user("bob", "Password123")
    session = auth_service.authenticate("bob", "Password123")
    user = auth_service.validate_token(session.token)
    assert user is not None
    assert user.username == "bob"
    auth_service.revoke_session(session.token)
    assert auth_service.validate_token(session.token) is None


def integration_protected_api_routes_require_token():
    client = TestClient(api_app)
    r = client.get("/users")
    assert r.status_code == 401
    assert r.json() == {"detail": "Unauthorized"}


def integration_auth_api_register_login_and_protected_route():
    client = TestClient(api_app)
    r = client.post("/auth/register", json={"username": "charlie", "password": "Secret123"})
    assert r.status_code == 200
    # Reset rate limiter to avoid 429 on subsequent requests in same test
    from copilot_app.rate_limit import rate_limiter as rl_module
    if rl_module.global_rate_limiter is not None:
        rl_module.global_rate_limiter._per_id.clear()
    r2 = client.post("/auth/login", json={"username": "charlie", "password": "Secret123"})
    assert r2.status_code == 200
    token = r2.json().get("token")
    assert token
    r3 = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
