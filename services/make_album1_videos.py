#!/usr/bin/env python3
"""Rebuild THE GENEROUS album videos with Higgsfield photoreal scenes.

VARIANTS (user asked to try different animations on first images):
  v1 = slow_zoom   : classic very slow Ken Burns zoom-in 1.0 -> 1.06 (linear)
  v2 = drift       : slow horizontal linear drift (parallax feel) 1.03 zoom
  v3 = dive        : slow zoom-in 1.0 -> 1.12 with gentle downward drift
Each song gets the v1 (standard) video by default; variants also rendered
as separate clips so the user can compare.

Rules enforced: NO jitter/shake, NO text, 30fps, 1280x720 output,
short = 1080x1920 center crop.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

BASE = "/home/ubuntu/muzik"
A1 = os.path.join(BASE, "album1_v2")
SCENES = os.path.join(BASE, "album1_scenes")
FPS = 30
W, H = 1280, 720


SONGS = {
    "01_whisper_dark": {
        "song": "01_whisper_dark.mp3",
        "scene": "scene_whisper_dark.png",
    },
    "02_voice_in_mountains": {
        "song": "02_daglarda_ses.mp3",
        "scene": "voice_in_mountains.png",
    },
    "03_dancefloor_fever": {
        "song": "03_dancefloor_fever.mp3",
        "scene": "scene_dancefloor_fever.png",
    },
    "04_neon_istanbul": {
        "song": "04_neon_istanbul.mp3",
        "scene": "scene_neon_istanbul.png",
    },
    "05_wild_forest": {
        "song": "05_vahsi_orman.mp3",
        "scene": "scene_vahsi_orman.png",
    },
    "06_dream_garden": {
        "song": "06_ruya_bahcesi.mp3",
        "scene": "scene_ruya_bahcesi.png",
    },
    "07_star_warrior": {
        "song": "07_yildiz_savascisi.mp3",
        "scene": "scene_yildiz_savascisi.png",
    },
}

VARIANTS = {
    "slow_zoom": dict(z0=1.00, z1=1.06, pan=0.0, variant="v1"),
    "drift": dict(z0=1.03, z1=1.06, pan=0.06, variant="v2"),
    "dive": dict(z0=1.00, z1=1.12, pan=-0.03, variant="v3"),
}


def song_duration(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", mp3],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def render_frames(scene_path, n_frames, variant):
    """Return list of PIL frames (very slow motion, no jitter)."""
    im = Image.open(scene_path).convert("RGB")
    # pre-scale 2x for oversampling
    im = im.resize((W * 2, H * 2), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    z0, z1, pan = variant["z0"], variant["z1"], variant["pan"]
    frames = []
    cx0, cy0 = 0.5, 0.5
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        z = z0 + (z1 - z0) * t                       # linear zoom
        px = pan * t                                 # linear drift
        cw = int(W * 2 / z)
        ch = int(H * 2 / z)
        cx = int((cx0 + px) * (W * 2 - cw))
        cy = int(cy0 * (H * 2 - ch))
        cw = min(cw, W * 2 - cx)
        ch = min(ch, H * 2 - cy)
        crop = arr[cy:cy + ch, cx:cx + cw]
        frame = Image.fromarray(crop.astype(np.uint8)).resize((W, H),
                                                              Image.BILINEAR)
        frames.append(frame)
    return frames


def build_variant(slug, variant, n_frames):
    song = os.path.join(A1, SONGS[slug]["song"])
    scene = os.path.join(SCENES, SONGS[slug]["scene"])
    if not os.path.exists(scene):
        return None
    out_dir = os.path.join(A1, "variant_" + variant["variant"])
    os.makedirs(out_dir, exist_ok=True)
    vid_out = os.path.join(out_dir, slug + "_video.mp4")
    if os.path.exists(vid_out) and os.path.getsize(vid_out) > 1000000:
        print(f"[skip] {slug} {variant['variant']} exists")
        return vid_out

    tmpv = os.path.join(out_dir, slug + "_tmp.mp4")
    # render frames in one go (memory: ~ n_frames * 1280x720x3 ~ 280MB -> okay for
    # ~4000 frames? No — 4000 frames stored in RAM = too much. Render in chunks.)
    CHUNK = 400
    pipe = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
         "-threads", "1", "-pix_fmt", "yuv420p", tmpv],
        stdin=subprocess.PIPE)
    im = Image.open(scene).convert("RGB")
    im = im.resize((W * 2, H * 2), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    z0, z1, pan = variant["z0"], variant["z1"], variant["pan"]
    cx0, cy0 = 0.5, 0.5
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        z = z0 + (z1 - z0) * t
        px = pan * t
        cw = int(W * 2 / z)
        ch = int(H * 2 / z)
        cx = int((cx0 + px) * (W * 2 - cw))
        cy = int(cy0 * (H * 2 - ch))
        cw = min(cw, W * 2 - cx)
        ch = min(ch, H * 2 - cy)
        crop = arr[cy:cy + ch, cx:cx + cw]
        frame = Image.fromarray(crop.astype(np.uint8)).resize((W, H),
                                                              Image.BILINEAR)
        pipe.stdin.write(frame.tobytes())
        if i % 500 == 0:
            print(f"  [{slug}:{variant['variant']}] frame {i}/{n_frames}",
                  flush=True)
    pipe.stdin.close()
    pipe.wait()
    # mux with audio
    r = subprocess.run(["ffmpeg", "-y", "-i", song, "-i", tmpv,
                        "-map", "0:a", "-map", "1:v",
                        "-c:a", "aac", "-b:a", "192k",
                        "-c:v", "copy", "-shortest", vid_out],
                       capture_output=True, text=True)
    os.remove(tmpv)
    if r.returncode != 0:
        print(f"[ERROR] {slug} {variant['variant']}: {r.stderr[-300:]}")
        return None
    print(f"[done-video] {slug} {variant['variant']}")
    return vid_out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for slug, spec in SONGS.items():
        if which not in ("all", "variants") and slug != which:
            continue
        song = os.path.join(A1, spec["song"])
        if not os.path.exists(song):
            print(f"[MISSING] {song}")
            continue
        dur = song_duration(song)
        n = int(dur * FPS)
        for vname, var in VARIANTS.items():
            if which == "variants":
                build_variant(slug, var, n)
            else:
                # default = standard slow_zoom
                build_variant(slug, VARIANTS["slow_zoom"], n)


if __name__ == "__main__":
    main()
