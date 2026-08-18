#!/usr/bin/env python3
"""THM Instrumental — multi-technique cinematic video builder.

Combines several professional techniques per category (no jitter/shake,
no zoom-pulse):
  1. Layered PARALLAX     — bg/mid/fg assets composited at different speeds
  2. LIGHT SWEEP          — slow diagonal light gradient travelling across
  3. COLOR GRADE SHIFT    — gentle warm<->cool grade breathing over minutes
  4. FOG/PARTICLE DRIFT   — bokeh, dust, rain (per category)
  5. FILM GRAIN           — subtle temporal grain for analog feel
  6. VIGNETTE BREATH      — very slow edge darkening pulse
  7. CROSSFADE SCENES     — when multiple scenes exist, slow 4s fades

Frames piped to ffmpeg rawvideo stdin (OOM-safe).
Usage: python3 cinematic_builder.py <slug> <cover> <fg> <bg> \
       [--duration SEC] [--out FILE] [--rain] [--no-grain]
"""
import argparse
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image

FPS = 24
W2, H2 = 960, 540


# ---------------------------------------------------------------- utils
def load_scaled(path, sx, sy, margin=1.10):
    im = Image.open(path).convert("RGB")
    tw, th = int(sx * margin), int(sy * margin)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1),
                   Image.LANCZOS)
    return np.asarray(im, dtype=np.float32), tw, th


