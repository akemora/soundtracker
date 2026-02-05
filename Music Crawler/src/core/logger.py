"""Base logging configuration for Music Crawler."""

from __future__ import annotations

import logging
from typing import Optional

_DEFAULT_LOGGER_NAME = "music_crawler"
_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"


def configure_logging(level: Optional[int] = None) -> None:
    """Configure base logging for the application.

    Args:
        level: Optional logging level to set globally.
    """
    if level is None:
        logging.basicConfig(format=_LOG_FORMAT)
    else:
        logging.basicConfig(level=level, format=_LOG_FORMAT)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Optional logger name. Defaults to the app logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name or _DEFAULT_LOGGER_NAME)


__all__ = ["configure_logging", "get_logger"]
