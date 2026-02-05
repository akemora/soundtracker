"""Batch control API for create_composer_files.py.

Provides a minimal UI and endpoints to start/stop the batch process and
inspect its status/logs.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/batch", tags=["Batch"])

ROOT_DIR = Path(__file__).resolve().parents[3]
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "batch_progress.log"
PID_FILE = LOG_DIR / "batch_progress.pid"
STATE_FILE = LOG_DIR / "batch_progress.json"
QUOTA_ALERT_FILE = LOG_DIR / "quota_alert.txt"
PROGRESS_FILE = ROOT_DIR / "outputs" / "batch_last_index.txt"
SCRIPT_PATH = ROOT_DIR / "scripts" / "create_composer_files.py"
ENV_FILE = ROOT_DIR / ".env"


@dataclass(frozen=True)
class BatchState:
    """State persisted for the running batch."""

    pid: int
    start_index: int
    started_at: str


def _load_env_file(path: Path) -> dict[str, str]:
    """Load key=value pairs from a .env file without external deps."""

    if not path.exists():
        return {}

    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("\"").strip("'")
    return env


def _pid_is_running(pid: int) -> bool:
    """Return True if PID exists and appears to be the batch script."""

    if pid <= 0:
        return False
    proc_cmd = Path(f"/proc/{pid}/cmdline")
    if not proc_cmd.exists():
        return False
    try:
        cmdline = proc_cmd.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "create_composer_files.py" in cmdline


def _read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    content = PID_FILE.read_text(encoding="utf-8").strip()
    if not content.isdigit():
        return None
    return int(content)


def _write_state(pid: int, start_index: int) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    state = BatchState(
        pid=pid,
        start_index=start_index,
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    STATE_FILE.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _clear_state() -> None:
    if PID_FILE.exists():
        PID_FILE.unlink()
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def _latest_completed_index() -> int:
    if PROGRESS_FILE.exists():
        try:
            lines = [line.strip() for line in PROGRESS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                parts = lines[-1].split()
                if parts and parts[0].isdigit():
                    return int(parts[0])
        except OSError:
            pass
    outputs = list((ROOT_DIR / "outputs").glob("[0-9][0-9][0-9]_*.md"))
    if not outputs:
        return 1
    indices: list[int] = []
    for path in outputs:
        stem = path.name.split("_", 1)[0]
        if stem.isdigit():
            indices.append(int(stem))
    return max(indices) if indices else 1


def _tail_log(lines: int) -> list[str]:
    if not LOG_FILE.exists():
        return []
    if lines <= 0:
        return []
    try:
        with LOG_FILE.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") <= lines:
                step = min(block, size)
                handle.seek(-step, os.SEEK_CUR)
                data = handle.read(step) + data
                handle.seek(-step, os.SEEK_CUR)
                size -= step
        return data.decode("utf-8", errors="ignore").splitlines()[-lines:]
    except OSError:
        return []


def _clear_quota_alert() -> None:
    try:
        if QUOTA_ALERT_FILE.exists():
            QUOTA_ALERT_FILE.write_text("", encoding="utf-8")
    except OSError:
        pass


def _build_env(start_index: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(_load_env_file(ENV_FILE))
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "DEEP_RESEARCH_ENABLED": env.get("DEEP_RESEARCH_ENABLED", "1"),
            "START_INDEX": str(start_index),
        }
    )
    return env


def _start_batch(start_index: int) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    env = _build_env(start_index)
    try:
        with LOG_FILE.open("ab") as log_handle:
            process = subprocess.Popen(
                [sys.executable, str(SCRIPT_PATH)],
                cwd=str(ROOT_DIR),
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start batch: {exc}") from exc

    _write_state(process.pid, start_index)
    return process.pid


def _stop_batch(pid: int) -> None:
    if not _pid_is_running(pid):
        _clear_state()
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        _clear_state()


@router.get("/status")
def batch_status(lines: int = Query(40, ge=0, le=500)) -> dict[str, Any]:
    """Return batch status and tail of the log."""

    pid = _read_pid()
    running = bool(pid and _pid_is_running(pid))
    if pid and not running:
        _clear_state()
        pid = None
    state: dict[str, Any] = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    alert_text = ""
    if QUOTA_ALERT_FILE.exists():
        try:
            alert_text = QUOTA_ALERT_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            alert_text = ""
    return {
        "running": running,
        "pid": pid,
        "state": state,
        "latest_index": _latest_completed_index(),
        "log_tail": _tail_log(lines),
        "quota_alert": alert_text,
    }


@router.post("/start")
def batch_start(start_index: int | None = None) -> dict[str, Any]:
    """Start the batch process from the given index."""

    pid = _read_pid()
    if pid and _pid_is_running(pid):
        raise HTTPException(status_code=409, detail="Batch already running")

    if start_index is None:
        start_index = max(1, _latest_completed_index() + 1)
    if start_index < 1:
        raise HTTPException(status_code=400, detail="start_index must be >= 1")

    _clear_quota_alert()
    new_pid = _start_batch(start_index)
    return {"started": True, "pid": new_pid, "start_index": start_index}


@router.post("/stop")
def batch_stop() -> dict[str, Any]:
    """Stop the running batch process if present."""

    pid = _read_pid()
    if not pid:
        return {"stopped": False, "message": "No running batch"}
    _stop_batch(pid)
    return {"stopped": True, "pid": pid}


@router.get("/ui", response_class=HTMLResponse)
def batch_ui() -> str:
    """Simple HTML UI to control batch execution."""

    return """
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <title>SOUNDTRACKER | Batch</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #0f172a;
        --panel: #111827;
        --text: #e5e7eb;
        --accent: #38bdf8;
        --danger: #f87171;
        --muted: #94a3b8;
      }
      body {
        font-family: "Helvetica Neue", Arial, sans-serif;
        background: radial-gradient(circle at top, #1e293b 0%, #0f172a 55%, #020617 100%);
        color: var(--text);
        margin: 0;
        padding: 24px;
      }
      h1 {
        margin: 0 0 8px;
        font-weight: 700;
        font-size: 28px;
      }
      .wrap {
        display: grid;
        gap: 16px;
      }
      .panel {
        background: var(--panel);
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
      }
      .row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
      }
      button {
        border: 0;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
        cursor: pointer;
      }
      .start {
        background: var(--accent);
        color: #0f172a;
      }
      .stop {
        background: var(--danger);
        color: #0f172a;
      }
      .ghost {
        background: #1f2937;
        color: var(--text);
      }
      input {
        background: #0b1220;
        color: var(--text);
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 8px 12px;
        width: 140px;
      }
      .status {
        font-weight: 600;
      }
      .status.running { color: #22c55e; }
      .status.stopped { color: #f97316; }
      pre {
        background: #0b1220;
        border-radius: 12px;
        padding: 12px;
        overflow: auto;
        overflow-y: scroll;
        max-height: 360px;
        min-height: 260px;
        scrollbar-gutter: stable;
        border: 1px solid #1f2937;
      }
      .muted { color: var(--muted); }
    </style>
  </head>
  <body>
    <h1>Batch Controller</h1>
    <p class="muted">Controla la generación masiva de compositores.</p>

    <div class="wrap">
      <div class="panel">
        <div class="row">
          <span id="status" class="status stopped">Detenido</span>
          <span class="muted" id="pid"></span>
          <span class="muted" id="latest"></span>
        </div>
        <div id="quotaAlert" class="muted" style="margin-top: 8px;"></div>
        <div class="row" style="margin-top: 12px;">
          <label>Start index:</label>
          <input id="startIndex" type="text" inputmode="numeric" pattern="[0-9]*" value="1" />
          <button class="start" onclick="startBatch()">Iniciar (auto)</button>
          <button class="ghost" onclick="resumeBatch()">Reanudar</button>
          <button class="stop" onclick="stopBatch()">Parar</button>
          <button class="ghost" onclick="refreshStatus()">Actualizar</button>
        </div>
        <div class="row" style="margin-top: 8px;">
          <button class="ghost" onclick="showRecent()">Ver últimas</button>
          <button class="ghost" onclick="showAll()">Ver todas</button>
          <button class="ghost" onclick="clearLog()">Limpiar pantalla</button>
        </div>
      </div>

      <div class="panel">
        <div class="row">
          <strong>Log (últimas líneas)</strong>
          <span class="muted" id="logMeta"></span>
        </div>
        <pre id="log"></pre>
      </div>
    </div>

    <script>
      let logLines = 80;
      let lastLogSnapshot = [];
      let clearMode = false;
      let startIndexEdited = false;

      const startIndexEl = document.getElementById('startIndex');
      startIndexEl.addEventListener('input', () => {
        startIndexEdited = true;
      });

      async function refreshStatus() {
        let data;
        try {
          const res = await fetch(`/batch/status?lines=${logLines}`);
          data = await res.json();
        } catch (err) {
          console.error(err);
          return;
        }
        const statusEl = document.getElementById('status');
        statusEl.textContent = data.running ? 'En marcha' : 'Detenido';
        statusEl.className = 'status ' + (data.running ? 'running' : 'stopped');
        document.getElementById('pid').textContent = data.pid ? `PID: ${data.pid}` : '';
        document.getElementById('latest').textContent = `Último índice procesado: ${data.latest_index}`;
        if (!startIndexEdited && document.activeElement !== startIndexEl) {
          startIndexEl.value = data.latest_index + 1;
        }
        const lines = data.log_tail || [];
        let displayLines = lines;
        if (clearMode && lastLogSnapshot.length > 0) {
          const lastLine = lastLogSnapshot[lastLogSnapshot.length - 1];
          const idx = lines.lastIndexOf(lastLine);
          displayLines = idx >= 0 ? lines.slice(idx + 1) : lines;
          clearMode = false;
        }
        document.getElementById('log').textContent = displayLines.join('\\n');
        document.getElementById('logMeta').textContent = `(${displayLines.length} líneas)`;
        lastLogSnapshot = lines;

        const quotaAlert = document.getElementById('quotaAlert');
        if (data.quota_alert) {
          quotaAlert.textContent = `ALERTA CUOTA: ${data.quota_alert}`;
          quotaAlert.style.color = '#f87171';
          quotaAlert.style.fontWeight = '700';
        } else {
          quotaAlert.textContent = '';
          quotaAlert.style.color = '';
          quotaAlert.style.fontWeight = '';
        }
      }

      async function startBatch() {
        const res = await fetch('/batch/start', { method: 'POST' });
        if (!res.ok) {
          const err = await res.json();
          alert(err.detail || 'Error al iniciar');
        }
        await refreshStatus();
      }

      async function resumeBatch() {
        const idx = parseInt(startIndexEl.value, 10);
        const res = await fetch(`/batch/start?start_index=${idx}`, { method: 'POST' });
        if (!res.ok) {
          const err = await res.json();
          alert(err.detail || 'Error al reanudar');
        }
        startIndexEdited = false;
        await refreshStatus();
      }

      async function stopBatch() {
        const res = await fetch('/batch/stop', { method: 'POST' });
        if (!res.ok) {
          alert('Error al detener');
        }
        await refreshStatus();
      }

      function showAll() {
        logLines = 500;
        refreshStatus();
      }

      function showRecent() {
        logLines = 80;
        refreshStatus();
      }

      function clearLog() {
        document.getElementById('log').textContent = '';
        document.getElementById('logMeta').textContent = '(0 líneas)';
        clearMode = true;
      }

      refreshStatus();
      setInterval(refreshStatus, 5000);
    </script>
  </body>
</html>
"""
