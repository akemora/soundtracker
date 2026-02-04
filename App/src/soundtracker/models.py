"""Data models for SOUNDTRACKER.

This module defines the core data structures used throughout the application
for representing films, awards, external sources, and composer information.

All models use dataclasses with full type hints and optional fields where
data may be incomplete from external sources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AwardStatus(Enum):
    """Status of an award (win or nomination)."""

    WIN = "Win"
    NOMINATION = "Nomination"


@dataclass
class Film:
    """Represents a film in a composer's filmography.

    Attributes:
        title: Display title (may be localized).
        original_title: Original release title.
        title_es: Spanish title for display.
        year: Release year.
        poster_url: URL to poster image (TMDB or web).
        poster_path: TMDB poster path segment.
        poster_local: Local path to downloaded poster.
        poster_file: Target file path for poster download.
        popularity: TMDB popularity score.
        vote_count: TMDB vote count.
        vote_average: TMDB average vote (0-10).
        spotify_popularity: Spotify popularity score (0-100).
        youtube_views: YouTube view count for soundtrack.
        imdb_id: IMDb title ID (tconst).
    """

    title: str
    original_title: Optional[str] = None
    title_es: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    poster_path: Optional[str] = None
    poster_local: Optional[str] = None
    poster_file: Optional[str] = None
    popularity: Optional[float] = None
    vote_count: Optional[int] = None
    vote_average: Optional[float] = None
    spotify_popularity: Optional[float] = None
    youtube_views: Optional[int] = None
    imdb_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure original_title defaults to title if not provided."""
        if self.original_title is None:
            self.original_title = self.title
        if self.title_es is None:
            self.title_es = self.original_title

    @property
    def display_title(self) -> str:
        """Return the best title for display (Spanish if available)."""
        return self.title_es or self.original_title or self.title

    @property
    def has_poster(self) -> bool:
        """Check if a poster is available (local or URL)."""
        return bool(self.poster_local or self.poster_url)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "original_title": self.original_title,
            "title_es": self.title_es,
            "year": self.year,
            "poster_url": self.poster_url,
            "poster_path": self.poster_path,
            "poster_local": self.poster_local,
            "poster_file": self.poster_file,
            "popularity": self.popularity,
            "vote_count": self.vote_count,
            "vote_average": self.vote_average,
            "spotify_popularity": self.spotify_popularity,
            "youtube_views": self.youtube_views,
            "imdb_id": self.imdb_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Film":
        """Create Film from dictionary."""
        return cls(
            title=data.get("title", ""),
            original_title=data.get("original_title"),
            title_es=data.get("title_es"),
            year=data.get("year"),
            poster_url=data.get("poster_url"),
            poster_path=data.get("poster_path"),
            poster_local=data.get("poster_local"),
            poster_file=data.get("poster_file"),
            popularity=data.get("popularity"),
            vote_count=data.get("vote_count"),
            vote_average=data.get("vote_average"),
            spotify_popularity=data.get("spotify_popularity"),
            youtube_views=data.get("youtube_views"),
            imdb_id=data.get("imdb_id"),
        )


@dataclass
class Award:
    """Represents an award or nomination for a composer.

    Attributes:
        award: Name of the award (e.g., "Oscar", "Grammy").
        year: Year the award was given/nominated.
        film: Film for which the award was given (if applicable).
        status: Whether this was a win or nomination.
        category: Specific award category (e.g., "Best Original Score").
    """

    award: str
    year: Optional[int] = None
    film: Optional[str] = None
    status: AwardStatus = AwardStatus.WIN
    category: Optional[str] = None

    @property
    def is_win(self) -> bool:
        """Check if this is a winning award."""
        return self.status == AwardStatus.WIN

    @property
    def display_text(self) -> str:
        """Return formatted display text for the award."""
        emoji = "🏆" if self.is_win else "🎯"
        parts = [f"{emoji} **{self.award}**"]
        if self.category:
            parts.append(f"({self.category})")
        if self.film:
            parts.append(f"por *{self.film}*")
        if self.year:
            parts.append(f"({self.year})")
        return " ".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "award": self.award,
            "year": self.year,
            "film": self.film,
            "status": self.status.value,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Award":
        """Create Award from dictionary."""
        status_str = data.get("status", "Win")
        status = AwardStatus.WIN if status_str == "Win" else AwardStatus.NOMINATION
        return cls(
            award=data.get("award", ""),
            year=data.get("year"),
            film=data.get("film"),
            status=status,
            category=data.get("category"),
        )


@dataclass
class ExternalSource:
    """Represents an external information source about a composer.

    Attributes:
        name: Display name for the source (e.g., "MundoBSO").
        url: URL to the source.
        snippet: Optional text snippet from the source.
        domain: Domain of the source for categorization.
    """

    name: str
    url: str
    snippet: Optional[str] = None
    text: Optional[str] = None
    domain: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "snippet": self.snippet,
            "text": self.text,
            "domain": self.domain,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalSource":
        """Create ExternalSource from dictionary."""
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            snippet=data.get("snippet"),
            text=data.get("text"),
            domain=data.get("domain"),
        )


