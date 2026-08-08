from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Tuple

from ..tracing import tracer as tracer_module
from ..tracing.span import Span

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_attempts: int
    backoff_strategy: str
    base_delay: float
    max_delay: float
    retry_on_exceptions: tuple[type[BaseException], ...] = (Exception,)


class RetryExecutor:
    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy

    def _sleep_for_attempt(self, attempt: int) -> None:
        if self.policy.backoff_strategy == "fixed":
            delay = self.policy.base_delay
        elif self.policy.backoff_strategy == "exponential":
            delay = self.policy.base_delay * (2 ** attempt)
        elif self.policy.backoff_strategy == "jitter":
            delay = self.policy.base_delay * (2 ** attempt) + random.uniform(0, self.policy.base_delay)
        else:
            delay = self.policy.base_delay

        if delay > self.policy.max_delay:
            delay = self.policy.max_delay
        logger.debug("Retry attempt %s sleeping for %.3fs", attempt, delay)
        time.sleep(delay)

    def execute(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        tracer = tracer_module.global_tracer
        policy = self.policy
        last_exception: BaseException | None = None

        for attempt in range(1, policy.max_attempts + 1):
            span: Span | None = None
            if tracer is not None:
                try:
                    span = tracer.start_span(f"retry.attempt:{attempt}")
                except Exception:
                    span = None

            try:
                logger.info("RetryExecutor attempt %s/%s", attempt, policy.max_attempts)
                result = fn(*args, **kwargs)
                logger.info("RetryExecutor succeeded on attempt %s", attempt)
                return result
            except Exception as exc:
                last_exception = exc
                if not isinstance(exc, policy.retry_on_exceptions):
                    logger.warning("Exception not retryable: %s", type(exc).__name__)
                    raise
                logger.warning(
                    "RetryExecutor caught %s on attempt %s/%s",
                    type(exc).__name__,
                    attempt,
                    policy.max_attempts,
                )
                if attempt == policy.max_attempts:
                    logger.error("RetryExecutor exhausted attempts after %s", attempt)
                    raise
                self._sleep_for_attempt(attempt)
            finally:
                if tracer is not None and span is not None:
                    try:
                        tracer.finish_span(span)
                    except Exception:
                        pass

        assert last_exception is not None
        raise last_exception
