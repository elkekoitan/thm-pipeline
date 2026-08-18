#!/usr/bin/env python3
"""THM Orchestrator — main loop engine.

Runs on the VPS 24/7 and dispatches jobs on a cron schedule:
  - Research rotation (daily 06:00 UTC)
  - Stats collection (daily 07:00 UTC)
  - Scorecard QC on new mixes (daily 08:15 UTC)
  - Upload retry bursts (every 20 min)
  - 24/7 live radio guardian (hourly)

Data dir: /data (mounted by Docker). State: /data/state/orchestrator.json
"""
import json
import os
import subprocess
import sys
import time

DATA_DIR = os.environ.get("THM_DATA_DIR", "/data")
STATE_PATH = os.path.join(DATA_DIR, "state", "orchestrator.json")
SERVICES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# (cron expr, label, command) — evaluated every 60s
SCHEDULE = [
    ("06:00", "research_rotation", ["python3", "research_engine.py", "--next"]),
    ("07:00", "stats_collection", ["python3", "channel_stats.py"]),
    ("08:15", "scorecard_qc", ["python3", "gods_eye_scorecard.py", "--batch"]),
    ("19:00", "daily_uploads", ["python3", "upload_parts_15min.py"]),
]


def state():
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as fh:
            return json.load(fh)
    return {"last_run": {}, "run_count": 0, "running_jobs": []}


def save(st):
    with open(STATE_PATH, "w") as fh:
        json.dump(st, fh, indent=2)


def can_run(label, interval_hours=1):
    st = state()
    last = st.get("last_run", {}).get(label, "1970-01-01T00:00:00Z")
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() >= interval_hours * 3600
    except Exception:
        return True


def run_job(label, cmd):
    workdir = os.path.join(SERVICES, os.path.dirname(cmd[1])) if len(cmd) > 1 else SERVICES
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    print(f"[orch] START {label}: {' '.join(cmd)}", flush=True)
    rc = subprocess.run(cmd, cwd=workdir, env=env).returncode
    print(f"[orch] END {label} rc={rc}", flush=True)
    st = state()
    from datetime import datetime, timezone
    st["last_run"][label] = datetime.now(timezone.utc).isoformat()
    st["run_count"] = st.get("run_count", 0) + 1
    save(st)


def main():
    print("[orch] THM orchestrator started", flush=True)
    while True:
        now = time.strftime("%H:%M", time.gmtime())
        st = state()
        for expr, label, cmd in SCHEDULE:
            if now == expr and can_run(label):
                run_job(label, cmd)
        time.sleep(60)


if __name__ == "__main__":
    main()
