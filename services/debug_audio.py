#!/usr/bin/env python3
"""Replicate make_mix.py audio step for mix_golden_hour exactly."""
import subprocess

tmp = "/tmp/mix_mix_golden_hour"
clips = [f"{tmp}/c{i}.mp4" for i in range(3)]
audio_inputs_files = [
    "/home/ubuntu/muzik/album1_v2/06_ruya_bahcesi.mp3",
    "/home/ubuntu/muzik/album2_v2/05_last_train_to_anywhere.mp3",
    "/home/ubuntu/muzik/album2_v2/02_midnight_ferryman.mp3",
]
a0 = len(clips)  # 3
afilter = ""
for i in range(1, 3):
    if i == 1:
        afilter = f"[{a0}:a][{a0+1}:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
    else:
        afilter += f";[o{i-1}][{a0+i}:a]acrossfade=d=2:c1=tri:c2=tri[o{i}]"
afilter += f";[o{2}]aformat=sample_rates=48000[a]"
print("AF:", afilter[:80], "...")
cmd = ["ffmpeg", "-y",
       "-i", clips[0], "-i", clips[1], "-i", clips[2],
       "-i", audio_inputs_files[0], "-i", audio_inputs_files[1], "-i", audio_inputs_files[2],
       "-filter_complex", afilter, "-map", "[a]",
       "-threads", "1", "-c:a", "aac", "-b:a", "192k", f"{tmp}/mix_a.m4a"]
r = subprocess.run(cmd, capture_output=True)
print("rc =", r.returncode)
print(r.stderr.decode()[-1200:])
