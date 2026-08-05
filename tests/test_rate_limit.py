import time
from fastapi.testclient import TestClient

from copilot_app.rate_limit.strategies import TokenBucketStrategy, FixedWindowStrategy, SlidingWindowStrategy
from copilot_app.rate_limit.rate_limiter import RateLimiter, global_rate_limiter
from copilot_app.api.routes import app as api_app


def test_token_bucket_basic():
    tb = TokenBucketStrategy(capacity=2, refill_rate=0)
    assert tb.consume() is True
    assert tb.consume() is True
    assert tb.consume() is False


def test_fixed_window():
    fw = FixedWindowStrategy(window_size=1, max_requests=2)
    assert fw.allow() is True
    assert fw.allow() is True
    assert fw.allow() is False
    time.sleep(1.1)
    assert fw.allow() is True


def test_sliding_window():
    sw = SlidingWindowStrategy(window_size=1, max_requests=2)
    assert sw.allow() is True
    assert sw.allow() is True
    assert sw.allow() is False
    time.sleep(1.1)
    assert sw.allow() is True


def test_middleware_rate_limit():
    # set a global limiter with capacity 1 and no refill
    rl = RateLimiter(strategy=TokenBucketStrategy(capacity=1, refill_rate=0))
    import importlib

    rl_mod = importlib.import_module("copilot_app.rate_limit.rate_limiter")
    rl_mod.global_rate_limiter = rl

    client = TestClient(api_app)
    r1 = client.get("/metrics")
    assert r1.status_code in (200, 204)
    r2 = client.get("/metrics")
    assert r2.status_code == 429


def test_cli_rate_limit_command():
    rl = RateLimiter(strategy=TokenBucketStrategy(capacity=2, refill_rate=0))
    import importlib

    rl_mod = importlib.import_module("copilot_app.rate_limit.rate_limiter")
    rl_mod.global_rate_limiter = rl

    # call CLI command function directly
    from copilot_app.cli.commands import _rate_limit_test

    out = _rate_limit_test({"rate_limiter": rl})
    assert "allowed" in out
