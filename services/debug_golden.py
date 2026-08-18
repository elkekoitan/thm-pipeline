#!/usr/bin/env python3
import subprocess

tmp = "/tmp/mix_mix_golden_hour"
FPS = 24
clips = [f"{tmp}/c{i}.mp4" for i in range(3)]
norm_fc = ";".join(f"[{i}:v]fps={FPS}[n{i}]" for i in range(3))
per_d = [181.0, 178.7]
off = 0.0
parts = []
for i in range(1, 3):
    off += per_d[i - 1]
    parts.append(f"[n{i-1}][n{i}]xfade=transition=fade:duration=1.000:offset={off:.3f}")
vfc = norm_fc + ";" + ";".join(parts) + f",fps={FPS},scale=1280:720,format=yuv420p[v]"
print("FC:", vfc[:100], "...")
r = subprocess.run(["ffmpeg", "-y", "-threads", "1", "-i", clips[0], "-i", clips[1],
                    "-i", clips[2], "-filter_complex", vfc, "-map", "[v]",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-an",
                    "/tmp/golden_v.mp4"], capture_output=True)
print("rc =", r.returncode)
print(r.stderr.decode()[-1500:])
