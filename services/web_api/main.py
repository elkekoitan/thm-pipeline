#!/usr/bin/env python3
"""THM Control API — FastAPI status dashboard + webhook controller.

GET  /status          -> pipeline status, queue, latest QC score
GET  /stats           -> channel stats snapshot (reads latest daily_stats.json)
POST /command/{name}  -> run a panel command (UPLOAD_PARTS, RUN_SCORECARD, RUN_STATS, RUN_RESEARCH)
"""
import json
import os
import subprocess
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException

DATA_DIR = os.environ.get("THM_DATA_DIR", "/data")
SERVICES = Path(os.environ.get("THM_DATA_DIR", "/data")).parent / "app" / "services"

app = FastAPI(title="THM Pipeline API", version="1.0.0")
_lock = threading.Lock()

ALLOWED_COMMANDS = {
    "UPLOAD_PARTS": ["python3", "upload_parts_15min.py"],
    "RUN_STATS": ["python3", "channel_stats.py"],
    "RUN_SCORECARD": ["python3", "gods_eye_scorecard.py", "--batch"],
    "RUN_RESEARCH": ["python3", "research_engine.py", "--next"],
    "RETRY_UPLOADS": ["python3", "retry_watchdog.py", "--once"],
}


def _run_async(cmd, workdir):
    def target():
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        log_dir = os.path.join(DATA_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cmd.log")
        subprocess.run(cmd, cwd=workdir, env=env,
                       stdout=open(log_file, "a"),
                       stderr=subprocess.STDOUT)
    threading.Thread(target=target, daemon=True).start()


@app.get("/status")
def status():
    resp = {
        "services": {},
        "latest_scorecard": None,
    }
    sc = Path("/data/state/scorecard_latest.json")
    if sc.exists():
        resp["latest_scorecard"] = json.loads(sc.read_text())
    up = Path("/data/state/upload_log_parts.json")
    if up.exists():
        log = json.loads(up.read_text())
        resp["uploads"] = {k: v.get("status") for k, v in log.items()}
    return resp


@app.post("/command/{name}")
def command(name: str):
    if name not in ALLOWED_COMMANDS:
        raise HTTPException(400, f"unknown command {name}")
    workdir = Path("/app/services/uploader") if "UPLOAD" in name or "STATS" in name else Path("/app/services/research") if name == "RUN_RESEARCH" else Path("/app/services/scorecard")
    with _lock:
        _run_async(ALLOWED_COMMANDS[name], workdir)
    return {"accepted": name}
