"""Tests for batch router helpers."""

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.routers import batch


def _patch_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(batch, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(batch, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(batch, "LOG_FILE", tmp_path / "logs" / "batch_progress.log")
    monkeypatch.setattr(batch, "PID_FILE", tmp_path / "logs" / "batch_progress.pid")
    monkeypatch.setattr(batch, "STATE_FILE", tmp_path / "logs" / "batch_progress.json")
    monkeypatch.setattr(batch, "QUOTA_ALERT_FILE", tmp_path / "logs" / "quota_alert.txt")
    monkeypatch.setattr(batch, "PROGRESS_FILE", tmp_path / "outputs" / "batch_last_index.txt")
    monkeypatch.setattr(batch, "SCRIPT_PATH", tmp_path / "scripts" / "create_composer_files.py")
    monkeypatch.setattr(batch, "ENV_FILE", tmp_path / ".env")


def test_load_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "KEY=value",
                "INVALID",
                "QUOTED=\"val\"",
            ]
        ),
        encoding="utf-8",
    )
    data = batch._load_env_file(env_file)
    assert data["KEY"] == "value"
    assert data["QUOTED"] == "val"


def test_pid_is_running(monkeypatch):
    original_exists = batch.Path.exists
    original_read = batch.Path.read_text

    def fake_exists(self):
        if str(self).startswith("/proc/1234/cmdline"):
            return True
        return original_exists(self)

    def fake_read_text(self, *args, **kwargs):
        if str(self).startswith("/proc/1234/cmdline"):
            return "python create_composer_files.py"
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(batch.Path, "exists", fake_exists, raising=False)
    monkeypatch.setattr(batch.Path, "read_text", fake_read_text, raising=False)

    assert batch._pid_is_running(1234) is True
    assert batch._pid_is_running(-1) is False
    assert batch._pid_is_running(9999) is False

    def fake_exists_error(self):
        if str(self).startswith("/proc/5678/cmdline"):
            return True
        return original_exists(self)

    def fake_read_text_error(self, *args, **kwargs):
        if str(self).startswith("/proc/5678/cmdline"):
            raise OSError("boom")
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(batch.Path, "exists", fake_exists_error, raising=False)
    monkeypatch.setattr(batch.Path, "read_text", fake_read_text_error, raising=False)
    assert batch._pid_is_running(5678) is False


