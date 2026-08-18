#!/usr/bin/env python3
"""TH Music channel branding v3 — Playfair Display serif, crisp text, cinematic palette."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random, os

OUT_DIR = "/home/ubuntu/muzik/channel"
os.makedirs(OUT_DIR, exist_ok=True)
FONT_PATH = "/tmp/playfair.ttf"

def font(size, wght=700):
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f

def hsl(h, s, l):
    h = h % 360
    s /= 100.0; l /= 100.0
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h/60) % 2 - 1))
    m = l - c/2
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

def smooth_grad(w, h, stops):
    img = Image.new("RGB", (w, h))
    pix = img.load()
    for y in range(h):
        t = y / h
        for i in range(len(stops)-1):
            t0, c0 = stops[i]; t1, c1 = stops[i+1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0) if t1 != t0 else 0
                k = k*k*(3-2*k)
                col = tuple(int(c0[j] + (c1[j]-c0[j])*k) for j in range(3))
                break
        for x in range(w):
            pix[x, y] = col
    return img

def add_particles(img, count, seed=42):
    img = img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(seed)
    for _ in range(count):
        x = random.uniform(0, img.width)
        y = random.uniform(0, img.height)
        r = random.uniform(0.8, 2.6)
        a = random.randint(100, 240)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 238, 195, a))
    return img

def glow_text(canvas, xy, text, fnt, color, glow_rgb, glow_alpha=0.8, blur=14):
    """draw soft glow + crisp text onto RGBA canvas"""
    d = ImageDraw.Draw(canvas, "RGBA")
    glow_l = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(glow_l).text(xy, text, font=fnt, fill=255)
    glow_l = glow_l.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(glow_rgb + (255,), (0, 0), glow_l)
    canvas.alpha_composite(layer)
    d.text(xy, text, font=fnt, fill=color + (255,))

def draw_soundwave(canvas, cx, cy, wspan, amp, color, lw=3, rgba=True):
    d = ImageDraw.Draw(canvas, "RGBA" if rgba else "RGB")
    d.line([(cx-wspan, cy), (cx+wspan, cy)], fill=color, width=lw)
    n = int(wspan // 5)
    for i in range(-n, n+1):
        x = cx + i*5
        env = math.exp(- (i/(n*0.38))**2)
        h = amp * env * math.sin(i*0.85 + 1.2)
        d.line([(x, cy-h), (x, cy+h)], fill=color, width=lw)

# palette
P_TOP = (15, 8, 28)
P_VIO = (62, 28, 74)
P_ROSE = (135, 65, 85)
P_SUN = (225, 140, 60)
P_GOLD = (255, 228, 185)

# ---------------- PROFILE 800x800 ----------------
S = 800
stops = [(0.0, P_TOP), (0.5, P_VIO), (0.8, P_ROSE), (1.0, P_SUN)]
prof = smooth_grad(S, S, stops)
prof = add_particles(prof, 110, seed=7)

canvas = prof.convert("RGBA")

# thin ring
cx, cy = S/2, S/2
r_ring = S*0.34
d = ImageDraw.Draw(canvas, "RGBA")
d.ellipse((cx-r_ring, cy-r_ring, cx+r_ring, cy+r_ring), outline=(255, 215, 160, 130), width=3)
d.ellipse((cx-r_ring-11, cy-r_ring-11, cx+r_ring+11, cy+r_ring+11), outline=(255, 215, 160, 55), width=1)

f_mon = font(310, 800)
text = "TH"
bb = d.textbbox((0, 0), text, font=f_mon)
tw, th = bb[2]-bb[0], bb[3]-bb[1]
tx, ty = cx - tw/2 - bb[0], cy - th/2 - bb[1]
glow_text(canvas, (tx, ty), text, f_mon, P_GOLD, (255, 170, 80), glow_alpha=0.85, blur=12)

f_lbl = font(52, 500)
lab = "M U S I C"
bb2 = d.textbbox((0, 0), lab, font=f_lbl)
tw2 = bb2[2]-bb2[0]
d.text((cx - tw2/2 - bb2[0], cy + r_ring + 28 - bb2[1]), lab, font=f_lbl, fill=(255, 232, 200, 240))

prof = canvas.convert("RGB")
prof.save(f"{OUT_DIR}/profile_pic.png")
print("profile v3 done")

# ---------------- BANNER 2560x1440 ----------------
BW, BH = 2560, 1440
bstops = [(0.0, (6, 4, 14)), (0.3, P_VIO), (0.58, P_ROSE), (0.8, P_SUN), (1.0, (245, 175, 90))]
ban = smooth_grad(BW, BH, bstops)

# sun glow centered at horizon-ish lower middle
glow2 = Image.new("L", (BW, BH), 0)
d2 = ImageDraw.Draw(glow2)
d2.ellipse((BW*0.28, BH*0.5, BW*0.72, BH*1.0), fill=240)
glow2 = glow2.filter(ImageFilter.GaussianBlur(240))
g2 = Image.new("RGB", (BW, BH), (0, 0, 0))
g2.paste((255, 185, 90), (0, 0), glow2)
ban = Image.blend(ban, g2, 0.45)

ban = add_particles(ban, 350, seed=11)

d2 = ImageDraw.Draw(ban, "RGBA")

# shoreline silhouette
land_top = BH * 0.885
pts = []
x = 0
y = land_top
random.seed(5)
while x <= BW:
    y += random.uniform(-3, 3)
    y = max(BH*0.845, min(BH*0.9, y))
    pts.append((x, y)); x += random.randint(40, 130)
d2.polygon(pts + [(BW, BH), (0, BH)], fill=(10, 6, 14))
for x0 in [220, 860, 1620, 2320]:
    h0 = random.randint(25, 65)
    d2.line([(x0, land_top), (x0, land_top-h0)], fill=(10, 6, 14), width=4)
    for i in range(2, 5):
        w0 = (5-i)*3
        d2.line([(x0-w0, land_top-h0+i*8), (x0+w0, land_top-h0+i*8)], fill=(10, 6, 14), width=2)

# text — draw into RGBA canvas so title is kept
ban_rgba = ban.convert("RGBA")
d3 = ImageDraw.Draw(ban_rgba, "RGBA")
f_banner = font(170, 800)
text = "TH MUSIC"
bb = d3.textbbox((0, 0), text, font=f_banner)
tw, th = bb[2]-bb[0], bb[3]-bb[1]
tx, ty = (BW-tw)/2 - bb[0], BH*0.46 - th/2 - bb[1]
glow_text(ban_rgba, (tx, ty), text, f_banner, P_GOLD, (255, 175, 85), glow_alpha=0.9, blur=18)

f_tag = font(48, 500)
tag = "original songs  ·  cinematic story videos"
bb3 = d3.textbbox((0, 0), tag, font=f_tag)
tw3 = bb3[2]-bb3[0]
d3.text((BW/2 - tw3/2 - bb3[0], BH*0.47 + 130 - bb3[1]), tag, font=f_tag, fill=(255, 235, 205, 215))

# soundwave under tagline
draw_soundwave(ban_rgba, BW/2, BH*0.47 + 245, 400, 14, (255, 220, 160, 230), 3)

ban = ban_rgba.convert("RGB")
ban.save(f"{OUT_DIR}/banner.png")
print("banner v3 done")
