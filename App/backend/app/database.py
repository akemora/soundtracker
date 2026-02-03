"""Database connection manager for SOUNDTRACKER SQLite database.

This module provides async database connection management, query execution,
and specialized methods for FTS5 full-text search operations.
"""

import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import aiosqlite

from .config import get_settings

settings = get_settings()


class DatabaseError(Exception):
    """Custom database operation exception."""

    pass


class DatabaseManager:
    """Async SQLite database connection manager with FTS5 support.

    Provides connection management, query execution, and specialized methods
    for full-text search operations on the composers database.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize database manager.

        Args:
            database_url: Optional database path override.
        """
        self.database_url = database_url or settings.database_url
        self.database_path = Path(self.database_url)

    async def initialize(self) -> None:
        """Initialize database and verify tables exist.

        Raises:
            DatabaseError: If database initialization fails.
        """
        if not self.database_path.exists():
            raise DatabaseError(f"Database file not found: {self.database_path}")

        try:
            async with self.get_connection() as conn:
                # Verify required tables exist
                required_tables = [
                    "composers",
                    "films",
                    "awards",
                    "sources",
                    "fts_composers",
                ]

                for table in required_tables:
                    cursor = await conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,),
                    )
                    if not await cursor.fetchone():
                        raise DatabaseError(f"Required table '{table}' not found")

        except aiosqlite.Error as e:
            raise DatabaseError(f"Database initialization failed: {e}") from e

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get async database connection with context management.

        Yields:
            aiosqlite.Connection: Database connection instance.

        Raises:
            DatabaseError: If connection fails.
        """
        conn = None
        try:
            conn = await aiosqlite.connect(
                self.database_url,
                timeout=settings.database_timeout,
            )
            conn.row_factory = aiosqlite.Row

            # Enable optimizations
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")
            await conn.execute("PRAGMA cache_size = 10000")

            yield conn

        except sqlite3.Error as e:
            raise DatabaseError(f"Database connection failed: {e}") from e
        finally:
            if conn:
                await conn.close()

    async def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] = (),
        fetch_one: bool = False,
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Execute SQL query with parameters.

        Args:
            query: SQL query string.
            params: Query parameters tuple.
            fetch_one: Return single row if True.

        Returns:
            Query results as list of dicts or single dict.

        Raises:
            DatabaseError: If query execution fails.
        """
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(query, params)

                if fetch_one:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
                else:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except sqlite3.Error as e:
            raise DatabaseError(f"Query execution failed: {e}") from e

    async def execute_fts_search(
        self,
        search_term: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Execute FTS5 full-text search on composers.

        Args:
            search_term: Search query string.
            limit: Maximum results to return.

        Returns:
            List of matching composer records.

        Raises:
            DatabaseError: If FTS search fails.
        """
        limit = limit or settings.max_search_results

        # Sanitize search term for FTS5
        sanitized_term = search_term.replace('"', '""').strip()
        if not sanitized_term:
            return []

        query = """
            SELECT c.*,
                   bm25(fts_composers) as rank
            FROM fts_composers fts
            JOIN composers c ON fts.rowid = c.id
            WHERE fts_composers MATCH ?
            ORDER BY rank
            LIMIT ?
        """

        try:
            results = await self.execute_query(query, (f'"{sanitized_term}"', limit))
            return results if isinstance(results, list) else []
        except DatabaseError:
            # Fallback to LIKE search if FTS fails
            fallback_query = """
                SELECT *, 0 as rank
                FROM composers
                WHERE name LIKE ? OR biography_es LIKE ?
                LIMIT ?
            """
            search_pattern = f"%{sanitized_term}%"
            results = await self.execute_query(
                fallback_query,
                (search_pattern, search_pattern, limit),
            )
            return results if isinstance(results, list) else []

    async def get_composer_by_id(self, composer_id: int) -> dict[str, Any] | None:
        """Get composer by ID.

        Args:
            composer_id: Composer database ID.

        Returns:
            Composer data or None if not found.
        """
        query = "SELECT * FROM composers WHERE id = ?"
        result = await self.execute_query(query, (composer_id,), fetch_one=True)
        return result if isinstance(result, dict) else None

    async def get_composer_by_slug(self, slug: str) -> dict[str, Any] | None:
        """Get composer by slug.

        Args:
            slug: Composer URL slug.

        Returns:
            Composer data or None if not found.
        """
        query = "SELECT * FROM composers WHERE slug = ?"
        result = await self.execute_query(query, (slug,), fetch_one=True)
        return result if isinstance(result, dict) else None

    async def get_composer_films(
        self,
        composer_id: int,
        top10_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get films for a composer.

        Args:
            composer_id: Composer database ID.
            top10_only: Return only Top 10 films.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of film records.
        """
        where_clause = "WHERE composer_id = ?"
        params: list[Any] = [composer_id]

        if top10_only:
            where_clause += " AND is_top10 = 1"

        order_clause = "ORDER BY is_top10 DESC, top10_rank ASC, year DESC"

        query = f"SELECT * FROM films {where_clause} {order_clause}"

        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        results = await self.execute_query(query, tuple(params))
        return results if isinstance(results, list) else []

    async def get_composer_awards(self, composer_id: int) -> list[dict[str, Any]]:
        """Get awards for a composer.

        Args:
            composer_id: Composer database ID.

        Returns:
            List of award records.
        """
        query = """
            SELECT * FROM awards
            WHERE composer_id = ?
            ORDER BY year DESC, status DESC
        """
        results = await self.execute_query(query, (composer_id,))
        return results if isinstance(results, list) else []

    async def get_composer_stats(self, composer_id: int) -> dict[str, Any] | None:
        """Get statistics for a composer from the view.

        Args:
            composer_id: Composer database ID.

        Returns:
            Composer statistics or None.
        """
        query = "SELECT * FROM v_composer_stats WHERE id = ?"
        result = await self.execute_query(query, (composer_id,), fetch_one=True)
        return result if isinstance(result, dict) else None


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> DatabaseManager:
    """Dependency for getting database manager instance.

    Returns:
        DatabaseManager: Database manager instance.
    """
    return db_manager