def test_read_pid(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    assert batch._read_pid() is None

    batch.PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.PID_FILE.write_text("abc", encoding="utf-8")
    assert batch._read_pid() is None

    batch.PID_FILE.write_text("123", encoding="utf-8")
    assert batch._read_pid() == 123


def test_write_and_clear_state(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch._write_state(123, 5)
    assert batch.PID_FILE.exists()
    assert batch.STATE_FILE.exists()
    batch._clear_state()
    assert not batch.PID_FILE.exists()
    assert not batch.STATE_FILE.exists()


def test_latest_completed_index_from_progress(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.PROGRESS_FILE.write_text("1 test\n5 done\n", encoding="utf-8")
    assert batch._latest_completed_index() == 5


def test_latest_completed_index_from_outputs(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    outputs = tmp_path / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "003_test.md").write_text("x", encoding="utf-8")
    (outputs / "010_other.md").write_text("x", encoding="utf-8")
    assert batch._latest_completed_index() == 10


def test_latest_completed_index_empty_outputs(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    assert batch._latest_completed_index() == 1


def test_latest_completed_index_progress_read_error(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.PROGRESS_FILE.mkdir()
    assert batch._latest_completed_index() == 1


def test_tail_log(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    assert batch._tail_log(10) == []
    batch.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.LOG_FILE.write_text("a\nb\nc\n", encoding="utf-8")
    assert batch._tail_log(0) == []
    assert batch._tail_log(2) == ["b", "c"]

    batch.LOG_FILE.unlink()
    batch.LOG_FILE.mkdir()
    assert batch._tail_log(2) == []


def test_clear_quota_alert(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.QUOTA_ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.QUOTA_ALERT_FILE.write_text("alert", encoding="utf-8")
    batch._clear_quota_alert()
    assert batch.QUOTA_ALERT_FILE.read_text(encoding="utf-8") == ""

    batch.QUOTA_ALERT_FILE.unlink()
    batch.QUOTA_ALERT_FILE.mkdir()
    batch._clear_quota_alert()


def test_build_env(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.ENV_FILE.write_text("DEEP_RESEARCH_ENABLED=0", encoding="utf-8")
    env = batch._build_env(10)
    assert env["START_INDEX"] == "10"
    assert env["DEEP_RESEARCH_ENABLED"] == "0"


def test_start_batch_success(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)

    class DummyProc:
        pid = 999

    def fake_popen(*args, **kwargs):
        return DummyProc()

    monkeypatch.setattr(batch.subprocess, "Popen", fake_popen)
    pid = batch._start_batch(1)
    assert pid == 999
    assert batch.PID_FILE.exists()


def test_start_batch_failure(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)

    def fake_popen(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(batch.subprocess, "Popen", fake_popen)
    with pytest.raises(HTTPException):
        batch._start_batch(1)


def test_stop_batch_clears_state(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch._write_state(123, 1)
    monkeypatch.setattr(batch, "_pid_is_running", lambda pid: False)
    batch._stop_batch(123)
    assert not batch.PID_FILE.exists()

    batch._write_state(123, 1)
    monkeypatch.setattr(batch, "_pid_is_running", lambda pid: True)
    monkeypatch.setattr(batch.os, "killpg", lambda *a, **k: (_ for _ in ()).throw(ProcessLookupError()))
    batch._stop_batch(123)
    assert not batch.PID_FILE.exists()


def test_batch_status(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.STATE_FILE.write_text("not json", encoding="utf-8")
    batch.QUOTA_ALERT_FILE.write_text("alert", encoding="utf-8")
    monkeypatch.setattr(batch, "_read_pid", lambda: 123)
    monkeypatch.setattr(batch, "_pid_is_running", lambda pid: False)
    monkeypatch.setattr(batch, "_latest_completed_index", lambda: 7)
    monkeypatch.setattr(batch, "_tail_log", lambda lines: ["line"])
    data = batch.batch_status(lines=10)
    assert data["running"] is False
    assert data["pid"] is None
    assert data["latest_index"] == 7
    assert data["log_tail"] == ["line"]
    assert data["quota_alert"] == "alert"

    batch.QUOTA_ALERT_FILE.unlink()
    batch.QUOTA_ALERT_FILE.mkdir()
    data = batch.batch_status(lines=10)
    assert data["quota_alert"] == ""


def test_batch_status_state_json_error(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    batch.STATE_FILE.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(batch, "_read_pid", lambda: None)
    data = batch.batch_status(lines=1)
    assert data["state"] == {}


def test_batch_start_conditions(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(batch, "_read_pid", lambda: 123)
    monkeypatch.setattr(batch, "_pid_is_running", lambda pid: True)
    with pytest.raises(HTTPException):
        batch.batch_start()

    monkeypatch.setattr(batch, "_read_pid", lambda: None)
    monkeypatch.setattr(batch, "_latest_completed_index", lambda: 5)
    monkeypatch.setattr(batch, "_start_batch", lambda idx: 111)
    result = batch.batch_start()
    assert result["pid"] == 111
    assert result["start_index"] == 6

    with pytest.raises(HTTPException):
        batch.batch_start(start_index=0)


def test_batch_stop(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(batch, "_read_pid", lambda: None)
    result = batch.batch_stop()
    assert result["stopped"] is False

    monkeypatch.setattr(batch, "_read_pid", lambda: 123)
    monkeypatch.setattr(batch, "_stop_batch", lambda pid: None)
    result = batch.batch_stop()
    assert result["stopped"] is True


def test_batch_ui():
    html = batch.batch_ui()
    assert "Batch Controller" in html
