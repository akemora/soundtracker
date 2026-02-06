"""Extra tests for track models."""

from src.models.track import CrawlResult, SearchResult, Track


def test_search_result_str():
    track = Track(rank=1, film="Film", cue_title="Cue", description="desc")
    result = SearchResult(track=track, source="youtube", url="u", is_free=True)
    assert "free" in str(result)
    result.downloaded = True
    assert "downloaded" in str(result)


def test_crawl_result_status():
    track = Track(rank=1, film="Film", cue_title="Cue", description="desc")
    result = CrawlResult(track=track)
    assert result.status == "not_found"
    result.free_alternatives.append(SearchResult(track=track, source="youtube", url="u", is_free=True))
    assert result.status == "free_available"
    result.paid_alternatives.append(SearchResult(track=track, source="spotify", url="u", is_free=False))
    assert result.status == "free_available"
    result.downloaded_from = SearchResult(track=track, source="youtube", url="u", is_free=True)
    assert result.status == "downloaded"
