from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Tuple

from . import jobs as default_jobs


logger = logging.getLogger(__name__)


class BackgroundScheduler:
    def __init__(self, custom_jobs: List[Tuple[Callable[[], None], float]] | None = None) -> None:
        """If custom_jobs is provided, use it as list of (callable, interval_seconds).
        Otherwise, schedule default jobs."""
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.is_running = False

        if custom_jobs is not None:
            self.jobs = custom_jobs
        else:
            # default jobs: cleanup every hour, snapshot every 5 minutes, metrics every minute
            self.jobs = [
                (default_jobs.cleanup_logs, 3600.0),
                (default_jobs.snapshot_system_info, 300.0),
                (default_jobs.run_metrics_collection, 60.0),
            ]

        # track last run times
        self._last_run = {id(job): 0.0 for job, _ in self.jobs}

    def _run_loop(self) -> None:
        logger.info("BackgroundScheduler started")
        self.is_running = True
        try:
            while not self._stop_event.is_set():
                now = time.time()
                for job, interval in self.jobs:
                    key = id(job)
                    last = self._last_run.get(key, 0.0)
                    if now - last >= interval:
                        try:
                            threading.Thread(target=job, daemon=True).start()
                            self._last_run[key] = now
                            logger.info("Scheduled job %s executed", getattr(job, "__name__", str(job)))
                        except Exception:
                            logger.exception("Failed to run scheduled job %s", job)
                # sleep a short time
                time.sleep(1)
        finally:
            self.is_running = False
            logger.info("BackgroundScheduler stopped")

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        with self._lock:
            if not self._thread:
                return
            self._stop_event.set()
            self._thread.join(timeout)
            if self._thread.is_alive():
                logger.warning("BackgroundScheduler thread did not stop within timeout")
