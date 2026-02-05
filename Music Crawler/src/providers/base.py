"""Search provider interfaces."""

from abc import ABC, abstractmethod

from src.core.rate_limiter import RateLimiter


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        self.rate_limiter = rate_limiter or RateLimiter()

    @abstractmethod
    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        """Search and return list of URLs."""
        pass

    @abstractmethod
    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        pass

    def get_name(self) -> str:
        """Return provider name."""
        return self.__class__.__name__

    def wait_rate_limit(self) -> None:
        """Wait according to provider rate limit settings."""
        self.rate_limiter.wait(self.get_name(), self.get_rate_limit())
