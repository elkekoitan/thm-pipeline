#!/usr/bin/env python3
"""Audit all videos on the THM channel with view/like stats."""
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"
CHANNEL = "UCV-7c2erzlx-lXcNjO-j7mg"

data = json.load(open(TOKEN))
c = Credentials(token=data["token"], refresh_token=data.get("refresh_token"),
                client_id=data["client_id"], client_secret=data["client_secret"],
                token_uri="https://oauth2.googleapis.com/token")
yt = build("youtube", "v3", credentials=c)

# get all video ids via channel uploads playlist
mine = yt.channels().list(part="contentDetails", id=CHANNEL).execute()
upl = mine["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
vids = []
tok = None
while True:
    r = yt.playlistItems().list(part="snippet", playlistId=upl, maxResults=50,
                                pageToken=tok).execute()
    for it in r["items"]:
        vids.append((it["snippet"]["publishedAt"], it["snippet"]["resourceId"]["videoId"],
                     it["snippet"]["title"]))
    tok = r.get("nextPageToken")
    if not tok:
        break

out = []
for pub, vid, title in vids:
    try:
        st = yt.videos().list(part="statistics", id=vid).execute()
        s = st["items"][0]["statistics"]
    except Exception:
        s = {}
    views, likes = int(s.get("viewCount", 0)), int(s.get("likeCount", 0))
    out.append((pub, views, likes, title))
    print(f"{pub[:10]} | {views:>7} views | {likes:>5} likes | {title[:65]}")

out.sort(key=lambda x: x[1], reverse=True)
print("\n--- TOP 5 by views ---")
for o in out[:5]:
    print(f"{o[1]:>7} views | {o[3][:65]}")
print("\n--- BOTTOM 5 by views ---")
for o in out[-5:]:
    print(f"{o[1]:>7} views | {o[3][:65]}")
