#!/usr/bin/env python3
"""Minimal test: xfade 3 clips + audio acrossfade at 1280x720, with -threads 1."""
import subprocess, sys

tmp = "/tmp/mix_mix_night_drive"
audio1 = "/home/ubuntu/muzik/album1_v2/04_neon_istanbul.mp3"
audio2 = "/home/ubuntu/muzik/album2_v2/03_rooftop_runners.mp3"
audio3 = "/home/ubuntu/muzik/album1_v2/03_dancefloor_fever.mp3"

vfc = ("[0:v]fps=24[n0];[1:v]fps=24[n1];[2:v]fps=24[n2];"
       "[n0][n1]xfade=transition=fade:duration=1.000:offset=170.604[m1];"
       "[m1][n2]xfade=transition=fade:duration=1.000:offset=346.187,fps=24,format=yuv420p[v]")
afc = ("[0:a][1:a]acrossfade=d=2:c1=tri:c2=tri[o1];"
       "[o1][2:a]acrossfade=d=2:c1=tri:c2=tri[o2];[o2]aformat=sample_rates=48000[a]")

cmd = ["ffmpeg", "-y",
       "-i", f"{tmp}/c0.mp4", "-i", f"{tmp}/c1.mp4", "-i", f"{tmp}/c2.mp4",
       "-i", audio1, "-i", audio2, "-i", audio3,
       "-filter_complex", vfc + ";" + afc,
       "-map", "[v]", "-map", "[a]",
       "-threads", "1",
       "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "/tmp/test_mix.mp4"]
r = subprocess.run(cmd, capture_output=True)
print("rc =", r.returncode)
if r.returncode != 0:
    print(r.stderr.decode()[-3000:])
