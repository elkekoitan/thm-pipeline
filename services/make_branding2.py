#!/usr/bin/env python3
"""Premium TH Music channel branding v2.
Profile: monogram 'TH' inside a subtle ring, deep plum->sunset gradient, cinematic glow.
Banner: TH MUSIC centered in safe zone, layered sunset sky with horizon silhouette and light rays."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math, random, os, glob

OUT_DIR = "/home/ubuntu/muzik/channel"
os.makedirs(OUT_DIR, exist_ok=True)

SERIF_CANDIDATES = sorted(glob.glob("/usr/share/fonts/**/*.ttf", recursive=True))
SERIF = [p for p in SERIF_CANDIDATES if "serif" in p.lower() and "bold" in p.lower()]
SERIF_R = [p for p in SERIF_CANDIDATES if "serif" in p.lower() and "bold" not in p.lower()]

def find_font(cands, size):
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def hsl(h, s, l):
    """simple hsl->rgb for richer palette"""
    h = h % 360
    s /= 100.0; l /= 100.0
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h/60) % 2 - 1))
    m = l - c/2
    if h < 60: r,g,b = c,x,0
    elif h < 120: r,g,b = x,c,0
    elif h < 180: r,g,b = 0,c,x
    elif h < 240: r,g,b = 0,x,c
    elif h < 300: r,g,b = x,0,c
    else: r,g,b = c,0,x
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

# Rich sunset palette
P_TOP    = (18, 10, 32)      # near-black plum
P_MID1   = (55, 25, 70)      # deep violet
P_MID2   = (120, 55, 75)     # rose
P_BOT    = (215, 130, 55)    # golden orange
P_GOLD   = (255, 215, 160)   # ivory gold for text

def smooth_grad(w, h, stops):
    """stops: list of (frac, (r,g,b)); vertical gradient with smooth interpolation"""
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / h
        # find bracketing stops
        for i in range(len(stops)-1):
            t0, c0 = stops[i]
            t1, c1 = stops[i+1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0) if t1 != t0 else 0
                k = k*k*(3-2*k)  # smoothstep
                color = tuple(int(c0[j] + (c1[j]-c0[j])*k) for j in range(3))
                break
        for x in range(w):
            img.putpixel((x, y), color)
    return img

def draw_vignette(img, strength=0.55):
    ov = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(ov)
    w,h = img.size
    d.ellipse((-w*0.15, -h*0.15, w*1.15, h*1.15), fill=int(255*(1-strength)))
    ov = ov.filter(ImageFilter.GaussianBlur(w*0.25))
    black = Image.new("RGB", img.size, (0,0,0))
    black.paste((255,255,255), (0,0), ov)
    return Image.blend(img, black, strength)

def add_particles(img, count, bright=True):
    img = img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(42)
    for _ in range(count):
        x = random.uniform(0, img.width)
        y = random.uniform(0, img.height)
        r = random.uniform(0.8, 2.8)
        a = random.randint(90, 230)
        col = (255, 235, 190, a) if bright else (120, 130, 255, a//2)
        d.ellipse((x-r, y-r, x+r, y+r), fill=col)
    return img

def draw_soundwave(draw, cx, cy, wspan, amp, color, lw):
    draw.line([(cx-wspan, cy), (cx+wspan, cy)], fill=color, width=lw)
    n = int(wspan // 5)
    for i in range(-n, n+1):
        x = cx + i*5
        env = math.exp(- (i/(n*0.38))**2)
        h = amp * env * math.sin(i*0.85 + 1.2)
        draw.line([(x, cy-h), (x, cy+h)], fill=color, width=lw)

# ---------------- PROFILE 800x800 ----------------
S = 800
stops = [(0.0, P_TOP), (0.45, P_MID1), (0.75, P_MID2), (1.0, P_BOT)]
prof = smooth_grad(S, S, stops)

# soft central glow
glow = Image.new("L", (S, S), 0)
ImageDraw.Draw(glow).ellipse((S*0.1, S*0.12, S*0.9, S*0.88), fill=200)
glow = glow.filter(ImageFilter.GaussianBlur(130))
gl = Image.new("RGB", (S, S), (0, 0, 0))
gl.paste((255, 160, 70), (0, 0), glow)
prof = Image.blend(prof, gl, 0.4)

prof = add_particles(prof, 90)

d = ImageDraw.Draw(prof, "RGBA")
f_big = find_font(SERIF, 300)

# thin circle ring around monogram
cx, cy = S/2, S/2
r_ring = S*0.36
d.ellipse((cx-r_ring, cy-r_ring, cx+r_ring, cy+r_ring), outline=P_GOLD + (110,), width=3)
r_ring2 = r_ring + 10
d.ellipse((cx-r_ring2, cy-r_ring2, cx+r_ring2, cy+r_ring2), outline=P_GOLD + (45,), width=1)

text = "TH"
bb = d.textbbox((0, 0), text, font=f_big)
tw, th = bb[2]-bb[0], bb[3]-bb[1]
# slight glow layer for text
tx, ty = cx - tw/2 - bb[0], cy*1.06 - th/2 - bb[1]
glow_t = Image.new("L", (S, S), 0)
ImageDraw.Draw(glow_t).text((tx, ty), text, font=f_big, fill=255)
glow_t = glow_t.filter(ImageFilter.GaussianBlur(18))
gtext = Image.new("RGB", (S, S), (0, 0, 0))
gtext.paste((255, 190, 110), (0, 0), glow_t)
prof = Image.blend(prof, gtext, 0.75)
d.text((tx, ty), text, font=f_big, fill=P_GOLD)

# MUSIC label below monogram
f_lbl = find_font(SERIF_R, 46)
lab = "M U S I C"
bb2 = d.textbbox((0, 0), lab, font=f_lbl)
tw2 = bb2[2]-bb2[0]
d.text((cx - tw2/2 - bb2[0], cy + r_ring*0.62), lab, font=f_lbl, fill=(255, 225, 185, 235))

prof = draw_vignette(prof, 0.45)
prof.save(f"{OUT_DIR}/profile_pic.png")

# ---------------- BANNER 2560x1440 ----------------
BW, BH = 2560, 1440
bstops = [(0.0, (8, 5, 18)), (0.35, P_MID1), (0.62, P_MID2), (0.82, (195, 105, 60)), (1.0, (235, 160, 75))]
ban = smooth_grad(BW, BH, bstops)

# sun glow near horizon (centered)
glow2 = Image.new("L", (BW, BH), 0)
d2 = ImageDraw.Draw(glow2)
d2.ellipse((BW*0.30, BH*0.55, BW*0.70, BH*0.95), fill=235)
glow2 = glow2.filter(ImageFilter.GaussianBlur(220))
g2 = Image.new("RGB", (BW, BH), (0, 0, 0))
g2.paste((255, 175, 80), (0, 0), glow2)
ban = Image.blend(ban, g2, 0.5)

ban = add_particles(ban, 300)

d2 = ImageDraw.Draw(ban, "RGBA")

# distant shoreline silhouette
import random
d2 = ImageDraw.Draw(ban, "RGB")
land_top = BH * 0.885
d2.rectangle((0, int(land_top), BW, BH), fill=(12, 8, 18))
random.seed(3)
# jagged silhouette edge
pts = []
x = 0
y = land_top
while x <= BW:
    y += random.uniform(-3, 3)
    y = max(BH*0.85, min(BH*0.90, y))
    pts.append((x, y)); x += random.randint(40, 120)
d2.polygon(pts + [(BW, BH), (0, BH)], fill=(12, 8, 18))

# small tree/antenna silhouettes
for x0 in [250, 900, 1650, 2300]:
    h0 = random.randint(30, 70)
    ytop = land_top - h0
    d2.line([(x0, ytop + h0), (x0, ytop)], fill=(12, 8, 18), width=4)
    for i in range(2, 5):
        w0 = (5-i)*3
        d2.line([(x0-w0, ytop + i*8), (x0+w0, ytop + i*8)], fill=(12, 8, 18), width=2)

# TEXT: TH MUSIC in middle safe band
d2a = ImageDraw.Draw(ban, "RGBA")
f_banner = find_font(SERIF, 168)
text = "TH MUSIC"
bb = d2a.textbbox((0, 0), text, font=f_banner)
tw, th = bb[2]-bb[0], bb[3]-bb[1]
tx, ty = (BW-tw)/2 - bb[0], BH*0.5 - th/2 - bb[1]

glow_t = Image.new("L", (BW, BH), 0)
ImageDraw.Draw(glow_t).text((tx, ty), text, font=f_banner, fill=255)
glow_t = glow_t.filter(ImageFilter.GaussianBlur(26))
gtext = Image.new("RGB", (BW, BH), (0, 0, 0))
gtext.paste((255, 200, 120), (0, 0), glow_t)
ban = Image.blend(ban, gtext, 0.85)
d2a.text((tx, ty), text, font=f_banner, fill=P_GOLD)

# underline soundwave
cy = BH*0.5 + 130
draw_soundwave(d2a, BW/2, cy, 420, 15, (255, 215, 160, 220), 3)

# tagline
f_tag = find_font(SERIF_R, 44)
tag = "original songs · story videos"
bb3 = d2a.textbbox((0, 0), tag, font=f_tag)
tw3 = bb3[2]-bb3[0]
d2a.text((BW/2 - tw3/2 - bb3[0], cy + 45), tag, font=f_tag, fill=(255, 230, 200, 200))

ban = draw_vignette(ban, 0.3)
ban.save(f"{OUT_DIR}/banner.png")
print("v2 done")
