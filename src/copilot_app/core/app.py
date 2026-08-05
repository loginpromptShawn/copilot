import logging

from ..utils.config import get_config
from ..utils.logging_setup import init_logging
from ..persistence.database import init_db
from .router import run_command
from ..plugins.plugin_manager import PluginManager
from ..scheduler.scheduler import BackgroundScheduler
import atexit
from ..events.event_bus import global_event_bus
from ..events.subscribers import (
    handle_user_created,
    handle_system_info_updated,
    handle_log_cleanup,
)
from ..events.event_types import UserCreatedEvent, SystemInfoUpdatedEvent, LogCleanupEvent
from ..metrics.metrics_registry import MetricsRegistry, global_metrics_registry
from ..events.distributed.distributed_event_bus import DistributedEventBus, global_distributed_bus
from ..events.distributed.transport import InMemoryTransport
from ..tracing.tracer import Tracer, global_tracer
from ..tracing.exporters import TraceExporter
from ..rate_limit.rate_limiter import RateLimiter, global_rate_limiter
from ..rate_limit import strategies as rl_strategies
from ..mesh.mesh_control_plane import MeshControlPlane, global_mesh_control_plane
from ..mesh.mesh_router import MeshRouter
from ..mesh.mesh_node import MeshNode


class App:
    def __init__(self) -> None:
        init_logging()
        # initialize the sqlite database
        init_db()
        self.config = get_config()
        # initialize plugin manager
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()

        # initialize metrics registry and set global reference
        self.metrics_registry = MetricsRegistry()
        try:
            import importlib

            mr_mod = importlib.import_module("copilot_app.metrics.metrics_registry")
            mr_mod.global_metrics_registry = self.metrics_registry
        except Exception:
            pass

        # initialize background scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        # app_context passed to plugins; plugins can access the app, config, plugin_manager and scheduler
        self.app_context = {
            "app": self,
            "config": self.config,
            "plugin_manager": self.plugin_manager,
            "scheduler": self.scheduler,
            "metrics_registry": self.metrics_registry,
        }
        self.plugin_manager.activate_all(self.app_context)

        # initialize EventBus and register core subscribers
        # replace global bus with app-scoped bus
        from ..events.event_bus import EventBus

        self.event_bus = EventBus()
        # register handlers
        self.event_bus.subscribe(UserCreatedEvent, handle_user_created)
        self.event_bus.subscribe(SystemInfoUpdatedEvent, handle_system_info_updated)
        self.event_bus.subscribe(LogCleanupEvent, handle_log_cleanup)
        # set global reference for modules that don't receive app_context
        global_event_bus = globals().get("global_event_bus")
        try:
            # override module-level global_event_bus
            import importlib

            eb_mod = importlib.import_module("copilot_app.events.event_bus")
            eb_mod.global_event_bus = self.event_bus
        except Exception:
            # fallback: ignore
            pass

        # initialize DistributedEventBus with in-memory transport and set global
        self.distributed_event_bus = DistributedEventBus(local_bus=self.event_bus, transport=InMemoryTransport())
        try:
            de_mod = importlib.import_module("copilot_app.events.distributed.distributed_event_bus")
            de_mod.global_distributed_bus = self.distributed_event_bus
        except Exception:
            pass

        # initialize tracer and exporter
        self.tracer = Tracer()
        try:
            tr_mod = importlib.import_module("copilot_app.tracing.tracer")
            tr_mod.global_tracer = self.tracer
        except Exception:
            pass
        self.trace_exporter = TraceExporter(self.tracer)
        self.app_context.update({"tracer": self.tracer, "trace_exporter": self.trace_exporter})

        # initialize rate limiter with a TokenBucketStrategy by default
        self.rate_limiter = RateLimiter(strategy=rl_strategies.TokenBucketStrategy(capacity=100, refill_rate=10))
        try:
            rl_mod = importlib.import_module("copilot_app.rate_limit.rate_limiter")
            rl_mod.global_rate_limiter = self.rate_limiter
        except Exception:
            pass
        self.app_context.update({"rate_limiter": self.rate_limiter})

        # initialize mesh control plane and router
        self.mesh_control_plane = MeshControlPlane()
        self.mesh_router = MeshRouter()
        try:
            mc_mod = importlib.import_module("copilot_app.mesh.mesh_control_plane")
            mc_mod.global_mesh_control_plane = self.mesh_control_plane
        except Exception:
            pass
        self.app_context.update({"mesh_control_plane": self.mesh_control_plane, "mesh_router": self.mesh_router})

        self.mesh_control_plane.register_node(MeshNode("user-service-01", "user-service", "127.0.0.1:9001", {"role": "backend"}))
        self.mesh_control_plane.register_node(MeshNode("system-service-01", "system-service", "127.0.0.1:9002", {"role": "backend"}))
        self.mesh_control_plane.register_node(MeshNode("api-gateway-01", "api-gateway", "127.0.0.1:9000", {"role": "gateway"}))

        # ensure scheduler stops on exit
        atexit.register(self.shutdown)
        logging.info(
            "App initialized with config: %s",
            dict(self.config.items("app")),
        )

    def run(self, command: str, args: list[str]) -> int:
        logging.info("Running command: %s %s", command, args)

        try:
            result = run_command(command, args, app_context=self.app_context)
            print(result)
            return 0
        except Exception as exc:
            logging.error("Command execution failed: %s", exc)
            print(f"Error: {exc}")
            return 1

    def shutdown(self) -> None:
        try:
            self.plugin_manager.deactivate_all()
        finally:
            try:
                self.scheduler.stop()
            except Exception:
                logging.exception("Failed stopping scheduler")
