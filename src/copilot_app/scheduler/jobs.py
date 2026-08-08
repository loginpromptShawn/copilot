import logging
import shutil
from pathlib import Path
import platform

from ..persistence.repository import SystemInfoRepository
from ..events.event_types import LogCleanupEvent
from ..events.event_bus import global_event_bus
from ..metrics import collectors
from ..metrics.metrics_registry import global_metrics_registry
from ..tracing.instrumentation import trace_block


logger = logging.getLogger(__name__)


def _default_log_dir() -> Path:
    try:
        from ..utils.config import get_config
        config = get_config()
        if config.has_section("paths") and config.has_option("paths", "data_dir"):
            return Path(config.get("paths", "data_dir")).parent / "logs"
    except Exception:
        pass
    return Path.home() / "copilot" / "logs"

def _default_log_rotation_bytes() -> int:
    try:
        from ..utils.config import get_config
        config = get_config()
        if config.has_section("paths") and config.has_option("paths", "log_rotation_bytes"):
            return config.getint("paths", "log_rotation_bytes")
    except Exception:
        pass
    return 5 * 1024 * 1024  # 5MB default

LOG_DIR = _default_log_dir()
LOG_ROTATION_BYTES = _default_log_rotation_bytes()


def cleanup_logs() -> None:
    """Rotate or prune old log files in LOG_DIR."""
    with trace_block("cleanup_logs"):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            # simple prune: remove files older than a threshold (not implemented here)
            # For demo, compress large logs (placeholder logic)
            for p in LOG_DIR.glob("*.log"):
                if p.stat().st_size > LOG_ROTATION_BYTES:
                    dest = p.with_suffix(p.suffix + ".old")
                    shutil.move(str(p), str(dest))
                    logger.info("Rotated log %s to %s", p, dest)
        except Exception:
            logger.exception("Failed to cleanup logs")


def snapshot_system_info() -> None:
    """Read system info and store via SystemInfoRepository."""
    with trace_block("snapshot_system_info"):
        try:
            os_name = platform.system()
            version = platform.release()
            repo = SystemInfoRepository()
            info = repo.save_system_info(os_name, version)
            logger.info("Snapshot saved: %s %s id=%s", os_name, version, info.id)
            try:
                evt = LogCleanupEvent()
                # snapshot doesn't strictly mean log cleanup, but publish a heartbeat-like event
                global_event_bus.publish(evt)
                # also publish distributed
                try:
                    from ..events.distributed.distributed_event_bus import global_distributed_bus

                    if global_distributed_bus is not None:
                        global_distributed_bus.publish(evt)
                except Exception:
                    logger.exception("Failed publishing distributed event")
            except Exception:
                logger.exception("Failed publishing snapshot event")
        except Exception:
            logger.exception("Failed snapshot_system_info")


def run_metrics_collection() -> None:
    """Run configured metrics collectors to update the metrics registry."""
    with trace_block("run_metrics_collection"):
        try:
            collectors.system_metrics_collector(global_metrics_registry)
            collectors.app_metrics_collector(global_metrics_registry)
        except Exception:
            logger.exception("Failed running metrics collection")
