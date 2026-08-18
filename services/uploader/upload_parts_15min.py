#!/usr/bin/env python3
"""Upload 15-min part videos for categories whose 1h mains got dropped.
Each category = 4 parts (15 min each, within the unverified-channel
15-min limit). Quota-guarded: 6 ops/day (uploads only; playlists reused).
Log: /home/ubuntu/muzik/upload_log_parts.json (duplicate-safe)."""
import importlib.util
import json
import os
import subprocess
import sys

MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BASE = os.path.dirname(os.path.abspath(__file__))
PARTS_LOG = os.path.join(MUSIC_DIR, "upload_log_parts.json")
PART_SEC = 14 * 60
PARTS = 4

# Only categories with finished 1h videos
SLUGS = ["01_cinematic", "02_lofi", "07_sleep_healing", "05_ambient_electronic"]

TITLE_BASE = {
    "01_cinematic": "Cinematic Sunset Music — Relaxing Orchestral for Focus & Dreaming",
    "02_lofi": "Lofi Rain Music — Cozy Rainy Room Chill for Sleep & Study",
    "07_sleep_healing": "Deep Sleep Music — 432Hz Healing Ambient for Insomnia & Stress Relief",
    "05_ambient_electronic": "Ambient Electronic Music — Dreamy Space Textures for Deep Focus & Relaxation",
}
# Research BATCH 8: nostalgia year hook (The Japanese Town 27M case) —
# optional hook variant per category, tried as PART 1 of future uploads
NOSTALGIA_HOOK = {
    "02_lofi": "90's Lofi Rain Music — Cozy Rainy Room Chill for Sleep & Study",
}
TAGS = ["instrumental music", "THM Instrumental", "relaxing music",
        "background music", "focus music", "sleep music", "study music",
        "15 minute"]
DESC = ("All-original instrumental music produced by THM Instrumental. "
        "100% copyright-safe original compositions. This is Part {part} of "
        "4 — watch the full playlist for the complete 1-hour experience.\n\n"
        "Listen to more: https://www.youtube.com/@THMusic-n1x\n\n"
        "Chapters:\n"
        "00:00 Introduction\n02:00 Main theme\n07:00 Development\n12:00 Closing variation\n\n"
        "Sleep music | 睡眠導入 | 수면음악 | musique pour dormir | "
        "موسيقى للنوم | música para dormir | Schlafmusik\n\n"
        "No mid-roll ads — enjoy uninterrupted.\n\n"
        "#InstrumentalMusic #THMInstrumental #RelaxingMusic")


def slice_part(slug, part):
    src = f"{BASE}/{slug}/{slug}_video.mp4"
    outdir = f"{BASE}/{slug}/parts"
    os.makedirs(outdir, exist_ok=True)
    out = f"{outdir}/{slug}_part{part}.mp4"
    if os.path.exists(out):
        return out
    start = (part - 1) * PART_SEC
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-ss", str(start), "-i", src, "-t", str(PART_SEC),
           "-vf", "scale=1920:1080", "-c:v", "libx264", "-preset",
           "veryfast", "-crf", "24",
           "-af", f"afade=t=out:st={PART_SEC - 8}:d=8",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out


def load_parts_log():
    if os.path.exists(PARTS_LOG):
        return json.load(open(PARTS_LOG))
    return {}


def save_parts_log(log):
    json.dump(log, open(PARTS_LOG, "w"), indent=2)


import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors


def api_client():
    creds = google.oauth2.credentials.Credentials(
        **json.load(open(os.path.join(MUSIC_DIR, "token.json"))))
    return googleapiclient.discovery.build("youtube", "v3",
                                           credentials=creds)


def main():
    yt = api_client()
    log = load_parts_log()
    ops = 0
    MAX_OPS = 6
    for slug in SLUGS:
        for part in range(1, PARTS + 1):
            if ops >= MAX_OPS:
                print("[quota] daily limit reached, stopping", flush=True)
                sys.exit(0)
            key = f"{slug}_part{part}"
            if log.get(key):
                continue
            path = slice_part(slug, part)
            title = f"{TITLE_BASE[slug]} | Part {part} of 4 | THM Instrumental"
            if len(title) > 100:
                title = f"{TITLE_BASE[slug]} | Part {part}/4"
                if len(title) > 100:
                    title = title[:100]
            desc = DESC.format(part=part)
            tags = TAGS + [slug.replace("_", " "),
                           f"part {part} of 4"]
            body = {
                "snippet": {"title": title, "description": desc,
                            "tags": tags, "categoryId": "10"},
                "status": {"privacyStatus": "public",
                           "selfDeclaredMadeForKids": False},
            }
            # AI disclosure (2026 requirement — hidden AI content is
            # removed from recommendations; disclosure protects reach)
            body["madeWithAI"] = True
            import googleapiclient.http
            media = googleapiclient.http.MediaFileUpload(
                path, mimetype="video/mp4", resumable=True)
            try:
                resp = yt.videos().insert(part="snippet,status", body=body,
                                          media_body=media).execute()
            except googleapiclient.errors.HttpError as e:
                if "uploadLimitExceeded" in str(e):
                    print("[quota] uploadLimitExceeded, stopping", flush=True)
                    sys.exit(0)
                raise
            vid = resp["id"]
            log[key] = vid
            save_parts_log(log)
            # add to existing playlist (created by main uploads)
            pkey = f"{slug}_playlist"
            pl = log.get(pkey)
            if pl:
                try:
                    yt.playlistItems().insert(
                        part="snippet", body={"snippet": {
                            "playlistId": pl,
                            "resourceId": {"kind": "youtube#video",
                                           "videoId": vid}}}).execute()
                except Exception as e:
                    print(f"[{slug}] playlist add failed: {e}", flush=True)
            ops += 1
            print(f"[{slug}] part{part} uploaded: {vid} (ops={ops})",
                  flush=True)
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
