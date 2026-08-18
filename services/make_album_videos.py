#!/usr/bin/env python3
"""Build 1920x1080 music videos for the SEVEN COLORS album.

For each track: a themed panel image (16:9, generated deterministically with
Pillow, matching the album cover palette) is animated with a single, smooth,
slow Ken Burns pan (no jitter), rendered to 30 fps frames, then muxed with the
song audio. 9:16 Shorts are produced via center crop.
"""
import json
import math
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BASE = "/home/ubuntu/muzik"
ALBUM = os.path.join(BASE, "album")
FONT = "/home/ubuntu/.fonts/PlayfairDisplay.ttf"

TRACKS = [
    ("01", "whisper_dark", "Whisper Dark", "TH Music - Whisper Dark (Official Audio)",
     "#0B1A33", "#1B2E5E", "Dark alt-pop — whispers in the night"),
    ("02", "daglarda_ses", "Dağlarda Ses", "TH Music - Dağlarda Ses (Official Audio)",
     "#8A5A1E", "#E8A93D", "Anatolian rock — the voice of the mountains"),
    ("03", "dancefloor_fever", "Dancefloor Fever", "TH Music - Dancefloor Fever (Official Audio)",
     "#C2185B", "#FF6FA3", "Dance-pop — lights, floor, heat"),
    ("04", "neon_istanbul", "Neon İstanbul", "TH Music - Neon İstanbul (Official Audio)",
     "#00838F", "#4DD0E1", "Synthwave — midnight city glide"),
    ("05", "vahsi_orman", "Vahşi Orman", "TH Music - Vahşi Orman (Official Audio)",
     "#7B1111", "#E53935", "Hard rock — the storm inside the forest"),
    ("06", "ruya_bahcesi", "Rüya Bahçesi", "TH Music - Rüya Bahçesi (Official Audio)",
     "#4A6B4F", "#A8C6A0", "Indie folk — a garden of dreams"),
    ("07", "yildiz_savascisi", "Yıldız Savaşçısı", "TH Music - Yıldız Savaşçısı (Official Audio)",
     "#1A0A2E", "#6A3FA0", "Trap anthem — the star warrior"),
]

W, H = 1920, 1080
FPS = 30


def build_panel(name, c1, c2, title, subtitle):
    """Create a 16:9 themed panel image for the track."""
    src = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(src)
    for y in range(H):
        t = y / H
        r = int(int(c1[1:3], 16) * (1 - t) + int(c2[1:3], 16) * t)
        g = int(int(c1[3:5], 16) * (1 - t) + int(c2[3:5], 16) * t)
        b = int(int(c1[5:7], 16) * (1 - t) + int(c2[5:7], 16) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    noise = Image.effect_noise((W, H), sigma=9).convert("RGB")
    src = Image.blend(src, noise, 0.10)

    # subtle glow orb near center-right (different size per track)
    orr = int(H * 0.62)
    orb = Image.new("RGBA", (orr * 2, orr * 2), (0, 0, 0, 0))
    od = ImageDraw.Draw(orb)
    for rad in range(orr, 0, -6):
        alpha = max(0, int(60 * (1 - rad / orr) ** 1.5))
        od.ellipse((orr - rad, orr - rad, orr + rad, orr + rad), fill=(255, 255, 255, alpha))
    orb = orb.filter(ImageFilter.GaussianBlur(60))
    ocx, ocy = int(W * 0.62), int(H * 0.5)
    src.paste(orb, (ocx - orr, ocy - orr), orb)
    src = src.convert("RGB")

    d = ImageDraw.Draw(src)
    # faint large title across background
    font_big = ImageFont.truetype(FONT, 170)
    bbox = d.textbbox((0, 0), title, font=font_big)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) / 2, int(H * 0.24) - bbox[1]), title, font=font_big, fill=(255, 255, 255))
    font_sub = ImageFont.truetype(FONT, 46)
    bbox2 = d.textbbox((0, 0), subtitle, font=font_sub)
    tw2 = bbox2[2] - bbox2[0]
    d.text(((W - tw2) / 2, int(H * 0.42) - bbox2[1]), subtitle, font=font_sub, fill=(255, 255, 255))
    font_th = ImageFont.truetype(FONT, 34)
    ttext = "TH Music"
    bbox3 = d.textbbox((0, 0), ttext, font=font_th)
    tw3 = bbox3[2] - bbox3[0]
    d.text(((W - tw3) / 2, int(H * 0.52) - bbox3[1]), ttext, font=font_th, fill=(200, 200, 200))
    return src


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def render_frames(panel, outdir, duration):
    os.makedirs(outdir, exist_ok=True)
    n = int(round(duration * FPS))
    max_off_x = int(W * 0.06)
    max_off_y = int(H * 0.08)
    for i in range(n):
        t = ease(i / max(1, n - 1))
        ox = int(max_off_x * (2 * t - 1))
        oy = int(max_off_y * math.sin(math.pi * t))
        s = 1.04 + 0.04 * math.sin(math.pi * t)  # very subtle zoom
        cw, ch = int(W * s), int(H * s)
        # crop centered with offset, scale back to WxH
        cx = int(panel.width * s / 2 + ox)
        cy = int(panel.height * s / 2 + oy)
        left = max(0, min(cx - W // 2, panel.width - W))
        top = max(0, min(cy - H // 2, panel.height - H))
        frame = panel.crop((left, top, left + W, top + H)).resize((W, H), Image.LANCZOS)
        frame.save(os.path.join(outdir, f"f{i:05d}.jpg"), quality=88)
    return n


def duration_of(mp3):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp3], capture_output=True, text=True)
    return float(r.stdout.strip())


def build_video(idx, name, duration, title):
    tmp = f"/tmp/thmvid_{name}"
    audio = os.path.join(ALBUM, f"{idx}_{name}.mp3")
    mp4 = os.path.join(ALBUM, f"{idx}_{name}_video.mp4")
    short = os.path.join(ALBUM, f"{idx}_{name}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {name} exists")
        return
    # render frames if not present
    n = int(duration * FPS)
    if not os.path.exists(os.path.join(tmp, f"f{n-1:05d}.jpg")):
        render_frames(panels[name], tmp, duration)
    # encode with audio
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.jpg"),
        "-i", audio, "-t", str(duration),
        "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", mp4,
    ], check=True, capture_output=True)
    # 9:16 short: center 1080x1080 square crop + blurred letterbox pillars to fill 1080x1920
    subprocess.run([
        "ffmpeg", "-y", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2[bgv];[fg]crop=1080:1080:420:0,scale=1080:1080[fgv];[bgv][fgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a", "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", short,
    ], check=True, capture_output=True)
    print(f"[done] {name}: {mp4} ({duration:.1f}s), short: {short}")


if __name__ == "__main__":
    panels = {}
    for idx, name, title, _, c1, c2, sub in TRACKS:
        panels[name] = build_panel(name, c1, c2, title, sub)
        panels[name].save(os.path.join(ALBUM, f"panel_{name}.png"))
    for idx, name, title, _, c1, c2, sub in TRACKS:
        dur = duration_of(os.path.join(ALBUM, f"{idx}_{name}.mp3"))
        build_video(idx, name, dur, title)
    print("ALL DONE")
