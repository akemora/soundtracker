"""Tests for core logger."""

import logging
from pathlib import Path

import pytest

from src.core import logger as core_logger


def test_resolve_level():
    assert core_logger._resolve_level(logging.INFO) == logging.INFO
    assert core_logger._resolve_level("debug") == logging.DEBUG
    with pytest.raises(ValueError):
        core_logger._resolve_level("invalid")


def test_configure_logging(tmp_path):
    log_file = tmp_path / "log.txt"
    core_logger.configure_logging(level="INFO", log_file=log_file)
    assert log_file.exists()
    logger = core_logger.get_logger()
    assert logger.name