def crop_center(arr, tw, th, cx_frac, cy_frac, sx, sy):
    cx, cy = int(tw * cx_frac), int(th * cy_frac)
    left = max(0, min(cx - sx // 2, arr.shape[1] - sx))
    top = max(0, min(cy - sy // 2, arr.shape[0] - sy))
    return arr[top:top + sy, left:left + sx]


# ---------------------------------------------------------------- grain
def _grain_lut(slug, sx, sy):
    """Cheap high-quality grain: 2x2 base + per-frame random offset."""
    base = np.random.RandomState(int(hash(slug + "g")) % (2 ** 32 - 1)).random(
        (sy // 2 + 4, sx // 2 + 4)).astype(np.float32)
    return base


def apply_grain(frame, lut, t, strength=7.0):
    sx, sy = frame.shape[1], frame.shape[0]
    ox, oy = int(t * 1000) % 2, int(t * 2347) % 2
    g = lut[oy:oy + sy // 2, ox:ox + sx // 2]
    g = np.repeat(np.repeat(g, 2, axis=1), 2, axis=0)[:sy, :sx]
    frame += (g - 0.5)[:, :, None] * strength
    return frame


# ---------------------------------------------------------------- light sweep
def light_sweep(sx, sy, t, alpha=0.09):
    """Slow diagonal light band travelling across the frame (period 24s)."""
    x = np.arange(sx, dtype=np.float32)
    phase = (t * 2 * np.pi / 24.0) % (2 * np.pi)
    pos = (np.sin(phase) + 1) * 0.5 * (sx + 300) - 150
    d = np.abs(x - pos)
    band = np.clip(1 - d / 300.0, 0, 1).reshape(1, -1, 1) ** 2
    return band * alpha * 220.0


# ---------------------------------------------------------------- fog drift
def fog_layers(rng, sx, sy, t):
    """Two huge soft Gaussian fog sheets drifting slowly (period ~60-90s)."""
    fog = np.zeros((sy, sx, 1), dtype=np.float32)
    for k in range(2):
        period = 70 + k * 25
        cx = (0.5 + 0.35 * np.sin(2 * np.pi * t / (period / 24.0) + k * 1.7)) * sx
        cy = (0.62 + 0.12 * np.sin(2 * np.pi * t / (period / 24.0) * 0.7 + k)) * sy
        r = rng.uniform(380, 520)
        yy, xx = np.ogrid[:sy, :sx]
        d2 = ((xx - cx) / r) ** 2 + ((yy - cy) / (r * 0.5)) ** 2
        sheet = np.clip(1 - d2, 0, 1)[:, :, None] * rng.uniform(0.05, 0.09)
        fog = np.maximum(fog, sheet)
    return fog * 200.0


# ---------------------------------------------------------------- rain
def rain_overlay(rng, sx, sy, t):
    """Diagonal rain streaks with per-frame variation."""
    n = 340
    mask = np.zeros((sy, sx, 1), dtype=np.float32)
    # deterministic-ish stream offsets via rng seeded once
    for _ in range(n):
        x = rng.uniform(-0.2, 1.2) * sx
        speed = rng.uniform(300, 500)
        phase = rng.uniform(0, 1)
        y = ((t * speed + phase * sy) % (sy + 120)) - 60
        length = rng.uniform(14, 26)
        alpha = rng.uniform(0.05, 0.14)
        x0, x1 = int(x), int(x + 4)
        y0, y1 = int(y - length / 2), int(y + length / 2)
        if x1 <= 0 or x0 >= sx or y1 <= 0 or y0 >= sy:
            continue
        x0, x1 = max(0, x0), min(sx, x1)
        y0, y1 = max(0, y0), min(sy, y1)
        mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], alpha)
    return mask


# ---------------------------------------------------------------- bokeh
def bokeh_particles(rng, n, sx, sy, t):
    mask = np.zeros((sy, sx, 1), dtype=np.float32)
    base = 1 - abs(np.sin(2 * np.pi * t)) * 0.35
    for _ in range(n):
        x = rng.uniform(0, sx)
        y = rng.uniform(0, sy)
        r = int(rng.uniform(6, 22))
        drift = np.sin(2 * np.pi * t + x) * rng.uniform(10, 30)
        bx = int(x + drift) % sx
        by = int(y + np.sin(2 * np.pi * t) * rng.uniform(6, 16)) % sy
        alpha = rng.uniform(0.03, 0.10) * base
        _draw_disc(mask, bx, by, r, alpha)
    return mask


def _draw_disc(mask, cx, cy, r, alpha):
    x0, y0 = cx - r, cy - r
    size = 2 * r + 1
    rx0, ry0 = max(0, x0), max(0, y0)
    rx1, ry1 = min(mask.shape[1], x0 + size), min(mask.shape[0], y0 + size)
    if rx1 <= rx0 or ry1 <= ry0:
        return
    dy0, dx0 = ry0 - y0, rx0 - x0
    disc = np.empty((ry1 - ry0, rx1 - rx0, 1), dtype=np.float32)
    for iy in range(ry1 - ry0):
        yy = dy0 + iy - r
        for ix in range(rx1 - rx0):
            xx = dx0 + ix - r
            disc[iy, ix, 0] = max(0.0, 1.0 - (xx * xx + yy * yy) / (r * r))
    mask[ry0:ry1, rx0:rx1] = np.maximum(mask[ry0:ry1, rx0:rx1], disc * alpha)


# ---------------------------------------------------------------- grade shift
def grade_shift(frame, t, warm_mag=6.0):
    """Slow warm <-> cool breathing over 90s. Returns additive shift (H,S,V)."""
    phase = np.sin(2 * np.pi * t / (90.0 / 24.0 * 1.0))  # ~90s period
    shift = phase * warm_mag
    out = frame.copy()
    out[:, :, 0] += shift        # R
    out[:, :, 2] -= shift * 0.7  # B
    return out


# ---------------------------------------------------------------- vignette
def vignette(sx, sy, t):
    yy, xx = np.mgrid[:sy, :sx]
    cx, cy = sx / 2.0, sy / 2.0
    d = np.sqrt(((xx - cx) / (sx * 0.62)) ** 2 + ((yy - cy) / (sy * 0.62)) ** 2)
    v = np.clip(1 - (d - 0.85) * 0.35, 0, 1)
    strength = 0.90 + 0.04 * np.sin(2 * np.pi * t / (120.0 / 24.0))
    return v[:, :, None] * strength + (1 - strength)


# ---------------------------------------------------------------- main
def build(slug, cover, fg, bg, duration, out, rain=False, grain=True,
          fog=True, sweep=True, grade=True, vign=True):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    n = int(duration * FPS)
    bg_arr, bgw, bgh = load_scaled(bg, W2, H2, margin=1.14)
    mid_arr, midw, midh = load_scaled(cover, W2, H2, margin=1.02)
    fg_arr, fgw, fgh = load_scaled(fg, W2, H2, margin=1.18)
    rng = random.Random(abs(hash(slug)) % 100000)
    p_rng = random.Random(abs(hash(slug + "p")) % 100000)
    g_lut = _grain_lut(slug, W2, H2)

    pipe = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W2}x{H2}", "-r", str(FPS), "-i", "-",
         "-vf", "fps=24,format=yuv420p",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
         "-threads", "1", "-an", out],
        stdin=subprocess.PIPE)

    for f_i in range(n):
        t = f_i / max(1, n - 1)
        # 1) parallax layers
        bg_crop = crop_center(bg_arr, bgw, bgh,
                              0.5 + 0.02 * np.sin(2 * np.pi * t / 20.0),
                              0.5, W2, H2)
        s = 1.0 + 0.012 * abs(np.sin(np.pi * t / 10.0))
        mid_x = max(0, min(int(midw * s / 2) - W2 // 2, midw - W2))
        mid_y = max(0, min(int(midh * s / 2) - H2 // 2, midh - H2))
        mid_crop = mid_arr[mid_y:mid_y + H2, mid_x:mid_x + W2]
        fg_crop = crop_center(fg_arr, fgw, fgh,
                              0.5 - 0.04 * np.sin(2 * np.pi * t / 14.0),
                              0.5 + 0.01 * np.sin(4 * np.pi * t / 8.0),
                              W2, H2)
        frame = mid_crop * 0.94 + bg_crop * 0.06
        fa = 0.35 + 0.10 * np.sin(2 * np.pi * t / 14.0)
        frame = frame * (1 - fa) + fg_crop * fa

        # 2) light sweep
        if sweep:
            frame = frame + light_sweep(W2, H2, t)

        # 3) fog drift
        if fog:
            frame = frame + fog_layers(rng, W2, H2, t)

        # 4) category particles (rain for lofi/nature, bokeh otherwise)
        if rain or slug in ("02_lofi", "08_nature"):
            frame = frame + rain_overlay(p_rng, W2, H2, t)
        else:
            frame = frame + bokeh_particles(p_rng, 22, W2, H2, t) * 220.0

        # 5) color grade shift
        if grade:
            frame = grade_shift(frame, t)

        frame = np.clip(frame, 0, 255)

        # 6) vignette
        if vign:
            frame = frame * vignette(W2, H2, t)

        # 7) film grain
        if grain:
            frame = apply_grain(frame, g_lut, t)

        frame = np.clip(frame, 0, 255).astype(np.uint8)
        pipe.stdin.write(frame.tobytes())
        if f_i % 1200 == 0:
            print(f"  [{slug}] frame {f_i}/{n}", flush=True)
    pipe.stdin.close()
    pipe.wait()
    if pipe.returncode != 0:
        raise RuntimeError(f"encode failed rc={pipe.returncode}")
    print(f"[cinematic] {slug}: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("cover")
    ap.add_argument("fg")
    ap.add_argument("bg")
    ap.add_argument("--duration", type=float, default=3600.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rain", action="store_true")
    ap.add_argument("--no-grain", action="store_true")
    args = ap.parse_args()
    build(args.slug, args.cover, args.fg, args.bg, args.duration, args.out,
          rain=args.rain, grain=not args.no_grain)
