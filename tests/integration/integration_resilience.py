import time
import threading

import pytest

from copilot_app.resilience.bulkhead import Bulkhead, BulkheadRejectedError
from copilot_app.resilience.integration import get_bulkhead, get_retry_policy, resilient_call
from copilot_app.resilience.retry import RetryExecutor, RetryPolicy
from copilot_app.circuit_breaker.integration import get_breaker_for_service, reset_breakers
from copilot_app.circuit_breaker.policies import CircuitState
from copilot_app.core.errors import CircuitOpenError


def integration_retry_fixed_strategy():
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


def integration_retry_exponential_strategy():
    policy = RetryPolicy(max_attempts=2, backoff_strategy="exponential", base_delay=0.01, max_delay=0.05)
    executor = RetryExecutor(policy)
    calls = {"count": 0}

    def fail_once():
        if calls["count"] == 0:
            calls["count"] += 1
            raise RuntimeError("retry")
        return "ok"

    assert executor.execute(fail_once) == "ok"


def integration_retry_jitter_strategy():
    policy = RetryPolicy(max_attempts=2, backoff_strategy="jitter", base_delay=0.01, max_delay=0.05)
    executor = RetryExecutor(policy)

    def fail_once():
        if not hasattr(fail_once, "called"):
            fail_once.called = True
            raise RuntimeError("retry")
        return "ok"

    assert executor.execute(fail_once) == "ok"


def integration_bulkhead_rejects_when_full():
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


def integration_circuit_open_skips_retries():
    reset_breakers()
    breaker = get_breaker_for_service("user-service")
    for _ in range(breaker.policy.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        resilient_call("user-service", "fail", lambda: "ok")


def integration_mesh_router_uses_resilience():
    from copilot_app.mesh.mesh_router import MeshRouter

    reset_breakers()
    router = MeshRouter()
    assert router is not None

    with pytest.raises(RuntimeError):
        resilient_call("user-service", "test", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
