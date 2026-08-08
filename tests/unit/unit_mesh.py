import time
from unittest.mock import patch
import pytest
from copilot_app.mesh.mesh_node import MeshNode
from copilot_app.mesh.mesh_control_plane import MeshControlPlane, global_mesh_control_plane
from copilot_app.mesh.mesh_router import MeshRouter
from copilot_app.tracing.tracer import Tracer
from copilot_app.mesh.mesh_observability import record_mesh_call, record_mesh_error


def unit_node_registration_and_deregistration():
    plane = MeshControlPlane()
    node = MeshNode("node-1", "user-service", "127.0.0.1:9001", {"role": "backend"})
    plane.register_node(node)
    assert node.registered
    assert plane.get_nodes("user-service")
    plane.deregister_node("node-1")
    assert not node.registered
    assert plane.get_nodes("user-service") == []


def unit_control_plane_node_lookup():
    plane = MeshControlPlane()
    node = MeshNode("n1", "svc-a", "10.0.0.1:8000")
    plane.register_node(node)
    assert plane.get_node("n1") is node
    assert plane.get_node("missing") is None
    assert plane.get_nodes("svc-a") == [node]
    assert plane.get_nodes("svc-b") == []


def unit_control_plane_config_management():
    plane = MeshControlPlane()
    plane.apply_global_config({"key": "value"})
    cfg = plane.get_config()
    assert cfg["key"] == "value"
    plane.apply_global_config({"key2": 2})
    cfg = plane.get_config()
    assert cfg["key2"] == 2
    assert cfg["key"] == "value"


def unit_control_plane_deregister_missing():
    plane = MeshControlPlane()
    plane.deregister_node("does-not-exist")
    assert plane.get_nodes("x") == []


def unit_node_heartbeat_updates_timestamp():
    node = MeshNode("n1", "svc", "addr")
    node.register()
    first = node.last_heartbeat
    assert first is not None
    time.sleep(0.01)
    node.heartbeat()
    second = node.last_heartbeat
    assert second is not None and second > first


def unit_node_metadata_defaults_to_empty():
    node = MeshNode("n1", "svc", "addr")
    assert node.metadata == {}


def unit_node_initial_not_registered():
    node = MeshNode("n1", "svc", "addr")
    assert node.registered is False
    assert node.last_heartbeat is None


def unit_round_robin_routing():
    plane = MeshControlPlane()
    n1 = MeshNode("node-1", "user-service", "127.0.0.1:9001")
    n2 = MeshNode("node-2", "user-service", "127.0.0.1:9002")
    plane.register_node(n1)
    plane.register_node(n2)
    import importlib
    mc_mod = importlib.import_module("copilot_app.mesh.mesh_control_plane")
    mc_mod.global_mesh_control_plane = plane
    router = MeshRouter()
    with pytest.raises(RuntimeError):
        router.load_balanced_call("user-service", "nonexistent_operation")
    assert router._counters["user-service"] == 1


def unit_mesh_observability_records_metrics_and_traces():
    tracer = Tracer()
    import importlib
    tr_mod = importlib.import_module("copilot_app.tracing.tracer")
    tr_mod.global_tracer = tracer
    record_mesh_call("user-service", 0.1)
    record_mesh_error("user-service", "TestError")
    traces = tracer.get_all_traces()
    assert any("mesh.call:user-service" in span.name for spans in traces.values() for span in spans)
    assert any("mesh.error:user-service" in span.name for spans in traces.values() for span in spans)


def unit_cli_mesh_call_behavior(monkeypatch):
    from copilot_app.cli.commands import _mesh_call
    class DummyRouter:
        def load_balanced_call(self, service_name, operation):
            return f"{service_name}:{operation}"
    monkeypatch.setattr("copilot_app.cli.commands.MeshRouter", lambda: DummyRouter())
    result = _mesh_call("user-service", "greet_user", app_context={"mesh_router": DummyRouter()})
    assert "mesh call result:" in result
