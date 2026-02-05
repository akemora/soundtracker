"""Rate limiting utilities for providers."""

from __future__ import annotations

import time

DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0


class RateLimiter:
    """Rate limiter with per-provider delays."""

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        self._last_request: dict[str, float] = {}
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay

    def wait(self, provider_name: str, min_delay: float) -> None:
        """Sleep if needed to respect per-provider rate limits."""
        now = time.monotonic()
        last_time = self._last_request.get(provider_name)
        if last_time is not None:
            elapsed = now - last_time
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
        self._last_request[provider_name] = time.monotonic()

    def backoff(
        self,
        provider_name: str,
        attempt: int,
        initial_delay: float | None = None,
        max_delay: float | None = None,
    ) -> None:
        """Apply exponential backoff for retryable errors."""
        initial = self.initial_delay if initial_delay is None else initial_delay
        maximum = self.max_delay if max_delay is None else max_delay
        delay = min(maximum, initial * (2 ** max(attempt - 1, 0)))
        time.sleep(delay)
        self._last_request[provider_name] = time.monotonic()
