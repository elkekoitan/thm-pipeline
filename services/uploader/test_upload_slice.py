#!/usr/bin/env python3
"""Diagnostic: upload a 10-minute slice of 01_cinematic_video.mp4.

If the slice sticks -> YouTube rejects long/large files for this channel.
If the slice drops too -> the resumable upload itself fails silently.
"""
import json, os, sys, subprocess, time

BASE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.dirname(BASE)
SLICE = "/tmp/cinematic_slice_10min.mp4"

sys.path.insert(0, BASE)
import upload_instrumental as up
import google.oauth2.credentials, googleapiclient.discovery

def make_slice():
    if not os.path.exists(SLICE):
        subprocess.run([
            "ffmpeg", "-y", "-i", f"{BASE}/01_cinematic/01_cinematic_video.mp4",
            "-t", "600", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "26", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", SLICE], check=True)
    print("slice:", os.path.getsize(SLICE) / 1e6, "MB")

def video_exists(yt, vid):
    r = yt.videos().list(part="id", id=vid).execute()
    return bool(r["items"])

def main():
    make_slice()
    yt = up.api_client()
    title = "[TEST] Cinematic Sunset 10-Min Preview — THM Instrumental"
    desc = "Test upload for diagnostics. Original 1-hour mix being rebuilt."
    body = {
        "snippet": {"title": title, "description": desc,
                    "tags": ["instrumental music", "test"],
                    "categoryId": "10"},
        "status": {"privacyStatus": "public",
                   "selfDeclaredMadeForKids": False},
    }
    media = googleapiclient.http.MediaFileUpload(SLICE, mimetype="video/mp4",
                                                 resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    vid = resp["id"]
    print(f"uploaded test id: {vid}", flush=True)
    for i in range(10):
        time.sleep(60)
        if video_exists(yt, vid):
            print(f"TEST VIDEO ALIVE after {i+1} min: {vid}", flush=True)
            return
        print(f"waiting {i+1}/10 ...", flush=True)
    print("TEST VIDEO DROPPED too", flush=True)

if __name__ == "__main__":
    main()
