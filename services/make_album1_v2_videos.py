#!/usr/bin/env python3
"""Build text-free Ken Burns music videos for THE GENEROUS album (v2 songs).

Each video: one scene image (panel from album/panel_*.png; text areas are
removed by cropping/blurring to keep the no-text requirement) animated with a
single smooth Ken Burns pan. Output: 1920x1080 video + 1080x1920 short.
"""
import math
import os
import random
import subprocess
import sys
import time
from PIL import Image, ImageFilter

BASE = "/home/ubuntu/muzik"
PANELS = os.path.join(BASE, "album1_scenes")   # scene_*.png (1920x1080 mood art)
AUDIO_DIR = os.path.join(BASE, "album1_v2")
OUT = os.path.join(BASE, "album1_v2")
W, H = 1920, 1080
FPS = 24

# Scene files: text bands on album1 panels sit near top/bottom; crop safe area.
TRACKS = [
    ("01", "whisper_dark", "scene_whisper_dark.png"),
    ("02", "daglarda_ses", "scene_daglarda_ses.png"),
    ("03", "dancefloor_fever", "scene_dancefloor_fever.png"),
    ("04", "neon_istanbul", "scene_neon_istanbul.png"),
    ("05", "vahsi_orman", "scene_vahsi_orman.png"),
    ("06", "ruya_bahcesi", "scene_ruya_bahcesi.png"),
    ("07", "yildiz_savascisi", "scene_yildiz_savascisi.png"),
]

def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)

def duration_of(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp3], capture_output=True, text=True)
    return float(r.stdout.strip())

def load_panel(path):
    """Load scene and 2x-upscale for smooth Ken Burns at 1920x1080."""
    im = Image.open(path).convert("RGB")
    if im.width < W * 2 or im.height < H * 2:
        s = max(W * 2 / im.width, H * 2 / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
    return im

def kenburns_frame(img, t, seed):
    rng = random.Random(seed)
    max_off_x = int(W * 0.06)
    max_off_y = int(H * 0.08)
    dx = 1 if rng.random() > 0.5 else -1
    dy = 1 if rng.random() > 0.5 else -1
    s = 1.06 + (1.00 - 1.06) * t
    ox = int(max_off_x * dx * (2 * t - 1))
    oy = int(max_off_y * dy * (2 * t - 1))
    cw, ch = int(img.width * s), int(img.height * s)
    cx = int(img.width * s / 2 + ox)
    cy = int(img.height * s / 2 + oy)
    left = max(0, min(cx - W // 2, img.width - W))
    top = max(0, min(cy - H // 2, img.height - H))
    return img.crop((left, top, left + W, top + H)).resize((W, H), Image.LANCZOS)

def build_song(idx, key, panel_file, audio_dur):
    mp4 = os.path.join(OUT, f"{idx}_{key}_video.mp4")
    short = os.path.join(OUT, f"{idx}_{key}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {key}")
        return
    n_total = int(round(audio_dur * FPS))
    tmp = f"/tmp/thm1_{key}"
    os.makedirs(tmp, exist_ok=True)
    img = load_panel(os.path.join(PANELS, panel_file))
    seed = hash(key) % 10000
    print(f"[{key}] {n_total} frames")
    # render every 2nd frame is risky for smoothness; render all but write in chunks
    for i in range(n_total):
        t = ease(i / max(1, n_total - 1))
        fr = kenburns_frame(img, t, seed + i)
        fr.save(os.path.join(tmp, f"f{i:06d}.jpg"), quality=80)
    audio = os.path.join(AUDIO_DIR, f"{idx}_{key}.mp3")
    frames_in = os.path.join(tmp, "f%06d.jpg")
    ok = False
    for _ in range(3):
        r = subprocess.run([
            "ffmpeg", "-y", "-threads", "1", "-framerate", str(FPS), "-i", frames_in, "-i", audio,
            "-filter_complex", "[0:v]fps=24[v]", "-map", "[v]", "-map", "1:a",
            "-t", str(audio_dur), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
        ], capture_output=True)
        if r.returncode == 0:
            ok = True
            break
        print(f"[warn] video encode attempt {_+1} failed, retrying"); time.sleep(15)
    if not ok:
        raise RuntimeError(f"video encode failed for {key}")
    subprocess.run(["rm", "-f"] + [os.path.join(tmp, f"f{i:06d}.jpg") for i in range(n_total)], capture_output=True)
    # short: center crop square + blurred pillars
    ok = False
    for _ in range(3):
        r = subprocess.run([
            "ffmpeg", "-y", "-threads", "1", "-i", mp4,
            "-filter_complex",
            "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2[bgv];[fg]crop=1080:1080:420:0,scale=1080:1080[fgv];[bgv][fgv]overlay=(W-w)/2:(H-h)/2[v]",
            "-map", "[v]", "-map", "0:a", "-t", str(audio_dur),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-c:a", "aac", "-b:a", "192k", "-shortest", short,
        ], capture_output=True)
        if r.returncode == 0:
            ok = True
            break
        print(f"[warn] short encode attempt {_+1} failed, retrying"); time.sleep(15)
    if not ok:
        raise RuntimeError(f"short encode failed for {key}")
    print(f"[done] {key}: {mp4}")

if __name__ == "__main__":
    for idx, key, pf in TRACKS:
        dur = duration_of(os.path.join(AUDIO_DIR, f"{idx}_{key}.mp3"))
        build_song(idx, key, pf, dur)
    print("ALL DONE")
