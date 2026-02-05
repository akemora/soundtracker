"""Base logging configuration for Music Crawler."""

from __future__ import annotations

import logging
from typing import Optional, Union

_DEFAULT_LOGGER_NAME = "music_crawler"
_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def _resolve_level(level: Optional[Union[int, str]]) -> int:
    if level is None:
        return logging.INFO
    if isinstance(level, int):
        return level
    normalized = level.upper()
    if normalized in _LOG_LEVELS:
        return _LOG_LEVELS[normalized]
    raise ValueError(f"Unsupported log level: {level}")


def configure_logging(level: Optional[Union[int, str]] = None) -> None:
    """Configure base logging for the application.

    Args:
        level: Optional logging level to set globally.
    """
    resolved_level = _resolve_level(level)
    logging.basicConfig(level=resolved_level, format=_LOG_FORMAT)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Optional logger name. Defaults to the app logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name or _DEFAULT_LOGGER_NAME)


__all__ = ["configure_logging", "get_logger"]
