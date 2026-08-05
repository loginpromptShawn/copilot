from __future__ import annotations

import importlib
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List

from .mesh_node import MeshNode
from .mesh_observability import record_mesh_call, record_mesh_error
from ..circuit_breaker.integration import wrap_service_call
from ..tracing.tracer import global_tracer

logger = logging.getLogger(__name__)


class MeshRouter:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = defaultdict(int)

    def _choose_node(self, service_name: str, nodes: List[MeshNode]) -> MeshNode | None:
        if not nodes:
            return None
        index = self._counters[service_name] % len(nodes)
        self._counters[service_name] += 1
        return nodes[index]

    def load_balanced_call(self, service_name: str, operation: str, *args: Any, **kwargs: Any) -> Any:
        tracer = global_tracer
        span = None
        if tracer is not None:
            try:
                span = tracer.start_span(f"mesh.load_balanced_call:{service_name}")
            except Exception:
                pass
        start = time.time()
        try:
            control_plane = importlib.import_module("copilot_app.mesh.mesh_control_plane").global_mesh_control_plane
            if control_plane is None:
                raise RuntimeError("Mesh control plane not initialized")
            nodes = control_plane.get_nodes(service_name)
            node = self._choose_node(service_name, nodes)
            if node is None:
                raise RuntimeError(f"No available nodes for {service_name}")
            if operation == "greet_user":
                from ..services.user_service import greet_user
                return wrap_service_call("user-service", operation, greet_user, *args, **kwargs)
            if operation == "get_system_info":
                from ..services.system_service import get_system_info
                return wrap_service_call("system-service", operation, get_system_info, *args, **kwargs)
            raise RuntimeError(f"Unknown operation: {operation}")
        except Exception as exc:
            record_mesh_error(service_name, type(exc).__name__)
            raise
        finally:
            record_mesh_call(service_name, time.time() - start)
            if tracer is not None and span is not None:
                try:
                    tracer.finish_span(span)
                except Exception:
                    pass

    def direct_call(self, node_id: str, operation: str, *args: Any, **kwargs: Any) -> Any:
        tracer = global_tracer
        span = None
        if tracer is not None:
            try:
                span = tracer.start_span(f"mesh.direct_call:{node_id}")
            except Exception:
                pass
        start = time.time()
        try:
            control_plane = importlib.import_module("copilot_app.mesh.mesh_control_plane").global_mesh_control_plane
            if control_plane is None:
                raise RuntimeError("Mesh control plane not initialized")
            node = control_plane.get_node(node_id)
            if node is None or not node.registered:
                raise RuntimeError(f"Node not found: {node_id}")
            if operation == "greet_user":
                from ..services.user_service import greet_user_mesh
                return wrap_service_call("user-service", operation, greet_user_mesh, *args, **kwargs)
            if operation == "get_system_info":
                from ..services.system_service import get_system_info_mesh
                return wrap_service_call("system-service", operation, get_system_info_mesh, *args, **kwargs)
            raise RuntimeError(f"Unknown operation: {operation}")
        except Exception as exc:
            record_mesh_error(node_id, type(exc).__name__)
            raise
        finally:
            record_mesh_call(node_id, time.time() - start)
            if tracer is not None and span is not None:
                try:
                    tracer.finish_span(span)
                except Exception:
                    pass
