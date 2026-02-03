"""Data models for tracks and search results."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Track:
    """Represents a music track to search for."""

    rank: int
    film: str
    cue_title: str
    description: str
    composer: str = "Herbert Stothart"
    notes: str = ""

    def search_query(self) -> str:
        """Generate a search query string for this track."""
        return f"{self.composer} {self.film} {self.cue_title}"

    def filename_base(self) -> str:
        """Generate a safe filename base for this track."""
        safe_film = "".join(c if c.isalnum() or c in " -" else "_" for c in self.film)
        safe_title = "".join(c if c.isalnum() or c in " -" else "_" for c in self.cue_title)
        return f"{self.rank:02d}_{safe_film}_{safe_title}".lower().replace(" ", "_")


@dataclass
class SearchResult:
    """Represents a search result from a source."""

    track: Track
    source: str  # "youtube", "archive", "spotify", "itunes", "amazon"
    url: str
    is_free: bool
    quality: str = "unknown"
    duration: str | None = None
    title: str = ""
    downloaded: bool = False
    local_path: Path | None = None
    error: str | None = None

    def __str__(self) -> str:
        status = "downloaded" if self.downloaded else ("free" if self.is_free else "paid")
        return f"[{self.source}] {self.title or self.track.cue_title} ({status})"


@dataclass
class CrawlResult:
    """Aggregated results for a single track."""

    track: Track
    results: list[SearchResult] = field(default_factory=list)
    downloaded_from: SearchResult | None = None
    free_alternatives: list[SearchResult] = field(default_factory=list)
    paid_alternatives: list[SearchResult] = field(default_factory=list)
    not_found: bool = False

    @property
    def status(self) -> str:
        if self.downloaded_from:
            return "downloaded"
        elif self.free_alternatives:
            return "free_available"
        elif self.paid_alternatives:
            return "paid_only"
        else:
            return "not_found"
