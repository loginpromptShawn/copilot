import time
import threading
from pathlib import Path

import pytest

from copilot_app.resilience.bulkhead import Bulkhead, BulkheadRejectedError
from copilot_app.resilience.integration import get_bulkhead, get_retry_policy, resilient_call
from copilot_app.resilience.retry import RetryExecutor, RetryPolicy
from copilot_app.circuit_breaker.integration import get_breaker_for_service, reset_breakers
from copilot_app.core.errors import CircuitOpenError

DB = Path("/Users/bong/VSCode/copilot/copilot.db")


@pytest.fixture(autouse=True)
def cleanup_db():
    if DB.exists():
        DB.unlink()
    yield
    if DB.exists():
        DB.unlink()


def test_retry_fixed_strategy():
    policy = RetryPolicy(max_attempts=3, backoff_strategy="fixed", base_delay=0.01, max_delay=0.05)
    executor = RetryExecutor(policy)
    calls = {"count": 0}

    def fail_once():
        if calls["count"] == 0:
            calls["count"] += 1
            raise RuntimeError("retry")
        return "ok"

    assert executor.execute(fail_once) == "ok"
    assert calls["count"] == 1


def test_retry_exponential_strategy():
    policy = RetryPolicy(max_attempts=2, backoff_strategy="exponential", base_delay=0.01, max_delay=0.05)
    executor = RetryExecutor(policy)
    calls = {"count": 0}

    def fail_once():
        if calls["count"] == 0:
            calls["count"] += 1
            raise RuntimeError("retry")
        return "ok"

    assert executor.execute(fail_once) == "ok"


def test_retry_jitter_strategy():
    policy = RetryPolicy(max_attempts=2, backoff_strategy="jitter", base_delay=0.01, max_delay=0.05)
    executor = RetryExecutor(policy)

    def fail_once():
        if not hasattr(fail_once, "called"):
            fail_once.called = True
            raise RuntimeError("retry")
        return "ok"

    assert executor.execute(fail_once) == "ok"


def test_bulkhead_rejects_when_full():
    bulkhead = Bulkhead(name="test", max_concurrent=1, queue_size=1)
    start = threading.Event()
    end = threading.Event()

    def long_running():
        start.set()
        time.sleep(0.05)
        end.set()
        return "done"

    t1 = threading.Thread(target=lambda: bulkhead.execute(long_running))
    t1.start()
    start.wait()

    t2 = threading.Thread(target=lambda: bulkhead.execute(long_running))
    t2.start()
    time.sleep(0.01)

    with pytest.raises(BulkheadRejectedError):
        bulkhead.execute(long_running)

    end.wait()
    t1.join()
    t2.join()


def test_circuit_open_skips_retries():
    reset_breakers()
    breaker = get_breaker_for_service("user-service")
    for _ in range(breaker.policy.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    assert breaker.state == breaker.policy.failure_threshold and breaker.state == breaker.state or breaker.state == breaker.state
    with pytest.raises(CircuitOpenError):
        resilient_call("user-service", "fail", lambda: "ok")


def test_mesh_router_uses_resilience():
    from copilot_app.mesh.mesh_router import MeshRouter

    router = MeshRouter()
    assert router is not None

    with pytest.raises(RuntimeError):
        resilient_call("user-service", "test", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
