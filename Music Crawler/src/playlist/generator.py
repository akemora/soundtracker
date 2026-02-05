"""Playlist generator for composer top tracks."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.playlist.embed import EmbedResolver
from src.playlist.models import Playlist, PlaylistTrack
from src.providers.chrome import ChromeProvider
from src.providers.perplexity import PerplexityProvider
from src.searchers.amazon import AmazonMusicSearcher
from src.searchers.archive_org import ArchiveOrgSearcher
from src.searchers.bandcamp import BandcampSearcher
from src.searchers.soundcloud import SoundCloudSearcher
from src.searchers.spotify import ITunesSearcher, SpotifySearcher
from src.searchers.youtube import YouTubeSearcher

logger = get_logger(__name__)


@dataclass
class Film:
    """Simple film representation for playlist generation."""

    title: str
    year: int | None


class SourcePriority(Enum):
    """Priority for playlist sources (higher is better)."""

    YOUTUBE = 100
    SOUNDCLOUD = 90
    ARCHIVE = 80
    SPOTIFY = 50
    BANDCAMP = 30
    ITUNES = 20
    AMAZON = 20


class PlaylistGenerator:
    """Generate a playable playlist from a composer's Top 10 films."""

    def __init__(
        self,
        composer_slug: str,
        db_path: Path,
        searchers: dict[str, list[Any]] | None = None,
    ) -> None:
        self.composer_slug = composer_slug
        self.db_path = db_path
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.composer_name = self._get_composer_name()
        self.free_searchers, self.paid_searchers = self._init_searchers(searchers)

    def close(self) -> None:
        """Close the database connection."""
        if self.db:
            self.db.close()

    def generate(self) -> Playlist:
        """Generate playlist with fallback logic."""
        top_films = self._get_top_films()
        tracks: list[PlaylistTrack] = []

        for position, film in enumerate(top_films, start=1):
            playlist_track = self._find_playable_track(film, position)
            if playlist_track:
                tracks.append(playlist_track)
            else:
                logger.warning("No playable track for %s", film.title)

        return Playlist(
            composer_slug=self.composer_slug,
            composer_name=self.composer_name,
            tracks=tracks,
        )

    def _get_composer_name(self) -> str:
        cursor = self.db.execute(
            "SELECT name FROM composers WHERE slug = ?",
            (self.composer_slug,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Composer not found: {self.composer_slug}")
        return row["name"]

    def _get_top_films(self) -> list[Film]:
        """Fetch Top 10 films for the composer."""
        cursor = self.db.execute(
            """
            SELECT top10_rank, title, title_es, original_title, year
            FROM v_top10_films
            WHERE composer_slug = ?
            ORDER BY top10_rank
            """,
            (self.composer_slug,),
        )
        rows = cursor.fetchall()

        if not rows:
            cursor = self.db.execute(
                """
                SELECT title, title_es, original_title, year
                FROM films
                WHERE composer_id = (SELECT id FROM composers WHERE slug = ?)
                  AND is_top10 = 1
                ORDER BY top10_rank
                """,
                (self.composer_slug,),
            )
            rows = cursor.fetchall()

        films: list[Film] = []
        for row in rows:
            title = row["title_es"] or row["title"] or row["original_title"]
            year = row["year"] if "year" in row.keys() else None
            if title:
                films.append(Film(title=title, year=year))
        return films

    def _get_popular_track(self, film: Film, position: int) -> Track:
        """Identify the primary track for a film (default Main Title)."""
        return Track(
            rank=position,
            film=film.title,
            cue_title="Main Title",
            description="",
            composer=self.composer_name,
        )

    def _get_alternative_tracks(self, film: Film, position: int) -> list[Track]:
        """Generate alternative tracks for fallback search."""
        candidates = [
            "Main Theme",
            "Theme",
            f"{film.title} Theme",
            "End Credits",
            "Suite",
        ]
        tracks: list[Track] = []
        seen = set()
        for title in candidates:
            normalized = title.lower()
            if normalized in seen or title == "Main Title":
                continue
            seen.add(normalized)
            tracks.append(
                Track(
                    rank=position,
                    film=film.title,
                    cue_title=title,
                    description="",
                    composer=self.composer_name,
                )
            )
        return tracks

    def _search_free_source(self, track: Track) -> list[SearchResult]:
        """Search free sources for a given track."""
        results: list[SearchResult] = []
        for searcher in self.free_searchers:
            try:
                results.extend(searcher.search(track))
            except Exception as exc:
                logger.error(
                    "Free search failed (%s): %s",
                    searcher.name,
                    exc,
                    exc_info=True,
                )
        return results

    def _search_paid_sources(self, track: Track) -> list[SearchResult]:
        """Search paid sources for purchase links."""
        results: list[SearchResult] = []
        for searcher in self.paid_searchers:
            try:
                results.extend(searcher.search(track))
            except Exception as exc:
                logger.error(
                    "Paid search failed (%s): %s",
                    searcher.name,
                    exc,
                    exc_info=True,
                )
        return results

    def _find_playable_track(self, film: Film, position: int) -> PlaylistTrack | None:
        """Find a playable track using fallback logic."""
        primary_track = self._get_popular_track(film, position)
        free_results = self._search_free_source(primary_track)
        best_free = self._pick_best_result(free_results)

        if best_free and best_free.is_free:
            return self._create_playlist_track(
                film=film,
                track=primary_track,
                result=best_free,
                position=position,
                alternatives=self._serialize_alternatives(free_results),
                is_original_pick=True,
            )

        for alt_track in self._get_alternative_tracks(film, position):
            alt_results = self._search_free_source(alt_track)
            best_alt = self._pick_best_result(alt_results)
            if best_alt and best_alt.is_free:
                return self._create_playlist_track(
                    film=film,
                    track=alt_track,
                    result=best_alt,
                    position=position,
                    alternatives=self._serialize_alternatives(alt_results),
                    is_original_pick=False,
                    fallback_reason=(
                        f"original '{primary_track.cue_title}' not available free"
                    ),
                )

        paid_results = self._search_paid_sources(primary_track)
        paid_links = self._get_purchase_links(primary_track, paid_results)
        best_paid = self._pick_best_result(paid_results)

        if best_paid:
            return self._create_playlist_track(
                film=film,
                track=primary_track,
                result=best_paid,
                position=position,
                alternatives=self._serialize_alternatives(paid_results),
                is_original_pick=True,
                purchase_links=paid_links,
            )

        if paid_links:
            placeholder = SearchResult(
                track=primary_track,
                source=paid_links[0]["source"],
                url=paid_links[0]["url"],
                is_free=False,
                quality="",
            )
            return self._create_playlist_track(
                film=film,
                track=primary_track,
                result=placeholder,
                position=position,
                alternatives=[],
                is_original_pick=True,
                purchase_links=paid_links,
            )

        return None

    def _get_purchase_links(
        self,
        track: Track,
        results: list[SearchResult] | None = None,
    ) -> list[dict[str, Any]]:
        """Collect purchase links from paid sources."""
        links: list[dict[str, Any]] = []
        paid_results = results or self._search_paid_sources(track)
        for result in paid_results:
            links.append({"source": result.source, "url": result.url, "price": None})
        return links

    def _create_playlist_track(
        self,
        film: Film,
        track: Track,
        result: SearchResult,
        position: int,
        alternatives: list[dict[str, Any]],
        is_original_pick: bool,
        fallback_reason: str | None = None,
        purchase_links: list[dict[str, Any]] | None = None,
    ) -> PlaylistTrack:
        is_free = result.is_free
        embed_url = EmbedResolver.resolve(result.source, result.url) if is_free else None
        thumbnail = self._youtube_thumbnail(result.url) if result.source == "youtube" else None

        return PlaylistTrack(
            position=position,
            film=film.title,
            film_year=film.year,
            track_title=track.cue_title,
            source=result.source,
            url=result.url,
            embed_url=embed_url,
            is_free=is_free,
            duration=result.duration,
            thumbnail=thumbnail,
            is_original_pick=is_original_pick,
            fallback_reason=fallback_reason,
            alternatives=alternatives,
            purchase_links=purchase_links or [],
        )

    def _serialize_alternatives(self, results: list[SearchResult]) -> list[dict[str, Any]]:
        return [
            {
                "source": result.source,
                "url": result.url,
                "is_free": result.is_free,
                "title": result.title,
            }
            for result in results
        ]

    def _pick_best_result(self, results: list[SearchResult]) -> SearchResult | None:
        if not results:
            return None
        return max(results, key=lambda result: self._priority_for_source(result.source))

    def _priority_for_source(self, source: str) -> int:
        try:
            return SourcePriority[source.upper()].value
        except KeyError:
            return 0

    def _youtube_thumbnail(self, url: str) -> str | None:
        video_id = EmbedResolver._extract_youtube_id(url)
        if not video_id:
            return None
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    def _init_searchers(
        self,
        searchers: dict[str, list[Any]] | None,
    ) -> tuple[list[Any], list[Any]]:
        if searchers:
            return searchers.get("free", []), searchers.get("paid", [])

        provider = self._build_provider()

        free_searchers = [
            self._safe_init_searcher(YouTubeSearcher, provider, 2),
            self._safe_init_searcher(SoundCloudSearcher, provider, 2),
            self._safe_init_searcher(ArchiveOrgSearcher, provider, 2),
        ]
        paid_searchers = [
            self._safe_init_searcher(SpotifySearcher, provider, 1),
            self._safe_init_searcher(ITunesSearcher, provider, 1),
            self._safe_init_searcher(AmazonMusicSearcher, provider, 1),
            self._safe_init_searcher(BandcampSearcher, provider, 1),
        ]
        return free_searchers, paid_searchers

    def _build_provider(self):
        provider = PerplexityProvider()
        if provider.api_key:
            logger.info("Using Perplexity provider for playlist search")
            return provider
        logger.warning("PPLX_API_KEY not set; using Chrome provider for playlist search")
        return ChromeProvider()

    def _safe_init_searcher(self, cls, provider, max_results: int):
        try:
            return cls(provider=provider, max_results=max_results)
        except TypeError:
            return cls(max_results=max_results)
