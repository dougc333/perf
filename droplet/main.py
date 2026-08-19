"""FastAPI server for the droplet side of the perf dashboard.

The MacBook React dashboard calls this server (directly or through the macos
Node proxy) to run profiling scripts like orig.py and to fetch the profiles
they produce.

Run on the droplet:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000

Optional: set CALLBACK_URL to have the server POST run-completion events back
to the macos dashboard server, e.g.
    CALLBACK_URL=http://<macos-ip>:3001/api/events/droplet-run-complete
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent

app = FastAPI(title="perf droplet runner", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RUNS: dict[str, dict] = {}
LOCK = threading.Lock()


class RunRequest(BaseModel):
    script: str = "orig.py"
    args: list[str] = []


def available_scripts() -> list[str]:
    return sorted(p.name for p in HERE.glob("*.py") if p.name != "main.py")


def scan_results() -> list[str]:
    return sorted(p.name for p in HERE.glob("hf_profile*.json"))


def notify_macos(run_id: str) -> None:
    url = os.environ.get("CALLBACK_URL", "")
    if not url:
        return
    with LOCK:
        payload = json.dumps(RUNS.get(run_id, {})).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"content-type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:
        print(f"callback failed: {exc}")


def run_job(run_id: str, script: str, args: list[str]) -> None:
    with LOCK:
        RUNS[run_id]["status"] = "running"
    cmd = [sys.executable, str(HERE / script), *args]
    proc = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            with LOCK:
                RUNS[run_id]["output"] += line
    finally:
        proc.wait()
        with LOCK:
            RUNS[run_id]["status"] = "done" if proc.returncode == 0 else "error"
            RUNS[run_id]["exit_code"] = proc.returncode
            RUNS[run_id]["results"] = scan_results()
            RUNS[run_id]["finished_at"] = time.time()
        notify_macos(run_id)


@app.get("/health")
def health():
    return {"ok": True, "host": socket.gethostname(), "python": sys.version.split()[0],
            "scripts": available_scripts()}


@app.get("/api/scripts")
def scripts():
    return {"scripts": available_scripts()}


@app.post("/api/run")
def run(req: RunRequest):
    script = Path(req.script).name  # strip any directory component
    if script == "main.py" or not script.endswith(".py") or not (HERE / script).is_file():
        raise HTTPException(status_code=404, detail=f"script not found: {req.script}")
    run_id = uuid.uuid4().hex[:12]
    with LOCK:
        RUNS[run_id] = {
            "run_id": run_id, "script": script, "status": "queued",
            "output": "", "exit_code": None, "results": [],
            "started_at": time.time(), "finished_at": None,
        }
    threading.Thread(target=run_job, args=(run_id, script, req.args), daemon=True).start()
    return {"run_id": run_id, "status": "running"}


@app.post("/api/run/orig")
def run_orig():
    return run(RunRequest(script="orig.py"))


@app.get("/api/run/{run_id}")
def run_status(run_id: str):
    with LOCK:
        info = RUNS.get(run_id)
    if info is None:
        raise HTTPException(status_code=404, detail="run not found")
    return info


@app.get("/api/runs")
def runs():
    with LOCK:
        ordered = sorted(RUNS.values(), key=lambda r: r["started_at"], reverse=True)
    return {"runs": ordered}


@app.get("/api/results")
def results():
    return {"results": scan_results()}
