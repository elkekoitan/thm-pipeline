#!/usr/bin/env python3
"""Upload instrumental videos to YouTube (6 ops/day quota guard).

Reads ready videos from /home/ubuntu/muzik/instrumental/{slug}/:
  - {slug}_video.mp4   (1h mix, main upload)
  - {slug}_short.mp4   (40s short)
Creates one playlist per slug on first upload of the main video.
Logs to /home/ubuntu/muzik/upload_log_instrumental.json (duplicate-safe).
Exits gracefully on uploadLimitExceeded.
"""
import json
import os
import sys
import time

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http

BASE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = "/home/ubuntu/muzik"
LOG = os.path.join(MUSIC_DIR, "upload_log_instrumental.json")
TOKEN = os.path.join(MUSIC_DIR, "token.json")
CLIENT_SECRETS = os.path.join(MUSIC_DIR, "client_secrets.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

ORDER = ["01_cinematic", "02_lofi", "03_jazz", "04_classical_piano",
         "05_ambient_electronic", "06_deep_bass", "07_sleep_healing",
         "08_nature", "09_epic_fantasy", "10_meditation",
         "11_chinese_guzheng", "14_indian_sitar", "16_arabic_oud",
         "17_acem_ottoman", "19_african_savanna", "22_celtic_harp",
         "23_viking_nordic", "27_turkish_instrumental", "12_incense_ambient"]

TITLES = {
    "01_cinematic": "Cinematic Sunset Music — Relaxing Orchestral for Focus & Dreaming | 1 Hour | THM Instrumental",
    "02_lofi": "Lofi Rain Music — Cozy Rainy Room Chill for Sleep & Study | 1 Hour | THM Instrumental",
    "03_jazz": "Smooth Jazz Cafe Music — Late Night Piano & Sax for Relaxation | 1 Hour | THM Instrumental",
    "04_classical_piano": "Classical Piano Music — Moonlit Castle Waltz for Sleep & Reflection | 1 Hour | THM Instrumental",
    "05_ambient_electronic": "Neon City Ambient — Electronic Chillwave for Night Drive & Focus | 1 Hour | THM Instrumental",
    "06_deep_bass": "Deep Bass Music — Deep Space Sub-Bass Meditation & Focus | 1 Hour | THM Instrumental",
    "07_sleep_healing": "Deep Sleep Music — 432Hz Healing Ambient for Insomnia & Stress Relief | 1 Hour | THM Instrumental",
    "08_nature": "Forest Rain & Nature Music — Calming Soundscape for Sleep & Anxiety Relief | 1 Hour | THM Instrumental",
    "09_epic_fantasy": "Epic Fantasy Music — Dragon Peak Orchestral Adventure | 1 Hour | THM Instrumental",
    "10_meditation": "Temple Meditation Music — Sacred Dawn Ambience for Mindfulness & Zen | 1 Hour | THM Instrumental",
    "11_chinese_guzheng": "Chinese Guzheng & Zen Music — Bamboo Forest Meditation for Sleep & Calm | 1 Hour | THM Instrumental",
    "14_indian_sitar": "Indian Sitar & Raga Music — Sacred River Meditation for Relaxation | 1 Hour | THM Instrumental",
    "16_arabic_oud": "Arabic Oud & Qanun Music — Desert Night Journey for Sleep & Focus | 1 Hour | THM Instrumental",
    "17_acem_ottoman": "Ottoman Palace Music — Acem Ensemble for Deep Relaxation | 1 Hour | THM Instrumental",
    "19_african_savanna": "African Savanna Music — Kora & Kalimba Sunset Groove for Peace | 1 Hour | THM Instrumental",
    "22_celtic_harp": "Celtic Harp Music — Emerald Hills & Misty Lakes for Sleep & Calm | 1 Hour | THM Instrumental",
    "23_viking_nordic": "Viking & Nordic Music — Epic Fog Seas for Focus & Adventure | 1 Hour | THM Instrumental",
    "27_turkish_instrumental": "Turkish Saz & Ney Music — Cappadocia Sunrise for Relaxation & Peace | 1 Hour | THM Instrumental",
    "12_incense_ambient": "Incense & Smoke Ambient Music — Temple Meditation Room for Deep Relaxation & Sleep | 1 Hour | THM Instrumental",
}

TAGS = ["instrumental music", "THM Instrumental", "1 hour", "relaxing music",
        "background music", "focus music", "sleep music", "study music"]


def api_client():
    creds = google.oauth2.credentials.Credentials(**json.load(open(TOKEN)))
    return googleapiclient.discovery.build("youtube", "v3",
                                           credentials=creds)


def load_log():
    if os.path.exists(LOG):
        return json.load(open(LOG))
    return {}


def save_log(log):
    json.dump(log, open(LOG, "w"), indent=2)


def ensure_playlist(yt, slug, video_id):
    log = load_log()
    key = f"{slug}_playlist"
    if log.get(key):
        return log[key]
    title = TITLES[slug].split(" — ")[0] + " | THM Instrumental"
    body = {
        "snippet": {"title": title,
                    "description": f"{' '.join(TITLES[slug].split('|')[:1])} "
                                   f"curated by THM Instrumental. "
                                   f"Updated weekly with new releases."},
        "status": {"privacyStatus": "public"},
    }
    req = yt.playlists().insert(part="snippet,status", body=body)
    pl = req.execute()
    pid = pl["id"]
    yt.playlistItems().insert(part="snippet", body={
        "snippet": {"playlistId": pid, "resourceId": {
            "kind": "youtube#video", "videoId": video_id}}}).execute()
    log[key] = pid
    save_log(log)
    print(f"[{slug}] playlist: {pid} ({title})", flush=True)
    return pid


def upload_video(yt, slug, kind, path, duration_seconds):
    longish = kind == "video"
    title = TITLES[slug]
    desc = (f"All-original instrumental music produced by THM Instrumental. "
            f"100% copyright-safe original compositions.\n\n"
            f"Listen to more: https://www.youtube.com/@THMusic-n1x\n\n"
            f"Chapters:\n"
            f"00:00 Introduction — 15:00 Theme Development\n"
            f"15:00 Main Theme — 30:00 Variations\n"
            f"30:00 Development — 45:00 Deep Variations\n"
            f"45:00 Closing Variations — 60:00 Outro\n\n"
            f"#InstrumentalMusic #THMInstrumental #RelaxingMusic")
    cats = ["Music"]
    tags = TAGS + [slug.replace("_", " ")]
    body = {
        "snippet": {
            "title": title if longish else (title.split(" | ")[0] + " | Short"),
            "description": desc,
            "tags": tags,
            "categoryId": cats[0] and "10",
        },
        "status": {"privacyStatus": "public",
                   "selfDeclaredMadeForKids": False},
    }
    body["madeWithAI"] = True  # 2026 AI disclosure — protects distribution
    media = googleapiclient.http.MediaFileUpload(path, mimetype="video/mp4",
                                                 resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    vid = resp["id"]
    return vid


def main():
    if len(sys.argv) > 1:
        slugs = sys.argv[1:]
    else:
        slugs = ORDER

    yt = api_client()
    log = load_log()
    ops = 0
    MAX_OPS = 6

    for slug in slugs:
        if ops >= MAX_OPS:
            print("[quota] daily limit reached, stopping", flush=True)
            break
        vid_key = f"{slug}_video"
        short_key = f"{slug}_short"
        v_path = os.path.join(BASE, slug, f"{slug}_video.mp4")
        s_path = os.path.join(BASE, slug, f"{slug}_short.mp4")

        if not log.get(vid_key) and os.path.exists(v_path):
            try:
                vid = upload_video(yt, slug, "video", v_path, 3600)
                log[vid_key] = vid
                save_log(log)
                ensure_playlist(yt, slug, vid)
                ops += 1
                print(f"[{slug}] main uploaded: {vid} (ops={ops})", flush=True)
            except googleapiclient.errors.HttpError as e:
                if "uploadLimitExceeded" in str(e):
                    print("[quota] uploadLimitExceeded, stopping", flush=True)
                    break
                raise

        if not log.get(short_key) and os.path.exists(s_path):
            try:
                vid = upload_video(yt, slug, "short", s_path, 40)
                log[short_key] = vid
                save_log(log)
                ops += 1
                print(f"[{slug}] short uploaded: {vid} (ops={ops})", flush=True)
            except googleapiclient.errors.HttpError as e:
                if "uploadLimitExceeded" in str(e):
                    print("[quota] uploadLimitExceeded, stopping", flush=True)
                    break
                raise
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
