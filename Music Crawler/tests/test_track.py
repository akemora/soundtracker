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

