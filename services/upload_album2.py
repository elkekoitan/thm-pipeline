#!/usr/bin/env python3
"""Upload ECHOES OF A CITY album videos + shorts to the Turhan Hamza Müzik channel."""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE = "/home/ubuntu/muzik/album2_v2"
TOKEN = "/home/ubuntu/muzik/token.json"
ALBUM = "ECHOES OF A CITY"
CHANNEL_HANDLE = "@THMusic-n1x"

TRACKS = [
    ("01", "rain_on_the_rooftop", "Rain on the Rooftop",
     "lo-fi alt-pop",
     "A lonely writer watches the rain fall over a neon city, searching for the "
     "words that keep escaping him.",
     ["lo-fi", "alt pop", "rain", "cinematic", "indie", "thm official"]),
    ("02", "midnight_ferryman", "Midnight Ferryman",
     "sea-breeze soft rock ballad",
     "An old ferryman crosses the night waters, carrying memories of a life "
     "that refused to stay behind.",
     ["soft rock", "ballad", "ferry", "sea", "cinematic", "thm official"]),
    ("03", "rooftop_runners", "Rooftop Runners",
     "energetic electro-pop",
     "Two siblings chase the sunrise across the city rooftops — freedom, speed, "
     "and the feeling that nothing can hold them down.",
     ["electro pop", "electronic", "upbeat", "sunrise", "cinematic", "thm official"]),
    ("04", "clockmakers_daughter", "The Clockmaker's Daughter",
     "orchestral indie-pop waltz",
     "Inside an antique clock shop, a girl winds time backward to find the "
     "letter her father never sent.",
     ["orchestral", "indie pop", "waltz", "clock", "cinematic", "thm official"]),
    ("05", "last_train_to_anywhere", "Last Train to Anywhere",
     "acoustic folk duet",
     "Two strangers share a bench on a foggy platform — the last train might "
     "take them anywhere, or nowhere at all.",
     ["acoustic folk", "duet", "train", "folk", "cinematic", "thm official"]),
    ("06", "fuego_en_la_calle", "Fuego en la Calle",
     "latin salsa/reggaeton",
     "The street erupts in brass, drums and fire — a Latin block party that "
     "turns the whole neighborhood into a dancefloor.",
     ["latin", "salsa", "reggaeton", "spanish", "party", "thm official"]),
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
        import time
        time.sleep(3)

    with open("/home/ubuntu/muzik/upload_log_album2.json", "w") as f:
        json.dump(log, f, indent=2)

    # Add uploaded videos to the ECHOES OF A CITY playlist
    playlist_id = "PLbJMdR2ZoYkA"
    for entry in log["uploads"]:
        try:
            yt.playlistItems().insert(
                part="snippet", body={"snippet": {"playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": entry["video_id"]}}}
            ).execute()
            print(f"[playlist] added video {entry['video_id']} to ECHOES OF A CITY playlist")
            time.sleep(2)
        except Exception as e:
            print(f"[playlist] failed for {entry['video_id']}: {e}")
    print("ALL DONE")


if __name__ == "__main__":
    main()
