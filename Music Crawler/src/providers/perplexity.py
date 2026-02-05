"""Perplexity search provider."""

from __future__ import annotations

import os
import re
from typing import Any, Optional

import requests

from src.core.logger import get_logger
from src.providers.base import SearchProvider

logger = get_logger(__name__)


class PerplexityProvider(SearchProvider):
    """Search provider backed by Perplexity API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.perplexity.ai/v2",
        model: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("PPLX_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model or os.environ.get("PPLX_MODEL", "sonar")
        self.timeout = timeout
        self.session = requests.Session()

    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        """Search and return list of URLs."""
        self.wait_rate_limit()
        data = self._request(query, site_filter=site_filter)
        if not data:
            return []
        urls: list[str] = []

        for item in data.get("search_results") or []:
            url = item.get("url")
            if url and url not in urls:
                urls.append(url)

        if not urls:
            for url in data.get("citations") or []:
                if url and url not in urls:
                    urls.append(url)

        if not urls:
            content = ""
            choices = data.get("choices") or []
            if choices:
                content = (choices[0].get("message") or {}).get("content") or ""
            for match in re.findall(r"https?://\\S+", content):
                cleaned = match.strip(').,;]"\\'')
                if cleaned not in urls:
                    urls.append(cleaned)

        return urls[:num_results]

    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        return 0.5

    def _request(self, query: str, site_filter: str | None = None) -> dict[str, Any] | None:
        if not self.api_key:
            logger.error("PPLX_API_KEY is not set", exc_info=True)
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

        try:
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
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else None
            if status in {401, 403}:
                logger.error("Perplexity API key unauthorized", exc_info=True)
            elif status == 429:
                logger.error("Perplexity API rate limited", exc_info=True)
            else:
                logger.error("Perplexity API request failed", exc_info=True)
        except requests.Timeout:
            logger.error("Perplexity API request timed out", exc_info=True)
        except requests.RequestException:
            logger.error("Perplexity API request error", exc_info=True)
        return None
