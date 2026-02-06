"""Extra tests for track list parser."""

from pathlib import Path

from src.parsers.track_list import parse_single_track, parse_title_line, parse_track_block, parse_track_list


def test_parse_track_list_skips_blocks(tmp_path):
    content = "1\nFilm\nTitle\n\ninvalid\n"
    path = tmp_path / "tracks.txt"
    path.write_text(content, encoding="utf-8")
    tracks = parse_track_list(path)
    assert len(tracks) == 1


def test_parse_track_block_invalid():
    assert parse_track_block(["a", "b"]) is None
    assert parse_track_block(["x", "y", "z"]) is None


def test_parse_title_line_unquoted():
    title, notes = parse_title_line("Main Title (notes)")
    assert title == "Main Title"
    assert notes == "notes"


def test_parse_title_line_fallback():
    title, notes = parse_title_line('"Title"')
    assert title == "Title"
    assert notes == ""


def test_parse_title_line_unmatched():
    title, notes = parse_title_line("(note)")
    assert title == "(note)"
    assert notes == ""


def test_parse_single_track():
    track = parse_single_track("Film - Title")
    assert track.film == "Film"
    track2 = parse_single_track("Title Only")
    assert track2.film == ""
