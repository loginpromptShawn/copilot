import time

import pytest

from copilot_app.circuit_breaker.breaker import CircuitBreaker
from copilot_app.circuit_breaker.integration import get_breaker_for_service, get_all_breakers, wrap_service_call
from copilot_app.circuit_breaker.policies import CircuitPolicy, CircuitState
from copilot_app.core.errors import CircuitOpenError


def integration_closed_to_open_transition():
    breaker = CircuitBreaker(policy=CircuitPolicy(failure_threshold=2, recovery_timeout=1.0, half_open_max_calls=1))

    def failing():
        raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    assert breaker.state == CircuitState.CLOSED

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count >= 2


def integration_open_to_half_open_after_timeout():
    breaker = CircuitBreaker(policy=CircuitPolicy(failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=1))

    def failing():
        raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    assert breaker.state == CircuitState.OPEN

    time.sleep(0.15)
    assert breaker.can_pass() is True
    assert breaker.state == CircuitState.HALF_OPEN


def integration_half_open_success_to_closed():
    breaker = CircuitBreaker(policy=CircuitPolicy(failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=1))

    def failing():
        raise RuntimeError("failure")

    def success():
        return "ok"

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    time.sleep(0.15)
    assert breaker.can_pass() is True
    assert breaker.state == CircuitState.HALF_OPEN

    assert breaker.call(success) == "ok"
    assert breaker.state == CircuitState.CLOSED


def integration_half_open_failure_returns_open():
    breaker = CircuitBreaker(policy=CircuitPolicy(failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=1))

    def failing():
        raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    time.sleep(0.15)
    assert breaker.can_pass() is True
    assert breaker.state == CircuitState.HALF_OPEN

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    assert breaker.state == CircuitState.OPEN


def integration_integration_with_wrap_service_call():
    service_name = "user-service"
    def success():
        return "hello"

    result = wrap_service_call(service_name, "greet_user", success)
    assert result == "hello"
    breakers = get_all_breakers()
    assert service_name in breakers


def integration_get_breaker_for_service_registry():
    breaker = get_breaker_for_service("system-service")
    assert breaker is get_breaker_for_service("system-service")
    assert breaker.state == CircuitState.CLOSED


def integration_circuit_open_error_raised_when_blocked():
    breaker = get_breaker_for_service("test-service")
    breaker.policy.failure_threshold = 1
    breaker.policy.recovery_timeout = 0.1

    def failing():
        raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    time.sleep(breaker.policy.recovery_timeout + 0.01)
    with pytest.raises(RuntimeError):
        breaker.call(failing)
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "ok")
