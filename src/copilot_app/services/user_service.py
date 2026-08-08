from pathlib import Path

from ..persistence.repository import UserRepository
from ..events.event_types import UserCreatedEvent
from ..events.event_bus import global_event_bus
from ..events.distributed.distributed_event_bus import global_distributed_bus
from ..tracing.instrumentation import trace_function
from ..rate_limit.rate_limiter import global_rate_limiter
from ..core.errors import RateLimitExceededError
from ..circuit_breaker.integration import wrap_service_call


@trace_function("greet_user")
def greet_user(name: str) -> str:
    # rate limit check
    rl = global_rate_limiter
    if rl is not None and not rl.allow_request("greet_user"):
        raise RateLimitExceededError("greet_user")
    repo = UserRepository()
    user = repo.create_user(name)
    try:
        evt = UserCreatedEvent(user_id=user.id, name=user.name)
        global_event_bus.publish(evt)
        if global_distributed_bus is not None:
            try:
                global_distributed_bus.publish(evt)
            except Exception:
                pass
    except Exception:
        # don't fail on event publish
        pass
    return f"Hello, {user.name} from macOS! Your home directory is {Path.home()}."


def greet_user_mesh(name: str) -> str:
    from ..resilience.integration import resilient_call

    return resilient_call("user-service", "greet_user", greet_user, name)
