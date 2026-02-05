"""Base logging configuration for Music Crawler."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

from src.core.config import settings
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
        level = settings.log_level
    if isinstance(level, int):
        return level
    normalized = level.upper()
    if normalized in _LOG_LEVELS:
        return _LOG_LEVELS[normalized]
    raise ValueError(f"Unsupported log level: {level}")


def configure_logging(
    level: Optional[Union[int, str]] = None,
    log_file: Optional[Union[str, Path]] = None,
) -> None:
    """Configure base logging for the application.

    Args:
        level: Optional logging level to set globally.
    """
    resolved_level = _resolve_level(level)
    handlers = [logging.StreamHandler()]

    if log_file is None:
        log_file = settings.log_file or (Path("logs") / "music_crawler.log")
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(
        RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
    )

    logging.basicConfig(level=resolved_level, format=_LOG_FORMAT, handlers=handlers)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Optional logger name. Defaults to the app logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name or _DEFAULT_LOGGER_NAME)


__all__ = ["configure_logging", "get_logger"]
