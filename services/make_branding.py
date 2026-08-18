#!/usr/bin/env python3
"""Create TH Music channel branding: profile pic (800x800) and banner (2560x1440).
Palette sampled from album_cover.png (sunset orange/plum)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

W_IMG = "/home/ubuntu/muzik/album_cover.png"
OUT_DIR = "/home/ubuntu/muzik/channel"

# sample palette from cover corners/edges
cover = Image.open(W_IMG).convert("RGB").resize((64, 64))
px = list(cover.getdata())
avg = tuple(sum(c[i] for c in px) // len(px) for i in range(3))

def gradient(w, h, top, bottom, vertical=True):
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / h if vertical else 0.0
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            img.putpixel((x, y), (r, g, b))
    return img

def find_font(candidates, size):
    for p in candidates:
        try:
            f = ImageFont.truetype(p, size)
            return f
        except Exception:
            continue
    return ImageFont.load_default()

SERIF = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
SERIF_B = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
]

# ---------- profile picture 800x800 ----------
SIZE = 800
top = (25, 12, 38)      # deep plum
bot = (170, 90, 40)     # burnt orange
img = gradient(SIZE, SIZE, top, bot)

# soft radial glow behind text
glow = Image.new("L", (SIZE, SIZE), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse((SIZE*0.15, SIZE*0.2, SIZE*0.85, SIZE*0.8), fill=220)
glow = glow.filter(ImageFilter.GaussianBlur(120))
orange = (230, 150, 60)
glayer = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
glayer.paste(orange, (0, 0), glow)
img = Image.blend(img, glayer, 0.35)

# particles
d = ImageDraw.Draw(img)
random.seed(7)
for _ in range(70):
    x = random.randint(0, SIZE); y = random.randint(0, SIZE)
    r = random.uniform(1, 3)
    a = random.randint(140, 255)
    d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 210, 140, a))

# TH letters
font = find_font(SERIF_B, 340)
text = "TH"
bb = d.textbbox((0, 0), text, font=font)
tw, th = bb[2]-bb[0], bb[3]-bb[1]
d.text(((SIZE-tw)/2 - bb[0], SIZE*0.36 - bb[1]), text, font=font, fill=(255, 225, 185))

# soundwave under letters
cy = SIZE*0.70
d.line([(SIZE*0.2, cy), (SIZE*0.8, cy)], fill=(255, 210, 140), width=3)
for i in range(-24, 25):
    x = SIZE*0.5 + i*9
    amp = 14 * math.exp(- (i/14)**2)
    h = amp * math.sin(i*0.9)
    d.line([(x, cy-h), (x, cy+h)], fill=(255, 210, 140), width=3)

img.save(f"{OUT_DIR}/profile_pic.png")

# ---------- banner 2560x1440 ----------
BW, BH = 2560, 1440
btop = (18, 10, 30)
bbot = (150, 80, 45)
banner = gradient(BW, BH, btop, bbot)
gd2 = ImageDraw.Draw(banner)

# horizon glow band (middle vertical band where text lives)
glow2 = Image.new("L", (BW, BH), 0)
gd3 = ImageDraw.Draw(glow2)
gd3.ellipse((BW*0.25, BH*0.25, BW*0.75, BH*0.75), fill=200)
glow2 = glow2.filter(ImageFilter.GaussianBlur(200))
orange2 = (200, 120, 50)
gl = Image.new("RGB", (BW, BH), (0, 0, 0))
gl.paste(orange2, (0, 0), glow2)
banner = Image.blend(banner, gl, 0.30)

# particles
for _ in range(220):
    x = random.randint(0, BW); y = random.randint(0, BH)
    r = random.uniform(1, 3.5)
    gd2.ellipse((x-r, y-r, x+r, y+r), fill=(255, 215, 150))

# TH MUSIC text in middle band
fontB = find_font(SERIF, 150)
text = "TH MUSIC"
bb = gd2.textbbox((0, 0), text, font=fontB)
tw = bb[2]-bb[0]
gd2.text(((BW-tw)/2 - bb[0], BH*0.5 - bb[1]), text, font=fontB, fill=(255, 230, 195))

# soundwave under text
cy = BH*0.5 + 120
gd2.line([(BW*0.35, cy), (BW*0.65, cy)], fill=(255, 210, 140), width=3)
for i in range(-30, 31):
    x = BW*0.5 + i*10
    amp = 16 * math.exp(- (i/16)**2)
    h = amp * math.sin(i*0.8)
    gd2.line([(x, cy-h), (x, cy+h)], fill=(255, 210, 140), width=3)

# subtle silhouette line at bottom (sea horizon)
gd2.line([(0, BH*0.86), (BW, BH*0.86)], fill=(35, 20, 40), width=4)
banner.save(f"{OUT_DIR}/banner.png")
print("done")
