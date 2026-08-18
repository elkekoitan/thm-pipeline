#!/usr/bin/env python3
"""Build polished channel branding visuals for Turhan Hamza Müzik (THM Official).

Outputs (all text-free or brand-text-only, professional look):
- profile_800.png   : 800x800 channel profile picture (THM monogram, premium dark)
- banner_2560.png   : 2560x1440 channel banner (desktop safe area 1546x423)
- promo_album1.png  : 1920x1080 THE GENEROUS album promo visual
- promo_album2.png  : 1920x1080 ECHOES OF A CITY album promo visual
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/ubuntu/muzik"
OUT = os.path.join(BASE, "channel_final")
FONT = "/home/ubuntu/.fonts/PlayfairDisplay.ttf"
os.makedirs(OUT, exist_ok=True)


def grad(d, w, h, stops, vertical=True):
    for y in range(h):
        for x in range(w):
            t = (y / h) if vertical else (x / w)
            # find segment
            i = 0
            for i in range(len(stops) - 1):
                if stops[i][0] <= t <= stops[i + 1][0]:
                    break
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            r = int(c0[0] * (1 - f) + c1[0] * f)
            g = int(c0[1] * (1 - f) + c1[1] * f)
            b = int(c0[2] * (1 - f) + c1[2] * f)
            d.point((x, y), fill=(r, g, b))


def add_noise(img, sigma=7, amount=0.09):
    noise = Image.effect_noise(img.size, sigma=sigma).convert("RGB")
    return Image.blend(img.convert("RGB"), noise, amount)


# ---------- 1. Profile picture 800x800 ----------
def build_profile():
    size = 800
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    stops = [(0.0, (6, 9, 20)), (0.45, (14, 20, 46)), (1.0, (36, 22, 70))]
    grad(d, size, size, stops)
    img = add_noise(img)
    d = ImageDraw.Draw(img)
    # concentric thin rings (premium)
    cx = cy = size // 2
    for r in range(360, 30, -40):
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  outline=(212, 175, 100), width=2)
    # THM monogram
    font = ImageFont.truetype(FONT, 260)
    txt = "THM"
    bbox = d.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), txt,
           font=font, fill=(248, 242, 232))
    # small tagline line
    font2 = ImageFont.truetype(FONT, 52)
    txt2 = "MUSIC"
    bbox2 = d.textbbox((0, 0), txt2, font=font2)
    tw2 = bbox2[2] - bbox2[0]
    d.text((cx - tw2 / 2 - bbox2[0], cy + 190 - bbox2[1]), txt2,
           font=font2, fill=(212, 175, 100))
    img.save(os.path.join(OUT, "profile_800.png"))
    print("[ok] profile_800.png")


# ---------- 2. Banner 2560x1440 ----------
def build_banner():
    w, h = 2560, 1440
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    stops = [(0.0, (3, 5, 14)), (0.5, (10, 12, 34)), (1.0, (22, 12, 42))]
    grad(d, w, h, stops)
    img = add_noise(img, sigma=10, amount=0.07)
    d = ImageDraw.Draw(img)
    # soft glowing horizon band (safe zone y 508-932)
    band = Image.new("RGBA", (w, 424), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(424):
        t = y / 424
        alpha = int(70 * math.sin(math.pi * t))
        bd.line([(0, y), (w, y)], fill=(212, 175, 100, alpha))
    band = band.filter(ImageFilter.GaussianBlur(40))
    img.paste(band, (0, 508), band)
    # THM wordmark centered in safe area
    cx, cy = w // 2, 720
    font = ImageFont.truetype(FONT, 150)
    txt = "THM OFFICIAL"
    bbox = d.textbbox((0, 0), txt, font=font)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2 - bbox[0], cy - 80 - bbox[1]), txt,
           font=font, fill=(248, 242, 232))
    font2 = ImageFont.truetype(FONT, 46)
    txt2 = "MUSIC CHANNEL"
    bbox2 = d.textbbox((0, 0), txt2, font=font2)
    tw2 = bbox2[2] - bbox2[0]
    d.text((cx - tw2 / 2 - bbox2[0], cy + 110 - bbox2[1]), txt2,
           font=font2, fill=(212, 175, 100))
    img.save(os.path.join(OUT, "banner_2560.png"))
    print("[ok] banner_2560.png")


# ---------- 3/4. Album promo visuals 1920x1080 ----------
def build_promo(filename, title, subtitle, colors):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    stops = [(0.0, colors[0]), (1.0, colors[1])]
    grad(d, w, h, stops)
    img = add_noise(img, sigma=8, amount=0.08)
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    r = 300
    panel = Image.new("RGBA", (r * 2 + 40, r * 2 + 40), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.ellipse((10, 10, r * 2 + 30, r * 2 + 30),
               fill=(10, 10, 18, 235), outline=(212, 175, 100), width=4)
    panel = panel.filter(ImageFilter.GaussianBlur(2))
    img.paste(panel, (cx - r - 20, cy - r - 20), panel)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 108)
    bbox = d.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2 - bbox[0], cy - 60 - bbox[1]), title,
           font=font, fill=(248, 242, 232))
    font2 = ImageFont.truetype(FONT, 44)
    bbox2 = d.textbbox((0, 0), subtitle, font=font2)
    tw2 = bbox2[2] - bbox2[0]
    d.text((cx - tw2 / 2 - bbox2[0], cy + 90 - bbox2[1]), subtitle,
           font=font2, fill=(212, 175, 100))
    img.save(os.path.join(OUT, filename))
    print("[ok]", filename)


if __name__ == "__main__":
    build_profile()
    build_banner()
    build_promo("promo_album1.png", "THE GENEROUS",
                "Seven Colors of Generosity",
                ((8, 10, 30), (40, 20, 60)))
    build_promo("promo_album2.png", "ECHOES OF A CITY",
                "Five Nights, Five Stories",
                ((6, 14, 26), (60, 30, 20)))
    print("ALL BUILT")
