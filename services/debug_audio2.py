#!/usr/bin/env python3
"""Same subprocess.run pattern as make_mix.py, run from /home/ubuntu/muzik."""
import subprocess

tmp = "/tmp/mix_mix_golden_hour"
clips = [f"{tmp}/c{i}.mp4" for i in range(3)]
audio_files = [
    "/home/ubuntu/muzik/album1_v2/06_ruya_bahcesi.mp3",
    "/home/ubuntu/muzik/album2_v2/05_last_train_to_anywhere.mp3",
    "/home/ubuntu/muzik/album2_v2/02_midnight_ferryman.mp3",
]
a0 = 3
afilter = (f"[{a0}:a][{a0+1}:a]acrossfade=d=2:c1=tri:c2=tri[o1];"
           f"[o1][{a0+2}:a]acrossfade=d=2:c1=tri:c2=tri[o2];"
           f"[o2]aformat=sample_rates=48000[a]")
cmd = ["ffmpeg", "-y",
       "-i", clips[0], "-i", clips[1], "-i", clips[2],
       "-i", audio_files[0], "-i", audio_files[1], "-i", audio_files[2],
       "-filter_complex", afilter, "-map", "[a]",
       "-threads", "1", "-c:a", "aac", "-b:a", "192k", f"{tmp}/mix_a.m4a"]
r = subprocess.run(cmd, capture_output=True)
print("rc =", r.returncode)
if r.returncode != 0:
    print(r.stderr.decode()[-1000:])
else:
    print("OK, written", r.stderr.decode()[-60:])
