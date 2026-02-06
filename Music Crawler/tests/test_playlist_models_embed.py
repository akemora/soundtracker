"""Tests for playlist models and embed resolver."""

from src.playlist.embed import EmbedResolver
from src.playlist.models import Playlist, PlaylistTrack


def test_playlist_track_to_dict():
    track = PlaylistTrack(
        position=1,
        film="Film",
        film_year=2000,
        track_title="Cue",
        source="youtube",
        url="https://youtube.com/watch?v=abc",
        embed_url="https://www.youtube.com/embed/abc",
        is_free=True,
        fallback_reason="fallback",
        purchase_links=[{"name": "store"}],
    )
    data = track.to_dict()
    assert data["fallback_reason"] == "fallback"
    assert data["purchase_links"] == [{"name": "store"}]


def test_playlist_to_json_counts():
    tracks = [
        PlaylistTrack(
            position=1,
            film="Film",
            film_year=2000,
            track_title="Cue",
            source="youtube",
            url="u",
            embed_url=None,
            is_free=True,
        ),
        PlaylistTrack(
            position=2,
            film="Film",
            film_year=2000,
            track_title="Cue2",
            source="spotify",
            url="u2",
            embed_url=None,
            is_free=False,
        ),
    ]
    playlist = Playlist(composer_slug="comp", composer_name="Composer", tracks=tracks)
    data = playlist.to_json()
    assert data["total_tracks"] == 2
    assert data["free_count"] == 1
    assert data["paid_count"] == 1


def test_embed_resolver():
    assert EmbedResolver.resolve("youtube", "https://youtu.be/abc") == "https://www.youtube.com/embed/abc"
    assert EmbedResolver.resolve("soundcloud", "https://soundcloud.com/a") is not None
    assert EmbedResolver.resolve("spotify", "https://open.spotify.com/track/abc") == "https://open.spotify.com/embed/track/abc"
    assert EmbedResolver.resolve("spotify", "https://open.spotify.com/album/abc") is None
    assert EmbedResolver.resolve("other", "url") is None


def test_embed_resolver_invalid_inputs():
    assert EmbedResolver.resolve("youtube", "") is None
    assert EmbedResolver.resolve("youtube", "https://example.com") is None
    assert EmbedResolver.resolve("soundcloud", "") is None


def test_embed_internal_helpers():
    assert EmbedResolver._soundcloud_embed("") is None
    assert EmbedResolver._extract_youtube_id("https://www.youtube.com/embed/xyz") == "xyz"
