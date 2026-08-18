#!/usr/bin/env python3
"""Build the 'SEVEN COLORS' album cover programmatically.

7 vertical color panels (one per track/mood) with a central circular badge
carrying the album title and artist, plus Playfair Display serif typography.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W = H = 1200
img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# (track color, gradient end color) — seven distinct moods
panels = [
    ("#0B1A33", "#1B2E5E"),  # 1 Whisper Dark — midnight blue
    ("#8A5A1E", "#E8A93D"),  # 2 Dağlarda Ses — amber gold
    ("#C2185B", "#FF6FA3"),  # 3 Dancefloor Fever — hot pink
    ("#00838F", "#4DD0E1"),  # 4 Neon İstanbul — cyan neon
    ("#7B1111", "#E53935"),  # 5 Vahşi Orman — crimson
    ("#4A6B4F", "#A8C6A0"),  # 6 Rüya Bahçesi — sage green
    ("#1A0A2E", "#6A3FA0"),  # 7 Yıldız Savaşçısı — cosmic violet
]

ph = H // len(panels)
for i, (c1, c2) in enumerate(panels):
    # vertical gradient per panel
    base = Image.new("RGB", (W, ph + 4))
    for y in range(ph + 4):
        t = y / (ph + 4)
        r = int(int(c1[1:3], 16) * (1 - t) + int(c2[1:3], 16) * t)
        g = int(int(c1[3:5], 16) * (1 - t) + int(c2[3:5], 16) * t)
        b = int(int(c1[5:7], 16) * (1 - t) + int(c2[5:7], 16) * t)
        ImageDraw.Draw(base).line([(0, y), (W, y)], fill=(r, g, b))
    # subtle film grain
    noise = Image.effect_noise((W, ph + 4), sigma=7).convert("RGB")
    base = Image.blend(base, noise, 0.08)
    img.paste(base, (0, i * ph))
draw = ImageDraw.Draw(img)

# Thin separator lines between panels
for i in range(1, len(panels)):
    draw.line([(0, i * ph), (W, i * ph)], fill=(255, 255, 255), width=3)

# Central circle badge with blur backdrop
cx, cy, r = W // 2, H // 2, 235
badge_src = img.crop((cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40))
badge_back = badge_src.filter(ImageFilter.GaussianBlur(18))
badge_back = ImageEnhance.Brightness(badge_back).enhance(0.55)
mask = Image.new("L", (r * 2 + 80, r * 2 + 80), 0)
ImageDraw.Draw(mask).ellipse((40, 40, r * 2 + 40, r * 2 + 40), fill=255)
img.paste(badge_back, (cx - r - 40, cy - r - 40), mask)
draw = ImageDraw.Draw(img)
draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255), width=5)

FONT_PATH = "/home/ubuntu/.fonts/PlayfairDisplay.ttf"
font_title = ImageFont.truetype(FONT_PATH, 74)
font_sub = ImageFont.truetype(FONT_PATH, 34)

def draw_centered(d, text, font, y, fill=(255, 255, 255)):
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2 - bbox[0], y), text, font=font, fill=fill)

draw_centered(draw, "SEVEN", font_title, cy - r + 108)
draw_centered(draw, "COLORS", font_title, cy - r + 188)
draw_centered(draw, "— TH Music —", font_sub, cy - r + 308)

# Track numbers centered on the right portion of each panel
font_num = ImageFont.truetype(FONT_PATH, 30)
for i in range(len(panels)):
    ty = i * ph + ph // 2
    draw.text((W - 110, ty - 15), str(i + 1), font=font_num, fill=(255, 255, 255, 180))

img.save("/home/ubuntu/muzik/album/album_cover_seven_colors.png")
print("saved")
