from src.models.track import CrawlResult, SearchResult, Track
from src.report.generator import ReportGenerator


def test_sources_summary_deduplicates_downloaded() -> None:
    track = Track(rank=1, film="Film", cue_title="Cue", description="")
    youtube = SearchResult(
        track=track,
        source="youtube",
        url="https://www.youtube.com/watch?v=abc",
        is_free=True,
        quality="varies",
        title="Test",
    )
    result = CrawlResult(
        track=track,
        free_alternatives=[youtube],
        downloaded_from=youtube,
    )

    generator = ReportGenerator(composer="Test")
    lines = generator._format_sources_summary([result])

    assert any("| YouTube | 1 |" in line for line in lines)
