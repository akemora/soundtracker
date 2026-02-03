"""Cache module for SOUNDTRACKER.

Provides file-based caching for API responses to reduce redundant calls
and improve performance.
"""

from soundtracker.cache.file_cache import FileCache

__all__ = ["FileCache"]
