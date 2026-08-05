from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from ..core.errors import AppError

logger = logging.getLogger(__name__)


class BulkheadRejectedError(AppError):
    def __init__(self, name: str):
        super().__init__(f"Bulkhead rejected call for: {name}")
        self.name = name


@dataclass
class Bulkhead:
    name: str
    max_concurrent: int
    queue_size: int

    def __post_init__(self) -> None:
        self._semaphore = threading.Semaphore(self.max_concurrent)
        self._queue: deque[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = deque()
        # Use a re-entrant lock because _run_next may be called
        # recursively from _execute_thread while the lock is held.
        self._lock = threading.RLock()
        self._active = 0

    def current_concurrency(self) -> int:
        with self._lock:
            return self._active

    def queued_requests(self) -> int:
        with self._lock:
            return len(self._queue)

    def _run_next(self) -> None:
        with self._lock:
            if self._queue and self._semaphore.acquire(blocking=False):
                fn, args, kwargs = self._queue.popleft()
                self._active += 1
                logger.info("Bulkhead %s dequeued a request; active=%s queued=%s", self.name, self._active, len(self._queue))
                threading.Thread(target=self._execute_thread, args=(fn, args, kwargs), daemon=True).start()
            elif self._queue:
                self._queue.appendleft((fn, args, kwargs))

    def _execute_thread(self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        try:
            fn(*args, **kwargs)
        finally:
            with self._lock:
                self._active -= 1
                self._semaphore.release()
                logger.info("Bulkhead %s completed a request; active=%s queued=%s", self.name, self._active, len(self._queue))
                if self._queue:
                    self._run_next()

    def execute(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        wrapper_event: threading.Event | None = None
        result: dict[str, Any] = {}

        def wrapper() -> None:
            try:
                result["value"] = fn(*args, **kwargs)
            except Exception as exc:
                result["error"] = exc
            finally:
                if wrapper_event is not None:
                    wrapper_event.set()

        with self._lock:
            if self._semaphore.acquire(blocking=False):
                self._active += 1
                logger.info("Bulkhead %s accepted request; active=%s queued=%s", self.name, self._active, len(self._queue))
                run_direct = True
            elif len(self._queue) < self.queue_size:
                wrapper_event = threading.Event()
                self._queue.append((wrapper, (), {}))
                logger.info("Bulkhead %s queued request; active=%s queued=%s", self.name, self._active, len(self._queue))
                run_direct = False
            else:
                logger.warning("Bulkhead %s rejected request because queue is full", self.name)
                raise BulkheadRejectedError(self.name)

        if not run_direct:
            wrapper_event.wait()
            if "error" in result:
                raise result["error"]
            return result.get("value")

        try:
            return fn(*args, **kwargs)
        finally:
            with self._lock:
                self._active -= 1
                self._semaphore.release()
                logger.info("Bulkhead %s released slot; active=%s queued=%s", self.name, self._active, len(self._queue))
                if self._queue:
                    self._run_next()

    def _wait_for_result(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        # retained for compatibility, but not used by execute directly.
        return fn(*args, **kwargs)
