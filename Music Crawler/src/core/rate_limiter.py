"""Rate limiting utilities for providers."""

from __future__ import annotations

import time


class RateLimiter:
    """Rate limiter with per-provider delays."""

    def __init__(self) -> None:
        self._last_request: dict[str, float] = {}

    def wait(self, provider_name: str, min_delay: float) -> None:
        """Sleep if needed to respect per-provider rate limits."""
        now = time.monotonic()
        last_time = self._last_request.get(provider_name)
        if last_time is not None:
            elapsed = now - last_time
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
        self._last_request[provider_name] = time.monotonic()
