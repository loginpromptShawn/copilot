import logging
import time
from typing import Optional

from ..persistence.database import get_connection
from ..utils.config import get_config
from .models import AuthUser, AuthSession
from .tokens import generate_token, hash_password, token_expiry, verify_password

logger = logging.getLogger(__name__)


class AuthRepository:
    def create_user(self, username: str, password_hash: str, is_active: bool = True) -> AuthUser:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (name, username, password_hash, is_active) VALUES (?, ?, ?, ?)",
                (username, username, password_hash, int(is_active)),
            )
            conn.commit()
            user_id = cur.lastrowid
            return AuthUser(id=user_id, username=username, password_hash=password_hash, is_active=is_active)
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[AuthUser]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password_hash, is_active FROM users WHERE username = ? LIMIT 1",
                (username,),
            )
            row = cur.fetchone()
            if row:
                return AuthUser(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    is_active=bool(row["is_active"]),
                )
            return None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password_hash, is_active FROM users WHERE id = ? LIMIT 1",
                (user_id,),
            )
            row = cur.fetchone()
            if row:
                return AuthUser(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    is_active=bool(row["is_active"]),
                )
            return None
        finally:
            conn.close()

    def create_session(self, user_id: int, token: str, expires_at: float) -> AuthSession:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO auth_sessions (user_id, token, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (user_id, token, time.time(), expires_at),
            )
            conn.commit()
            session_id = cur.lastrowid
            return AuthSession(
                id=session_id,
                user_id=user_id,
                token=token,
                created_at=time.time(),
                expires_at=expires_at,
            )
        finally:
            conn.close()

    def get_session(self, token: str) -> Optional[AuthSession]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, user_id, token, created_at, expires_at FROM auth_sessions WHERE token = ? LIMIT 1",
                (token,),
            )
            row = cur.fetchone()
            if row:
                return AuthSession(
                    id=row["id"],
                    user_id=row["user_id"],
                    token=row["token"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                )
            return None
        finally:
            conn.close()

    def revoke_session(self, token: str) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()


class AuthService:
    def __init__(self) -> None:
        self.config = get_config()
        self.token_expiry_hours = self.config.getint("auth", "token_expiry_hours", fallback=8)
        self.password_hash_algorithm = self.config.get("auth", "password_hash_algorithm", fallback="sha256")

    def register_user(self, username: str, password: str) -> AuthUser:
        repo = AuthRepository()
        if repo.get_user_by_username(username) is not None:
            logger.warning("Attempted to register duplicate username: %s", username)
            raise ValueError("User already exists")
        password_hash = hash_password(password, algorithm=self.password_hash_algorithm)
        user = repo.create_user(username=username, password_hash=password_hash, is_active=True)
        logger.info("Registered user %s", username)
        return user

    def authenticate(self, username: str, password: str) -> AuthSession:
        repo = AuthRepository()
        user = repo.get_user_by_username(username)
        if user is None or not user.is_active:
            logger.warning("Authentication failed for username: %s", username)
            raise ValueError("Invalid credentials")
        if not verify_password(password, user.password_hash, algorithm=self.password_hash_algorithm):
            logger.warning("Authentication failed for username: %s", username)
            raise ValueError("Invalid credentials")
        token = generate_token()
        expires_at = token_expiry(self.token_expiry_hours)
        session = repo.create_session(user.id, token, expires_at)
        logger.info("Authentication successful for username: %s", username)
        return session

    def validate_token(self, token: str) -> Optional[AuthUser]:
        repo = AuthRepository()
        session = repo.get_session(token)
        if session is None:
            logger.debug("Token validation failed: session not found")
            return None
        if session.expires_at < time.time():
            logger.info("Token validation failed: token expired for session %s", session.id)
            return None
        user = repo.get_user_by_id(session.user_id)
        if user is None or not user.is_active:
            logger.info("Token validation failed: inactive or missing user for session %s", session.id)
            return None
        return user

    def revoke_session(self, token: str) -> None:
        repo = AuthRepository()
        repo.revoke_session(token)
        logger.info("Revoked auth session for token")
