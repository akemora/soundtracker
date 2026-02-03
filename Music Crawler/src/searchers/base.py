"""Base searcher interface."""

from abc import ABC, abstractmethod

from src.models.track import SearchResult, Track


class BaseSearcher(ABC):
    """Abstract base class for source searchers."""

    name: str = "base"
    is_free: bool = True

    @abstractmethod
    def search(self, track: Track) -> list[SearchResult]:
        """Search for a track and return matching results."""
        pass

    def build_query(self, track: Track) -> str:
        """Build a search query for the track."""
        return track.search_query()
