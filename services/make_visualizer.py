#!/usr/bin/env python3
"""Build a Trap-Nation-style spectrum visualizer video for a single song.

Single cinematic scene (Ken Burns, slow, no jitter) + audio-reactive
spectrum bars, text-free. 1280x720, 24fps.
Outputs {slug}_video.mp4 (full length) and {slug}_short.mp4 (60s chorus cut).

usage: python3 make_visualizer.py <slug> <scene.png> <track.mp3>
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

BASE = "/home/ubuntu/muzik"
OUT = os.path.join(BASE, "calendar")
W, H = 1280, 720
FPS = 24


def duration_of(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", f],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    slug, scene, track = sys.argv[1], sys.argv[2], sys.argv[3]
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4) and os.path.getsize(mp4) > 5_000_000:
        print("[skip]", slug)
        return
    os.makedirs(OUT, exist_ok=True)
    tmp = f"/tmp/vis_{slug}"
    os.makedirs(tmp, exist_ok=True)

    d = duration_of(track)
    n = int(round(d * FPS))
    im = Image.open(scene).convert("RGB")
    s = max(W * 2 / im.width, H * 2 / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1),
                   Image.LANCZOS)
    im.save(os.path.join(tmp, "scene.png"))

    # Audio-first encode (as in make_mix_v2 pattern)
    audio_tmp = os.path.join(tmp, "audio.m4a")
    subprocess.run(["ffmpeg", "-y", "-i", track, "-c:a", "aac", "-b:a",
                    "192k", audio_tmp], check=True, capture_output=True)

    # Very slow Ken Burns frames: zoom 1.0 -> 1.05, linear horizontal drift.
    # Memory-safe: downsample to 2x target then crop/resize (quality 90 path)
    sx, sy = W * 2, H * 2
    small = im.resize((sx + 1, sy + 1), Image.LANCZOS)
    raw = np.array(small, dtype=np.uint8)[:, :, ::-1].copy()
    fh = open(os.path.join(tmp, "frame.bin"), "wb")
    for i in range(n):
        f = i / n
        z = 1.0 + 0.05 * f
        zx, zy = int(z * W), int(z * H)
        cx = int(W / 2 + 0.06 * W * f - zx / 2)
        cy = int(H / 2 - zy / 2)
        cx = max(0, min(cx, sx - zx))
        cy = max(0, min(cy, sy - zy))
        crop = raw[cy:cy + zy, cx:cx + zx]
        Image.fromarray(crop, "RGB").resize((W, H), Image.BILINEAR).save(
            fh, format="BMP", compression="raw", dpi=(1, 1))
    fh.close()

    vf = ("[0:v]scale=1280:520:force_original_aspect_ratio=decrease,"
          "pad=1280:720:0:200:color=black@0,format=yuv420p[bg];"
          "[1:a]showspectrum=mode=combined:scale=sqrt:color=moreland:"
          "saturation=4[size];[size]scale=1280:200[sp];"
          "[bg][sp]overlay=0:0[v]")
    r = subprocess.run(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pixel_format", "bgr24",
         "-video_size", f"{W}x{H}", "-framerate", str(FPS),
         "-i", os.path.join(tmp, "frame.bin"), "-i", audio_tmp,
         "-filter_complex", vf, "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
         "-threads", "1", "-c:a", "copy", "-shortest", mp4],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("visualizer failed: " + r.stderr[-400:])

    # Short: 60s from 35s mark (chorus), vertical 1080x1920 crop
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-ss", "35", "-t", "60", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bgv];[fg][bgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", short,
    ], check=True, capture_output=True)
    print(f"[done] {slug}: {duration_of(mp4):.0f}s -> {mp4}, {short}")


if __name__ == "__main__":
    main()
