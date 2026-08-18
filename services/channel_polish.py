#!/usr/bin/env python3
"""Professional polish for THM Official channel.

1. Update channel name -> THM OFFICIAL (channels.update brandingSettings + snippet)
2. Update channel description (About) with professional English text
3. Create playlists: THE GENEROUS full album, ECHOES OF A CITY full album, Shorts
4. Add album1 videos to THE GENEROUS playlist
"""
import json
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"
ALBUM1_IDS = ["zz8X1NAL2bg", "A2tGs_EBRnw", "kmObouNDIX0", "YZrdtGx5c1c",
              "3DufO-LWdXE", "ItERnlkPS6U", "X1JmyAY6EBM"]
CHANNEL_ID = "UCV-7c2erzlx-lXcNjO-j7mg"

ABOUT = (
    "Welcome to THM Official — an independent music channel delivering cinematic original music and "
    "story-driven visual albums.\n\n"
    "Latest releases:\n"
    "• THE GENEROUS (Yediverenler) — a seven-track album spanning dark alt-pop, Anatolian rock, dance-pop, "
    "synthwave, hard rock, indie folk and trap. Each song a different color of generosity.\n"
    "• ECHOES OF A CITY — a story album: five nights, five stories, plus one Latin street festival anthem. "
    "Every video is a short film telling the song's story.\n\n"
    "Subscribe for new music and short films every week. All music is original, written and produced for "
    "this channel.\n\n"
    "#THMusic #OriginalMusic #CinematicMusic"
)

KEYWORDS = ("music, original music, cinematic music, THM Official, TH Music, album, music video, "
            "alternative pop, rock, synthwave, trap, folk, latin")


def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN,
                                                  ["https://www.googleapis.com/auth/youtube"])
    return build("youtube", "v3", credentials=creds)


def main():
    svc = get_service()
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("branding", "all"):
        print("=== Updating channel name & about ===")
        body = {
            "id": CHANNEL_ID,
            "snippet": {
                "title": "THM OFFICIAL",
                "description": ABOUT,
                "keywords": KEYWORDS,
                "defaultLanguage": "en",
            },
            "brandingSettings": {
                "channel": {
                    "title": "THM OFFICIAL",
                    "description": ABOUT,
                    "keywords": KEYWORDS,
                    "unsubscribedTrailer": ALBUM1_IDS[0],
                }
            },
        }
        try:
            res = svc.channels().update(part="snippet", body=body).execute()
            print("Snippet title now:", res["snippet"]["title"])
        except Exception as e:
            print("ERROR snippet update:", e)
        try:
            branding_body = {
                "id": CHANNEL_ID,
                "brandingSettings": {
                    "channel": {
                        "title": "THM OFFICIAL",
                        "description": ABOUT,
                        "keywords": KEYWORDS,
                        "unsubscribedTrailer": ALBUM1_IDS[0],
                    }
                },
            }
            res = svc.channels().update(part="brandingSettings", body=branding_body).execute()
            print("Branding title now:", res["brandingSettings"]["channel"]["title"])
        except Exception as e:
            print("ERROR branding update:", e)

    if mode in ("playlists", "all"):
        print("=== Creating playlists ===")
        # fetch existing playlists first
        existing = {}
        tok = None
        while True:
            r = svc.playlists().list(part="snippet", channelId=CHANNEL_ID,
                                     maxResults=50, pageToken=tok).execute()
            for p in r.get("items", []):
                existing[p["snippet"]["title"]] = p["id"]
            tok = r.get("nextPageToken")
            if not tok:
                break
        print("Existing playlists:", list(existing))

        playlists = [
            ("THE GENEROUS — Yediverenler (Full Album)", ALBUM1_IDS,
             "The complete first album: seven songs, seven colors. Dark alt-pop to trap."),
            ("ECHOES OF A CITY (Full Album)", None,
             "The story album: five nights, five stories — plus one Latin street festival anthem."),
            ("THM Official Shorts", None,
             "Official YouTube Shorts from the channel."),
        ]
        for title, ids, desc in playlists:
            if title in existing:
                pid = existing[title]
                print("playlist exists:", title, pid)
            else:
                try:
                    r = svc.playlists().insert(part="snippet,status", body={
                        "snippet": {"title": title, "description": desc},
                        "status": {"privacyStatus": "public"},
                    }).execute()
                    pid = r["id"]
                    existing[title] = pid
                    print("created:", title, pid)
                except Exception as e:
                    print("ERROR creating", title, e)
                    continue
            if title.startswith("THE GENEROUS") and ids:
                # add album1 videos
                done = set()
                r = None
                for _ in range(6):
                    try:
                        r = svc.playlistItems().list(part="snippet", playlistId=pid,
                                                     maxResults=50).execute()
                        break
                    except Exception as e:
                        print("waiting for playlist propagation...")
                        time.sleep(15)
                if r is None:
                    print("WARN: cannot list playlist", pid, "— skipping items")
                    continue
                for it in r.get("items", []):
                    done.add(it["snippet"].get("resourceId", {}).get("videoId"))
                for vid in ids:
                    if vid in done:
                        continue
                    try:
                        svc.playlistItems().insert(part="snippet", body={
                            "snippet": {"playlistId": pid,
                                        "resourceId": {"kind": "youtube#video", "videoId": vid}},
                        }).execute()
                        print("added", vid, "to", title)
                    except Exception as e:
                        print("ERROR adding", vid, e)
        print("DONE playlists")


if __name__ == "__main__":
    main()
