from dataclasses import dataclass


@dataclass
class AuthUser:
    id: int
    username: str
    password_hash: str
    is_active: bool = True


@dataclass
class AuthSession:
    id: int
    user_id: int
    token: str
    created_at: float
    expires_at: float
