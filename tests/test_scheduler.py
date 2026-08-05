import time
import threading

import pytest

from copilot_app.scheduler.scheduler import BackgroundScheduler


def test_start_stop_scheduler():
    s = BackgroundScheduler(custom_jobs=[])
    s.start()
    assert s.is_running is True
    s.stop()
    # allow thread to stop
    time.sleep(0.1)
    assert s.is_running is False


def test_jobs_run(monkeypatch):
    calls = {"a": 0, "b": 0}

    def job_a():
        calls["a"] += 1

    def job_b():
        calls["b"] += 1

    s = BackgroundScheduler(custom_jobs=[(job_a, 0.2), (job_b, 0.2)])
    s.start()
    # wait a bit for jobs to run
    time.sleep(0.7)
    s.stop()
    assert calls["a"] >= 1
    assert calls["b"] >= 1
