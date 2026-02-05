"""Search provider interfaces."""

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        """Search and return list of URLs."""
        pass
