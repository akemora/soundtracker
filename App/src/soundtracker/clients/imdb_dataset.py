"""IMDb dataset client for offline lookups.

Provides read-only access to a local SQLite database built from
IMDb TSV datasets (title.principals, name.basics, title.basics,
optional title.ratings).
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from soundtracker.config import settings
from soundtracker.models import Film

logger = logging.getLogger(__name__)


@dataclass
class ImdbPerson:
    """Represents a person entry from IMDb dataset."""

    nconst: str
    name: str
    birth_year: Optional[int]
    death_year: Optional[int]
    professions: Optional[str]
    credit_count: int = 0

    @property
    def is_music_professional(self) -> bool:
        """Check if IMDb professions hint at music/composer roles."""
        if not self.professions:
            return False
        lowered = self.professions.lower()
        return any(token in lowered for token in ("composer", "music", "soundtrack"))


class ImdbDataset:
    """Read-only client for local IMDb dataset in SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else settings.imdb_db_path

    @property
    def is_available(self) -> bool:
        """Check if the IMDb SQLite database exists."""
        return self.db_path.exists()

    def get_person_years(self, name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[ImdbPerson]:
        """Resolve person by name and return year metadata."""
        return self.resolve_person(name, conn=conn)

    def resolve_person(self, name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[ImdbPerson]:
        """Find the best matching person for a given name."""
        candidates = self.find_person_candidates(name, limit=8, conn=conn)
        return candidates[0] if candidates else None

    def find_person_candidates(
        self,
        name: str,
        limit: int = 5,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[ImdbPerson]:
        """Return candidate IMDb people matching a name."""
        if not self.is_available:
            return []

        normalized = name.strip()
        if not normalized:
            return []
        if conn is None:
            with self._connect() as opened:
                return self._find_person_candidates(opened, normalized, limit)
        return self._find_person_candidates(conn, normalized, limit)

    def get_composer_filmography(
        self,
        name: str,
        title_types: Optional[set[str]] = None,
        max_titles: Optional[int] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[Film]:
        """Fetch composer filmography from IMDb dataset."""
        if not self.is_available:
            return []

        person = self.resolve_person(name, conn=conn)
        if not person:
            return []

        title_types = title_types or {"movie", "tvMovie"}
        placeholders = ",".join("?" for _ in title_types)

        query = (
            "SELECT DISTINCT t.tconst, t.primaryTitle, t.originalTitle, "
            "       t.startYear, t.titleType, r.averageRating, r.numVotes "
            "FROM composer_credits c "
            "JOIN titles t ON t.tconst = c.tconst "
            "LEFT JOIN title_ratings r ON r.tconst = c.tconst "
            "WHERE c.nconst = ? "
            f"  AND t.titleType IN ({placeholders}) "
            "ORDER BY t.startYear, t.primaryTitle"
        )

        params = [person.nconst, *sorted(title_types)]
        films: list[Film] = []

        if conn is None:
            with self._connect() as opened:
                return self._fetch_films(opened, query, params, max_titles)
        return self._fetch_films(conn, query, params, max_titles)

    def _find_person_candidates(
        self,
        conn: sqlite3.Connection,
        normalized: str,
        limit: int,
    ) -> list[ImdbPerson]:
        exact_query = (
            "SELECT nconst, primaryName, birthYear, deathYear, primaryProfession "
            "FROM people "
            "WHERE primaryName = ? COLLATE NOCASE "
            "LIMIT ?"
        )
        rows = conn.execute(exact_query, (normalized, limit)).fetchall()

        if not rows:
            like_query = (
                "SELECT nconst, primaryName, birthYear, deathYear, primaryProfession "
                "FROM people "
                "WHERE primaryName LIKE ? COLLATE NOCASE "
                "LIMIT ?"
            )
            rows = conn.execute(like_query, (f"{normalized}%", limit)).fetchall()

        if not rows:
            fallback_query = (
                "SELECT nconst, primaryName, birthYear, deathYear, primaryProfession "
                "FROM people "
                "WHERE primaryName LIKE ? COLLATE NOCASE "
                "LIMIT ?"
            )
            rows = conn.execute(fallback_query, (f"%{normalized}%", limit)).fetchall()

        candidates = [
            ImdbPerson(
                nconst=row["nconst"],
                name=row["primaryName"],
                birth_year=row["birthYear"],
                death_year=row["deathYear"],
                professions=row["primaryProfession"],
            )
            for row in rows
        ]

        self._attach_credit_counts(conn, candidates)
        candidates.sort(key=lambda c: self._candidate_sort_key(c, normalized))
        return candidates

    def _fetch_films(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: list[str],
        max_titles: Optional[int],
    ) -> list[Film]:
        films: list[Film] = []
        for row in conn.execute(query, params):
            title = row["primaryTitle"] or row["originalTitle"] or ""
            if not title:
                continue
            films.append(
                Film(
                    title=title,
                    original_title=row["originalTitle"] or title,
                    year=row["startYear"],
                    vote_average=row["averageRating"],
                    vote_count=row["numVotes"],
                    imdb_id=row["tconst"],
                )
            )
            if max_titles and len(films) >= max_titles:
                break
        return films

    def _attach_credit_counts(self, conn: sqlite3.Connection, candidates: list[ImdbPerson]) -> None:
        """Attach composer credit counts for candidate ranking."""
        if not candidates:
            return

        for candidate in candidates:
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM composer_credits WHERE nconst = ?",
                (candidate.nconst,),
            ).fetchone()
            candidate.credit_count = int(count["count"]) if count else 0

    @staticmethod
    def _candidate_sort_key(candidate: ImdbPerson, target_name: str) -> tuple:
        """Sort candidates by match quality and composer likelihood."""
        exact = candidate.name.lower() == target_name.lower()
        return (
            0 if exact else 1,
            0 if candidate.is_music_professional else 1,
            -candidate.credit_count,
            candidate.birth_year or 9999,
            candidate.name,
        )

    def _connect(self) -> sqlite3.Connection:
        if not self.is_available:
            raise FileNotFoundError(f"IMDb database not found: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
