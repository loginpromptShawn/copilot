from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class UserCreatedEvent:
    user_id: int
    name: str
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class SystemInfoUpdatedEvent:
    os: str
    version: str
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class LogCleanupEvent:
    timestamp: str = field(default_factory=_now_iso)
