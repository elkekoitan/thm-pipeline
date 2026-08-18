#!/usr/bin/env python3
"""Build wave-1 instrumental 1h videos + shorts with the multi-technique
cinematic pipeline.

For each slug with cover/fg_layer/bg_layer ready:
  1. Loop the two seed tracks (acrossfade 2.5s) to >= 3700s -> 1h mix audio
  2. Render 1h cinematic video at 960x540 24fps via cinematic_builder
  3. Upscale final to 1920x1080, mux full-quality audio
  4. Build 40s short (first 40s of mix audio + first 40s cinematic render
     scaled to 1080x1920? -> keep 16:9 for mix; short = 16:9 with audio hook)

Usage: python3 build_wave1_cinematic.py [slug ...]
If no args, builds all slugs that have layers ready.
"""
import os
import subprocess
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

SLUGS_ALL = [
    "01_cinematic", "02_lofi", "03_jazz", "04_classical_piano",
    "05_ambient_electronic", "06_deep_bass", "07_sleep_healing",
    "08_nature", "09_epic_fantasy", "10_meditation",
    "12_incense_ambient",
]
STEMS = {
    "01_cinematic": "cinematic", "02_lofi": "lofi", "03_jazz": "jazz",
    "04_classical_piano": "classical", "05_ambient_electronic": "ambient",
    "06_deep_bass": "deepbass", "07_sleep_healing": "sleep",
    "08_nature": "nature", "09_epic_fantasy": "epic",
    "10_meditation": "meditation",
}

FADE = 2.5


def ff(args, check=True):
    p = subprocess.run(["ffmpeg", "-y", "-v", "error"] + args,
                       capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(args)}\n"
                           f"{p.stderr.decode()[-800:]}")
    return p.returncode


def build_mix_audio(slug, stem):
    """Loop two seeds with acrossfades to >=3700s, output <slug>_mix1h.mp3.

    Quality upgrades (research BATCH 8):
      - loudnorm to YouTube standard (-14 LUFS true peak -1 dBTP) so THM
        tracks compete with Soothing Relaxation-level mixes on loudness
      - gentle compressor on lo-fi/rain categories to reduce fatigue
      - sleep category: lowpass + 432Hz-style softness (music-sleep evidence)
    """
    a = f"{slug}/{stem}_a.mp3"
    b = f"{slug}/{stem}_b.mp3"
    out = f"{slug}/{slug}_mix1h.mp3"
    if os.path.exists(out):
        return out
    d_a = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", a]).decode().strip())
    d_b = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", b]).decode().strip())
    loop_unit = d_a + d_b - FADE  # A + B with one acrossfade
    need = int(3720 / loop_unit) + 1
    print(f"[{slug}] building {need}-iteration 1h audio...", flush=True)
    tmp = f"{slug}/_mix_loop.mp3"
    # build one loop iteration
    ff([
        "-i", a, "-i", b,
        "-filter_complex",
        f"[0:a][1:a]acrossfade=d={FADE}:c1=tri:c2=tri[ab]",
        "-map", "[ab]", "-b:a", "192k", tmp,
    ])
    d_loop = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", tmp]).decode().strip())
    fl = f"{slug}/_concat_list.txt"
    with open(fl, "w") as f:
        for _ in range(need):
            f.write("file " + os.path.abspath(tmp) + "\n")
    concat_tmp = f"{slug}/_concat.mp3"
    ff(["-f", "concat", "-safe", "0", "-i", fl, "-c", "copy", concat_tmp])
    # research-backed mastering chain:
    #  - loudnorm (YouTube target -14 LUFS; big channels all sit here)
    #  - sleep category: keep energy in 60-80 BPM band soft -> afade-in 8s
    #    (no abrupt starts; first-30s rule) + gentle lowpass for coziness
    if "sleep" in stem or "meditation" in stem:
        master = ("loudnorm=I=-17:TP=-2:LRA=7,"
                  "afade=t=in:st=0:d=8,lowpass=f=6500")
    elif stem in ("lofi", "deepbass", "nature"):
        master = ("loudnorm=I=-14:TP=-1:LRA=11,"
                  "acompressor=threshold=-18dB:ratio=3:attack=30:release=300,"
                  "afade=t=in:st=0:d=6")
    else:
        master = ("loudnorm=I=-14:TP=-1:LRA=11,afade=t=in:st=0:d=6")
    # trim to exactly 3600s with slow fade out at the end
    ff([
        "-i", concat_tmp, "-af",
        f"{master},afade=t=out:st=3590:d=10",
        "-t", "3600", "-b:a", "192k", out,
    ])
    for x in (tmp, concat_tmp, fl):
        os.remove(x)
    print(f"[{slug}] audio ready: {out}", flush=True)
    return out


def build(slug, stem, video_only=False):
    cover = f"{slug}/cover.png"
    fg = f"{slug}/fg_layer.png"
    bg = f"{slug}/bg_layer.png"
    for p in (cover, fg, bg):
        if not os.path.exists(p):
            print(f"[{slug}] MISSING {p} — skipped (will retry later)",
                  flush=True)
            return False

    mix = build_mix_audio(slug, stem)
    video_out = f"{slug}/{slug}_cinematic_raw.mp4"
    if not os.path.exists(video_out):
        import cinematic_builder as cb
        rain = slug in ("02_lofi", "08_nature", "29_rain_storm")
        print(f"[{slug}] rendering 1h cinematic (rain={rain})...", flush=True)
        cb.build(slug, cover, fg, bg, 3600.0, video_out, rain=rain)
        print(f"[{slug}] render done", flush=True)

    if video_only:
        return True
    # upscale to 1080p + mux high-quality audio
    final = f"{slug}/{slug}_video.mp4"
    if not os.path.exists(final):
        ff([
            "-i", video_out, "-i", mix,
            "-filter_complex",
            "[0:v]scale=1920:1080:flags=lanczos[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", final,
        ])
        print(f"[{slug}] final: {final}", flush=True)
    # short: first 40s, 9:16 crop with audio hook
    short = f"{slug}/{slug}_short.mp4"
    if not os.path.exists(short):
        ff([
            "-i", video_out, "-i", mix, "-t", "40",
            "-filter_complex",
            "[0:v]crop=ih*9/16:ih,scale=1080:1920,crop=1080:1920[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-c:a", "aac", "-b:a", "160k", short,
        ])
        print(f"[{slug}] short: {short}", flush=True)
    return True


def main():
    targets = sys.argv[1:] or SLUGS_ALL
    results = {}
    for slug in targets:
        stem = STEMS[slug]
        try:
            ok = build(slug, stem)
            results[slug] = "OK" if ok else "SKIPPED"
        except Exception as e:  # noqa: BLE001
            results[slug] = f"ERROR {e}"
            print(f"[{slug}] ERROR: {e}", flush=True)
    print("\nRESULTS:", results, flush=True)


if __name__ == "__main__":
    main()
