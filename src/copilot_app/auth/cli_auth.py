import getpass
import logging
from typing import Any

from .service import AuthService

logger = logging.getLogger(__name__)


def _auth_service(app_context: dict[str, Any] | None = None) -> AuthService:
    if app_context is not None and "auth_service" in app_context:
        return app_context["auth_service"]
    return AuthService()


def register_user(username: str, app_context: dict[str, Any] | None = None) -> str:
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    if password != confirm_password:
        raise ValueError("Passwords do not match")
    service = _auth_service(app_context)
    user = service.register_user(username, password)
    logger.info("CLI registered user %s", username)
    return f"Registered user {user.username} with id={user.id}"


def login(username: str, app_context: dict[str, Any] | None = None) -> str:
    password = getpass.getpass("Password: ")
    service = _auth_service(app_context)
    session = service.authenticate(username, password)
    logger.info("CLI login successful for %s", username)
    return session.token


def whoami(token: str, app_context: dict[str, Any] | None = None) -> str:
    service = _auth_service(app_context)
    user = service.validate_token(token)
    if user is None:
        raise ValueError("Unauthorized")
    return f"id={user.id}, username={user.username}, active={user.is_active}"
