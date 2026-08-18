#!/usr/bin/env python3
"""Build a 30s 'coming soon' teaser from an existing source video.

Crops the best 30s, applies a very slow zoom (Ken Burns), darkens slightly and
adds a single ambient fade-in/out. No text overlays. Outputs video + short.

usage: python3 make_teaser.py <slug> <source.mp4> <start_sec>
"""
import os
import subprocess
import sys

OUT = "/home/ubuntu/muzik/calendar"
T = 30.0


def main():
    slug, src, start = sys.argv[1], sys.argv[2], float(sys.argv[3])
    mp4 = os.path.join(OUT, f"{slug}_video.mp4")
    short = os.path.join(OUT, f"{slug}_short.mp4")
    if os.path.exists(mp4):
        print(f"[skip] {slug}")
        return
    os.makedirs(OUT, exist_ok=True)
    # slow zoom + fade in/out, 1280x720
    vf = (f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
          f"zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24,"
          f"fade=t=in:st=0:d=1,fade=t=out:st=29:d=1,format=yuv420p")
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-ss", str(start), "-t", str(T), "-i", src,
        "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k", "-af", "afade=t=in:st=0:d=1,afade=t=out:st=29:d=1",
        "-shortest", mp4,
    ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-threads", "1", "-i", mp4,
        "-filter_complex",
        "[0:v]split=2[fg][bg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bgv];[fg][bgv]overlay=(W-w)/2:(H-h)/2[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k", short,
    ], check=True, capture_output=True)
    print(f"[done] {slug}")


if __name__ == "__main__":
    main()
