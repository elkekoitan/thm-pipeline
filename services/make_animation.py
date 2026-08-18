"""
Generates a rhythm-synced background animation (1920x1080, 30fps) for the song,
built around the album cover. Beat pulses scale rings, energy modulates glow,
and sections change color mood to match the song's dynamics.
"""
import json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import subprocess, os

COVER = '/home/ubuntu/muzik/album_cover.png'
W, H = 1920, 1080
FPS = 30
FRAMES_DIR = '/home/ubuntu/muzik/frames'
os.makedirs(FRAMES_DIR, exist_ok=True)

data = json.load(open('/home/ubuntu/muzik/rhythm.json'))
duration = data['duration']
beats = np.array(data['pulses'])
tempo = data['tempo']
per_sec = {p['t']: p for p in data['per_second']}

# Per-frame energy lookup (interpolate per-second norm)
def energy(t):
    t = min(t, duration - 1e-6)
    i = int(t)
    f = t - i
    a = per_sec.get(i, {'norm': 0.3})['norm']
    b = per_sec.get(i + 1, {'norm': a})['norm']
    return a + (b - a) * f

# Beat index for each time
def beat_index(t):
    return int(np.searchsorted(beats, t, side='right')) - 1

# Cover preparation: 1920x1080 background from cover (center crop) + blurred edges
cover = Image.open(COVER).convert('RGB').resize((W, H), Image.LANCZOS)
# Letterbox effect: blurred cover background, crisp cover centered
bg = cover.filter(ImageFilter.GaussianBlur(40))
cover_cropped = Image.open(COVER).convert('RGB')
w_c, h_c = cover_cropped.size
cover_small = cover_cropped.resize((int(H * w_c / h_c), H), Image.LANCZOS)

def render_frame(t, frame_no):
    e = energy(t)                      # 0..1 energy
    bi = beat_index(t)
    if bi < 0: bi = 0
    bt = beats[bi]
    phase = (t - bt) / (60.0 / tempo)  # 0..1 within beat

    # Rhythm pulse: sharp attack, decay
    pulse = max(0, 1 - phase) ** 2.5

    # Section-based mood (energy-driven)
    if t < 20: base_hue = (220, 200, 150)   # intro warm
    elif t < 55: base_hue = (200, 180, 130) # verse
    elif t < 85: base_hue = (255, 180, 90)  # chorus bright
    elif t < 110: base_hue = (200, 180, 130)
    elif t < 145: base_hue = (255, 190, 100)
    elif t < 165: base_hue = (150, 130, 180)  # bridge cool
    else: base_hue = (220, 200, 160)          # outro

    frame = bg.copy()
    # Energy-based color wash
    tint = Image.new('RGB', (W, H), tuple(int(c * (0.55 + 0.9 * e)) for c in base_hue))
    frame = Image.blend(frame, tint, 0.35 + 0.25 * e)

    # Floating particles synced to beats
    rng = np.random.default_rng(frame_no // 3 + 7)
    particles = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(particles)
    n_p = int(40 + 60 * e)
    for _ in range(n_p):
        x = rng.random() * W
        y = (rng.random() * H + t * 15 * (0.4 + 0.6 * e)) % H
        r = 1 + rng.random() * 2.5
        a = int(80 + 150 * rng.random())
        pd.ellipse([x, y, x + r * 2, y + r * 2], fill=(255, 220, 160, a))
    frame = Image.alpha_composite(frame.convert('RGBA'), particles).convert('RGB')

    # Beat-synced concentric rings centered on cover
    ring_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_layer)
    cx, cy = W // 2, H // 2
    n_rings = 5
    for i in range(n_rings):
        off = (i + phase) % n_rings
        radius = 300 + off * 170 * (0.7 + 0.6 * pulse)
        alpha = int((1 - off / n_rings) * (90 + 160 * pulse) * (0.5 + e))
        width = 2 + int(4 * (0.5 + pulse))
        if radius < max(W, H):
            rd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                       outline=(255, 225, 170, alpha), width=width)
    frame = Image.alpha_composite(frame.convert('RGBA'), ring_layer).convert('RGB')

    # Cover with pulse zoom
    zoom = 1 + 0.025 * pulse + 0.015 * np.sin(t * 0.5)
    cs = cover_small.resize((int(cover_small.width * zoom), int(cover_small.height * zoom)), Image.LANCZOS)
    ox = (W - cs.width) // 2
    oy = (H - cs.height) // 2
    frame.paste(cs, (ox, oy))

    # Vignette
    vig = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W*0.25, -H*0.25, W*1.25, H*1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    black = Image.new('RGB', (W, H), (0, 0, 0))
    frame = Image.composite(frame, black, vig)

    frame.save(f'{FRAMES_DIR}/f_{frame_no:06d}.jpg', quality=82)

total_frames = int(duration * FPS)
start = len(os.listdir(FRAMES_DIR))
print(f"Resuming from frame {start}, rendering {total_frames - start} more...")
for n in range(start, total_frames):
    render_frame(n / FPS, n)
    if n % 300 == 0:
        print(f"  {n}/{total_frames}")
print("Frames done")
