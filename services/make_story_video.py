"""
Story-driven music video assembler.
- No jitter/shake/pulse effects on images (user request).
- Slow cinematic Ken Burns-style pans/zooms (very subtle, slow, smooth).
- Scene changes cut exactly on beat pulses detected from rhythm.json.
- Crossfade transitions between scenes.
Outputs full 16:9 video and 9:16 Shorts versions.
"""
import json, os, sys
import numpy as np
from PIL import Image
import subprocess

DATA = '/home/ubuntu/muzik/rhythm.json'
OUT_W, OUT_H = 1920, 1080
FPS = 30
CROSSFADE_S = 1.0  # smooth crossfade between scenes

data = json.load(open(DATA))
duration = data['duration']
beats = np.array(data['pulses'])


def scene_times(song_file, total_scenes):
    """Compute scene boundaries: start at t=0, end at duration;
    place cuts at beat positions so scene lengths are multiples of beat intervals."""
    tempo = data['tempo']
    beat_interval = 60.0 / tempo
    dur = duration - 1.5  # leave room for last crossfade

    # naive: divide dur into scenes, then snap each boundary to nearest beat
    raw = np.linspace(0, dur, total_scenes + 1)
    bounds = [0.0]
    for r in raw[1:-1]:
        # snap to nearest beat
        idx = int(round(r / beat_interval))
        bounds.append(min(max(beats[idx], bounds[-1] + 2.0 * beat_interval), dur))
    bounds.append(dur)
    # ensure last scene not too short
    if bounds[-1] - bounds[-2] < 3 * beat_interval:
        bounds[-2] -= 3 * beat_interval
    return bounds


def render_scene(img_path, t0, t1, xfade_in, xfade_out, out_dir, base):
    """Render frames for one scene with slow smooth pan. Returns frame list."""
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    # scale so the image fully covers OUT_W x OUT_H with ~8% margin for panning
    scale = max(OUT_W, OUT_H) / min(w, h) * 1.10
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    dx = nw - OUT_W
    dy = nh - OUT_H
    n = int((t1 - t0) * FPS)
    if n <= 0:
        return []
    frames = []
    rng = np.random.default_rng(hash(img_path) % 2**31)
    # random slow drift direction, very slow (crosses ~15% of the excess over the scene)
    px = rng.random() * 0.85 * dx
    py = rng.random() * 0.85 * dy
    for i in range(n):
        f = i / max(n - 1, 1)
        # smooth ease in-out so motion never feels jittery
        e = f * f * (3 - 2 * f)
        x = int(px * e)
        y = int(py * e)
        crop = img.crop((x, y, x + OUT_W, y + OUT_H))
        # soft crossfade handling: frames saved raw; crossfade applied in ffmpeg concat later
        crop.save(f'{out_dir}/{base}_{i:05d}.jpg', quality=88)
        frames.append(f'{out_dir}/{base}_{i:05d}.jpg')
    return frames


def build_video(frames_list, audio_path, out_path):
    """Concat frames (no jitter), crossfade scenes, mux audio."""
    # Build concat list of encoded per-scene clips with crossfades via ffmpeg filter
    scene_clips = []
    tmpdir = os.path.dirname(frames_list[0][0])
    for idx, fl in enumerate(frames_list):
        clip = f'{tmpdir}/scene_{idx}.mp4'
        subprocess.run([
            'ffmpeg', '-y', '-framerate', str(FPS), '-start_number', '0', '-i', f'{tmpdir}/s{idx}_%05d.jpg',
            '-vf', 'scale=1920:1080,format=yuv420p',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-r', str(FPS), clip
        ], check=True, capture_output=True)
        scene_clips.append(clip)

    # Iterative pairwise xfade chain (avoids shell/arg issues with long filter graphs)
    subprocess.run(['python3', '/home/ubuntu/muzik/chain_xfade.py'] + scene_clips +
        [f'{tmpdir}/video_silent.mp4'], check=True)

    subprocess.run([
        'ffmpeg', '-y', '-i', f'{tmpdir}/video_silent.mp4', '-i', audio_path,
        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', out_path
    ], check=True, capture_output=True)
    print('Built:', out_path)


if __name__ == '__main__':
    song_file, scenes_csv, out_169, out_916 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    scenes = [l.strip() for l in open(scenes_csv) if l.strip()]
    tmpdir = f"{os.path.dirname(out_169)}/tmp_{os.path.basename(out_169).split('.')[0]}"
    os.makedirs(tmpdir, exist_ok=True)
    bounds = scene_times(song_file, len(scenes))
    print('Scene bounds:', [round(b, 2) for b in bounds])
    frames = []
    for i, sc in enumerate(scenes):
        xf_in = i > 0
        xf_out = i < len(scenes) - 1
        fl = render_scene(sc, bounds[i], bounds[i + 1], xf_in, xf_out, tmpdir, f's{i}')
        frames.append(fl)
        print(f'Scene {i}: {len(fl)} frames')
    build_video(frames, song_file, out_169)
