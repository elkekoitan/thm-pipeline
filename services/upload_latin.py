#!/usr/bin/env python3
"""Upload Latin EP videos + shorts, create ANTHROPOS EP playlist."""
import json
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN = "/home/ubuntu/muzik/token.json"
BASE = "/home/ubuntu/muzik/album_latin"
LOG = "/home/ubuntu/muzik/upload_log_latin.json"
PLAYLIST_TITLE = "ANTHROPOS EP — Latin Sessions"
PLAYLIST_DESC = (
    "Four nights, four Latin worlds — reggaeton fire, a moonlit rooftop ballad, "
    "the breath of the Andes, and a golden Caribbean dusk. A cinematic Latin EP "
    "by TH Music (@THMusic-n1x)."
)


ITEMS = [
    {
        "slug": "01_fuego_en_la_noch",
        "title": "Fuego en la Noche — Single | THM Official",
        "desc": (
            "Fuego en la Noche — a Latin reggaeton night in the old streets of "
            "Havana.\nTwo dancers chase neon fire through colonial streets after "
            "dark — rivals at first, then a pair burning through the night.\n\n"
            "Genre: Reggaeton / Dembow — 96 BPM, G minor\n\n"
            "Stream all Latin sessions: ANTHROPOS EP playlist below.\n"
            "THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "Original composition and production: TH Music (@THMusic-n1x).\n\n"
            "#THMusic #LatinMusic #Reggaeton #FuegoEnLaNoche #NewMusic"
        ),
        "tags": ["latin reggaeton", "fuego en la noche", "thm official", "latin music",
                 "reggaeton 2026", "dembow", "latin pop"],
    },
    {
        "slug": "02_luna_en_tu_mirada",
        "title": "Luna en Tu Mirada — Single | THM Official",
        "desc": (
            "Luna en Tu Mirada — a Latin pop ballad on a Mexico City rooftop.\n"
            "Under the full moon, he writes a love letter to the city lights: she "
            "is the moon, and her eyes are his sky.\n\n"
            "Genre: Latin pop ballad — 84 BPM, C major\n\n"
            "Stream all Latin sessions: ANTHROPOS EP playlist below.\n"
            "THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "Original composition and production: TH Music (@THMusic-n1x).\n\n"
            "#THMusic #LatinBallad #LunaEnTuMirada #NewMusic #THMOfficial"
        ),
        "tags": ["latin ballad", "luna en tu mirada", "thm official", "latin pop",
                 "romantic latin music", "mexico city"],
    },
    {
        "slug": "03_cordillera",
        "title": "Cordillera — Single | THM Official",
        "desc": (
            "Cordillera — an Andean folk-pop dream.\nA girl in a mountain village "
            "watches the clouds roll through the Andes and dreams of the sea she "
            "has never seen. Pan flute, charango and modern pulse collide.\n\n"
            "Genre: Andean folk-pop — 100 BPM, A minor\n\n"
            "Stream all Latin sessions: ANTHROPOS EP playlist below.\n"
            "THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "Original composition and production: TH Music (@THMusic-n1x).\n\n"
            "#THMusic #AndeanMusic #Cordillera #PanFlute #NewMusic"
        ),
        "tags": ["andean music", "pan flute", "cordillera", "thm official",
                 "folk pop", "latin folk"],
    },
    {
        "slug": "04_playa_dorada",
        "title": "Playa Dorada — Single | THM Official",
        "desc": (
            "Playa Dorada — a golden Caribbean dusk.\nFriends, rum, dancing in the "
            "sand and a sunset he wants to keep forever. Marimba, requinto guitar "
            "and horns light the beach.\n\n"
            "Genre: Caribbean bachata / reggaeton fusion — 112 BPM, E minor\n\n"
            "Stream all Latin sessions: ANTHROPOS EP playlist below.\n"
            "THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "Original composition and production: TH Music (@THMusic-n1x).\n\n"
            "#THMusic #LatinMusic #PlayaDorada #Caribbean #NewMusic"
        ),
        "tags": ["latin fusion", "playa dorada", "thm official", "caribbean music",
                 "bachata reggaeton", "beach party"],
    },
]


def creds():
    with open(TOKEN) as f:
        data = json.load(f)
    return Credentials(
        token=data["token"],
        refresh_token=data.get("refresh_token"),
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )


def main():
    c = creds()
    yt = build("youtube", "v3", credentials=c)
    log = {"uploads": [], "playlist_id": None}
    if os.path.exists(LOG):
        with open(LOG) as f:
            log = json.load(f)
    done = {u.get("slug") for u in log["uploads"] if u.get("slug")}
    LIMIT_REACHED = False
    for it in ITEMS:
        if LIMIT_REACHED:
            print(f"[deferred] {it['slug']} deferred (daily upload limit reached)")
            continue
        if it["slug"] in done:
            print(f"[skip] {it['slug']} already uploaded")
            continue
        video_path = os.path.join(BASE, f"{it['slug']}_video.mp4")
        short_path = os.path.join(BASE, f"{it['slug']}_short.mp4")
        if not os.path.exists(video_path):
            print(f"[MISSING] {video_path}")
            continue
        body = {
            "snippet": {"title": it["title"], "description": it["desc"],
                        "tags": it["tags"], "categoryId": "10"},
            "status": {"privacyStatus": "public"},
        }
        try:
            r = yt.videos().insert(part="snippet,status", body=body,
                                   media_body=MediaFileUpload(video_path,
                                                              mimetype="video/mp4",
                                                              resumable=True)).execute()
            vid = r["id"]
        except Exception as e:
            es = str(e)
            if "uploadLimitExceeded" in es:
                print(f"[LIMIT] daily upload limit reached; retry tomorrow for {it['slug']}")
                LIMIT_REACHED = True
                continue
            raise
        short_id = None
        if os.path.exists(short_path):
            try:
                r2 = yt.videos().insert(part="snippet,status", body=body,
                                        media_body=MediaFileUpload(short_path,
                                                                   mimetype="video/mp4",
                                                                   resumable=True)).execute()
                short_id = r2["id"]
            except Exception as e:
                es = str(e)
                if "uploadLimitExceeded" in es:
                    print(f"[LIMIT] short deferred for {it['slug']} (daily limit)")
                else:
                    raise
            time.sleep(5)
        log["uploads"].append({"slug": it["slug"], "video_id": vid,
                               "short_id": short_id})
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)
        print(f"[uploaded] {it['slug']}: https://www.youtube.com/watch?v={vid}"
              + (f" | short: {short_id}" if short_id else ""))
        time.sleep(5)
    # playlist
    if log.get("playlist_id"):
        pl_id = log["playlist_id"]
    else:
        r = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": PLAYLIST_TITLE, "description": PLAYLIST_DESC},
            "status": {"privacyStatus": "public"},
        }).execute()
        pl_id = r["id"]
        log["playlist_id"] = pl_id
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)
        print(f"[playlist] {pl_id}")
    for u in log["uploads"]:
        if u.get("video_id"):
            try:
                yt.playlistItems().insert(part="snippet", body={
                    "snippet": {"playlistId": pl_id, "resourceId": {
                        "kind": "youtube#video", "videoId": u["video_id"]}}}).execute()
                print(f"[playlist] added {u['slug']}")
            except Exception as e:
                print(f"[playlist-fail] {u['slug']}: {e}")
            time.sleep(2)
    print("[DONE]")
    if LIMIT_REACHED:
        print("[NOTE] Some items were deferred due to the daily upload limit. "
              "Re-run this script tomorrow to finish.")


if __name__ == "__main__":
    main()
