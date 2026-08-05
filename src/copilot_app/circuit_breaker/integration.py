from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from .breaker import CircuitBreaker
from .policies import CircuitPolicy
from ..core.errors import CircuitOpenError

logger = logging.getLogger(__name__)

_BREAKERS: Dict[str, CircuitBreaker] = {}


def get_breaker_for_service(service_name: str) -> CircuitBreaker:
    if service_name not in _BREAKERS:
        _BREAKERS[service_name] = CircuitBreaker(policy=CircuitPolicy())
        logger.info("Created circuit breaker for service: %s", service_name)
    return _BREAKERS[service_name]


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    return dict(_BREAKERS)


def reset_breakers() -> None:
    _BREAKERS.clear()
    logger.info("Circuit breaker registry reset")


def wrap_service_call(service_name: str, operation: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    breaker = get_breaker_for_service(service_name)
    logger.debug("Wrapping service call %s.%s with circuit breaker %s", service_name, operation, breaker.state)
    try:
        return breaker.call(fn, *args, **kwargs)
    except CircuitOpenError:
        logger.warning("Circuit open for service %s during %s", service_name, operation)
        raise CircuitOpenError(service_name)
