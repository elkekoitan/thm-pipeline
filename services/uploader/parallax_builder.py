#!/usr/bin/env python3
"""Layered parallax video system for THM Instrumental.

Takes a single photoreal cover image, semantically splits it into layers
(background / mid / foreground) using AI-free heuristics (center-crop
reconstruction via outpaint-free scaling) OR, preferably, AI-generated
layer assets (we generate 2 extra layer images per category: foreground
and background variants) and animates them at different speeds (parallax)
plus subtle particle overlays (dust/bokeh/rain streaks, per category).

Pipeline per category:
  1. Generate layer assets with generate_image (foreground.png, background.png)
     from the same scene, keeping composition consistent.
  2. Animate at 24fps:
     - background: slow horizontal drift (0.03 px/frame scaled)
     - mid: original cover, near-static with 0.5-1% breathing zoom
     - foreground: slightly faster drift + alpha fade-in
     - particles: procedural layer (bokeh dots / rain / dust), additive
  3. Pipe frames to ffmpeg rawvideo stdin (memory safe).

Usage: python3 parallax_builder.py <slug> <cover.png> <fg.png> <bg.png>
       [--duration SEC] [--out FILE]
"""
import argparse
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

FPS = 24
W, H = 1280, 720
W2, H2 = 960, 540  # render resolution (upscaled to 1280x720 at mux)


def load_scaled(path, sx, sy, margin=1.10):
    """Load image scaled so it fully covers sx*margin x sy*margin."""
    im = Image.open(path).convert("RGB")
    tw, th = int(sx * margin), int(sy * margin)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1),
                   Image.LANCZOS)
    return np.asarray(im, dtype=np.float32), tw, th


