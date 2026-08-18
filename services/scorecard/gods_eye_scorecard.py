#!/usr/bin/env python3
"""GOD'S EYE — automated quality scorecard for every produced audio asset.

Scores each track 0-100 across weighted dimensions derived from the
research knowledge base (BATCH 8 music-sleep evidence, mastering norms,
first-30s rule). Stores per-track JSON in THM data dir and maintains a
rolling trend log for the improvement loop.

Usage:
  python3 gods_eye_scorecard.py <audio.mp3> [--category slug]
  python3 gods_eye_scorecard.py --batch   (scores all category seeds + mixes)
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

DATA_DIR = "/home/ubuntu/muzik/gods_eye"
INST = "/home/ubuntu/muzik/instrumental"

# Category-specific reference recipes (from music-prompter section 8)
RECIPES = {
    "sleep_healing": {"bpm_lo": 50, "bpm_hi": 80, "max_tp_db": -2.0,
                      "max_high_pct": 12, "min_len_s": 120},
    "meditation": {"bpm_lo": 50, "bpm_hi": 80, "max_tp_db": -2.0,
                   "max_high_pct": 15, "min_len_s": 120},
    "lofi": {"bpm_lo": 70, "bpm_hi": 95, "max_tp_db": -1.0,
             "max_high_pct": 32, "min_len_s": 120},
    "cinematic": {"bpm_lo": 60, "bpm_hi": 130, "max_tp_db": -1.0,
                  "max_high_pct": 35, "min_len_s": 120},
    "jazz": {"bpm_lo": 70, "bpm_hi": 120, "max_tp_db": -1.0,
             "max_high_pct": 30, "min_len_s": 120},
    "classical_piano": {"bpm_lo": 50, "bpm_hi": 110, "max_tp_db": -1.5,
                        "max_high_pct": 28, "min_len_s": 120},
    "ambient_electronic": {"bpm_lo": 60, "bpm_hi": 110, "max_tp_db": -1.0,
                           "max_high_pct": 30, "min_len_s": 120},
    "deep_bass": {"bpm_lo": 110, "bpm_hi": 140, "max_tp_db": -1.0,
                  "max_high_pct": 35, "min_len_s": 120},
    "nature": {"bpm_lo": 50, "bpm_hi": 90, "max_tp_db": -2.0,
               "max_high_pct": 25, "min_len_s": 120},
    "epic_fantasy": {"bpm_lo": 80, "bpm_hi": 140, "max_tp_db": -1.0,
                     "max_high_pct": 35, "min_len_s": 120},
    "incense_ambient": {"bpm_lo": 50, "bpm_hi": 90, "max_tp_db": -2.0,
                        "max_high_pct": 22, "min_len_s": 120},
    "turkish_instrumental": {"bpm_lo": 60, "bpm_hi": 130, "max_tp_db": -1.0,
                             "max_high_pct": 30, "min_len_s": 120},
    "chinese_guzheng": {"bpm_lo": 50, "bpm_hi": 100, "max_tp_db": -1.5,
                        "max_high_pct": 28, "min_len_s": 120},
    "indian_sitar": {"bpm_lo": 60, "bpm_hi": 120, "max_tp_db": -1.0,
                     "max_high_pct": 30, "min_len_s": 120},
    "arabic_oud": {"bpm_lo": 60, "bpm_hi": 120, "max_tp_db": -1.0,
                   "max_high_pct": 30, "min_len_s": 120},
    "african_savanna": {"bpm_lo": 80, "bpm_hi": 130, "max_tp_db": -1.0,
                        "max_high_pct": 32, "min_len_s": 120},
    "celtic_harp": {"bpm_lo": 50, "bpm_hi": 100, "max_tp_db": -1.5,
                    "max_high_pct": 26, "min_len_s": 120},
    "viking_nordic": {"bpm_lo": 60, "bpm_hi": 120, "max_tp_db": -1.0,
                      "max_high_pct": 30, "min_len_s": 120},
    "acem_ottoman": {"bpm_lo": 60, "bpm_hi": 120, "max_tp_db": -1.0,
                     "max_high_pct": 30, "min_len_s": 120},
}
DEFAULT_RECIPE = {"bpm_lo": 60, "bpm_hi": 120, "max_tp_db": -1.0,
                  "max_high_pct": 30, "min_len_s": 120}

os.makedirs(DATA_DIR, exist_ok=True)


def ff(args):
    r = subprocess.run(["ffmpeg"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def raw_data(path, seconds):
    tmp = f"/tmp/ge_{abs(hash(path)) % 90000}.raw"
    rc, _ = ff(["-y", "-loglevel", "error", "-i", path,
                "-t", str(seconds), "-f", "f32le", "-ac", "1", tmp])
    if rc != 0:
        return None
    data = np.fromfile(tmp, dtype=np.float32)
    os.remove(tmp)
    return data


def volume_stats(path):
    rc, out = ff(["-i", path, "-af", "volumedetect", "-f", "null", "-"])
    stats = {}
    for line in (out + "\n").splitlines():
        if "mean_volume" in line:
            stats["mean_db"] = float(line.split(":")[-1].strip().replace(
                " dB", ""))
        if "max_volume" in line:
            stats["peak_db"] = float(line.split(":")[-1].strip().replace(
                " dB", ""))
    return stats


def spectral(path):
    data = raw_data(path, 90)
    if data is None or len(data) < 44100:
        return None
    sr = 44100
    n = len(data) // sr
    chunks = data[:n * sr].reshape(n, sr)
    spec = np.mean(np.abs(np.fft.rfft(chunks, axis=1)), axis=0)
    freqs = np.fft.rfftfreq(sr, 1.0 / sr)
    tot = spec.sum() or 1
    return {"low_pct": 100 * spec[freqs < 300].sum() / tot,
            "mid_pct": 100 * spec[(freqs >= 300) & (freqs < 3000)].sum() / tot,
            "high_pct": 100 * spec[freqs >= 3000].sum() / tot,
            "centroid_hz": float(np.sum(freqs * spec) / tot)}


def hook_energy(path):
    """First-30s rule: does the track establish character early?
    Score based on energy onset slope and variance (motif presence)."""
    data = raw_data(path, 30)
    if data is None or len(data) < 44100:
        return None
    sr = 44100
    n = len(data) // (sr // 10)
    env = np.abs(data[:n * (sr // 10)].reshape(n, sr // 10)).mean(axis=1)
    env = env / (env.max() or 1)
    onset = env[0]
    growth = env[25:].mean() - env[:5].mean()
    # variance captures motif movement (too flat = no character)
    motif_var = float(np.std(env))
    score = min(100, max(0, (1 - onset) * 40 + min(1.0, growth + 0.15) * 40
                         + min(0.35, motif_var) / 0.35 * 20))
    return round(score, 1)


def duration_s(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", path],
                           capture_output=True, text=True)
        val = "".join(c for c in r.stdout.strip()
                      if c in "0123456789.")
        return float(val) if val else None
    except (ValueError, FileNotFoundError):
        return None


def score_track(path, category=None):
    rec = RECIPES.get(category or "", DEFAULT_RECIPE)
    vol = volume_stats(path)
    spec = spectral(path)
    hook = hook_energy(path)
    dur = duration_s(path)
    if not vol or spec is None or hook is None:
        return None

    g = {}  # grades
    # 1. Mastering safety (30 pts): true peak within safe range
    tp = vol.get("peak_db", 0)
    g["mastering"] = (30 if tp <= rec["max_tp_db"]
                      else max(0, 30 - (tp - rec["max_tp_db"]) * 15))
    # 2. Genre spectral fit (25 pts): high-freq energy within range
    hp = spec["high_pct"]
    target = rec["max_high_pct"]
    g["spectral"] = (25 - min(25, max(0, abs(hp - target) - 3) * 3))
    # 3. First-30s hook (25 pts)
    g["hook"] = hook * 0.25
    # 4. Length adequacy (10 pts)
    g["length"] = 10 if dur and dur >= rec["min_len_s"] else 5
    # 5. Dynamic comfort (10 pts): mean level reasonable, not clipped avg
    mean = vol.get("mean_db", -20)
    g["dynamics"] = (10 if -24 <= mean <= -10 else 5)

    total = round(sum(g.values()), 1)
    verdict = ("PASS" if total >= 75 else "REVIEW" if total >= 55
               else "FAIL")
    rec = {"category": category, "path": path,
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "metrics": {**{k: round(float(v), 2) for k, v in vol.items()}, **{k: round(float(v), 2)
                                 for k, v in spec.items()}},
           "hook_score": round(float(hook), 1), "duration_s": dur,
           "grades": {k: round(float(v), 1) for k, v in g.items()},
           "total": total, "verdict": verdict}
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--category")
    ap.add_argument("--batch", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.batch:
        for slug in sorted(os.listdir(INST)):
            d = os.path.join(INST, slug)
            if not os.path.isdir(d) or slug == "samples_v2":
                continue
            for f in os.listdir(d):
                if f.endswith((".mp3", ".wav")) and not f.startswith(
                        ("cover", "fg_", "bg_")):
                    targets.append((slug, os.path.join(d, f)))
    else:
        for p in args.paths:
            targets.append((args.category or "", p))

    results, history = [], []
    hist_path = f"{DATA_DIR}/trend_log.json"
    if os.path.exists(hist_path):
        history = json.load(open(hist_path))
    for cat, p in targets:
        r = score_track(p, cat)
        if r is None:
            print(f"SKIP (unreadable): {p}")
            continue
        results.append(r)
        history.append(r)

    json.dump(results, open(f"{DATA_DIR}/latest_scorecard.json", "w"),
              indent=1, ensure_ascii=False, default=lambda x: float(x))
    json.dump(history[-2000:], open(hist_path, "w"), indent=1,
              ensure_ascii=False, default=lambda x: float(x))
    for r in results:
        print(f"{r['verdict']:6} {r['total']:5.1f}  {r['path']}")
    print("saved", f"{DATA_DIR}/latest_scorecard.json")


if __name__ == "__main__":
    sys.exit(main())
