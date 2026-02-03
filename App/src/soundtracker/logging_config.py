"""Logging configuration for SOUNDTRACKER.

Provides centralized logging setup with consistent formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from soundtracker.config import settings


def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Configure logging for the application.

    Args:
        level: Logging level (default: from settings or INFO).
        log_file: Optional file path for logging.
        format_string: Custom format string.

    Returns:
        Root logger configured.
    """
    level = level or getattr(logging, settings.log_level.upper(), logging.INFO)

    format_string = format_string or (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name (usually __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class LoggingContext:
    """Context manager for temporary logging configuration."""

    def __init__(
        self,
        level: int,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize logging context.

        Args:
            level: Temporary logging level.
            logger: Logger to modify (default: root).
        """
        self.level = level
        self.logger = logger or logging.getLogger()
        self.original_level: Optional[int] = None

    def __enter__(self) -> "LoggingContext":
        """Enter context and change log level."""
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore log level."""
        if self.original_level is not None:
            self.logger.setLevel(self.original_level)


def log_progress(
    current: int,
    total: int,
    message: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log progress for batch operations.

    Args:
        current: Current item number.
        total: Total items.
        message: Progress message.
        logger: Logger to use.
    """
    logger = logger or logging.getLogger(__name__)
    percentage = (current / total * 100) if total > 0 else 0
    logger.info("[%d/%d %.0f%%] %s", current, total, percentage, message)
