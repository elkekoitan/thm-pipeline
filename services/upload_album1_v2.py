#!/usr/bin/env python3
"""Replace THE GENEROUS album videos with v2 versions.

1. Delete old videos (IDs in OLD_IDS).
2. Upload new videos + shorts from album1_v2/.
3. Add new videos to THE GENEROUS playlist.
"""
import json
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE = "/home/ubuntu/muzik/album1_v2"
TOKEN = "/home/ubuntu/muzik/token.json"
ALBUM = "THE GENEROUS"
CHANNEL_HANDLE = "@THMusic-n1x"
PLAYLIST_ID = "PLMtvWQDI5GHU"

OLD_IDS = ["zz8X1NAL2bg", "A2tGs_EBRnw", "kmObouNDIX0",
           "YZrdtGx5c1c", "3DufO-LWdXE", "ItERnlkPS6U", "X1JmyAY6EBM"]

TRACKS = [
    ("01", "whisper_dark", "Whisper Dark",
     "dark alt-pop",
     "In the blue hour, a confession finally finds its voice — dark alt-pop "
     "with whispers that bloom into an anthem.",
     ["dark alt pop", "alt pop", "moody", "cinematic", "night", "thm official"]),
    ("02", "daglarda_ses", "Voice in the Mountains",
     "Anatolian rock",
     "A call echoes across golden Anatolian ridges — Anatolian rock with "
     "breathtaking open-air energy.",
     ["anatolian rock", "turkish rock", "epic", "mountains", "cinematic", "thm official"]),
    ("03", "dancefloor_fever", "Dancefloor Fever",
     "dance-pop",
     "The night takes over and the crowd becomes one heartbeat — dance-pop "
     "made for neon-lit floors.",
     ["dance pop", "edm", "club", "party", "neon", "thm official"]),
    ("04", "neon_istanbul", "Neon Istanbul",
     "synthwave",
     "Chrome reflections on the Bosphorus at dusk — a synthwave cruise through "
     "a city that never stops glowing.",
     ["synthwave", "retro wave", "80s", "istanbul", "cinematic", "thm official"]),
    ("05", "vahsi_orman", "Wild Forest",
     "hard rock",
     "A storm tears through the forest and a guitar answers the thunder — raw "
     "hard rock with untamed power.",
     ["hard rock", "rock", "storm", "electric guitar", "thm official"]),
    ("06", "ruya_bahcesi", "Dream Garden",
     "indie folk",
     "Sunlight, wildflowers and a lone tree — indie folk for the daydreamers.",
     ["indie folk", "folk", "dreamy", "acoustic", "sunlight", "thm official"]),
    ("07", "yildiz_savascisi", "Star Warrior",
     "trap",
     "Beyond the horizon a warrior rises among the stars — trap with cosmic "
     "weight and heavy 808s.",
     ["trap", "hip hop", "trap beat", "cosmic", "808", "thm official"]),
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

    # 1) delete old videos
    for vid in OLD_IDS:
        try:
            yt.videos().delete(id=vid).execute()
            print(f"[deleted] {vid}")
        except Exception as e:
            print(f"[delete fail] {vid}: {e}")
        time.sleep(2)

    # 2) upload v2
    log = {"uploads": []}
    for idx, key, title, genre, story, tags in TRACKS:
        video_path = os.path.join(BASE, f"{idx}_{key}_video.mp4")
        short_path = os.path.join(BASE, f"{idx}_{key}_short.mp4")
        if not os.path.exists(video_path):
            print(f"[MISSING] {video_path}")
            continue
        body = {
            "snippet": {
                "title": f"{title} (Official Video) | {ALBUM} Album",
                "description": (
                    f"{title} — {genre}\n"
                    f"From the album '{ALBUM}' by TH Music ({CHANNEL_HANDLE}).\n\n"
                    f"{story}\n\n"
                    f"Stream the full album on the {ALBUM} (Full Album) playlist.\n\n"
                    f"#THMusic #{ALBUM.replace(' ', '')} #{title.replace(' ', '')} "
                    f"#CinematicMusic #NewMusic"
                ),
                "tags": tags,
                "categoryId": "10",
            },
            "status": {"privacyStatus": "public"},
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            status, resp = req.next_chunk()
            if status:
                print(f"  [{title}] upload {int(status.progress() * 100)}%")
        vid = resp["id"]
        print(f"[uploaded] {title}: https://www.youtube.com/watch?v={vid}")
        log["uploads"].append({"key": key, "video_id": vid})

        if os.path.exists(short_path):
            sbody = dict(body["snippet"])
            sbody["title"] = f"{title} (Short) | {ALBUM} Album"
            smedia = MediaFileUpload(short_path, mimetype="video/mp4", resumable=True)
            sreq = yt.videos().insert(part="snippet,status", body={
                "snippet": sbody, "status": {"privacyStatus": "public"}}, media_body=smedia)
            sresp = None
            while sresp is None:
                status, sresp = sreq.next_chunk()
                if status:
                    print(f"  [{title} short] upload {int(status.progress() * 100)}%")
            sid = sresp["id"]
            print(f"[uploaded short] {title}: https://www.youtube.com/watch?v={sid}")
            log["uploads"][-1]["short_id"] = sid
        time.sleep(3)

    with open("/home/ubuntu/muzik/upload_log_album1_v2.json", "w") as f:
        json.dump(log, f, indent=2)

    # 3) add to playlist
    for entry in log["uploads"]:
        try:
            yt.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": PLAYLIST_ID,
                                  "resourceId": {"kind": "youtube#video",
                                                 "videoId": entry["video_id"]}}},
            ).execute()
            print(f"[playlist] added {entry['video_id']} to THE GENEROUS playlist")
            time.sleep(2)
        except Exception as e:
            print(f"[playlist] failed for {entry['video_id']}: {e}")
    print("ALL DONE")


if __name__ == "__main__":
    main()
