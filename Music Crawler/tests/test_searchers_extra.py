"""Extra tests for searchers."""

import subprocess
import requests

from src.models.track import Track
from src.searchers.amazon import AmazonMusicSearcher
from src.searchers.deezer import DeezerSearcher
from src.searchers.fma import FreeMusiceArchiveSearcher
from src.searchers.jamendo import JamendoSearcher
from src.searchers.musopen import IMSLPSearcher, MusopenSearcher
from src.searchers.spotify import SpotifySearcher, ITunesSearcher
from src.searchers.tidal import QobuzSearcher, TidalSearcher
from src.searchers.youtube import YouTubeSearcher
from src.searchers.archive_org import ArchiveOrgSearcher
from src.searchers.base import BaseSearcher


class DummyProvider:
    def __init__(self, urls):
        self.urls = urls

    def search_urls(self, *args, **kwargs):
        return self.urls


def _track():
    return Track(rank=1, film="Film", cue_title="Cue", description="desc")


def test_base_searcher_build_query():
    class Dummy(BaseSearcher):
        def search(self, track):
            return []

    searcher = Dummy()
    assert "Film" in searcher.build_query(_track())


def test_base_searcher_abstract_pass_line():
    class Dummy(BaseSearcher):
        def search(self, track):
            return super().search(track)

    searcher = Dummy()
    assert searcher.search(_track()) is None


def test_amazon_searcher_filters():
    provider = DummyProvider(["https://music.amazon.com/track", "https://example.com"])
    searcher = AmazonMusicSearcher(provider=provider)
    results = searcher.search(_track())
    assert len(results) == 1


def test_fma_searcher():
    provider = DummyProvider(["https://freemusicarchive.org/track"])
    searcher = FreeMusiceArchiveSearcher(provider=provider)
    results = searcher.search(_track())
    assert results


def test_musopen_searchers():
    provider = DummyProvider(["https://musopen.org/track"])
    searcher = MusopenSearcher(provider=provider)
    assert searcher.search(_track())

    provider2 = DummyProvider(["https://imslp.org/score"])
    searcher2 = IMSLPSearcher(provider=provider2)
    assert searcher2.search(_track())


def test_tidal_qobuz_searchers():
    provider = DummyProvider(["https://tidal.com/track"])
    assert TidalSearcher(provider=provider).search(_track())

    provider2 = DummyProvider(["https://qobuz.com/track"])
    assert QobuzSearcher(provider=provider2).search(_track())


def test_deezer_searcher_success(monkeypatch):
    track = _track()
    searcher = DeezerSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": [
                    {
                        "link": "https://deezer.com/track/1",
                        "title": "Title",
                        "artist": {"name": "Artist"},
                        "album": {"title": "Album"},
                        "duration": 120,
                    }
                ]
            }

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results[0].duration == "2:00"


def test_deezer_searcher_no_link(monkeypatch):
    track = _track()
    searcher = DeezerSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"title": "x"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results == []


def test_deezer_searcher_error(monkeypatch):
    track = _track()
    searcher = DeezerSearcher()

    def fake_get(*args, **kwargs):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "get", fake_get)
    assert searcher.search(track) == []


def test_jamendo_searcher_api(monkeypatch):
    track = _track()
    searcher = JamendoSearcher(max_results=1, provider=DummyProvider([]))
    searcher.client_id = "id"

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [
                    {
                        "id": "1",
                        "name": "Title",
                        "artist_name": "Artist",
                        "duration": 60,
                        "audio": "url",
                        "shareurl": "share",
                    }
                ]
            }

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results and results[0].duration == "1:00"


def test_jamendo_searcher_api_item_missing_id(monkeypatch):
    track = _track()
    searcher = JamendoSearcher(max_results=1, provider=DummyProvider([]))
    searcher.client_id = "id"

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [{"name": "Title"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    assert searcher.search(track) == []


def test_jamendo_searcher_api_error(monkeypatch):
    track = _track()
    searcher = JamendoSearcher(max_results=1, provider=DummyProvider([]))
    searcher.client_id = "id"

    def fake_get(*args, **kwargs):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "get", fake_get)
    assert searcher.search(track) == []


def test_jamendo_searcher_web_fallback():
    track = _track()
    provider = DummyProvider(["https://jamendo.com/track"])
    searcher = JamendoSearcher(max_results=1, provider=provider)
    searcher.client_id = None
    results = searcher.search(track)
    assert results


def test_archive_org_parse(monkeypatch):
    track = _track()
    searcher = ArchiveOrgSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": {"docs": [{"identifier": "id", "title": ["t"], "format": ["FLAC"]}]}}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results[0].quality == "FLAC"


def test_archive_org_parse_missing_identifier():
    track = _track()
    searcher = ArchiveOrgSearcher()
    assert searcher._parse_result(track, {"title": "t"}) is None


def test_archive_org_parse_non_list_format(monkeypatch):
    track = _track()
    searcher = ArchiveOrgSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": {"docs": [{"identifier": "id", "title": "t", "format": "MP3"}]}}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results and results[0].quality == "unknown"


def test_archive_org_parse_mp3_format(monkeypatch):
    track = _track()
    searcher = ArchiveOrgSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": {"docs": [{"identifier": "id", "title": "t", "format": ["MP3"]}]}}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results and results[0].quality == "MP3"


def test_archive_org_error(monkeypatch):
    track = _track()
    searcher = ArchiveOrgSearcher()

    monkeypatch.setattr(requests, "get", lambda *a, **k: (_ for _ in ()).throw(requests.RequestException()))
    assert searcher.search(track) == []


def test_spotify_searcher():
    provider = DummyProvider(["https://open.spotify.com/track/1"])
    searcher = SpotifySearcher(provider=provider)
    assert searcher.search(_track())


def test_itunes_searcher(monkeypatch):
    track = _track()
    searcher = ITunesSearcher()

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [{"trackViewUrl": "https://itunes.com/1", "trackName": "Title", "artistName": "Artist"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    results = searcher.search(track)
    assert results

    class Resp2:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [{"trackName": "Title"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp2())
    assert searcher.search(track) == []


def test_itunes_searcher_error(monkeypatch):
    track = _track()
    searcher = ITunesSearcher()
    monkeypatch.setattr(requests, "get", lambda *a, **k: (_ for _ in ()).throw(requests.RequestException()))
    assert searcher.search(track) == []


def test_youtube_searcher(monkeypatch):
    track = _track()
    searcher = YouTubeSearcher(max_results=1)

    class Proc:
        returncode = 0
        stdout = '{"id": "abc", "title": "Title", "duration": 65}\n\ninvalid'

    monkeypatch.setattr("src.searchers.youtube.subprocess.run", lambda *a, **k: Proc())
    results = searcher.search(track)
    assert results and results[0].duration == "1:05"

    class Proc2:
        returncode = 1
        stdout = ""

    monkeypatch.setattr("src.searchers.youtube.subprocess.run", lambda *a, **k: Proc2())
    assert searcher.search(track) == []

    monkeypatch.setattr(
        "src.searchers.youtube.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd="x", timeout=1)),
    )
    assert searcher.search(track) == []

    monkeypatch.setattr(
        "src.searchers.youtube.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
    )
    assert searcher.search(track) == []


def test_youtube_parse_result_missing_id():
    track = _track()
    searcher = YouTubeSearcher(max_results=1)
    assert searcher._parse_result(track, {"title": "x"}) is None


def test_youtube_format_duration_long():
    searcher = YouTubeSearcher(max_results=1)
    assert searcher._format_duration(3661) == "1:01:01"
