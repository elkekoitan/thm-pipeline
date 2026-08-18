#!/usr/bin/env python3
"""Build a long mood mix (30-60 min) from existing album tracks.

Approach (memory-safe): concat with audio crossfades via ffmpeg across small
encoded segments per track, each track gets one Ken Burns scene. Output 1280x720
for 4GB sandbox safety, then upscale-free delivery (YouTube accepts it).

usage: python3 make_mix.py <slug> <scene1.png> <track1.mp3> <scene2.png> <track2.mp3> ...
Tracks are joined with 2s audio crossfades; scene crossfades 1s (per-clip xfade
pattern proven to work: bare labels, comma-chain).
"""
import math
import os
import random
import subprocess
import sys
from PIL import Image

BASE = "/home/ubuntu/muzik"
OUT = os.path.join(BASE, "calendar")
W, H = 1280, 720  # memory-safe working resolution
FPS = 24
XF = int(2.0 * FPS)  # 2s audio xfade


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def kb_frame(img, t, seed):
    rng = random.Random(seed)
    max_off_x = int(W * 0.06)
    max_off_y = int(H * 0.08)
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


def build_mix(slug, pairs):
    """pairs = [(scene.png, track.mp3), ...]"""
    import time as _t
    from PIL import Image
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {slug}")
        return mp4
    os.makedirs(OUT, exist_ok=True)
    tmp = f"/tmp/mix_{slug}"
    os.makedirs(tmp, exist_ok=True)
    # audio acrossfade FIRST (lightweight, memory is free) — build filter with
    # fixed input indices since it doesn't depend on clip order
    audio_inputs = []
    for _, a in pairs:
        audio_inputs += ["-i", a]
    afilter = ""
    for i in range(1, len(pairs)):
        if i == 1:
            afilter = f"[0:a][1:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
        else:
            afilter += f";[o{i-1}][{i}:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
    afilter += f";[o{len(pairs)-1}]aformat=sample_rates=48000[a]"
    _aud_tmp = os.path.join(tmp, "mix_a.m4a")
    if os.path.exists(_aud_tmp):
        print("[skip] audio temp already exists")
    else:
        ok = False
        for _attempt in range(3):
            r = subprocess.run(
                ["ffmpeg", "-y", *audio_inputs, "-filter_complex", afilter, "-map", "[a]",
                 "-threads", "1", "-c:a", "aac", "-b:a", "192k", _aud_tmp],
                capture_output=True,
            )
            if r.returncode == 0:
                ok = True
                break
            print(f"[warn] audio step attempt {_attempt+1} rc={r.returncode}, retrying")
            _t.sleep(20)
        if not ok:
            raise RuntimeError("mix audio step failed")
    # per-track: render frames → encode clip
    clips = []
    durs = []
    for i, (scene, audio) in enumerate(pairs):
        d = duration_of(audio)
        durs.append(d)
        n = int(round(d * FPS)) + (XF if i < len(pairs) - 1 else 0)
        img = load_scene(scene)
        seed = hash(slug + scene) % 10000
        print(f"[{slug}] track {i+1}/{len(pairs)}: {n} frames")
        cdir = os.path.join(tmp, f"t{i}")
        os.makedirs(cdir, exist_ok=True)
        for f_i in range(n):
            t = f_i / max(1, n - 1)
            fr = kb_frame(img, t, seed + f_i)
            fr.save(os.path.join(cdir, f"f{f_i:05d}.jpg"), quality=80)
        clip = os.path.join(tmp, f"c{i}.mp4")
        if os.path.exists(clip):
            clips.append(clip)
            print(f"[skip-clip] c{i}")
            continue
        subprocess.run([
            "ffmpeg", "-y", "-threads", "1", "-framerate", str(FPS),
            "-i", os.path.join(cdir, "f%05d.jpg"),
            "-vf", "scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "21", "-an", clip,
        ], check=True, capture_output=True)
        # remove frames dir to free disk
        subprocess.run(["rm", "-rf", cdir], capture_output=True)
        clips.append(clip)
    # video xfade chain (bare labels, comma-chain after last)
    norm_inputs = []
    norm_fc = []
    per_d = [d - (2.0 if i < len(pairs) - 1 else 0) for i, d in enumerate(durs)]
    for i, c in enumerate(clips):
        norm_inputs += ["-i", c]
        norm_fc.append(f"[{i}:v]fps={FPS}[n{i}]")
    xparts = []
    off = 0.0
    prev = "n0"
    for i in range(1, len(clips)):
        off = off + per_d[i - 1]
        out = f"m{i}"
        xparts.append(
            f"[{prev}][n{i}]xfade=transition=fade:duration=1.000:offset={off:.3f}[{out}]")
        prev = out
    video_fc = (";".join(norm_fc) + ";" + ";".join(xparts)
                + f";[{prev}]fps={FPS},scale=1280:720,format=yuv420p[v]")
    # video xfade only (heavy); audio already done above
    _vid_tmp = os.path.join(tmp, "mix_v.mp4")
    if os.path.exists(_vid_tmp):
        print("[skip] video temp already exists")
    else:
        ok = False
        for _attempt in range(3):
            r = subprocess.run(
                ["ffmpeg", "-y", *norm_inputs, "-filter_complex", video_fc, "-map", "[v]",
                 "-threads", "1", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
                 "-an", _vid_tmp],
                capture_output=True,
            )
            if r.returncode == 0:
                ok = True
                break
            print(f"[warn] video step attempt {_attempt+1} rc={r.returncode}, retrying")
            _t.sleep(20)
        if not ok:
            raise RuntimeError("mix video step failed")
    r = subprocess.run(
        ["ffmpeg", "-y", "-threads", "1", "-i", _vid_tmp, "-i", _aud_tmp,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
         "-shortest", mp4],
        capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError("mix mux failed")
    # short: crop of the strongest 60s (from track 1's chorus ~40s in)
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-ss", "40", "-t", "60", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bgv];[fg][bgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", short,
    ], check=True, capture_output=True)
    print(f"[done] {slug}: {mp4}, {short}")
    return mp4


if __name__ == "__main__":
    args = sys.argv[2:]
    if len(args) < 4 or len(args) % 2:
        print("usage: make_mix.py <slug> <scene> <track> [<scene> <track> ...]")
        sys.exit(1)
    slug = sys.argv[1]
    pairs = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]
    build_mix(slug, pairs)
    print("OK")
