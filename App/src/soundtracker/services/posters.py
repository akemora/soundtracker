"""Poster download service for film posters.

Provides functionality to download and manage poster images
from TMDB and web sources.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import requests

from soundtracker.clients import SearchClient, TMDBClient
from soundtracker.config import settings
from soundtracker.models import Film

logger = logging.getLogger(__name__)


class PosterService:
    """Service for downloading and managing film posters.

    Downloads posters from TMDB with web search fallback.

    Example:
        service = PosterService()
        service.download_posters(films, composer_folder)
    """

    PLACEHOLDER_IMAGE = "https://example.com/placeholder.jpg"

    def __init__(
        self,
        tmdb_client: Optional[TMDBClient] = None,
        search_client: Optional[SearchClient] = None,
        workers: int = 8,
        timeout: int = 10,
        web_fallback: bool = True,
    ) -> None:
        """Initialize poster service.

        Args:
            tmdb_client: TMDB client for posters.
            search_client: Search client for fallback.
            workers: Concurrent download workers.
            timeout: Download timeout in seconds.
            web_fallback: Enable web search fallback.
        """
        self.tmdb = tmdb_client or TMDBClient()
        self.search = search_client or SearchClient()
        self.workers = workers or settings.poster_workers
        self.timeout = timeout
        self.web_fallback = web_fallback if web_fallback is not None else settings.poster_web_fallback
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Soundtracker/2.0",
            "Referer": "https://en.wikipedia.org",
        })

    def download_posters(
        self,
        films: list[Film],
        composer_folder: Path,
        limit: Optional[int] = None,
    ) -> None:
        """Download posters for a list of films.

        Args:
            films: Films to download posters for.
            composer_folder: Folder to save posters.
            limit: Maximum posters to download.
        """
        if not settings.download_posters:
            return

        limit = limit or settings.poster_limit or len(films)
        posters_dir = composer_folder / "posters"
        posters_dir.mkdir(parents=True, exist_ok=True)

        tasks = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            for idx, film in enumerate(films):
                if limit and idx >= limit:
                    break

                poster_url = film.poster_url
                if not poster_url and film.poster_path:
                    poster_url = self.tmdb.get_poster_url(film.poster_path)

                if not poster_url:
                    continue

                poster_file = Path(film.poster_file) if film.poster_file else (
                    posters_dir / self._poster_filename(
                        film.original_title or film.title,
                        film.year,
                    )
                )

                if poster_file.exists():
                    film.poster_local = str(poster_file)
                    continue

                tasks[executor.submit(self._download_image, poster_url, poster_file)] = film

            for future in as_completed(tasks):
                film = tasks[future]
                try:
                    saved = future.result()
                    if saved:
                        film.poster_local = saved
                except Exception as e:
                    logger.debug("Poster download failed: %s", e)

        # Handle missing posters with web fallback
        if self.web_fallback:
            missing = [f for f in films[:limit] if not f.poster_local]
            self._download_missing(missing, composer_folder)

    def _download_missing(
        self,
        films: list[Film],
        composer_folder: Path,
    ) -> None:
        """Download missing posters using web search.

        Args:
            films: Films with missing posters.
            composer_folder: Folder to save posters.
        """
        posters_dir = composer_folder / "posters"

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            tasks = {}
            for film in films:
                poster_file = Path(film.poster_file) if film.poster_file else (
                    posters_dir / self._poster_filename(
                        film.original_title or film.title,
                        film.year,
                    )
                )

                tasks[executor.submit(
                    self._get_poster_from_web,
                    film.original_title or film.title or "",
                    composer_folder,
                    film.poster_url,
                    film.year,
                    poster_file,
                )] = film

            for future in as_completed(tasks):
                film = tasks[future]
                try:
                    result = future.result()
                    if result:
                        film.poster_local = result
                    else:
                        film.poster_local = self.PLACEHOLDER_IMAGE
                except Exception:
                    film.poster_local = self.PLACEHOLDER_IMAGE

    def _download_image(self, url: str, path: Path) -> Optional[str]:
        """Download an image from URL.

        Args:
            url: Image URL.
            path: Target file path.

        Returns:
            Path string if successful, None otherwise.
        """
        if not url:
            return None

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = self._session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            with path.open("wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)

            return str(path)
        except Exception as e:
            logger.debug("Image download error %s: %s", url, e)
            if path.exists():
                path.unlink()
            return None

    def _get_poster_from_web(
        self,
        title: str,
        composer_folder: Path,
        primary_url: Optional[str] = None,
        year: Optional[int] = None,
        target_path: Optional[Path] = None,
    ) -> Optional[str]:
        """Get poster from web search.

        Args:
            title: Film title.
            composer_folder: Composer assets folder.
            primary_url: Primary URL to try first.
            year: Release year.
            target_path: Target file path.

        Returns:
            Path string if successful, None otherwise.
        """
        posters_dir = composer_folder / "posters"
        target = target_path or (posters_dir / self._poster_filename(title, year))

        if target.exists():
            return str(target)

        # Try primary URL first
        if primary_url:
            result = self._download_image(primary_url, target)
            if result:
                return result

        # Search for poster
        query = f"{title} {year or ''} movie poster".strip()
        urls = self.search.search(query, num=3)

        for url in urls:
            if not self._is_image_url(url):
                continue
            result = self._download_image(url, target)
            if result:
                return result

        return None

    def _is_image_url(self, url: str) -> bool:
        """Check if URL appears to be an image.

        Args:
            url: URL to check.

        Returns:
            True if likely an image URL.
        """
        lower = url.lower()
        return any(ext in lower for ext in [".jpg", ".jpeg", ".png", ".webp"])

    def _poster_filename(self, title: str, year: Optional[int] = None) -> str:
        """Generate poster filename.

        Args:
            title: Film title.
            year: Release year.

        Returns:
            Filename for poster.
        """
        slug = re.sub(r"[^a-z0-9]+", "_", (title or "poster").lower()).strip("_") or "poster"
        if year:
            return f"poster_{slug}_{year}.jpg"
        return f"poster_{slug}.jpg"
