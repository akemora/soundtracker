import json
from types import SimpleNamespace

import requests

from src.models.track import Track
from src.searchers.archive_org import ArchiveOrgSearcher
from src.searchers.bandcamp import BandcampSearcher
from src.searchers.soundcloud import SoundCloudSearcher
from src.searchers.spotify import ITunesSearcher, SpotifySearcher
from src.searchers.youtube import YouTubeSearcher


class DummyProvider:
    def __init__(self, urls):
        self.urls = urls

    def search_urls(self, query, num_results=3, site_filter=None):
        return self.urls


def test_youtube_searcher_parses_results(monkeypatch) -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")

    sample = {"id": "abc123", "title": "Main Theme", "duration": 123}
    stdout = json.dumps(sample) + "\n"

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout)

    monkeypatch.setattr("subprocess.run", fake_run)

    results = YouTubeSearcher(max_results=1).search(track)
    assert results
    assert results[0].url == "https://www.youtube.com/watch?v=abc123"


def test_spotify_searcher_uses_provider() -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")
    provider = DummyProvider(["https://open.spotify.com/track/abc"])

    results = SpotifySearcher(provider=provider, max_results=1).search(track)
    assert results
    assert results[0].source == "spotify"


def test_soundcloud_searcher_filters_sets() -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")
    provider = DummyProvider(
        [
            "https://soundcloud.com/artist/track",
            "https://soundcloud.com/artist/sets/playlist",
        ]
    )

    results = SoundCloudSearcher(provider=provider, max_results=2).search(track)
    assert len(results) == 1
    assert "sets" not in results[0].url


def test_archive_org_searcher_parses_results(monkeypatch) -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "response": {
                    "docs": [
                        {"identifier": "item123", "title": "Theme", "format": ["MP3"]}
                    ]
                }
            }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())

    results = ArchiveOrgSearcher(max_results=1).search(track)
    assert results
    assert results[0].url.endswith("item123")


def test_itunes_searcher_parses_results(monkeypatch) -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [
                    {
                        "trackViewUrl": "https://music.apple.com/track/1",
                        "trackName": "Main Title",
                        "artistName": "John Williams",
                        "collectionName": "Star Wars",
                    }
                ]
            }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())

    results = ITunesSearcher(max_results=1).search(track)
    assert results
    assert results[0].source == "itunes"


def test_bandcamp_searcher_returns_results() -> None:
    track = Track(rank=1, film="Star Wars", cue_title="Main Title", description="")
    provider = DummyProvider(["https://bandcamp.com/track/test-track"])

    results = BandcampSearcher(provider=provider, max_results=1).search(track)
    assert results
    assert results[0].source == "bandcamp"