@dataclass
class ComposerInfo:
    """Complete information about a film composer.

    This is the main data structure that aggregates all information
    gathered about a composer from various sources.

    Attributes:
        name: Full name of the composer.
        index: Numeric index in the master list.
        birth_year: Year of birth.
        death_year: Year of death (None if still alive).
        country: Country of origin/nationality.
        biography: Biography text in Spanish.
        style: Musical style description.
        anecdotes: Personal anecdotes and trivia.
        filmography: List of films scored by the composer.
        awards: List of awards and nominations.
        external_sources: List of external information sources.
        external_snippets: List of text snippets from external sources.
        top_10: Top 10 most notable soundtracks.
        image_url: URL to composer portrait.
        image_local: Local path to downloaded portrait.
        wikipedia_url: URL to Wikipedia article.
        tmdb_id: TMDB person ID.
        wikidata_qid: Wikidata entity ID.
        created_at: Timestamp when this record was created.
        updated_at: Timestamp when this record was last updated.
    """

    name: str
    index: Optional[int] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    country: Optional[str] = None
    biography: Optional[str] = None
    style: Optional[str] = None
    anecdotes: Optional[str] = None
    filmography: list[Film] = field(default_factory=list)
    awards: list[Award] = field(default_factory=list)
    external_sources: list[ExternalSource] = field(default_factory=list)
    external_snippets: list[ExternalSource] = field(default_factory=list)
    top_10: list[Film] = field(default_factory=list)
    image_url: Optional[str] = None
    image_local: Optional[str] = None
    wikipedia_url: Optional[str] = None
    tmdb_id: Optional[int] = None
    wikidata_qid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set timestamps if not provided."""
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def photo(self) -> Optional[str]:
        """Return the photo path (local or URL)."""
        return self.image_local or self.image_url

    @property
    def is_alive(self) -> bool:
        """Check if the composer is still alive."""
        return self.death_year is None

    @property
    def life_span(self) -> str:
        """Return formatted life span string."""
        if self.birth_year is None:
            return ""
        if self.death_year is None:
            return f"({self.birth_year}-)"
        return f"({self.birth_year}-{self.death_year})"

    @property
    def slug(self) -> str:
        """Generate URL-safe slug from name."""
        import re
        import unicodedata

        normalized = unicodedata.normalize("NFKD", self.name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower())
        return slug.strip("_") or "composer"

    @property
    def filename(self) -> str:
        """Generate filename for the composer's Markdown file."""
        if self.index is not None:
            return f"{self.index:03d}_{self.slug}.md"
        return f"{self.slug}.md"

    @property
    def folder_name(self) -> str:
        """Generate folder name for composer assets."""
        if self.index is not None:
            return f"{self.index:03d}_{self.slug}"
        return self.slug

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "index": self.index,
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "country": self.country,
            "biography": self.biography,
            "style": self.style,
            "anecdotes": self.anecdotes,
            "filmography": [f.to_dict() for f in self.filmography],
            "awards": [a.to_dict() for a in self.awards],
            "external_sources": [s.to_dict() for s in self.external_sources],
            "external_snippets": [s.to_dict() for s in self.external_snippets],
            "top_10": [f.to_dict() for f in self.top_10],
            "image_url": self.image_url,
            "image_local": self.image_local,
            "wikipedia_url": self.wikipedia_url,
            "tmdb_id": self.tmdb_id,
            "wikidata_qid": self.wikidata_qid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComposerInfo":
        """Create ComposerInfo from dictionary."""
        created_at = None
        updated_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            name=data.get("name", ""),
            index=data.get("index"),
            birth_year=data.get("birth_year"),
            death_year=data.get("death_year"),
            country=data.get("country"),
            biography=data.get("biography"),
            style=data.get("style"),
            anecdotes=data.get("anecdotes"),
            filmography=[Film.from_dict(f) for f in data.get("filmography", [])],
            awards=[Award.from_dict(a) for a in data.get("awards", [])],
            external_sources=[
                ExternalSource.from_dict(s) for s in data.get("external_sources", [])
            ],
            external_snippets=[
                ExternalSource.from_dict(s) for s in data.get("external_snippets", [])
            ],
            top_10=[Film.from_dict(f) for f in data.get("top_10", [])],
            image_url=data.get("image_url"),
            image_local=data.get("image_local"),
            wikipedia_url=data.get("wikipedia_url"),
            tmdb_id=data.get("tmdb_id"),
            wikidata_qid=data.get("wikidata_qid"),
            created_at=created_at,
            updated_at=updated_at,
        )
