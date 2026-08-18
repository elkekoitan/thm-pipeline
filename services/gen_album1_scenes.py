#!/usr/bin/env python3
"""Generate 7 clean, atmospheric, text-free mood backgrounds for THE GENEROUS v2.

Design philosophy: one strong gradient base + one or two signature elements
(moon, sun, laser beams, city glow, lightning, tree, planet) + gentle vignette.
Kept simple and high-contrast so Ken Burns reads clearly at a glance.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = "/home/ubuntu/muzik/album1_scenes"
W, H = 1920, 1080
os.makedirs(OUT, exist_ok=True)


def vgrad(c1, c2):
    img = Image.new("RGB", (W, H))
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        ImageDraw.Draw(img).line([(0, y), (W, y)], fill=c)
    return img


def radgrad(cx, cy, r, c1, c2):
    """Radial gradient disc rendered as image."""
    img = Image.new("RGB", (W, H), c2)
    d = ImageDraw.Draw(img)
    n = 16
    for k in range(n, 0, -1):
        rr = int(r * k / n)
        t = k / n
        c = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)
    return img


def blur_layer(img, rad):
    return img.filter(ImageFilter.GaussianBlur(rad))


def blend(img, layer, alpha):
    return Image.blend(img, layer, alpha)


def vignette(img, strength=0.40):
    mask = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(mask)
    d.ellipse([-W * 0.3, -H * 0.3, W * 1.3, H * 1.3], fill=int(255 * (1 - strength)))
    mask = mask.filter(ImageFilter.GaussianBlur(W // 4))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img, black, mask)


def save(name, img):
    img.save(os.path.join(OUT, name))
    print("saved", name)


def mountains(img, color, y0, amp=90, freq=1.3, blur=0, alpha=1.0):
    d = ImageDraw.Draw(img)
    n = 48
    pts = [(0, H)]
    for j in range(n + 1):
        x = int(W * j / n)
        y = int(y0 + math.sin(j * freq) * amp + math.sin(j * freq * 2.3) * amp * 0.35)
        pts.append((x, y))
    pts.append((W, H))
    d.polygon(pts, fill=color)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1.0:
        img = blend(img, img, alpha)
    return img


# 1. Whisper Dark — night ocean, moon, mist
img = vgrad((26, 46, 100), (66, 98, 170))
moon = radgrad(int(W * 0.72), int(H * 0.12), 110, (250, 253, 255), (0, 0, 0))
img = blend(img, blur_layer(moon, 18), 0.95)
# moon halo
halo = radgrad(int(W * 0.72), int(H * 0.12), 420, (180, 205, 245), (0, 0, 0))
img = blend(img, blur_layer(halo, 130), 0.45)
# sea horizon with reflection (only darken the sea band gently)
sea = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(sea)
d.rectangle([0, int(H * 0.66), W, H], fill=(24, 40, 82))
r = random.Random(11)
for k in range(70):
    y = int(H * 0.68 + k * 4.6)
    xw = 180 + k * 6
    d.line([(int(W * 0.72) - xw, y), (int(W * 0.72) + xw, y)],
           fill=(170, 195, 240), width=2)
img = blend(img, blur_layer(sea, 4), 0.45)
img = vignette(img, 0.30)
save("scene_whisper_dark.png", img)

# 2. Daglarda Ses — amber mountain dusk
img = vgrad((255, 225, 165), (220, 130, 80))
sun = radgrad(int(W * 0.5), int(H * 0.28), 170, (255, 250, 235), (0, 0, 0))
img = blend(img, blur_layer(sun, 10), 0.95)
halo = radgrad(int(W * 0.5), int(H * 0.28), 560, (255, 210, 140), (0, 0, 0))
img = blend(img, blur_layer(halo, 160), 0.40)
img = mountains(img, (150, 85, 60), H * 0.60, amp=110, freq=1.1, blur=0)
img = mountains(img, (105, 55, 42), H * 0.70, amp=80, freq=1.6)
img = mountains(img, (60, 30, 32), H * 0.80, amp=60, freq=2.1)
img = vignette(img, 0.30)
save("scene_daglarda_ses.png", img)

# 3. Dancefloor Fever — dark club with lasers and crowd lights
img = vgrad((120, 0, 180), (55, 0, 90))
d = ImageDraw.Draw(img)
rr = random.Random(31)
for k in range(10):
    x = rr.randint(int(W * 0.2), int(W * 0.8))
    c = (255, 40, 170) if k % 2 else (0, 235, 255)
    x2 = int(W / 2 + (x - W / 2) * 3)
    poly = [(x - 14, 0), (x + 14, 0), (x2 + 20, H), (x2 - 20, H)]
    d.polygon(poly, fill=c)
img = blur_layer(img, 6)
# floor grid
flr = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(flr)
for k in range(9):
    yy = int(H * 0.72 + k * (H * 0.28 / 9))
    d.line([(0, yy), (W, yy)], fill=(255, 60, 200), width=3)
for k in range(-12, 13):
    x0 = int(W / 2 + k * 100)
    d.line([(x0, int(H * 0.72)), (int(W / 2 + (x0 - W / 2) * 3.6), H)], fill=(0, 220, 255), width=3)
img = blend(img, flr, 0.55)
# crowd glow orbs
orbs = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(orbs)
for k in range(14):
    x = rr.randint(80, W - 80)
    y = rr.randint(int(H * 0.58), int(H * 0.92))
    r = rr.randint(45, 110)
    c = (255, 40, 170) if k % 3 else (0, 235, 255)
    d.ellipse([x - r, y - r, x + r, y + r], fill=c)
img = blend(img, blur_layer(orbs, 70), 0.5)
img = vignette(img, 0.40)
save("scene_dancefloor_fever.png", img)

# 4. Neon Istanbul — synthwave sunset + grid water + bridge
img = vgrad((90, 20, 140), (235, 110, 160))
d = ImageDraw.Draw(img)
sx, sy, sr = int(W * 0.5), int(H * 0.48), 300
d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 150, 90))
for k in range(8):
    yy = int(sy + 25 + k * 36)
    d.rectangle([sx - sr, yy, sx + sr, yy + 11], fill=(185, 40, 140))
# glow rings around sun
halo = radgrad(sx, sy, 560, (255, 130, 180), (0, 0, 0))
img = blend(img, blur_layer(halo, 150), 0.45)
# water reflections
wtr = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(wtr)
r = random.Random(41)
for k in range(140):
    x = r.randint(0, W)
    y = r.randint(int(H * 0.76), H)
    ww = r.randint(120, 520)
    c = (255, 130, 195) if k % 3 else (130, 215, 255)
    d.rectangle([x, y, x + ww, y + 4], fill=c)
img = blend(img, blur_layer(wtr, 6), 0.65)
# bridge silhouette
img = mountains(img, (8, 2, 34), H * 0.80, amp=34, freq=0.5)
img = vignette(img, 0.30)
save("scene_neon_istanbul.png", img)

# 5. Vahsi Orman — storm sky, lightning, treeline
img = vgrad((14, 16, 34), (76, 68, 120))
r = random.Random(51)
# clouds
cld = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(cld)
for k in range(12):
    x = r.randint(-300, W + 300)
    y = r.randint(0, int(H * 0.40))
    rad = r.randint(220, 440)
    d.ellipse([x - rad, y - rad // 2, x + rad, y + rad // 2], fill=(46, 44, 80))
img = blend(img, blur_layer(cld, 100), 0.6)
# lightning
d = ImageDraw.Draw(img)
for bx in [int(W * 0.34), int(W * 0.70)]:
    pts = [(bx, 0)]
    xx, yy = bx, 0
    while yy < int(H * 0.52):
        xx += r.randint(-80, 80)
        yy += r.randint(55, 130)
        pts.append((xx, min(yy, int(H * 0.52))))
    d.line(pts, fill=(215, 228, 255), width=16)
    d.line(pts, fill=(255, 255, 255), width=6)
# treeline
img = mountains(img, (3, 5, 12), H * 0.84, amp=90, freq=4.5)
img = vignette(img, 0.45)
save("scene_vahsi_orman.png", img)

# 6. Ruya Bahcesi — warm dream meadow, lone tree, fireflies
img = vgrad((255, 242, 215), (255, 200, 165))
sun = radgrad(int(W * 0.24), int(H * 0.26), 140, (255, 252, 240), (0, 0, 0))
img = blend(img, blur_layer(sun, 15), 0.95)
halo = radgrad(int(W * 0.24), int(H * 0.26), 480, (255, 230, 185), (0, 0, 0))
img = blend(img, blur_layer(halo, 130), 0.30)
# rolling hills
img = mountains(img, (190, 215, 160), H * 0.78, amp=50, freq=1.0)
img = mountains(img, (160, 190, 130), H * 0.85, amp=40, freq=1.4)
img = mountains(img, (130, 160, 105), H * 0.92, amp=30, freq=1.8)
# lone tree
d = ImageDraw.Draw(img)
tx = int(W * 0.74)
d.rectangle([tx - 11, int(H * 0.66), tx + 11, int(H * 0.94)], fill=(96, 66, 46))
d.ellipse([tx - 100, int(H * 0.54), tx + 100, int(H * 0.80)], fill=(140, 175, 110))
# fireflies
d = ImageDraw.Draw(img)
r = random.Random(61)
for k in range(70):
    x = r.randint(0, W)
    y = r.randint(int(H * 0.70), H - 20)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 248, 220))
img = vignette(img, 0.25)
save("scene_ruya_bahcesi.png", img)

# 7. Yildiz Savascisi — cosmic nebula, planet, stars
img = vgrad((10, 5, 36), (90, 35, 160))
neb = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(neb)
r = random.Random(71)
for k in range(7):
    x = r.randint(0, W)
    y = r.randint(0, H)
    rad = r.randint(240, 480)
    c = [(150, 75, 245), (80, 135, 255), (230, 80, 175)][k % 3]
    d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=c)
img = blend(img, blur_layer(neb, 160), 0.5)
# stars
d = ImageDraw.Draw(img)
for k in range(380):
    x = r.randint(0, W)
    y = r.randint(0, H)
    rad = r.choice([1, 1, 1, 2, 2, 3])
    d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(255, 252, 255))
# planet with ring (left third)
px, py, pr = int(W * 0.28), int(H * 0.44), 170
plt = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(plt)
d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(105, 65, 190))
d.ellipse([px - pr * 0.82, py - pr * 0.82, px + pr * 0.82, py + pr * 0.82], fill=(135, 95, 215))
d.ellipse([px - pr * 1.9, py - pr * 0.28, px + pr * 1.9, py + pr * 0.28], outline=(210, 185, 255), width=10)
img = blend(img, blur_layer(plt, 1), 0.95)
img = vignette(img, 0.35)
save("scene_yildiz_savascisi.png", img)

print("ALL 7 SCENES SAVED to", OUT)
