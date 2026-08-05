from typing import Callable, Any
import logging

from ..mesh.mesh_router import MeshRouter
from ..services.system_service import get_system_info
from ..services.user_service import greet_user
from ..services.async_user_service import greet_user as async_greet_user
from ..services.async_system_service import get_system_info as async_get_system_info


class Command:
    def __init__(self, name: str, description: str, handler: Callable[..., str], is_async: bool = False) -> None:
        self.name = name
        self.description = description
        self.handler = handler
        self.is_async = is_async


def _list_plugins(app_context: dict | None = None) -> str:
    pm = None
    if app_context:
        pm = app_context.get("plugin_manager")
    if pm is None:
        return "No plugin manager available"
    names = list(pm.active_plugins.keys())
    return "\n".join(names) if names else "No plugins loaded"


def _plugin_info(name: str, app_context: dict | None = None) -> str:
    pm = None
    if app_context:
        pm = app_context.get("plugin_manager")
    if pm is None:
        return "No plugin manager available"
    p = pm.get_plugin(name)
    if not p:
        return f"Plugin {name} not found"
    return f"{p.name} v{p.version}: {p.description}"


def _scheduler_status(app_context: dict | None = None) -> str:
    if app_context is None:
        return "No app context"
    sched = app_context.get("scheduler")
    if sched is None:
        return "No scheduler available"
    return "running" if getattr(sched, "is_running", False) else "stopped"


def _list_events(app_context: dict | None = None) -> str:
    try:
        from ..events.event_bus import global_event_bus

        # inspect registered event types
        handlers = getattr(global_event_bus, "_handlers", {})
        return "\n".join([t.__name__ for t in handlers.keys()]) or "No events registered"
    except Exception:
        return "Error listing events"


def _emit_test_event(app_context: dict | None = None) -> str:
    try:
        from ..events.event_types import LogCleanupEvent
        from ..events.event_bus import global_event_bus

        evt = LogCleanupEvent()
        global_event_bus.publish(evt)
        return "Emitted LogCleanupEvent"
    except Exception as exc:
        return f"Error emitting event: {exc}"


def _print_metrics(app_context: dict | None = None) -> str:
    try:
        from ..metrics.exporters import MetricsExporter

        exporter = MetricsExporter()
        return exporter.export_metrics()
    except Exception as exc:
        return f"Error exporting metrics: {exc}"


def _print_traces(app_context: dict | None = None) -> str:
    try:
        import json
        from ..tracing.exporters import TraceExporter

        exporter = TraceExporter()
        traces = exporter.export_all()
        return json.dumps(traces, indent=2)
    except Exception as exc:
        return f"Error exporting traces: {exc}"


def _distributed_events_test(app_context: dict | None = None) -> str:
    try:
        from ..events.event_types import UserCreatedEvent
        from ..events.distributed.distributed_event_bus import global_distributed_bus
        from ..events.event_bus import global_event_bus

        invoked = {"ok": False}

        def _handler(evt):
            invoked["ok"] = True

        # subscribe locally to detect handling
        global_event_bus.subscribe(UserCreatedEvent, _handler)
        evt = UserCreatedEvent(user_id=9999, name="dist-test")
        if global_distributed_bus is not None:
            global_distributed_bus.publish(evt)
        else:
            global_event_bus.publish(evt)

        # small wait for in-memory transport routing
        import time

        time.sleep(0.05)
        global_event_bus.unsubscribe(UserCreatedEvent, _handler)
        return "handled" if invoked["ok"] else "not-handled"
    except Exception as exc:
        return f"Error running distributed events test: {exc}"


def _rate_limit_test(app_context: dict | None = None) -> str:
    try:
        rl = None
        if app_context:
            rl = app_context.get("rate_limiter")
        if rl is None:
            from ..rate_limit.rate_limiter import global_rate_limiter as rl

        out = []
        # run a burst of 10 requests
        for i in range(10):
            allowed = rl.allow_request("cli_test") if rl is not None else True
            out.append(f"{i}: {'allowed' if allowed else 'blocked'}")
        return "\n".join(out)
    except Exception as exc:
        return f"Error running rate-limit-test: {exc}"


def _mesh_status(app_context: dict | None = None) -> str:
    try:
        mesh = None
        if app_context:
            mesh = app_context.get("mesh_control_plane")
        if mesh is None:
            return "No mesh control plane available"
        nodes = mesh._nodes.values()
        lines = [f"{node.id} {node.name} {node.address} {node.metadata}" for node in nodes]
        return "\n".join(lines) if lines else "No nodes registered"
    except Exception as exc:
        return f"Error fetching mesh status: {exc}"


def _mesh_call(service: str, operation: str, app_context: dict | None = None) -> str:
    try:
        mesh = None
        if app_context:
            mesh = app_context.get("mesh_router")
        if mesh is None:
            from ..mesh.mesh_router import MeshRouter
            mesh = MeshRouter()
        result = mesh.load_balanced_call(service, operation)
        return f"mesh call result: {result}"
    except Exception as exc:
        return f"Error performing mesh call: {exc}"


def _circuit_status(app_context: dict | None = None) -> str:
    try:
        from ..circuit_breaker.integration import get_all_breakers

        breakers = get_all_breakers()
        if not breakers:
            return "No circuit breakers registered"
        lines = []
        for service_name, breaker in breakers.items():
            lines.append(
                f"{service_name}: state={breaker.state}, failure_count={breaker.failure_count}, last_failure_time={breaker.last_failure_time}"
            )
        return "\n".join(lines)
    except Exception as exc:
        return f"Error fetching circuit status: {exc}"


def _circuit_test(service: str, app_context: dict | None = None) -> str:
    try:
        from ..circuit_breaker.integration import get_breaker_for_service

        breaker = get_breaker_for_service(service)
        # intentionally trigger failures until OPEN
        for i in range(breaker.policy.failure_threshold):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("circuit test failure")))
            except RuntimeError:
                pass
        return f"After {breaker.policy.failure_threshold} failures: {breaker.state}"
    except Exception as exc:
        return f"Error running circuit test: {exc}"


COMMANDS = [
    Command("greet", "Print a macOS greeting", greet_user),
    Command("sysinfo", "Print macOS system information", get_system_info),
    Command("plugins", "List loaded plugins", _list_plugins),
    Command("plugin-info", "Show plugin metadata by name", _plugin_info),
    # async variants
    Command("async-greet", "Print a macOS greeting (async)", async_greet_user, is_async=True),
    Command("async-sysinfo", "Print system information (async)", async_get_system_info, is_async=True),
    Command("scheduler-status", "Report scheduler running status", _scheduler_status),
    Command("events", "List registered event types", _list_events),
    Command("emit-test-event", "Emit a test LogCleanupEvent", _emit_test_event),
    Command("metrics", "Print current metrics in Prometheus format", _print_metrics),
    Command("distributed-events-test", "Publish test UserCreatedEvent via DistributedEventBus", _distributed_events_test),
    Command("traces", "Print collected tracing data", _print_traces),
    Command("rate-limit-test", "Run a CLI rate limit test", _rate_limit_test),
    Command("mesh-status", "List registered mesh nodes", _mesh_status),
    Command("mesh-call", "Perform a simulated mesh call", _mesh_call),
    Command("circuit-status", "Print circuit breaker states", _circuit_status),
    Command("circuit-test", "Run a circuit breaker failure test", _circuit_test),
]

logging.getLogger(__name__).debug("Registered commands: %s", [c.name for c in COMMANDS])
