"""ETL package for SOUNDTRACKER database building."""

from .parser import (
    ParsedAward,
    ParsedComposer,
    ParsedFilm,
    ParsedSource,
    parse_all_files,
    parse_markdown_file,
)

__all__ = [
    "ParsedAward",
    "ParsedComposer",
    "ParsedFilm",
    "ParsedSource",
    "parse_all_files",
    "parse_markdown_file",
]
