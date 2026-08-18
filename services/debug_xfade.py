#!/usr/bin/env python3
import subprocess, os, math, random
FPS = 24
FADE_FRAMES = int(1.0 * FPS)
clips = ["/tmp/thm2_rain_on_the_rooftop/clip0.mp4", "/tmp/thm2_rain_on_the_rooftop/clip1.mp4"]
audio = "/home/ubuntu/muzik/album2_v2/01_rain_on_the_rooftop.mp3"
mp4 = "/tmp/xfade_dbg.mp4"
per = 2118
per_d = per / FPS
# downscale inputs to reduce xfade memory
low = []
for i, c in enumerate(clips):
    lo = f"/tmp/xfade_lo{i}.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", c, "-vf", "scale=960:540", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", lo], check=True, capture_output=True)
    low.append(lo)
clips = low

norm_inputs = []
norm_fc = []
for i, c in enumerate(clips):
    norm_inputs += ["-i", c]
    norm_fc.append(f"[{i}:v]fps={FPS}[n{i}]")
xfade_parts = []
for i in range(1, len(clips)):
    off = i * (per_d - FADE_FRAMES / FPS)
    xfade_parts.append(f"[n{i-1}][n{i}]xfade=transition=fade:duration={FADE_FRAMES/FPS:.3f}:offset={off:.3f}")
full_fc = ";".join(norm_fc) + ";" + ";".join(xfade_parts) + f",fps={FPS},format=yuv420p[v]"
print("FC:", full_fc)

r = subprocess.run(["ffmpeg", "-y", *norm_inputs, "-i", audio, "-filter_complex", full_fc,
                    "-map", "[v]", "-map", f"{len(norm_inputs)}:a", "-t", "176.535458",
                    "-threads", "1", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", mp4],
                   capture_output=True, text=True)
print("rc =", r.returncode)
print("STDERR (last 25 lines):")
print("\n".join(r.stderr.strip().splitlines()[-25:]))
