"""Perplexity search provider."""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

from src.providers.base import SearchProvider


class PerplexityProvider(SearchProvider):
    """Search provider backed by Perplexity API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.perplexity.ai/v2",
        model: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        self.api_key = api_key or os.environ.get("PPLX_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model or os.environ.get("PPLX_MODEL", "sonar")
        self.timeout = timeout
        self.session = requests.Session()

    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        """Search and return list of URLs."""
        data = self._request(query, site_filter=site_filter)
        if not data:
            return []
        return []

    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        return 1.0

    def _request(self, query: str, site_filter: str | None = None) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        final_query = query
        if site_filter:
            final_query = f"site:{site_filter} {query}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Devuelve resultados de busqueda con URLs fiables.",
                },
                {"role": "user", "content": final_query},
            ],
            "max_tokens": 128,
            "temperature": 0.2,
        }

        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
