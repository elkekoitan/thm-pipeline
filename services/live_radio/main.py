#!/usr/bin/env python3
"""THM Live Radio — 24/7 YouTube live publisher guardian.

Publishes playlist loops as continuous RTMP livestreams:
  RTMP_KEY_<ID> env var required (stream key per radio channel).
Falls back to a safe idle loop when no key is configured (avoids crashes).

Guardian model: monitors child ffmpeg; auto-restarts on exit.
"""
import os
import subprocess
import sys
import time

ID = os.environ.get("RADIO_ID", "radio1")
RTMP_KEY = os.environ.get(f"RTMP_KEY_{ID.upper()}", "")
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
PLAYLIST_M3U = os.environ.get("THM_DATA_DIR", "/data") + f"/playlists/{ID}.m3u"
LOOP_MP4 = os.environ.get("THM_DATA_DIR", "/data") + "/assets/radio_loop.mp4"


def build_cmd():
    if not RTMP_KEY:
        return None  # no stream key -> idle mode
    return [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", LOOP_MP4,
        "-stream_loop", "-1", "-i", PLAYLIST_M3U,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4500k",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-f", "flv", f"{RTMP_URL}/{RTMP_KEY}",
    ]


def main():
    print(f"[radio-{ID}] guardian started", flush=True)
    while True:
        cmd = build_cmd()
        if not cmd:
            print(f"[radio-{ID}] no RTMP_KEY_{ID.upper()} set, idling 60s", flush=True)
            time.sleep(60)
            continue
        print(f"[radio-{ID}] starting stream ...", flush=True)
        p = subprocess.Popen(cmd)
        rc = p.wait()
        print(f"[radio-{ID}] ffmpeg exited rc={rc}, restart in 30s", flush=True)
        time.sleep(30)


if __name__ == "__main__":
    main()
