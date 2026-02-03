"""Tests for track list parser."""

from pathlib import Path

from src.parsers.track_list import parse_single_track, parse_track_block, parse_title_line


def test_parse_title_line_quoted():
    """Test parsing a quoted title with notes."""
    title, notes = parse_title_line('"Main Title" (de la colección FSM)')
    assert title == "Main Title"
    assert notes == "de la colección FSM"


def test_parse_title_line_simple():
    """Test parsing a simple title."""
    title, notes = parse_title_line("Main Title")
    assert title == "Main Title"
    assert notes == ""


def test_parse_track_block():
    """Test parsing a complete track block."""
    lines = [
        "10",
        "Treasure Island",
        '"Main Title" (FSM collection)',
        "Classic pirate fanfare.",
    ]
    track = parse_track_block(lines)
    assert track is not None
    assert track.rank == 10
    assert track.film == "Treasure Island"
    assert track.cue_title == "Main Title"
    assert track.description == "Classic pirate fanfare."
    assert track.notes == "FSM collection"


def test_parse_single_track_with_film():
    """Test parsing a single track with film name."""
    track = parse_single_track("Treasure Island - Main Title")
    assert track is not None
    assert track.film == "Treasure Island"
    assert track.cue_title == "Main Title"


def test_parse_single_track_title_only():
    """Test parsing a single track title only."""
    track = parse_single_track("Main Title")
    assert track is not None
    assert track.film == ""
    assert track.cue_title == "Main Title"
