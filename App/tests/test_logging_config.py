"""Tests for soundtracker.logging_config."""

import logging
from pathlib import Path

from soundtracker.logging_config import LoggingContext, get_logger, log_progress, setup_logging


def test_setup_logging_with_file(tmp_path):
    """Test logging setup creates file handler."""
    log_file = tmp_path / "app.log"

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    try:
        logger = setup_logging(level=logging.DEBUG, log_file=log_file)
        assert logger is root_logger
        assert log_file.exists()
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


def test_get_logger_returns_named_logger():
    """Test get_logger returns logger with name."""
    logger = get_logger("soundtracker.test")
    assert logger.name == "soundtracker.test"


def test_logging_context_restores_level():
    """Test LoggingContext restores original log level."""
    logger = logging.getLogger("soundtracker.context")
    original_level = logger.level
    with LoggingContext(logging.DEBUG, logger=logger):
        assert logger.level == logging.DEBUG
    assert logger.level == original_level


def test_logging_context_exit_without_enter():
    """Test LoggingContext exit is safe without enter."""
    logger = logging.getLogger("soundtracker.context.exit")
    original_level = logger.level
    context = LoggingContext(logging.WARNING, logger=logger)
    context.__exit__(None, None, None)
    assert logger.level == original_level


def test_log_progress_handles_zero_total(caplog):
    """Test log_progress handles total=0."""
    logger = logging.getLogger("soundtracker.progress")
    with caplog.at_level(logging.INFO):
        log_progress(1, 0, "testing", logger=logger)
        assert "0%" in caplog.text
