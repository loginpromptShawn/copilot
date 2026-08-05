from __future__ import annotations

import threading
import time
import logging
from typing import Deque
from collections import deque

logger = logging.getLogger(__name__)


class TokenBucketStrategy:
    def __init__(self, capacity: int = 100, refill_rate: float = 1.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = capacity
        self._last = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last
        if elapsed <= 0:
            return
        refill = elapsed * self.refill_rate
        if refill > 0:
            self._tokens = min(self.capacity, self._tokens + refill)
            self._last = now

    def consume(self) -> bool:
        with self._lock:
            try:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    logger.debug("TokenBucket allow (tokens left=%.2f)", self._tokens)
                    return True
                logger.info("TokenBucket deny (tokens=%.2f)", self._tokens)
                return False
            except Exception:
                logger.exception("TokenBucket error")
                return False

    def clone(self) -> "TokenBucketStrategy":
        return TokenBucketStrategy(self.capacity, self.refill_rate)


class FixedWindowStrategy:
    def __init__(self, window_size: float = 60.0, max_requests: int = 100) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self._window_start = time.time()
        self._count = 0
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            now = time.time()
            if now - self._window_start >= self.window_size:
                self._window_start = now
                self._count = 0
            if self._count < self.max_requests:
                self._count += 1
                logger.debug("FixedWindow allow (%d/%d)", self._count, self.max_requests)
                return True
            logger.info("FixedWindow deny (%d/%d)", self._count, self.max_requests)
            return False

    def clone(self) -> "FixedWindowStrategy":
        return FixedWindowStrategy(self.window_size, self.max_requests)


class SlidingWindowStrategy:
    def __init__(self, window_size: float = 60.0, max_requests: int = 100) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self._timestamps: Deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            now = time.time()
            # evict old
            while self._timestamps and now - self._timestamps[0] > self.window_size:
                self._timestamps.popleft()
            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                logger.debug("SlidingWindow allow (%d/%d)", len(self._timestamps), self.max_requests)
                return True
            logger.info("SlidingWindow deny (%d/%d)", len(self._timestamps), self.max_requests)
            return False

    def clone(self) -> "SlidingWindowStrategy":
        return SlidingWindowStrategy(self.window_size, self.max_requests)
