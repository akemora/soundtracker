import re

from src.models.track import Track


def test_filename_base_truncates_with_hash() -> None:
    track = Track(
        rank=1,
        film="A" * 150,
        cue_title="B" * 150,
        description="",
    )
    filename = track.filename_base()

    assert len(filename) == 200
    assert re.match(r".*_[0-9a-f]{6}$", filename)


def test_filename_base_sanitizes_special_chars() -> None:
    track = Track(
        rank=2,
        film='My:Film/Name*?"<>|',
        cue_title="Cue\\Name:Part*?",
        description="",
    )
    filename = track.filename_base()

    forbidden = set('<>:"/\\\\|?*')
    assert not any(ch in forbidden for ch in filename)