def crop_center(arr, tw, th, cx_frac, cy_frac, sx, sy):
    cx = int(tw * cx_frac)
    cy = int(th * cy_frac)
    left = max(0, min(cx - sx // 2, arr.shape[1] - sx))
    top = max(0, min(cy - sy // 2, arr.shape[0] - sy))
    return arr[top:top + sy, left:left + sx]


def _draw_disc(mask, cx, cy, r, alpha):
    """Blit one soft disc onto mask with proper clipping."""
    x0 = cx - r
    y0 = cy - r
    size = 2 * r + 1
    # crop mask region
    rx0 = max(0, x0)
    ry0 = max(0, y0)
    rx1 = min(mask.shape[1], x0 + size)
    ry1 = min(mask.shape[0], y0 + size)
    if rx1 <= rx0 or ry1 <= ry0:
        return
    # matching disc region
    dy0 = ry0 - y0
    dx0 = rx0 - x0
    disc = np.empty((ry1 - ry0, rx1 - rx0, 1), dtype=np.float32)
    for iy in range(ry1 - ry0):
        yy = dy0 + iy - r
        for ix in range(rx1 - rx0):
            xx = dx0 + ix - r
            disc[iy, ix, 0] = max(0.0, 1.0 - (xx * xx + yy * yy) / (r * r))
    mask[ry0:ry1, rx0:rx1] = np.maximum(mask[ry0:ry1, rx0:rx1], disc * alpha)


def bokeh_particles(rng, n, sx, sy, t):
    """Slowly drifting soft bokeh dots, additive alpha mask."""
    mask = np.zeros((sy, sx, 1), dtype=np.float32)
    base = 1 - abs(t - 0.5) * 0.4
    for _ in range(n):
        x = rng.uniform(0, sx)
        y = rng.uniform(0, sy)
        r = int(rng.uniform(6, 22))
        drift = (t - 0.5) * rng.uniform(10, 30)
        bx = int(x + drift) % sx
        by = int(y + (t - 0.5) * rng.uniform(5, 15)) % sy
        alpha = rng.uniform(0.03, 0.10) * base
        _draw_disc(mask, bx, by, r, alpha)
    return mask


def dust_particles(rng, n, sx, sy, t):
    mask = np.zeros((sy, sx, 1), dtype=np.float32)
    for _ in range(n):
        x = int(rng.uniform(0, sx) + t * rng.uniform(20, 60)) % sx
        y = int(rng.uniform(0, sy) + np.sin(t * 3 + x) * 8) % sy
        r = int(rng.uniform(2, 5))
        alpha = rng.uniform(0.04, 0.12)
        _draw_disc(mask, x, y, r, alpha)
    return mask


def build(slug, cover, fg, bg, duration, out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    n = int(duration * FPS)
    bg_arr, bgw, bgh = load_scaled(bg, W2, H2, margin=1.14)
    mid_arr, midw, midh = load_scaled(cover, W2, H2, margin=1.02)
    fg_arr, fgw, fgh = load_scaled(fg, W2, H2, margin=1.18)
    rng = random.Random(abs(hash(slug)) % 100000)
    p_rng = random.Random(abs(hash(slug + "p")) % 100000)

    pipe = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W2}x{H2}", "-r", str(FPS), "-i", "-",
         "-vf", "fps=24,format=yuv420p",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
         "-threads", "1", "-an", out],
        stdin=subprocess.PIPE)

    breath_max = 0.012
    for f_i in range(n):
        t = f_i / max(1, n - 1)
        # background: slow drift
        bg_crop = crop_center(bg_arr, bgw, bgh,
                              0.5 + 0.02 * np.sin(2 * np.pi * t),
                              0.5, W2, H2)
        # mid: barely-breathing zoom (no jitter, no shake)
        s = 1.0 + breath_max * abs(np.sin(np.pi * t))
        cw, ch = int(midw * s), int(midh * s)
        mid_x = max(0, min(int(midw * s / 2) - W2 // 2, midw - W2))
        mid_y = max(0, min(int(midh * s / 2) - H2 // 2, midh - H2))
        mid_crop = mid_arr[mid_y:mid_y + H2, mid_x:mid_x + W2]
        # foreground: faster drift + edge softness
        fg_crop = crop_center(fg_arr, fgw, fgh,
                              0.5 - 0.04 * np.sin(2 * np.pi * t),
                              0.5 + 0.01 * np.sin(4 * np.pi * t), W2, H2)

        # composite: mid base, bg visible through slight exposure blend,
        # fg alpha-blended (light edges stay crisp)
        frame = mid_crop.copy()
        # bg glow: lighten blend at low alpha
        frame = frame * 0.94 + bg_crop * 0.06
        fg_alpha = 0.35 + 0.10 * np.sin(2 * np.pi * t)  # gentle pulse, not jitter
        frame = frame * (1 - fg_alpha) + fg_crop * fg_alpha
        # particles
        if slug in ("02_lofi", "05_ambient_electronic"):
            frame = frame + bokeh_particles(p_rng, 26, W2, H2, t) * 220.0
        else:
            frame = frame + dust_particles(p_rng, 60, W2, H2, t) * 180.0
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        pipe.stdin.write(frame.tobytes())
        if f_i % 900 == 0:
            print(f"  [{slug}] frame {f_i}/{n}", flush=True)
    pipe.stdin.close()
    pipe.wait()
    if pipe.returncode != 0:
        raise RuntimeError(f"encode failed rc={pipe.returncode}")
    print(f"[parallax] {slug}: {out}")


def make_layer(slug, base_prompt, kind, out_path):
    """Generate a foreground/background layer asset variant."""
    # This function is a placeholder invoked via the main media pipeline,
    # kept here so usage is self-documenting. Actual generation happens
    # in the batch generate call (media_generation tool).
    raise NotImplementedError


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("cover")
    ap.add_argument("fg")
    ap.add_argument("bg")
    ap.add_argument("--duration", type=float, default=3600.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    build(args.slug, args.cover, args.fg, args.bg, args.duration, args.out)
