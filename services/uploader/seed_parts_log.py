#!/usr/bin/env python3
"""Seed upload_log_parts.json with known playlist IDs from the first upload
round (calendariy upload, Aug 16)."""
import json
import os

MUSIC_DIR = "/home/ubuntu/muzik"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "upload_log_parts.json")
PL = {"01_cinematic_playlist": "PLOTQCstUtZHY",
      "02_lofi_playlist": "PLcaMgFGioKuE",
      "07_sleep_healing_playlist": "PLamtPYfcqlRI"}
log = json.load(open(LOG)) if os.path.exists(LOG) else {}
log.update(PL)
json.dump(log, open(LOG, "w"), indent=2)
print("seeded:", json.dumps(PL))
