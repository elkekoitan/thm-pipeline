#!/bin/bash
# THM Pipeline: run orchestrator + control API in parallel
set -u
export PYTHONUNBUFFERED=1
cd /app

# 1) FastAPI control dashboard on 0.0.0.0:8000
( exec python3 -m uvicorn services.web_api.main:app --host 0.0.0.0 --port 8000 ) &

# 2) Upload retry watchdog (background, keeps retrying until quota opens)
( cd services/uploader && exec python3 -u retry_watchdog.py ) &

# 3) Main orchestrator cron loop (foreground-ish)
exec python3 -u services/orchestrator/main.py
