"""YouTube Data API client.

Provides access to YouTube API for searching soundtrack videos
and getting view counts.
"""

import logging
from typing import Optional

from soundtracker.cache import FileCache
from soundtracker.clients.base import BaseClient
from soundtracker.config import settings

logger = logging.getLogger(__name__)


class YouTubeClient(BaseClient):
    """Client for YouTube Data API v3.

    Provides methods to search for soundtrack videos and get
    popularity metrics (view counts).

    Example:
        client = YouTubeClient(api_key="your_key")
        views = client.search_views("John Williams", "Star Wars")
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[FileCache] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize YouTube client.

        Args:
            api_key: YouTube Data API v3 key.
            cache: Optional cache for responses.
            timeout: Request timeout in seconds.
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )
        self.api_key = api_key or settings.youtube_api_key
        self.cache = cache

    @property
    def is_available(self) -> bool:
        """Check if API key is configured and enabled."""
        return settings.youtube_enabled and bool(self.api_key)

    def health_check(self) -> bool:
        """Check if YouTube API is available.

        Returns:
            True if API responds successfully.
        """
        if not self.api_key:
            return False

        result = self._get("videos", {"part": "id", "id": "dQw4w9WgXcQ", "key": self.api_key})
        return result is not None

    def search_views(
        self,
        composer: str,
        title: str,
        max_results: int = 5,
    ) -> Optional[int]:
        """Search for soundtrack video and get max view count.

        Args:
            composer: Composer name.
            title: Film/soundtrack title.
            max_results: Number of videos to check.

        Returns:
            Maximum view count found or None.
        """
        if not self.is_available or not title:
            return None

        # Check cache
        if self.cache:
            cache_key = f"youtube|{composer}|{title}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached.get("views")

        query = f"{title} soundtrack {composer}".strip()

        # Search for videos
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": str(max_results),
            "order": "viewCount",
            "videoCategoryId": "10",  # Music category
            "key": self.api_key,
        }

        search_data = self._get("search", search_params)
        if not search_data:
            return None

        video_ids = [
            item.get("id", {}).get("videoId")
            for item in search_data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return None

        # Get video statistics
        videos_params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
        }

        videos_data = self._get("videos", videos_params)
        if not videos_data:
            return None

        max_views: Optional[int] = None
        for item in videos_data.get("items", []):
            count_str = item.get("statistics", {}).get("viewCount")
            if count_str is None:
                continue
            try:
                views = int(count_str)
                if max_views is None or views > max_views:
                    max_views = views
            except (ValueError, TypeError):
                continue

        # Cache result
        if self.cache and max_views is not None:
            self.cache.set(f"youtube|{composer}|{title}", {"views": max_views})

        return max_views

    def get_video_views(self, video_id: str) -> Optional[int]:
        """Get view count for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            View count or None.
        """
        if not self.is_available:
            return None

        params = {
            "part": "statistics",
            "id": video_id,
            "key": self.api_key,
        }

        data = self._get("videos", params)
        if not data:
            return None

        items = data.get("items", [])
        if not items:
            return None

        count_str = items[0].get("statistics", {}).get("viewCount")
        if count_str is None:
            return None

        try:
            return int(count_str)
        except (ValueError, TypeError):
            return None
