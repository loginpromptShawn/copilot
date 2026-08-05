from __future__ import annotations

import logging
from typing import Any

from ..circuit_breaker.integration import get_breaker_for_service
from ..core.errors import CircuitOpenError
from ..rate_limit.rate_limiter import global_rate_limiter
from .bulkhead import Bulkhead, BulkheadRejectedError
from .retry import RetryExecutor, RetryPolicy
from ..utils.config import get_config

logger = logging.getLogger(__name__)

_RETRY_POLICIES: dict[str, RetryPolicy] = {}
_BULKHEADS: dict[str, Bulkhead] = {}


def _load_policy(service_name: str) -> RetryPolicy:
    config = get_config()
    section = f"resilience.{service_name.replace('-', '_')}"
    if not config.has_section(section):
        return RetryPolicy(max_attempts=1, backoff_strategy="fixed", base_delay=0.1, max_delay=0.5)
    return RetryPolicy(
        max_attempts=config.getint(section, "max_attempts", fallback=1),
        backoff_strategy=config.get(section, "backoff_strategy", fallback="fixed"),
        base_delay=config.getfloat(section, "base_delay", fallback=0.1),
        max_delay=config.getfloat(section, "max_delay", fallback=1.0),
    )


def _load_bulkhead(service_name: str) -> Bulkhead:
    config = get_config()
    section = f"resilience.{service_name.replace('-', '_')}"
    return Bulkhead(
        name=service_name,
        max_concurrent=config.getint(section, "max_concurrent", fallback=1),
        queue_size=config.getint(section, "queue_size", fallback=0),
    )


def get_retry_policy(service_name: str) -> RetryPolicy:
    if service_name not in _RETRY_POLICIES:
        _RETRY_POLICIES[service_name] = _load_policy(service_name)
        logger.info("Loaded retry policy for %s", service_name)
    return _RETRY_POLICIES[service_name]


def get_bulkhead(service_name: str) -> Bulkhead:
    if service_name not in _BULKHEADS:
        _BULKHEADS[service_name] = _load_bulkhead(service_name)
        logger.info("Loaded bulkhead for %s", service_name)
    return _BULKHEADS[service_name]


def resilient_call(service_name: str, operation: str, fn: callable, *args: Any, **kwargs: Any) -> Any:
    if global_rate_limiter is not None and not global_rate_limiter.allow_request(service_name):
        logger.warning("Resilient call blocked by rate limiter for %s", service_name)
        raise RuntimeError("Rate limit exceeded")

    breaker = get_breaker_for_service(service_name)
    if not breaker.can_pass():
        logger.warning("Resilient call fast-fail due to open circuit for %s", service_name)
        raise CircuitOpenError(service_name)

    bulkhead = get_bulkhead(service_name)
    policy = get_retry_policy(service_name)
    executor = RetryExecutor(policy)

    def inner() -> Any:
        return fn(*args, **kwargs)

    try:
        return bulkhead.execute(executor.execute, inner)
    except BulkheadRejectedError as exc:
        logger.error("Bulkhead rejection for service %s", service_name)
        raise
