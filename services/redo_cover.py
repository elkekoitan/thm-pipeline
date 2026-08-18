#!/usr/bin/env python3
"""Rebuild album cover with new English title 'THE GIVERS' (Yediverenler).
Keeps the 7-color horizontal panel design and central dark circle with
Playfair Display typography."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W = H = 1200
OUT = "/home/ubuntu/muzik/album/album_cover_yediverenler.png"

# 7 palette colors (same as original)
COLORS = [
    (26, 42, 74),      # dark navy
    (212, 165, 74),    # gold
    (214, 46, 100),    # magenta-pink
    (22, 130, 134),    # teal
    (180, 45, 40),     # deep red
    (124, 150, 110),   # sage green
    (84, 56, 118),     # deep purple
]

img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# smooth vertical gradient per band
band_h = H / len(COLORS)
for i, (r, g, b) in enumerate(COLORS):
    y0, y1 = int(i * band_h), int((i + 1) * band_h)
    for y in range(y0, y1):
        t = (y - y0) / max(band_h - 1, 1)
        # blend into neighboring colors for smoothness
        if i < len(COLORS) - 1:
            r2, g2, b2 = COLORS[i + 1]
            rr = int(r + (r2 - r) * t)
            gg = int(g + (g2 - g) * t)
            bb = int(b + (b2 - b) * t)
        else:
            rr, gg, bb = r, g, b
        draw.line([(0, y), (W, y)], fill=(rr, gg, bb))

# thin white separator lines
for i in range(1, len(COLORS)):
    y = int(i * band_h)
    draw.line([(0, y), (W, y)], fill=(255, 255, 255), width=3)

# central circle (dark, subtle blend)
cx, cy, cr = W // 2, H // 2, 280
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
od.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(20, 18, 30, 215))
overlay = overlay.filter(ImageFilter.GaussianBlur(6))
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)
draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=(255, 255, 255), width=4)

FONT_PATH = "/home/ubuntu/.fonts/PlayfairDisplay.ttf"

def txt(size):
    return ImageFont.truetype(FONT_PATH, size)

d2 = ImageDraw.Draw(img)
# main title
d2.text((cx, cy - 80), "THE", font=txt(96), fill="white", anchor="mm")
d2.text((cx, cy + 20), "GENEROUS", font=txt(96), fill="white", anchor="mm")
d2.text((cx, cy + 130), "— Yediverenler —", font=txt(40), fill="white", anchor="mm")

# track numbers on right side
for i in range(1, 8):
    y = int((i - 0.5) * band_h)
    d2.text((W - 70, y), str(i), font=txt(34), fill=(255, 255, 255), anchor="mm")

img.save(OUT)
print("saved", OUT)
