#!/usr/bin/env python3
"""Build 1920x1080 story music videos for the ECHOES OF A CITY album.

Each video: available story scene images (photorealistic, no text) are animated
with a single smooth slow Ken Burns pan per scene, scenes crossfade at
transitions. 30 fps H.264 + AAC. Shorts = 1080x1920 blurred pillarbox.
"""
import math
import os
import subprocess
import sys
from PIL import Image, ImageFilter

BASE = "/home/ubuntu/muzik/album2"
W, H = 1920, 1080
FPS = 24
FADE_FRAMES = int(1.0 * FPS)  # 1.0s crossfade


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


import random


def kenburns_frames(img, n_frames, seed):
    """Smooth single-direction Ken Burns pan for n_frames; returns list of
    (WxH) PIL frames."""
    rng = random.Random(seed)
    max_off_x = int(W * 0.07)
    max_off_y = int(H * 0.09)
    # direction per scene (deterministic from seed)
    dx = 1 if rng.random() > 0.5 else -1
    dy = 1 if rng.random() > 0.5 else -1
    s_start = 1.06
    s_end = 1.00
    frames = []
    for i in range(n_frames):
        t = ease(i / max(1, n_frames - 1))
        ox = int(max_off_x * dx * (2 * t - 1))
        oy = int(max_off_y * dy * (2 * t - 1))
        s = s_start + (s_end - s_start) * t
        cw, ch = int(img.width * s), int(img.height * s)
        cx = int(img.width * s / 2 + ox)
        cy = int(img.height * s / 2 + oy)
        left = max(0, min(cx - W // 2, img.width - W))
        top = max(0, min(cy - H // 2, img.height - H))
        frame = img.crop((left, top, left + W, top + H)).resize((W, H), Image.LANCZOS)
        frames.append(frame)
    return frames


def duration_of(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp3], capture_output=True, text=True)
    return float(r.stdout.strip())


def load_scene(path):
    im = Image.open(path).convert("RGB")
    # keep at 2x oversample for smooth Ken Burns without full-res cost
    if im.width < W * 2 or im.height < H * 2:
        s = max(W * 2 / im.width, H * 2 / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
    return im


def build_song(idx, key, title, scenes, audio_dur):
    mp4 = os.path.join(BASE, f"{idx}_{key}_video.mp4")
    short = os.path.join(BASE, f"{idx}_{key}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {key}")
        return
    if not scenes:
        print(f"[NO SCENES] {key} — skipping")
        return
    n_total = int(round(audio_dur * FPS))
    n_scenes = len(scenes)
    per = n_total // n_scenes
    tmp = f"/tmp/thm2_{key}"
    os.makedirs(tmp, exist_ok=True)
    print(f"[{key}] {n_scenes} scenes, {per} frames each, total {n_total}")
    # render scenes one-at-a-time (memory-safe), encode each to mp4, then xfade
    clips = []
    for i, s in enumerate(scenes):
        im = load_scene(os.path.join(BASE, s))
        extra = FADE_FRAMES if i < n_scenes - 1 else 0
        n = per + extra
        seed = hash(key + s) % 10000
        out_n = n
        frame_idx = 0
        # write scene frames in small chunks with crossfade blending against next
        nxt_im = load_scene(os.path.join(BASE, scenes[i + 1])) if i < n_scenes - 1 else None
        for fi in range(n):
            frs = kenburns_frames(im, 1, seed + fi)
            fr = frs[0]
            if nxt_im is not None and fi >= n - FADE_FRAMES:
                nxt_frs = kenburns_frames(nxt_im, 1, hash(key + scenes[i + 1]) % 10000 + (fi - (n - FADE_FRAMES)))
                alpha = (fi - (n - FADE_FRAMES)) / FADE_FRAMES
                fr = Image.blend(fr.convert("RGB"), nxt_frs[0].convert("RGB"), alpha)
            fr.save(os.path.join(tmp, f"f{frame_idx:05d}.jpg"), quality=80)
            frame_idx += 1
        clip = os.path.join(tmp, f"clip{i}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-threads", "2", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.jpg"),
            "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-x264-params", "threads=2", "-an", clip,
        ], check=True, capture_output=True)
        # clean frames for memory
        subprocess.run(["rm", "-rf", os.path.join(tmp, "f*.jpg")], capture_output=True)
        import glob
        for f in glob.glob(os.path.join(tmp, "f*.jpg")):
            os.remove(f)
        clips.append(clip)
    audio = os.path.join(BASE, f"{idx}_{key}.mp3")
    mp4 = os.path.join(BASE, f"{idx}_{key}_video.mp4")
    if len(clips) == 1:
        subprocess.run([
            "ffmpeg", "-y", "-i", clips[0], "-i", audio, "-t", str(audio_dur),
            "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
        ], check=True, capture_output=True)
    else:
        # xfade chain of clips, durations computed from frame counts
        from itertools import accumulate
        per_d = per / FPS
        inputs = []
        for c in clips:
            inputs += ["-i", c]
        filters = []
        prev = "0:v"
        offset = 0.0
        for i in range(1, len(clips)):
            # overlap: FADE seconds; each clip after first starts FADE later in timeline
            off = offset + per_d - FADE_FRAMES / FPS
            new = f"[v{i}]"
            filters.append(
                f"[{prev}][{i}:v]xfade=transition=fade:duration={FADE_FRAMES / FPS:.3f}:offset={off:.3f}{new}"
            )
            offset = off
            prev = new
        fc = ";".join(filters) + f";{prev},format=yuv420p[v]"
        subprocess.run([
            "ffmpeg", "-y", *inputs, "-i", audio,
            "-filter_complex", fc, "-map", "[v]", "-map", f"{len(clips)}:a",
            "-t", str(audio_dur),
            "-threads", "2",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
        ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-threads", "2", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2[bgv];[fg]crop=1080:1080:420:0,scale=1080:1080[fgv];[bgv][fgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a", "-t", str(audio_dur),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", short,
    ], check=True, capture_output=True)
    print(f"[done] {key}: {mp4}, {short}")


TRACKS = {
    "01": ("rain_on_the_rooftop", ["scene_rain_1.png", "scene_rain_2.png"]),
    "02": ("midnight_ferryman", ["scene_ferry_1.png", "scene_ferry_2.png"]),
    "03": ("rooftop_runners", ["scene_rooftop_1.png", "scene_rooftop_2.png"]),
    "04": ("clockmakers_daughter", ["scene_clock_1.png", "scene_clock_2.png"]),
    "05": ("last_train_to_anywhere", ["scene_train_1.png", "scene_train_2.png"]),
    "06": ("fuego_en_la_calle", ["scene_fuego_1.png", "scene_fuego_2.png"]),
}

if __name__ == "__main__":
    for idx, (key, scenes) in TRACKS.items():
        dur = duration_of(os.path.join(BASE, f"{idx}_{key}.mp3"))
        build_song(idx, key, key, scenes, dur)
    print("ALL DONE")
