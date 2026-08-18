#!/usr/bin/env python3
"""Apply keywords + description via snippet part (brandingSettings title rename blocked)."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CHANNEL_ID = "UCV-7c2erzlx-lXcNjO-j7mg"

ABOUT = (
    "Welcome to THM Official — an independent music channel delivering cinematic original music and "
    "story-driven visual albums.\n\n"
    "Latest releases:\n"
    "\u2022 THE GENEROUS (Yediverenler) \u2014 a seven-track album spanning dark alt-pop, Anatolian rock, dance-pop, "
    "synthwave, hard rock, indie folk and trap. Each song a different color of generosity.\n"
    "\u2022 ECHOES OF A CITY \u2014 a story album: five nights, five stories, plus one Latin street festival anthem. "
    "Every video is a short film telling the song's story.\n\n"
    "Subscribe for new music and short films every week. All music is original, written and produced for "
    "this channel.\n\n"
    "#THMusic #OriginalMusic #CinematicMusic"
)

KEYWORDS = ("music, original music, cinematic music, THM Official, TH Music, album, music video, "
            "alternative pop, rock, synthwave, trap, folk, latin")

creds = Credentials.from_authorized_user_file("/home/ubuntu/muzik/token.json",
                                              ["https://www.googleapis.com/auth/youtube"])
svc = build("youtube", "v3", credentials=creds)
try:
    res = svc.channels().update(part="snippet", body={
        "id": CHANNEL_ID,
        "snippet": {"title": "Turhan Hamza M\u00fczik",
                    "description": ABOUT, "keywords": KEYWORDS,
                    "defaultLanguage": "en"},
    }).execute()
    print("OK snippet:", res["snippet"].get("title"))
except Exception as e:
    print("ERROR:", e)

r = svc.channels().list(part="snippet,brandingSettings", id=CHANNEL_ID).execute()
ch = r["items"][0]
print("title:", ch["snippet"]["title"])
print("desc set:", bool(ch["brandingSettings"]["channel"].get("description")))
print("keywords:", ch["snippet"].get("keywords"))
