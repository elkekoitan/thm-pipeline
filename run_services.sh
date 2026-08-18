#!/bin/bash
# THM Pipeline: run orchestrator + control API + 24/7 radio in parallel
set -u
export PYTHONUNBUFFERED=1
cd /app

# 1) FastAPI control dashboard on 0.0.0.0:8000
( exec python3 -m uvicorn services.web_api.main:app --host 0.0.0.0 --port 8000 ) &

# 2) Upload retry watchdog (background, keeps retrying until quota opens)
( cd services/uploader && exec python3 -u retry_watchdog.py ) &

# 3) 24/7 Radio - Lofi/Study (if stream key available)
if [ -n "${YOUTUBE_STREAM_KEY_LOFI:-}" ]; then
  ( exec python3 -u services/radio/live_radio.py --channel lofi --stream-key "$YOUTUBE_STREAM_KEY_LOFI" --port 8001 ) &
fi

# 4) 24/7 Radio - World Lounge (if stream key available)
if [ -n "${YOUTUBE_STREAM_KEY_WORLD:-}" ]; then
  ( exec python3 -u services/radio/live_radio.py --channel world --stream-key "$YOUTUBE_STREAM_KEY_WORLD" --port 8002 ) &
fi

# 5) Main orchestrator cron loop (foreground-ish)
exec python3 -u services/orchestrator/main.py
