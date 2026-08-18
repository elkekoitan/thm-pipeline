#!/usr/bin/env python3
"""Upload calendar content: Rooftop Runners single + Night Drive Mix."""
import json
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE = "/home/ubuntu/muzik/calendar"
TOKEN = "/home/ubuntu/muzik/token.json"
CHANNEL_HANDLE = "@THMusic-n1x"
SHORTS_PL = "PLQYyTJMErr2w"

ITEMS = [
    {
        "slug": "teaser_anthropos_ep",
        "title": "Coming Soon — New Music | THM Official",
        "desc": (
            "Something new is on the way…\n"
            "TH Music (@THMusic-n1x) — new releases coming this season.\n"
            "Turn on notifications so you never miss a drop.\n\n"
            "#THMusic #ComingSoon #NewMusic #CinematicMusic"
        ),
        "tags": ["coming soon", "new music", "cinematic music", "thm official",
                 "music teaser"],
        "album_pl": None,
    },
    {
        "slug": "mix_golden_hour",
        "title": "Golden Hour Mix — Dream Garden | THM Official",
        "desc": (
            "Golden Hour Mix — indie folk, soft rock ballad & sea-breeze folk\n"
            "Warm sunset warmth: a dream garden, a lonely train platform, and a "
            "night ferry crossing — stitched into one seamless mix by TH Music "
            "(@THMusic-n1x).\n\n"
            "Tracks: Dream Garden • Last Train to Anywhere • Midnight Ferryman\n\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "#THMusic #GoldenHour #IndieFolk #Mix #NewMusic"
        ),
        "tags": ["golden hour mix", "indie folk", "soft rock ballad", "folk mix",
                 "dream garden", "mix", "thm official"],
        "album_pl": None,
    },
    {
        "slug": "single_rooftop_runners",
        "title": "Rooftop Runners — Single | THM Official",
        "desc": (
            "Rooftop Runners — energetic electro-pop\n"
            "Two siblings chase the sunrise across the city rooftops — freedom, speed,\n"
            "and the feeling that nothing can hold them down. From the album "
            "'ECHOES OF A CITY' by TH Music (@THMusic-n1x).\n\n"
            "Stream the full album on the ECHOES OF A CITY (Full Album) playlist.\n\n"
            "#THMusic #RooftopRunners #ElectroPop #CinematicMusic #NewMusic"
        ),
        "tags": ["rooftop runners", "electro pop", "electronic", "upbeat",
                 "sunrise", "cinematic", "thm official", "echoes of a city"],
        "album_pl": "PLbJMdR2ZoYkA",
    },
    {
        "slug": "mix_night_drive",
        "title": "Night Drive Mix — Neon Istanbul | THM Official",
        "desc": (
            "Night Drive Mix — synthwave, electro-pop & dance-pop\n"
            "A late-night drive through neon-lit Istanbul: synthwave sunsets, "
            "rooftop energy and dancefloor fever, stitched into one seamless mix "
            "by TH Music (@THMusic-n1x).\n\n"
            "Tracks: Neon Istanbul • Rooftop Runners • Dancefloor Fever\n\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "#THMusic #NightDrive #Synthwave #Mix #NewMusic"
        ),
        "tags": ["night drive mix", "synthwave", "electro pop", "dance pop",
                 "neon istanbul", "mix", "thm official", "lofi mix"],
        "album_pl": None,
    },
    {
        "slug": "ep_02_luna_en_tu_mirada",
        "folder": "album_latin",
        "title": "Luna en Tu Mirada (Official Video) — Latin Pop 2026 | THM Official | ANTHROPOS EP",
        "desc": (
            "Luna en Tu Mirada — a heartfelt Latin pop ballad about seeing your "
            "whole world reflected in someone's eyes, from the ANTHROPOS EP by "
            "TH Music (@THMusic-n1x).\n\n"
            "A moonlit confession: under the night sky, every word he never said "
            "lives in her gaze. Written in Spanish with cinematic Latin-pop "
            "arrangement — strings, nylon guitar, soft percussion.\n\n"
            "ANTHROPOS EP: https://www.youtube.com/playlist?list=PLeEEgZuryyEE\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "#THMusic #LatinPop #LunaEnTuMirada #LatinMusic2026 #NewMusic"
        ),
        "tags": ["latin pop", "latin pop ballad", "spanish song", "latin music 2026",
                 "ballad en espanol", "anthropos ep", "thm official"],
        "album_pl": "PLeEEgZuryyEE",
    },
    {
        "slug": "ep_03_cordillera",
        "folder": "album_latin",
        "title": "Cordillera (Official Video) — Andean Cinematic 2026 | THM Official | ANTHROPOS EP",
        "desc": (
            "Cordillera — an Andean cinematic journey across the great mountain "
            "range, from the ANTHROPOS EP by TH Music (@THMusic-n1x).\n\n"
            "Pan flutes and charango meet orchestral depth: a tribute to the "
            "Andes, to altitude, thin air, and the people who call the "
            "mountains home.\n\n"
            "ANTHROPOS EP: https://www.youtube.com/playlist?list=PLeEEgZuryyEE\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "#THMusic #Andean #Cordillera #LatinMusic2026 #NewMusic"
        ),
        "tags": ["andean music", "cordillera", "pan flute", "latin cinematic", "andean pop",
                 "anthropos ep", "thm official", "latin music 2026"],
        "album_pl": "PLeEEgZuryyEE",
    },
    {
        "slug": "ep_04_playa_dorada",
        "folder": "album_latin",
        "title": "Playa Dorada (Official Video) — Tropical Latin 2026 | THM Official | ANTHROPOS EP",
        "desc": (
            "Playa Dorada — golden-hour tropical Latin rhythm from the ANTHROPOS "
            "EP by TH Music (@THMusic-n1x).\n\n"
            "Sand, sea breeze and a warm steel-string groove: a love song to "
            "the golden beach at the end of summer.\n\n"
            "ANTHROPOS EP: https://www.youtube.com/playlist?list=PLeEEgZuryyEE\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n\n"
            "#THMusic #TropicalLatin #PlayaDorada #LatinMusic2026 #NewMusic"
        ),
        "tags": ["tropical latin", "playa dorada", "summer latin", "caribbean music",
                 "anthropos ep", "thm official", "latin music 2026"],
        "album_pl": "PLeEEgZuryyEE",
    },
    {
        "slug": "single_rooftop_runners_visualizer",
        "title": "Rooftop Runners — Spectrum Visualizer | THM Official | ECHOES OF A CITY",
        "desc": (
            "Rooftop Runners — audio-reactive spectrum visualizer by TH Music "
            "(@THMusic-n1x), from the album ECHOES OF A CITY.\n\n"
            "Two runners, one city below them at dawn. The track blends "
            "driving synth-pop with live drum energy.\n\n"
            "Official video: https://www.youtube.com/watch?v=tG9cXWHNyHA\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n\n"
            "#THMusic #RooftopRunners #Visualizer #SynthPop2026 #NewMusic"
        ),
        "tags": ["rooftop runners", "spectrum visualizer", "synth pop", "audio spectrum",
                 "echoes of a city", "thm official", "2026"],
        "album_pl": "PLbJMdR2ZoYkA",
    },
    {
        "slug": "latin_dance_mix_2026",
        "title": "Latin Dance Mix 2026 — Reggaeton & Caribbean Hits | THM Official",
        "desc": (
            "Latin Dance Mix 2026 — the best of reggaeton, Latin pop and Caribbean "
            "rhythm in one seamless cinematic mix by TH Music (@THMusic-n1x).\n\n"
            "Tracks: Fuego en la Noche • Fuego en la Calle • Luna en Tu Mirada • "
            "Playa Dorada • Cordillera\n\n"
            "From the ANTHROPOS EP (Latin Sessions) and ECHOES OF A CITY by "
            "TH Music (@THMusic-n1x).\n\n"
            "ANTHROPOS EP: https://www.youtube.com/playlist?list=PLeEEgZuryyEE\n"
            "Stream ECHOES OF A CITY: https://www.youtube.com/playlist?list=PLbJMdR2ZoYkA\n"
            "Stream THE GENEROUS: https://www.youtube.com/playlist?list=PLMtvWQDI5GHU\n\n"
            "#THMusic #LatinMusic #Reggaeton #LatinDanceMix2026 #NewMusic"
        ),
        "tags": ["latin dance mix 2026", "best latin music 2026", "reggaeton mix",
                 "latin reggaeton", "spanish hits", "caribbean music", "latin pop",
                 "mix", "thm official", "fuego en la calle", "anthropos ep"],
        "album_pl": "PLeEEgZuryyEE",
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
    log_path = "/home/ubuntu/muzik/upload_log_calendar.json"
    log = {"uploads": []}
    if os.path.exists(log_path):
        with open(log_path) as f:
            log = json.load(f)
    done = {u.get("slug") for u in log["uploads"] if u.get("slug")}
    for it in ITEMS:
        if it["slug"] in done:
            print(f"[skip] {it['slug']} already uploaded")
            continue
        folder = it.get("folder", "")
        video_path = os.path.join(BASE, folder, f"{it['slug']}_video.mp4") if folder \
            else os.path.join(BASE, f"{it['slug']}_video.mp4")
        short_path = os.path.join(BASE, folder, f"{it['slug']}_short.mp4") if folder \
            else os.path.join(BASE, f"{it['slug']}_short.mp4")
        if not os.path.exists(video_path):
            print(f"[MISSING] {video_path}")
            continue
        body = {
            "snippet": {"title": it["title"], "description": it["desc"],
                        "tags": it["tags"], "categoryId": "10"},
            "status": {"privacyStatus": "public"},
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            status, resp = req.next_chunk()
            if status:
                print(f"  [{it['slug']}] upload {int(status.progress() * 100)}%")
        vid = resp["id"]
        print(f"[uploaded] {it['title']}: https://www.youtube.com/watch?v={vid}")
        log["uploads"].append({"slug": it["slug"], "video_id": vid})
        if it["album_pl"]:
            try:
                yt.playlistItems().insert(
                    part="snippet", body={"snippet": {"playlistId": it["album_pl"],
                    "resourceId": {"kind": "youtube#video", "videoId": vid}}}
                ).execute()
                print(f"[playlist] added {vid}")
            except Exception as e:
                print(f"[playlist] failed: {e}")
            time.sleep(2)

        if os.path.exists(short_path):
            sbody = dict(body["snippet"])
            sbody["title"] = it["title"].replace("Single |", "Short |").replace(
                "Mix — Neon Istanbul", "Mix Short")
            sbody["title"] += " #Shorts"
            smedia = MediaFileUpload(short_path, mimetype="video/mp4", resumable=True)
            sreq = yt.videos().insert(part="snippet,status", body={
                "snippet": sbody, "status": {"privacyStatus": "public"}},
                media_body=smedia)
            sresp = None
            while sresp is None:
                status, sresp = sreq.next_chunk()
                if status:
                    print(f"  [{it['slug']} short] upload {int(status.progress() * 100)}%")
            sid = sresp["id"]
            print(f"[uploaded short] {it['slug']}: https://www.youtube.com/watch?v={sid}")
            log["uploads"][-1]["short_id"] = sid
            # add short to Shorts playlist
            try:
                yt.playlistItems().insert(
                    part="snippet", body={"snippet": {"playlistId": SHORTS_PL,
                    "resourceId": {"kind": "youtube#video", "videoId": sid}}}
                ).execute()
                print(f"[playlist] short added to THM Official Shorts")
            except Exception as e:
                print(f"[playlist] short failed: {e}")
        time.sleep(3)

    with open("/home/ubuntu/muzik/upload_log_calendar.json", "w") as f:
        json.dump(log, f, indent=2)
    print("ALL DONE")


if __name__ == "__main__":
    main()
