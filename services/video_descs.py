#!/usr/bin/env python3
"""Set professional English descriptions for all album videos."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"
ALBUM1 = {
    "zz8X1NAL2bg": {
        "name": "Whisper Dark",
        "genre": "Dark alt-pop",
        "story": "A confession whispered to the shadows of a city that never listens.",
    },
    "A2tGs_EBRnw": {
        "name": "Dağlarda Ses",
        "genre": "Anatolian rock",
        "story": "A voice echoing through mountain valleys, calling everyone home.",
    },
    "kmObouNDIX0": {
        "name": "Dancefloor Fever",
        "genre": "Dance-pop",
        "story": "One unforgettable night where strangers become family on the dancefloor.",
    },
    "YZrdtGx5c1c": {
        "name": "Neon İstanbul",
        "genre": "Synthwave",
        "story": "A midnight drive through the neon veins of a restless city.",
    },
    "3DufO-LWdXE": {
        "name": "Vahşi Orman",
        "genre": "Hard rock",
        "story": "A wild chase through the forest, where only the fearless survive.",
    },
    "ItERnlkPS6U": {
        "name": "Rüya Bahçesi",
        "genre": "Indie folk",
        "story": "A secret garden where dreams bloom and time stands still.",
    },
    "X1JmyAY6EBM": {
        "name": "Yıldız Savaşçısı",
        "genre": "Trap",
        "story": "A warrior rising from the streets, guided by starlight.",
    },
}
ALBUM2 = {
    "01_rain_on_the_rooftop": {
        "name": "Rain on the Rooftop",
        "genre": "Lo-fi alt-pop",
        "story": "A young writer finds his voice while the city rains neon below his balcony.",
    },
    "02_midnight_ferryman": {
        "name": "Midnight Ferryman",
        "genre": "Sea-breeze soft rock",
        "story": "An old man sails the last ferry of the night, carrying fifty years of memory.",
    },
    "03_rooftop_runners": {
        "name": "Rooftop Runners",
        "genre": "Electro-pop",
        "story": "Two siblings race across rooftops, chasing the sunrise before the city wakes.",
    },
    "04_clockmakers_daughter": {
        "name": "The Clockmaker's Daughter",
        "genre": "Orchestral indie-pop",
        "story": "A daughter discovers her father's final letter hidden inside his last pocket watch.",
    },
    "05_last_train_to_anywhere": {
        "name": "Last Train to Anywhere",
        "genre": "Acoustic folk",
        "story": "Two strangers share a bench at midnight — the last train changes everything.",
    },
    "06_fuego_en_la_calle": {
        "name": "Fuego en la Calle",
        "genre": "Latin salsa / reggaeton fusion",
        "story": "A street festival erupts in fire, brass and joy under a sky of lanterns.",
    },
}

ALBUM1_TITLE = "THE GENEROUS — Yediverenler"
ALBUM2_TITLE = "ECHOES OF A CITY"
SOCIALS = (
    "Subscribe to THM Official for original cinematic music and story films every week: "
    "https://www.youtube.com/@THMusic-n1x"
)


def desc(track, album, story):
    return (
        f"{track['name']} — an original {track['genre']} song from the album {album}.\n\n"
        f"{story}\n\n"
        "Every song on this channel comes with its own short film. Listen, watch, and share.\n\n"
        f"Album: {album}\nChannel: THM Official (@THMusic-n1x)\n\n"
        f"{SOCIALS}\n\n"
        f"#THMusic #OriginalMusic #" + track['genre'].replace(',', '').replace(' ', '')
    )


def main():
    creds = Credentials.from_authorized_user_file(TOKEN, ["https://www.googleapis.com/auth/youtube"])
    svc = build("youtube", "v3", credentials=creds)
    ok, fail = 0, []
    items = ALBUM1 if mode != "album2" else ALBUM2
    album_name = ALBUM1_TITLE if mode != "album2" else ALBUM2_TITLE
    for vid, t in items.items():
        try:
            existing = svc.videos().list(part="snippet", id=vid).execute()
            title = existing["items"][0]["snippet"]["title"] if existing.get("items") else t["name"]
            svc.videos().update(part="snippet", body={
                "id": vid,
                "snippet": {"title": title,
                            "description": desc(t, album_name, t["story"]),
                            "categoryId": "10"},
            }).execute()
            ok += 1
            print("album1 ok:", vid)
        except Exception as e:
            print("album1 FAIL", vid, e)
            fail.append(vid)
    return ok, fail


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "album1"
    if mode == "album1":
        creds = Credentials.from_authorized_user_file(TOKEN, ["https://www.googleapis.com/auth/youtube"])
        svc = build("youtube", "v3", credentials=creds)
        ok, fail = 0, []
        for vid, t in ALBUM1.items():
            try:
                existing = svc.videos().list(part="snippet", id=vid).execute()
                title = existing["items"][0]["snippet"]["title"] if existing.get("items") else t["name"]
                svc.videos().update(part="snippet", body={
                    "id": vid,
                    "snippet": {"title": title,
                                "description": desc(t, ALBUM1_TITLE, t["story"]),
                                "categoryId": "10"},
                }).execute()
                ok += 1
                print("album1 ok:", vid)
            except Exception as e:
                print("album1 FAIL", vid, e)
                fail.append(vid)
        print("album1 done:", ok, "failed:", fail)
    elif mode == "test":
        creds = Credentials.from_authorized_user_file(TOKEN, ["https://www.googleapis.com/auth/youtube"])
        svc = build("youtube", "v3", credentials=creds)
        # dry-run: print one description
        t = ALBUM1["zz8X1NAL2bg"]
        print(desc(t, ALBUM1_TITLE, t["story"]))
