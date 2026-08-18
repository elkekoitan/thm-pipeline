#!/usr/bin/env python3
"""Slice completed 1h category videos into 15-min parts (stream copy for
speed, then re-mux with 8s audio fade at each part's end so parts end
smoothly). Parts land in {slug}/parts/ as {slug}_part{n}.mp4."""
import os
import subprocess
import sys

SLUGS = ["01_cinematic", "02_lofi", "07_sleep_healing"]
PART_SEC = 14 * 60
PARTS = 4


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    for slug in SLUGS:
        src = f"{slug}/{slug}_video.mp4"
        if not os.path.exists(src):
            print(f"[skip] {src} missing")
            continue
        outdir = f"{slug}/parts"
        os.makedirs(outdir, exist_ok=True)
        done = 0
        for i in range(1, PARTS + 1):
            out = f"{outdir}/{slug}_part{i}.mp4"
            if os.path.exists(out):
                done += 1
                continue
            start = (i - 1) * PART_SEC
            # copy streams, cut with -ss before -i for speed; part ends get
            # afade-out only when re-encoding audio is cheap (aac encode
            # ~30s per part)
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-ss", str(start), "-i", src,
                   "-t", str(PART_SEC),
                   "-vf", "scale=1920:1080",
                   "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "24",
                   "-af", f"afade=t=out:st={PART_SEC - 8}:d=8",
                   "-c:a", "aac", "-b:a", "128k",
                   "-movflags", "+faststart", out]
            print(f"[{slug}] part {i} (start {start}s) ...", flush=True)
            subprocess.run(cmd, check=True)
            print(f"[{slug}] part {i} done", flush=True)
            done += 1
        print(f"[{slug}] parts: {done}/{PARTS}")


if __name__ == "__main__":
    main()
