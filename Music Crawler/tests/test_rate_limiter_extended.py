"""Extended tests for RateLimiter."""

from src.core.rate_limiter import RateLimiter


def test_rate_limiter_wait_and_backoff(monkeypatch):
    calls = {"sleep": 0}

    def fake_sleep(seconds):
        calls["sleep"] += 1

    times = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    def fake_monotonic():
        return times.pop(0)

    monkeypatch.setattr("src.core.rate_limiter.time.sleep", fake_sleep)
    monkeypatch.setattr("src.core.rate_limiter.time.monotonic", fake_monotonic)

    limiter = RateLimiter()
    limiter.wait("provider", 0.5)
    limiter.wait("provider", 0.5)
    limiter.backoff("provider", attempt=2, initial_delay=1.0, max_delay=2.0)
    assert calls["sleep"] >= 1
