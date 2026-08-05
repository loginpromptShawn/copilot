from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from .policies import CircuitPolicy, CircuitState
from ..core.errors import CircuitOpenError

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, policy: CircuitPolicy | None = None) -> None:
        self.policy = policy or CircuitPolicy()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_attempts = 0
        self._lock = threading.RLock()

    def can_pass(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if now - self.last_failure_time >= self.policy.recovery_timeout:
                    logger.info("Circuit breaker transitioning OPEN -> HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_attempts < self.policy.half_open_max_calls:
                    return True
                logger.warning("Circuit breaker blocking call in HALF_OPEN after max attempts")
                return False
            return False

    def record_success(self) -> None:
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_attempts += 1
                logger.info(
                    "Circuit breaker HALF_OPEN success count=%s/%s",
                    self.half_open_attempts,
                    self.policy.half_open_max_calls,
                )
                if self.half_open_attempts >= self.policy.half_open_max_calls:
                    self._transition_to_closed()
            else:
                if self.failure_count > 0:
                    self.failure_count = 0
                    logger.debug("Circuit breaker reset failure count after success")

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.warning(
                "Circuit breaker recorded failure count=%s/%s",
                self.failure_count,
                self.policy.failure_threshold,
            )
            if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.policy.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self) -> None:
        self.state = CircuitState.OPEN
        self.half_open_attempts = 0
        logger.warning(
            "Circuit breaker transitioning to OPEN; failure_count=%s, recovery_timeout=%s",
            self.failure_count,
            self.policy.recovery_timeout,
        )

    def _transition_to_closed(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0
        self.last_failure_time = 0.0
        logger.info("Circuit breaker transitioning to CLOSED")

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not self.can_pass():
            logger.warning("Circuit breaker blocked a call while in %s state", self.state)
            raise CircuitOpenError("service")

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result
