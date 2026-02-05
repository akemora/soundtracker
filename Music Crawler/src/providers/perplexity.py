"""Perplexity search provider."""

from __future__ import annotations

import os
from typing import Optional

import requests

from src.providers.base import SearchProvider


class PerplexityProvider(SearchProvider):
    """Search provider backed by Perplexity API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.perplexity.ai/v2",
        timeout: int = 10,
    ) -> None:
        self.api_key = api_key or os.environ.get("PPLX_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        """Search and return list of URLs."""
        return []

    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        return 1.0
