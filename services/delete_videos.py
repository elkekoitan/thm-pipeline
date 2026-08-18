#!/usr/bin/env python3
"""Delete a list of video IDs (usage: python3 delete_videos.py id1 id2 ...)."""
import json
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"


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
    for vid in sys.argv[1:]:
        try:
            yt.videos().delete(id=vid).execute()
            print(f"[deleted] {vid}")
        except Exception as e:
            print(f"[FAIL] {vid}: {e}")
        time.sleep(2)


if __name__ == "__main__":
    main()
