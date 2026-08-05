class AppError(Exception):
    """Base application exception."""


class CommandNotFoundError(AppError):
    """Raised when an unknown command is requested."""
    def __init__(self, command: str):
        super().__init__(f"Command not found: {command}")
        self.command = command


class RateLimitExceededError(AppError):
    """Raised when a rate limit blocks an operation."""
    def __init__(self, identifier: str):
        super().__init__(f"Rate limit exceeded for: {identifier}")
        self.identifier = identifier


class CircuitOpenError(AppError):
    """Raised when a circuit breaker blocks a call."""
    def __init__(self, service_name: str):
        super().__init__(f"Circuit is open for: {service_name}")
        self.service_name = service_name


class BulkheadRejectedError(AppError):
    """Raised when a bulkhead rejects an incoming request."""

    def __init__(self, service_name: str):
        super().__init__(f"Bulkhead rejected call for: {service_name}")
        self.service_name = service_name
