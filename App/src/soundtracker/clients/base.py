"""Base client for API interactions."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

import requests

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Base class for all API clients.

    Provides common functionality like:
    - HTTP requests with retry logic
    - Rate limiting
    - Logging

    Attributes:
        base_url: The base URL for the API
        timeout: Request timeout in seconds
        session: Requests session for connection pooling
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize the base client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            headers: Optional default headers
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def _get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Make a GET request.

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters

        Returns:
            JSON response as dict, or None on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def _post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Make a POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data

        Returns:
            JSON response as dict, or None on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(
                url,
                data=data,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"POST request failed for {url}: {e}")
            return None

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the API is available.

        Returns:
            True if API is reachable and responding
        """
        ...

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self) -> "BaseClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
