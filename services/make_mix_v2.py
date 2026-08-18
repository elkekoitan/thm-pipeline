#!/usr/bin/env python3
"""Robust long mix builder (v2).

Audio-first acrossfade chain (works), then per-track video clips rendered by
piping PIL Ken Burns frames directly to ffmpeg (stdin pipe = no JPEG disk IO,
no OOM). Same xfade chain + final upscale as make_mix.py.

usage: python3 make_mix_v2.py <slug> <scene1.png> <track1.mp3> ...
"""
import math
import os
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image

BASE = "/home/ubuntu/muzik"
OUT = os.path.join(BASE, "calendar")
W, H = 1280, 720
FPS = 24
W2, H2 = 960, 540


def duration_of(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", mp3],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def kb_frame(arr, t, seed, sx=W2, sy=H2):
    rng = random.Random(seed)
    max_off_x = int(arr.shape[1] * 0.06)
    max_off_y = int(arr.shape[0] * 0.08)
    dx = 1 if rng.random() > 0.5 else -1
    dy = 1 if rng.random() > 0.5 else -1
    s_start, s_end = 1.06, 1.00
    ox = int(max_off_x * dx * (2 * t - 1))
    oy = int(max_off_y * dy * (2 * t - 1))
    s = s_start + (s_end - s_start) * t
    cw, ch = int(arr.shape[1] * s), int(arr.shape[0] * s)
    cx = int(arr.shape[1] * s / 2 + ox)
    cy = int(arr.shape[0] * s / 2 + oy)
    left = max(0, min(cx - sx // 2, arr.shape[1] - sx))
    top = max(0, min(cy - sy // 2, arr.shape[0] - sy))
    return Image.fromarray(arr[top:top + sy, left:left + sx].astype(np.uint8))


def build_mix(slug, pairs):
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4) and os.path.getsize(mp4) > 10_000_000:
        print(f"[skip] {slug}")
        return mp4
    os.makedirs(OUT, exist_ok=True)
    tmp = f"/tmp/mixv2_{slug}"
    os.makedirs(tmp, exist_ok=True)

    # ---- audio acrossfade chain FIRST ----
    afilter = ""
    for i in range(1, len(pairs)):
        if i == 1:
            afilter = f"[0:a][1:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
        else:
            afilter += f";[o{i-1}][{i}:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
    afilter += f";[o{len(pairs)-1}]aformat=sample_rates=48000[a]"
    aud_tmp = os.path.join(tmp, "mix_a.m4a")
    if not os.path.exists(aud_tmp) or os.path.getsize(aud_tmp) < 1_000_000:
        r = subprocess.run(
            ["ffmpeg", "-y", *sum((["-i", b] for _, b in pairs), []),
             "-filter_complex", afilter, "-map", "[a]", "-threads", "1",
             "-c:a", "aac", "-b:a", "192k", aud_tmp],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("audio step failed: " + r.stderr[-300:])
        print(f"[audio] {slug}: {duration_of(aud_tmp):.1f}s")

    # ---- per-track clips via stdin pipe ----
    clips, durs = [], []
    for i, (scene, audio) in enumerate(pairs):
        d = duration_of(audio)
        durs.append(d)
        n = int(round(d * FPS)) + (int(2.0 * FPS) if i < len(pairs) - 1 else 0)
        im = Image.open(scene).convert("RGB")
        s = max(W2 * 2 / im.width, H2 * 2 / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1),
                       Image.LANCZOS)
        arr = np.asarray(im, dtype=np.float32)
        seed = abs(hash(slug + scene)) % 10000
        print(f"[{slug}] track {i+1}/{len(pairs)}: {n} frames", flush=True)
        clip = os.path.join(tmp, f"c{i}.mp4")
        if os.path.exists(clip) and os.path.getsize(clip) > 1_000_000:
            clips.append(clip)
            continue
        pipe = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W2}x{H2}", "-r", str(FPS), "-i", "-",
             "-vf", "fps=24,format=yuv420p",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
             "-threads", "1", "-an", clip],
            stdin=subprocess.PIPE)
        for f_i in range(n):
            t = f_i / max(1, n - 1)
            frame = kb_frame(arr, t, seed + f_i % 3)
            pipe.stdin.write(frame.tobytes())
            if f_i % 800 == 0:
                print(f"  [{slug}] t{i+1} frame {f_i}/{n}", flush=True)
        pipe.stdin.close()
        pipe.wait()
        if pipe.returncode != 0:
            raise RuntimeError(f"clip {i} encode failed rc={pipe.returncode}")
        clips.append(clip)
        if i < len(pairs) - 1:
            # free frames dir memory between tracks
            subprocess.run(["rm", "-rf", os.path.join(tmp, f"t{i}")],
                           capture_output=True)

    # ---- video xfade chain ----
    norm_fc = []
    for i, c in enumerate(clips):
        norm_fc.append(f"[{i}:v]fps={FPS}[n{i}]")
    per_d = [d - (2.0 if i < len(pairs) - 1 else 0) for i, d in enumerate(durs)]
    xparts = []
    off, prev = 0.0, "n0"
    for i in range(1, len(clips)):
        off += per_d[i - 1]
        out = f"m{i}"
        xparts.append(
            f"[{prev}][n{i}]xfade=transition=fade:duration=1.000:offset={off:.3f}[{out}]")
        prev = out
    video_fc = (";".join(norm_fc) + ";" + ";".join(xparts)
                + f";[{prev}]fps={FPS},scale=1280:720,format=yuv420p[v]")
    vid_tmp = os.path.join(tmp, "mix_v.mp4")
    if not os.path.exists(vid_tmp) or os.path.getsize(vid_tmp) < 1_000_000:
        r = subprocess.run(
            ["ffmpeg", "-y", *sum((["-i", c] for c in clips), []),
             "-filter_complex", video_fc, "-map", "[v]", "-threads", "1",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
             "-an", vid_tmp], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("video xfade failed: " + r.stderr[-300:])
    r = subprocess.run(
        ["ffmpeg", "-y", "-threads", "1", "-i", vid_tmp, "-i", aud_tmp,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
         "-shortest", mp4], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("mux failed: " + r.stderr[-300:])
    # short: strongest 60s from track 1 chorus
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-ss", "40", "-t", "60", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bgv];[fg][bgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", short,
    ], check=True, capture_output=True)
    print(f"[done] {slug}: {mp4} ({duration_of(mp4):.1f}s), {short}")
    return mp4


if __name__ == "__main__":
    args = sys.argv[2:]
    if len(args) < 4 or len(args) % 2:
        print("usage: make_mix_v2.py <slug> <scene> <track> [<scene> <track> ...]")
        sys.exit(1)
    slug = sys.argv[1]
    pairs = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]
    build_mix(slug, pairs)
    print("OK")
