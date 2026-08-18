#!/usr/bin/env python3
"""Replace THE GENEROUS album videos with new Higgsfield photoreal versions.

1. Deletes the 7 old album1_v2 video IDs (already uploaded earlier).
2. Uploads the new *_video.mp4 and *_short.mp4 from album1_v2/ (Higgsfield
   scenes, slow Ken Burns, no jitter) with year+genre retrofit titles.
3. Adds videos to THE GENEROUS playlist PLMtvWQDI5GHU.

Duplicate-safe via upload_log_album1_repl.json. Daily quota respected:
~1,600 units/video; script defers on uploadLimitExceeded and re-run finishes.
"""
import json
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN = "/home/ubuntu/muzik/token.json"
BASE = "/home/ubuntu/muzik/album1_v2"
LOG = "/home/ubuntu/muzik/upload_log_album1_repl.json"
PLAYLIST_ID = "PLMtvWQDI5GHU"
ALBUM = "THE GENEROUS"

# Old IDs (delete first, then never reference again)
OLD_IDS = [
    ("01_whisper_dark", "2E9z_HftZEc"),
    ("02_voice_in_mountains", "eDJhvJLtuOE"),
    ("03_dancefloor_fever", "gIz3HFirzqw"),
    ("04_neon_istanbul", "CYyVpMnXhuE"),
    ("05_wild_forest", "6R_agjD8UmM"),
    ("06_dream_garden", "vX7j95QPDrU"),
    ("07_star_warrior", "5L75uVb48Xk"),
]

# Genre mapping for retrofit titles
GENRE = {
    "01_whisper_dark": "Dark Pop",
    "02_voice_in_mountains": "Cinematic Anthem",
    "03_dancefloor_fever": "Dance Pop",
    "04_neon_istanbul": "Synthwave",
    "05_wild_forest": "Folk Fusion",
    "06_dream_garden": "Dream Pop",
    "07_star_warrior": "Epic Rock",
}

ITEMS = [
    {"slug": "01_whisper_dark", "title": "Whisper in the Dark"},
    {"slug": "02_voice_in_mountains", "title": "Voice in the Mountains"},
    {"slug": "03_dancefloor_fever", "title": "Dancefloor Fever"},
    {"slug": "04_neon_istanbul", "title": "Neon Istanbul"},
    {"slug": "05_wild_forest", "title": "Wild Forest"},
    {"slug": "06_dream_garden", "title": "Dream Garden"},
    {"slug": "07_star_warrior", "title": "Star Warrior"},
]


def creds():
    data = json.load(open(TOKEN))
    return Credentials(
        token=data["token"],
        refresh_token=data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=data["client_id"],
        client_secret=data["client_secret"],
    )


def main():
    c = creds()
    yt = build("youtube", "v3", credentials=c)
    log = {"uploads": [], "deleted": False}
    if os.path.exists(LOG):
        with open(LOG) as f:
            log = json.load(f)

    # 1. Delete old videos (once)
    if not log.get("deleted"):
        for slug, vid in OLD_IDS:
            try:
                yt.videos().delete(id=vid).execute()
                print(f"[deleted-old] {slug}: {vid}")
                time.sleep(3)
            except Exception as e:
                es = str(e)
                if "videoNotFound" in es:
                    print(f"[already-deleted] {slug}")
                else:
                    print(f"[delete-error] {slug}: {es}")
                    raise
        log["deleted"] = True
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)

    done = {u.get("slug") for u in log["uploads"] if u.get("slug")}
    LIMIT_REACHED = False
    for it in ITEMS:
        if LIMIT_REACHED:
            print(f"[deferred] {it['slug']} (daily upload limit reached)")
            continue
        if it["slug"] in done:
            print(f"[skip] {it['slug']}")
            continue
        slug, title = it["slug"], it["title"]
        video_path = os.path.join(BASE, f"{slug}_video.mp4")
        short_path = os.path.join(BASE, f"{slug}_short.mp4")
        if not os.path.exists(video_path):
            print(f"[MISSING] {video_path}")
            continue
        genre = GENRE.get(slug, "Pop")
        vtitle = f"{title} (Official Video) — {genre} 2026 | THM Official | {ALBUM}"
        stitle = f"{title} (Short) — {genre} 2026 | THM Official #Shorts"
        desc = (
            f"{title} — from the debut album {ALBUM} by TH Music (@THMusic-n1x).\n"
            f"Cinematic photoreal visuals, slow motion storytelling, no text — "
            f"the song's narrative carried purely by image and sound.\n\n"
            f"Genre: {genre} — Original composition and production.\n\n"
            f"Full album: https://www.youtube.com/playlist?list={PLAYLIST_ID}\n"
            f"ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n"
            f"ANTHROPOS EP (Latin): https://www.youtube.com/playlist?list=PLeEEgZuryyEE\n\n"
            f"Original composition and production: TH Music (@THMusic-n1x).\n\n"
            f"#THMusic #{genre.replace(' ', '')} #NewMusic2026"
        )
        tags = [slug.replace("_", " "), "thm official", "th music",
                genre.lower(), f"{genre.lower()} 2026", "the generous",
                "official video", "cinematic music video"]
        body = {"snippet": {"title": vtitle, "description": desc,
                            "tags": tags, "categoryId": "10"},
                "status": {"privacyStatus": "public"}}
        try:
            r = yt.videos().insert(part="snippet,status", body=body,
                                   media_body=MediaFileUpload(
                                       video_path, mimetype="video/mp4",
                                       resumable=True)).execute()
            vid = r["id"]
        except Exception as e:
            es = str(e)
            if "uploadLimitExceeded" in es:
                print(f"[LIMIT] daily upload limit reached; retry tomorrow for {slug}")
                LIMIT_REACHED = True
                continue
            raise
        short_id = None
        if os.path.exists(short_path):
            try:
                body["snippet"]["title"] = stitle
                body["snippet"]["tags"].append("shorts")
                r2 = yt.videos().insert(part="snippet,status", body=body,
                                        media_body=MediaFileUpload(
                                            short_path, mimetype="video/mp4",
                                            resumable=True)).execute()
                short_id = r2["id"]
            except Exception as e:
                es = str(e)
                if "uploadLimitExceeded" in es:
                    print(f"[LIMIT] short deferred for {slug}")
                else:
                    raise
            time.sleep(5)
        log["uploads"].append({"slug": slug, "video_id": vid,
                               "short_id": short_id, "title": vtitle})
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)
        print(f"[uploaded] {slug}: https://www.youtube.com/watch?v={vid}"
              + (f" | short: {short_id}" if short_id else ""))
        time.sleep(5)

    # playlist
    for u in log["uploads"]:
        if u.get("video_id"):
            try:
                yt.playlistItems().insert(part="snippet", body={
                    "snippet": {"playlistId": PLAYLIST_ID,
                                "resourceId": {"kind": "youtube#video",
                                               "videoId": u["video_id"]}}}).execute()
                print(f"[playlist] added {u['slug']}")
            except Exception as e:
                print(f"[playlist-fail] {u['slug']}: {e}")
            time.sleep(2)
    print("[DONE]")
    if LIMIT_REACHED:
        print("[NOTE] Some items deferred — re-run tomorrow to finish.")


if __name__ == "__main__":
    main()
