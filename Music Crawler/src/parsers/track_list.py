"""Parser for track list files."""

import re
from pathlib import Path

from src.models.track import Track


def parse_track_list(file_path: Path) -> list[Track]:
    """
    Parse a track list file in the format:

    10
    Treasure Island
    "Main Title" (de la colección FSM o Lust for Life album)
    Fanfarria pirata clásica.

    Returns a list of Track objects.
    """
    tracks: list[Track] = []
    content = file_path.read_text(encoding="utf-8")

    # Split into blocks (separated by blank lines or multiple newlines)
    blocks = re.split(r"\n\s*\n", content.strip())

    for block in blocks:
        lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            continue

        track = parse_track_block(lines)
        if track:
            tracks.append(track)

    # Sort by rank
    tracks.sort(key=lambda t: t.rank)
    return tracks


def parse_track_block(lines: list[str]) -> Track | None:
    """Parse a single track block."""
    if len(lines) < 3:
        return None

    # First line: rank number
    try:
        rank = int(lines[0])
    except ValueError:
        return None

    # Second line: film name
    film = lines[1]

    # Third line: cue title (possibly with notes in parentheses)
    title_line = lines[2]
    cue_title, notes = parse_title_line(title_line)

    # Fourth line (if exists): description
    description = lines[3] if len(lines) > 3 else ""

    return Track(
        rank=rank,
        film=film,
        cue_title=cue_title,
        description=description,
        notes=notes,
    )


def parse_title_line(line: str) -> tuple[str, str]:
    """
    Parse a title line that may contain notes in parentheses.
    Example: "Main Title" (de la colección FSM o Lust for Life album)
    Returns: (cue_title, notes)
    """
    # Match quoted title with optional parenthetical notes
    match = re.match(r'"([^"]+)"\s*(?:\(([^)]+)\))?', line)
    if match:
        cue_title = match.group(1)
        notes = match.group(2) or ""
        return cue_title, notes

    # Match unquoted title with optional parenthetical notes
    match = re.match(r"([^(]+?)(?:\s*\(([^)]+)\))?$", line)
    if match:
        cue_title = match.group(1).strip().strip('"')
        notes = match.group(2) or ""
        return cue_title, notes

    return line.strip().strip('"'), ""


def parse_single_track(text: str) -> Track | None:
    """Parse a single track from text input (for --track option)."""
    # Try to parse as "Film - Title" or just "Title"
    if " - " in text:
        parts = text.split(" - ", 1)
        film = parts[0].strip()
        cue_title = parts[1].strip()
    else:
        film = ""
        cue_title = text.strip()

    return Track(
        rank=1,
        film=film,
        cue_title=cue_title,
        description="",
    )
