from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..utils.config import get_config
from ..utils.logging_setup import init_logging
from ..persistence.database import init_db
from ..auth.service import AuthService
from ..plugins.plugin_manager import PluginManager
from ..rate_limit.rate_limiter import RateLimiter
from ..rate_limit import strategies as rl_strategies
from ..mesh.mesh_control_plane import MeshControlPlane
from ..mesh.mesh_router import MeshRouter
from ..mesh.mesh_node import MeshNode


class AsyncApp:
    """Async version of App using asyncio."""

    def __init__(self) -> None:
        # synchronous init pieces are still done here
        init_logging()
        init_db()
        self.config = get_config()
        self.plugin_manager = PluginManager()
        self.auth_service = AuthService()
        self.rate_limiter = RateLimiter(strategy=rl_strategies.TokenBucketStrategy(capacity=100, refill_rate=10))
        self.mesh_control_plane = MeshControlPlane()
        self.mesh_router = MeshRouter()
        self.app_context: dict[str, Any] = {
            "app": self,
            "config": self.config,
            "plugin_manager": self.plugin_manager,
            "auth_service": self.auth_service,
            "rate_limiter": self.rate_limiter,
            "mesh_control_plane": self.mesh_control_plane,
            "mesh_router": self.mesh_router,
        }

    async def init(self) -> None:
        # load plugins synchronously, then activate asynchronously
        self.plugin_manager.load_plugins()
        # set global references for modules that don't receive app_context
        import importlib
        try:
            rl_mod = importlib.import_module("copilot_app.rate_limit.rate_limiter")
            rl_mod.global_rate_limiter = self.rate_limiter
        except Exception:
            pass
        try:
            mc_mod = importlib.import_module("copilot_app.mesh.mesh_control_plane")
            mc_mod.global_mesh_control_plane = self.mesh_control_plane
        except Exception:
            pass
        # register default mesh nodes
        self.mesh_control_plane.register_node(MeshNode("user-service-01", "user-service", "127.0.0.1:9001", {"role": "backend"}))
        self.mesh_control_plane.register_node(MeshNode("system-service-01", "system-service", "127.0.0.1:9002", {"role": "backend"}))
        self.mesh_control_plane.register_node(MeshNode("api-gateway-01", "api-gateway", "127.0.0.1:9000", {"role": "gateway"}))
        # plugins may perform blocking work; run activation in thread pool
        await asyncio.to_thread(self.plugin_manager.activate_all, self.app_context)
        logging.info("AsyncApp initialized with config: %s", dict(self.config.items("app")))

    async def run(self, command: str, args: list[str]) -> int:
        logging.info("Running async command: %s %s", command, args)
        try:
            # delegate to async router if needed
            from .async_router import AsyncRouter

            result = await AsyncRouter().run_command(command, *args, app_context=self.app_context)
            print(result)
            return 0
        except Exception as exc:
            logging.error("Async command execution failed: %s", exc)
            print(f"Error: {exc}")
            return 1