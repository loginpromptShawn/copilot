from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitPolicy:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    def __post_init__(self) -> None:
        logger.info(
            "CircuitPolicy configured: failure_threshold=%s, recovery_timeout=%s, half_open_max_calls=%s",
            self.failure_threshold,
            self.recovery_timeout,
            self.half_open_max_calls,
        )
