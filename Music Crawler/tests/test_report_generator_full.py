"""Tests for report generator."""

from pathlib import Path

from src.models.track import CrawlResult, SearchResult, Track
from src.report.generator import ReportGenerator


def _track(rank=1):
    return Track(rank=rank, film="Film", cue_title=f"Cue {rank}", description="desc")


def test_report_generator_sections(tmp_path):
    downloaded_result = CrawlResult(track=_track(1))
    downloaded_result.downloaded_from = SearchResult(
        track=downloaded_result.track,
        source="youtube",
        url="https://youtube.com",
        is_free=True,
        quality="320",
        title="Title",
        local_path=tmp_path / "file.mp3",
    )
    downloaded_result.paid_alternatives.append(
        SearchResult(track=downloaded_result.track, source="spotify", url="https://spotify.com", is_free=False)
    )

    free_result = CrawlResult(track=_track(2))
    free_result.free_alternatives.append(
        SearchResult(track=free_result.track, source="archive", url="https://archive.org", is_free=True, title="Alt", duration="1:00")
    )
    free_result.paid_alternatives.append(
        SearchResult(track=free_result.track, source="itunes", url="https://itunes.com", is_free=False, title="Paid")
    )

    paid_result = CrawlResult(track=_track(3))
    paid_result.paid_alternatives.append(
        SearchResult(track=paid_result.track, source="deezer", url="https://deezer.com", is_free=False, title="Paid")
    )

    not_found = CrawlResult(track=_track(4))

    generator = ReportGenerator(composer="Composer")
    report = generator._build_report([downloaded_result, free_result, paid_result, not_found])
    assert "Downloaded Tracks" in report
    assert "Available on Free Sources" in report
    assert "Available on Paid Services Only" in report
    assert "Not Found" in report

    out_path = tmp_path / "REPORT.md"
    generator.generate([downloaded_result], out_path)
    assert out_path.exists()


def test_format_sources_summary_empty():
    generator = ReportGenerator()
    assert generator._format_sources_summary([]) == []


def test_format_sources_summary_with_results():
    generator = ReportGenerator()
    result = CrawlResult(track=_track(1))
    result.downloaded_from = SearchResult(
        track=result.track,
        source="youtube",
        url="https://youtube.com/watch?v=1",
        is_free=True,
    )
    result.free_alternatives.append(
        SearchResult(track=result.track, source="archive", url="https://archive.org", is_free=True)
    )
    lines = generator._format_sources_summary([result])
    assert any("Sources Found" in line for line in lines)
