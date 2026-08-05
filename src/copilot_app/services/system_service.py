import platform

from ..persistence.repository import SystemInfoRepository
from ..events.event_types import SystemInfoUpdatedEvent
from ..events.event_bus import global_event_bus
from ..events.distributed.distributed_event_bus import global_distributed_bus
from ..tracing.instrumentation import trace_function
from ..rate_limit.rate_limiter import global_rate_limiter
from ..core.errors import RateLimitExceededError
from ..circuit_breaker.integration import wrap_service_call


@trace_function("get_system_info")
def get_system_info() -> str:
    rl = global_rate_limiter
    if rl is not None and not rl.allow_request("get_system_info"):
        raise RateLimitExceededError("get_system_info")
    os_name = platform.system()
    version = platform.release()
    repo = SystemInfoRepository()
    info = repo.save_system_info(os_name, version)
    try:
        evt = SystemInfoUpdatedEvent(os=os_name, version=version)
        global_event_bus.publish(evt)
        if global_distributed_bus is not None:
            try:
                global_distributed_bus.publish(evt)
            except Exception:
                pass
    except Exception:
        pass
    return (
        f"System: {os_name} {version}\n"
        f"Platform: {platform.platform()}\n"
        "Home: /Users/bong\n"
        f"Saved id: {info.id}"
    )


def get_system_info_mesh() -> str:
    from ..resilience.integration import resilient_call

    return resilient_call("system-service", "get_system_info", get_system_info)
