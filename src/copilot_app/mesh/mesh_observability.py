from __future__ import annotations

from ..metrics.metrics_registry import global_metrics_registry
import importlib

_tracer_module = None


def _get_tracer():
    global _tracer_module
    if _tracer_module is None:
        try:
            _tracer_module = importlib.import_module("copilot_app.tracing.tracer")
        except Exception:
            return None
    return getattr(_tracer_module, "global_tracer", None)


def record_mesh_call(service_name: str, latency: float) -> None:
    registry = global_metrics_registry
    registry.increment_counter("mesh_calls_total", {"service": service_name})
    registry.observe_histogram("mesh_call_latency_seconds", latency, {"service": service_name})
    tracer = _get_tracer()
    if tracer is not None:
        span = tracer.start_span(f"mesh.call:{service_name}")
        tracer.finish_span(span)


def record_mesh_error(service_name: str, error_type: str) -> None:
    registry = global_metrics_registry
    registry.increment_counter("mesh_errors_total", {"service": service_name, "error": error_type})
    tracer = _get_tracer()
    if tracer is not None:
        span = tracer.start_span(f"mesh.error:{service_name}")
        tracer.finish_span(span)
