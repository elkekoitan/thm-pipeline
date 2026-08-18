#!/usr/bin/env python3
import json
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

data = json.load(open("/home/ubuntu/muzik/token.json"))
c = Credentials(
    token=data["token"],
    refresh_token=data.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=data["client_id"],
    client_secret=data["client_secret"],
)
yt = build("youtube", "v3", credentials=c)
r = yt.channels().list(part="contentDetails", mine=True).execute()
pl = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
items = yt.playlistItems().list(
    part="snippet", playlistId=pl, maxResults=50).execute()
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
for i in list(items.get("items", []))[:limit]:
    sn = i["snippet"]
    print(sn["publishedAt"], "|", sn["resourceId"]["videoId"], "|",
          sn["title"][:70])
