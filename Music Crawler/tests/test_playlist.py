import sqlite3
from pathlib import Path

from src.models.track import SearchResult, Track
from src.playlist.embed import EmbedResolver
from src.playlist.generator import PlaylistGenerator


class DummySearcher:
    def __init__(self, name, result_fn):
        self.name = name
        self._result_fn = result_fn

    def search(self, track: Track):
        return self._result_fn(track)


def create_test_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE composers (id INTEGER PRIMARY KEY, slug TEXT, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE v_top10_films (composer_slug TEXT, top10_rank INTEGER, title TEXT, title_es TEXT, original_title TEXT, year INTEGER)"
    )
    conn.execute(
        "INSERT INTO composers (id, slug, name) VALUES (1, 'john_williams', 'John Williams')"
    )
    conn.execute(
        "INSERT INTO v_top10_films (composer_slug, top10_rank, title, title_es, original_title, year) VALUES ('john_williams', 1, 'Star Wars', NULL, NULL, 1977)"
    )
    conn.commit()
    conn.close()


def test_embed_resolver_youtube() -> None:
    url = "https://www.youtube.com/watch?v=abc123"
    assert EmbedResolver.resolve("youtube", url) == "https://www.youtube.com/embed/abc123"


def test_embed_resolver_soundcloud() -> None:
    url = "https://soundcloud.com/artist/track"
    embed = EmbedResolver.resolve("soundcloud", url)
    assert embed is not None
    assert "w.soundcloud.com/player" in embed


def test_embed_resolver_spotify() -> None:
    url = "https://open.spotify.com/track/abc"
    assert EmbedResolver.resolve("spotify", url) == "https://open.spotify.com/embed/track/abc"


def test_playlist_generator_free_track(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    def free_results(track: Track):
        return [
            SearchResult(
                track=track,
                source="youtube",
                url="https://www.youtube.com/watch?v=abc123",
                is_free=True,
                duration="2:03",
                title="Main Title",
            )
        ]

    generator = PlaylistGenerator(
        composer_slug="john_williams",
        db_path=db_path,
        searchers={"free": [DummySearcher("youtube", free_results)], "paid": []},
    )
    try:
        playlist = generator.generate()
    finally:
        generator.close()

    assert playlist.tracks
    assert playlist.tracks[0].is_free is True
    assert playlist.tracks[0].embed_url is not None


def test_playlist_generator_fallback_alt_track(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    def free_results(track: Track):
        if track.cue_title == "Main Title":
            return []
        return [
            SearchResult(
                track=track,
                source="youtube",
                url="https://www.youtube.com/watch?v=alt123",
                is_free=True,
                duration="1:11",
                title=track.cue_title,
            )
        ]

    generator = PlaylistGenerator(
        composer_slug="john_williams",
        db_path=db_path,
        searchers={"free": [DummySearcher("youtube", free_results)], "paid": []},
    )
    try:
        playlist = generator.generate()
    finally:
        generator.close()

    assert playlist.tracks
    assert playlist.tracks[0].is_original_pick is False
    assert playlist.tracks[0].fallback_reason is not None


def test_playlist_generator_paid_only(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    def free_results(track: Track):
        return []

    def paid_results(track: Track):
        return [
            SearchResult(
                track=track,
                source="itunes",
                url="https://music.apple.com/track/1",
                is_free=False,
                title="Main Title",
            )
        ]

    generator = PlaylistGenerator(
        composer_slug="john_williams",
        db_path=db_path,
        searchers={
            "free": [DummySearcher("youtube", free_results)],
            "paid": [DummySearcher("itunes", paid_results)],
        },
    )
    try:
        playlist = generator.generate()
    finally:
        generator.close()

    assert playlist.tracks
    assert playlist.tracks[0].is_free is False
    assert playlist.tracks[0].purchase_links
