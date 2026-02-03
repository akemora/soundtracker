"""Top 10 soundtrack selection service.

Provides functionality to select and rank the top 10 most notable
soundtracks for a composer based on multiple signals.
"""

import logging
import math
import re
from datetime import datetime
from typing import Optional

from soundtracker.clients import SearchClient, SpotifyClient, YouTubeClient
from soundtracker.config import settings
from soundtracker.models import Award, Film

logger = logging.getLogger(__name__)


class Top10Service:
    """Service for selecting top 10 soundtracks.

    Uses multiple signals to rank films:
    - TMDB popularity and votes
    - Spotify popularity
    - YouTube views
    - Web search rankings
    - Awards

    Example:
        service = Top10Service()
        top10 = service.select_top_10(composer, filmography, awards)
    """

    def __init__(
        self,
        spotify_client: Optional[SpotifyClient] = None,
        youtube_client: Optional[YouTubeClient] = None,
        search_client: Optional[SearchClient] = None,
        min_vote_count: int = 50,
        streaming_candidate_limit: int = 30,
        force_awards: bool = True,
    ) -> None:
        """Initialize Top 10 service.

        Args:
            spotify_client: Spotify client for popularity.
            youtube_client: YouTube client for views.
            search_client: Search client for web rankings.
            min_vote_count: Minimum TMDB votes for eligibility.
            streaming_candidate_limit: Films to check for streaming.
            force_awards: Force award winners in Top 10.
        """
        self.spotify = spotify_client or SpotifyClient()
        self.youtube = youtube_client or YouTubeClient()
        self.search = search_client or SearchClient()
        self.min_vote_count = min_vote_count or settings.top_min_vote_count
        self.streaming_limit = streaming_candidate_limit or settings.streaming_candidate_limit
        self.force_awards = force_awards if force_awards is not None else settings.top_force_awards

    def select_top_10(
        self,
        composer: str,
        filmography: list[Film],
        awards: Optional[list[Award]] = None,
        boost_scores: Optional[dict[str, int]] = None,
    ) -> list[Film]:
        """Select top 10 soundtracks for a composer.

        Args:
            composer: Composer name.
            filmography: List of all films.
            awards: List of awards.
            boost_scores: External ranking boosts.

        Returns:
            Top 10 films sorted by score.
        """
        if not filmography:
            return []

        awards = awards or []
        boost_scores = boost_scores or {}

        # Build award keys
        award_keys = set()
        for award in awards:
            if award.film:
                award_keys.add(self._normalize_key(award.film))

        current_year = datetime.utcnow().year

        # Filter eligible films
        eligible = []
        for film in filmography:
            if film.year and film.year > current_year:
                continue
            if isinstance(film.vote_count, (int, float)) and film.vote_count < self.min_vote_count:
                continue
            eligible.append(film)

        if len(eligible) < 10:
            eligible = filmography

        # Add streaming signals for top candidates
        self._add_streaming_signals(composer, eligible, boost_scores, award_keys)

        # Check for signal coverage
        signaled = [f for f in eligible if self._has_signal(f, boost_scores, award_keys)]
        if len(signaled) >= 6:
            eligible = signaled

        # Score and rank
        ranked = sorted(
            eligible,
            key=lambda f: (
                self._score_film(f, boost_scores, award_keys, current_year),
                f.year or 0,
            ),
            reverse=True,
        )

        # Select unique top 10
        unique: list[Film] = []
        seen_keys: set[str] = set()

        # Force award winners first
        if self.force_awards and award_keys:
            award_entries = [
                f for f in eligible
                if any(key in award_keys for key in self._build_keys(f))
            ]
            award_entries.sort(
                key=lambda f: (
                    self._score_film(f, boost_scores, award_keys, current_year),
                    f.year or 0,
                ),
                reverse=True,
            )
            for film in award_entries:
                keys = self._build_keys(film)
                if any(key in seen_keys for key in keys):
                    continue
                seen_keys.update(keys)
                unique.append(film)
                if len(unique) >= 10:
                    return unique

        # Fill remaining slots
        for film in ranked:
            keys = self._build_keys(film)
            if any(key in seen_keys for key in keys):
                continue
            seen_keys.update(keys)
            unique.append(film)
            if len(unique) >= 10:
                break

        return unique

    def get_web_rankings(self, composer: str) -> dict[str, int]:
        """Get film rankings from web searches.

        Args:
            composer: Composer name.

        Returns:
            Dict mapping title keys to boost scores.
        """
        if not self.search.is_enabled:
            return {}

        queries = [
            f"{composer} mejores bandas sonoras lista",
            f"{composer} mejores bandas sonoras",
            f"{composer} best film scores ranked list",
            f"{composer} best film scores",
        ]

        urls: list[str] = []
        for query in queries:
            urls.extend(self.search.search(query, num=6))

        counts: dict[str, int] = {}
        for url in urls:
            html = self.search.fetch_url_text(url)
            if not html:
                continue

            titles = self._extract_titles_from_html(html)
            for title in titles:
                key = self._normalize_key(title)
                if key:
                    counts[key] = counts.get(key, 0) + 1

        return counts

    def _score_film(
        self,
        film: Film,
        boost_scores: dict[str, int],
        award_keys: set[str],
        current_year: int,
    ) -> float:
        """Calculate film score for ranking.

        Args:
            film: Film to score.
            boost_scores: External ranking boosts.
            award_keys: Keys of award-winning films.
            current_year: Current year for recency.

        Returns:
            Numeric score.
        """
        score = 0.0

        # TMDB signals
        if isinstance(film.popularity, (int, float)):
            score += float(film.popularity)
        if isinstance(film.vote_count, (int, float)):
            score += math.log10(float(film.vote_count) + 1) * 7
        if isinstance(film.vote_average, (int, float)):
            score += float(film.vote_average) * 2

        # Streaming signals
        if isinstance(film.spotify_popularity, (int, float)):
            score += float(film.spotify_popularity) * 0.6
        if isinstance(film.youtube_views, (int, float)):
            score += math.log10(float(film.youtube_views) + 1) * 5

        # Web ranking boost
        for key in self._build_keys(film):
            if key in boost_scores:
                score += 40 + (boost_scores[key] * 10)
                break

        # Award boost
        for key in self._build_keys(film):
            if key in award_keys:
                score += 20
                break

        # Recency bonus
        if film.year:
            score += (film.year % 100) * 0.05
            if film.year > current_year:
                score -= 100

        # Low vote penalty
        if isinstance(film.vote_count, (int, float)) and film.vote_count < self.min_vote_count:
            score -= 30

        return score

    def _add_streaming_signals(
        self,
        composer: str,
        films: list[Film],
        boost_scores: dict[str, int],
        award_keys: set[str],
    ) -> None:
        """Add streaming signals to top candidates.

        Args:
            composer: Composer name.
            films: Films to check.
            boost_scores: For initial ranking.
            award_keys: Award-winning film keys.
        """
        if not (self.spotify.is_available or self.youtube.is_available):
            return

        current_year = datetime.utcnow().year

        # Pre-rank for candidate selection
        ranked = sorted(
            films,
            key=lambda f: (
                self._score_film(f, boost_scores, award_keys, current_year),
                f.year or 0,
            ),
            reverse=True,
        )

        for film in ranked[: self.streaming_limit]:
            title = film.original_title or film.title
            if not title:
                continue

            if film.spotify_popularity is None and self.spotify.is_available:
                film.spotify_popularity = self.spotify.search_popularity(composer, title)

            if film.youtube_views is None and self.youtube.is_available:
                film.youtube_views = self.youtube.search_views(composer, title)

    def _has_signal(
        self,
        film: Film,
        boost_scores: dict[str, int],
        award_keys: set[str],
    ) -> bool:
        """Check if film has any ranking signal.

        Args:
            film: Film to check.
            boost_scores: Web ranking boosts.
            award_keys: Award-winning film keys.

        Returns:
            True if film has a signal.
        """
        for key in self._build_keys(film):
            if key in boost_scores or key in award_keys:
                return True
        return False

    def _build_keys(self, film: Film) -> list[str]:
        """Build normalized keys for a film.

        Args:
            film: Film to process.

        Returns:
            List of normalized keys.
        """
        keys: list[str] = []
        for title in [film.original_title, film.title, film.title_es]:
            if title:
                key = self._normalize_key(title)
                if key and key not in keys:
                    keys.append(key)
        return keys

    def _normalize_key(self, title: str) -> str:
        """Normalize title for comparison.

        Args:
            title: Title to normalize.

        Returns:
            Normalized key.
        """
        return re.sub(r"[^a-z0-9]+", "", title.lower())

    def _extract_titles_from_html(self, html: str, max_titles: int = 15) -> list[str]:
        """Extract film titles from HTML list.

        Args:
            html: HTML content.
            max_titles: Maximum titles to extract.

        Returns:
            List of titles.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        container = (
            soup.select_one("div.mw-parser-output")
            or soup.select_one("article")
            or soup.select_one("main")
            or soup
        )

        titles: list[str] = []
        for li in container.find_all("li"):
            candidate = self._normalize_title(li.get_text(" ", strip=True))
            if not candidate:
                continue
            if candidate not in titles:
                titles.append(candidate)
            if len(titles) >= max_titles:
                break

        return titles

    def _normalize_title(self, text: str) -> Optional[str]:
        """Normalize extracted title text.

        Args:
            text: Raw title text.

        Returns:
            Cleaned title or None.
        """
        cleaned = re.sub(r"^\d+\.?\s*", "", text.strip())
        cleaned = re.sub(r"\s*\(\d{4}\)\s*", "", cleaned).strip(" .-–:;")
        if not cleaned or len(cleaned) < 2 or len(cleaned) > 90:
            return None
        return cleaned
