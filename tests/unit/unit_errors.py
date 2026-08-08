import pytest

from copilot_app.core.errors import (
    AppError,
    CommandNotFoundError,
    AuthError,
    RateLimitExceededError,
    CircuitOpenError,
    BulkheadRejectedError,
)


def unit_app_error_is_exception():
    with pytest.raises(AppError):
        raise AppError("base error")


def unit_command_not_found_error():
    err = CommandNotFoundError("start")
    assert "start" in str(err)
    assert err.command == "start"


def unit_auth_error():
    err = AuthError("invalid token")
    assert "invalid token" in str(err)


def unit_rate_limit_exceeded_error():
    err = RateLimitExceededError("user-123")
    assert "user-123" in str(err)
    assert err.identifier == "user-123"


def unit_circuit_open_error():
    err = CircuitOpenError("payment-service")
    assert "payment-service" in str(err)
    assert err.service_name == "payment-service"


def unit_bulkhead_rejected_error():
    err = BulkheadRejectedError("search-service")
    assert "search-service" in str(err)
    assert err.service_name == "search-service"


def unit_all_errors_are_app_errors():
    errors = [
        CommandNotFoundError("cmd"),
        AuthError("msg"),
        RateLimitExceededError("id"),
        CircuitOpenError("svc"),
        BulkheadRejectedError("svc"),
    ]
    for err in errors:
        assert isinstance(err, AppError)