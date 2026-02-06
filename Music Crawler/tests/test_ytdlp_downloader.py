"""Tests for yt-dlp downloader."""

from pathlib import Path

import pytest

from src.downloaders.ytdlp import YtDlpDownloader
from src.models.track import SearchResult, Track


def _make_result(tmp_path):
    track = Track(rank=1, film="Film", cue_title="Cue", description="desc")
    return SearchResult(track=track, source="youtube", url="http://example.com", is_free=True)


def test_download_success(monkeypatch, tmp_path):
    result = _make_result(tmp_path)
    downloader = YtDlpDownloader(output_dir=tmp_path, audio_format="mp3", audio_quality="320")

    class Proc:
        returncode = 0
        stderr = ""

    def fake_run(*args, **kwargs):
        # create file
        path = tmp_path / f"{result.track.filename_base()}.mp3"
        path.write_text("data", encoding="utf-8")
        return Proc()

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", fake_run)
    updated = downloader.download(result)
    assert updated.downloaded is True
    assert updated.local_path is not None


def test_download_success_missing_file(monkeypatch, tmp_path):
    result = _make_result(tmp_path)
    downloader = YtDlpDownloader(output_dir=tmp_path, audio_format="mp3", audio_quality="320")

    class Proc:
        returncode = 0
        stderr = ""

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", lambda *a, **k: Proc())
    monkeypatch.setattr(downloader, "_find_output_file", lambda base: None)
    updated = downloader.download(result)
    assert updated.error == "Download completed but file not found"


def test_download_error(monkeypatch, tmp_path):
    result = _make_result(tmp_path)
    downloader = YtDlpDownloader(output_dir=tmp_path)

    class Proc:
        returncode = 1
        stderr = "error"

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", lambda *a, **k: Proc())
    updated = downloader.download(result)
    assert updated.error == "error"


def test_download_timeout(monkeypatch, tmp_path):
    result = _make_result(tmp_path)
    downloader = YtDlpDownloader(output_dir=tmp_path)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="yt-dlp", timeout=1)

    import subprocess
    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", fake_run)
    updated = downloader.download(result)
    assert updated.error == "Download timed out"


def test_download_missing_ytdlp(monkeypatch, tmp_path):
    result = _make_result(tmp_path)
    downloader = YtDlpDownloader(output_dir=tmp_path)

    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", fake_run)
    updated = downloader.download(result)
    assert updated.error == "yt-dlp not installed"


def test_find_output_file(tmp_path):
    downloader = YtDlpDownloader(output_dir=tmp_path, audio_format="mp3")
    path = tmp_path / "file.mp3"
    path.write_text("x", encoding="utf-8")
    assert downloader._find_output_file("file") == path


def test_find_output_file_none(tmp_path):
    downloader = YtDlpDownloader(output_dir=tmp_path, audio_format="mp3")
    assert downloader._find_output_file("missing") is None


def test_get_info(monkeypatch, tmp_path):
    downloader = YtDlpDownloader(output_dir=tmp_path)

    class Proc:
        returncode = 0
        stdout = '{"title": "x"}'

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", lambda *a, **k: Proc())
    data = downloader.get_info("http://example.com")
    assert data["title"] == "x"


def test_get_info_error(monkeypatch, tmp_path):
    downloader = YtDlpDownloader(output_dir=tmp_path)

    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("src.downloaders.ytdlp.subprocess.run", fake_run)
    assert downloader.get_info("http://example.com") is None
