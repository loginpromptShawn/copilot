from __future__ import annotations

import logging
import shutil
import os
from typing import Any

from .metrics_registry import global_metrics_registry, MetricsRegistry

logger = logging.getLogger(__name__)


def _safe_psutil_import():
    try:
        import psutil

        return psutil
    except Exception:
        return None


def system_metrics_collector(reg: MetricsRegistry | None = None) -> None:
    """Collect CPU, memory, and disk usage and update gauges."""
    psutil = _safe_psutil_import()
    registry = reg or global_metrics_registry
    try:
        if psutil:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        else:
            # fallback: use os.getloadavg for CPU and shutil for disk
            load = os.getloadavg()[0]
            cpu = float(load)
            mem = 0.0
            total, used, free = shutil.disk_usage("/")
            disk = used / total * 100.0 if total else 0.0

        registry.set_gauge("system_cpu_percent", cpu)
        registry.set_gauge("system_mem_percent", mem)
        registry.set_gauge("system_disk_percent", disk)
    except Exception:
        logger.exception("Failed collecting system metrics")


def app_metrics_collector(reg: MetricsRegistry | None = None, plugin_manager=None) -> None:
    """Collect application metrics: number of users and plugins loaded."""
    registry = reg or global_metrics_registry
    try:
        # users count
        from ..persistence.repository import UserRepository

        repo = UserRepository()
        users = len(repo.list_users())
        registry.set_gauge("app_users_count", users)

        # plugins count: use provided plugin manager if available, otherwise count installed files
        if plugin_manager is not None:
            plugins_count = len(plugin_manager.active_plugins)
        else:
            from ..plugins.plugin_manager import PluginManager
            pm = PluginManager()
            pm.load_plugins()
            plugins_count = len(pm.active_plugins)
        registry.set_gauge("app_plugins_count", plugins_count)
    except Exception:
        logger.exception("Failed collecting app metrics")
