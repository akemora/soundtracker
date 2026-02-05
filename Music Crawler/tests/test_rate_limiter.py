import src.core.rate_limiter as rl
from src.core.rate_limiter import RateLimiter


def test_backoff_uses_exponential_delay(monkeypatch) -> None:
    sleeps: list[float] = []

    def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(rl.time, "sleep", fake_sleep)

    limiter = RateLimiter(initial_delay=1.0, max_delay=30.0)
    limiter.backoff("provider", attempt=1)
    limiter.backoff("provider", attempt=3)

    assert sleeps == [1.0, 4.0]
