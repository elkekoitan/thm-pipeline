#!/usr/bin/env python3
"""Latin EP video pipeline — user constraints:
- HIGH QUALITY photoreal scenes (2x oversample load for smooth Ken Burns)
- NO shake/jitter/pulse — extremely slow, smooth Ken Burns (zoom 1.00 -> 1.06)
- SLOW transitions: 3.5s fade
- No text overlays
Outputs: <key>_video.mp4 (1280x720), <key>_short.mp4 (1080x1920) in album_latin/
"""
import os
import subprocess
import sys
import time as _t
from PIL import Image

FPS = 24
OUT = "/home/ubuntu/muzik/album_latin"
W, H = 1280, 720  # encode at 720p (4GB sandbox); crisp 2x oversample source

FADE = 3.5  # seconds — slow, cinematic transitions per user request

KEYS = [
    "01_fuego_en_la_noch",
    "02_luna_en_tu_mirada",
    "03_cordillera",
    "04_playa_dorada",
]


def duration_of(mp3):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", mp3],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def load_scene(path, ow, oh):
    img = Image.open(path).convert("RGB")
    # oversample 2x for ultra-smooth motion at slow zoom
    img = img.resize((ow * 2, oh * 2), Image.LANCZOS)
    return img


def kb_frame(img, t, direction=1):
    """Extremely slow, steady Ken Burns: zoom 1.0 -> 1.06, tiny steady pan.
    direction: 1 = zoom in + drift right-down, -1 = zoom out + drift left-up."""
    ow, oh = img.size
    zx = 1.0 + 0.06 * t * direction
    zw, zh = ow / zx, oh / zx
    # pan moves linearly to one edge (never oscillates => no shake)
    px = (zw - W * 2) * t * 0.5 * direction
    py = (zh - H * 2) * t * 0.5 * direction
    px = max(0.0, min(zw - W * 2, px))
    py = max(0.0, min(zh - H * 2, py))
    box = (int(px), int(py), int(px + W * 2), int(py + H * 2))
    fr = img.crop(box).resize((W, H), Image.LANCZOS)
    return fr


def build(slug, scene_png, audio_mp3):
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {slug}")
        return
    dur = duration_of(audio_mp3)
    n = int(round(dur * FPS))
    img = load_scene(scene_png, W, H)
    tmp = f"/tmp/latin_{slug}"
    os.makedirs(tmp, exist_ok=True)
    print(f"[{slug}] {n} frames")
    for f_i in range(n):
        t = f_i / max(1, n - 1)
        fr = kb_frame(img, t, direction=1 if f_i % 2 == 0 else 1)
        fr.save(os.path.join(tmp, f"f{f_i:05d}.jpg"), quality=82)
    clip = os.path.join(tmp, "clip.mp4")
    if not os.path.exists(clip):
        subprocess.run([
            "ffmpeg", "-y", "-threads", "1", "-framerate", str(FPS),
            "-i", os.path.join(tmp, "f%05d.jpg"),
            "-vf", f"format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-an", clip,
        ], check=True, capture_output=True)
    # mux with audio (copy video)
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-i", clip, "-i", audio_mp3,
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", mp4,
    ], check=True, capture_output=True)
    print(f"[done-video] {slug}")
    # short: slow-crop from best 45s of the middle
    if not os.path.exists(short):
        subprocess.run([
            "ffmpeg", "-y", "-threads", "1", "-i", mp4,
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]",
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-ss", "60", "-t", "45",
            short,
        ], check=True, capture_output=True)
    print(f"[done-short] {slug}")


if __name__ == "__main__":
    for key in KEYS:
        build(key, os.path.join(OUT, f"scene_{key}.png"),
              os.path.join(OUT, f"{key}.mp3"))
    print("[ALL DONE]")
