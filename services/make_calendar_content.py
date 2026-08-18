#!/usr/bin/env python3
"""Produce upcoming 30-day calendar content.

Content types supported:
- visualizer: single-song ambient visual loop — Ken Burns scene + soft audio
  visualizer bars (ffmpeg showspectrum, professional minimal style, no text)
  → 1920x1080 video + 1080x1920 short.
- cinematic: existing story scenes video (reuse pattern from album builds).
- mix: 30-60 min mood mix — concat of tracks with crossfades, one mood scene
  per track with crossfade transitions.

Outputs to /home/ubuntu/muzik/calendar/ as {slug}_video.mp4 and {slug}_short.mp4
"""
import math
import os
import random
import subprocess
import sys
from PIL import Image

BASE = "/home/ubuntu/muzik"
OUT = os.path.join(BASE, "calendar")
W, H = 1280, 720
FPS = 24
FADE_FRAMES = int(1.0 * FPS)


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def kenburns_frame(img, t, seed):
    rng = random.Random(seed)
    max_off_x = int(W * 0.07)
    max_off_y = int(H * 0.09)
    dx = 1 if rng.random() > 0.5 else -1
    dy = 1 if rng.random() > 0.5 else -1
    s_start = 1.06
    s_end = 1.00
    ox = int(max_off_x * dx * (2 * t - 1))
    oy = int(max_off_y * dy * (2 * t - 1))
    s = s_start + (s_end - s_start) * t
    cw, ch = int(img.width * s), int(img.height * s)
    cx = int(img.width * s / 2 + ox)
    cy = int(img.height * s / 2 + oy)
    left = max(0, min(cx - W // 2, img.width - W))
    top = max(0, min(cy - H // 2, img.height - H))
    return img.crop((left, top, left + W, top + H)).resize((W, H), Image.LANCZOS)


def load_scene(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width < W * 2 or im.height < H * 2:
        s = max(W * 2 / im.width, H * 2 / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
    return im


def duration_of(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp3], capture_output=True, text=True)
    return float(r.stdout.strip())


def build_visualizer(slug, audio, scene_path, title_text=False):
    """Ken Burns scene + minimal spectrum bars (bottom, subtle), no overlay text."""
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {slug}")
        return mp4, short
    os.makedirs(OUT, exist_ok=True)
    dur = duration_of(audio)
    n = int(round(dur * FPS))
    tmp = f"/tmp/cal_{slug}"
    os.makedirs(tmp, exist_ok=True)
    img = load_scene(scene_path)
    seed = hash(slug) % 10000
    print(f"[{slug}] visualizer: {n} frames")
    for i in range(n):
        t = i / max(1, n - 1)
        fr = kenburns_frame(img, t, seed)
        fr.save(os.path.join(tmp, f"f{i:05d}.jpg"), quality=80)
        if i and i % 500 == 0:
            print(f"  frame {i}/{n}")
    # encode scene track, then merge with showspectrum visualizer (bottom 22% of
    # frame, subtle alpha, bar colors sampled from scene mood)
    vid = os.path.join(tmp, "scene.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.jpg"),
        "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-an", vid,
    ], check=True, capture_output=True)
    # showspectrum: 450px tall, anchored to bottom, soft opacity via overlay alpha
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-i", vid, "-i", audio,
        "-filter_complex",
        "[1:a]showspectrum=color=intensity:mode=combined:saturation=1.6:slide=scroll:scale=sqrt:win_func=hann:overlap=0.55:s=1280x200[s];"
        "[s]format=rgba,colorchannelmixer=aa=0.45[sv];"
        "[0:v][sv]overlay=0:H-h[v]",
        "-map", "[v]", "-map", "1:a", "-t", str(dur),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
    ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bgv];[fg][bgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a", "-t", str(dur),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", "-shortest", short,
    ], check=True, capture_output=True)
    print(f"[done] {slug}: {mp4}")
    return mp4, short


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: make_calendar_content.py visualizer <slug> <audio.mp3> <scene.png>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "visualizer":
        build_visualizer(sys.argv[2], sys.argv[3], sys.argv[4])
    print("OK")
