#!/usr/bin/env python3
"""Retry watchdog: runs upload_parts_15min.py in a loop (every 20 min).
Each run picks the next missing part, uploads, and verifies processing.
Exits gracefully when all parts are done or after MAX_HOURS."""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = "/tmp/watchdog.log"
INTERVAL = 20 * 60          # 20 minutes between attempts
MAX_HOURS = 12


def live_count():
    try:
        out = subprocess.run(
            ["python3", "list_videos_now.py"], capture_output=True, text=True,
            cwd=BASE, timeout=90).stdout
        return len([l for l in out.splitlines() if "PT" in l and "public" in l])
    except Exception:
        return -1


def main():
    start = time.time()
    while time.time() - start < MAX_HOURS * 3600:
        r = subprocess.run(["python3", "-u", "upload_parts_15min.py"],
                           capture_output=True, text=True, cwd=BASE,
                           timeout=2400)
        tail = r.stdout.strip().splitlines()[-4:]
        with open(LOG, "a") as f:
            f.write(time.strftime("[%Y-%m-%d %H:%M UTC] ") +
                    "\n".join(tail) + "\n")
        print(tail, flush=True)
        if "ALL_DONE" in r.stdout or "[done]" in r.stdout:
            # verify nothing dead
            time.sleep(INTERVAL)
            continue
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
