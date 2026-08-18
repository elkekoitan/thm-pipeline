#!/usr/bin/env python3
"""Rename the 7 album video titles from SEVEN COLORS to THE GENEROUS.

The youtube.upload scope DOES permit videos().update of snippet for owned
videos. Run with '--test' first to see what would change without writing.
"""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"
LOG = "/home/ubuntu/muzik/upload_log.json"

VIDS = json.load(open(LOG))

def creds():
    d = json.load(open(TOKEN))
    return Credentials(
        token=d["token"], refresh_token=d["refresh_token"], token_uri=d["token_uri"],
        client_id=d["client_id"], client_secret=d["client_secret"])

def main(test_only=False):
    yt = build("youtube", "v3", credentials=creds())
    for slug, info in VIDS.items():
        vid = info["id"]
        new_title = info["title"].replace("SEVEN COLORS Album", "THE GENEROUS Album")
        if "SEVEN COLORS" in new_title:
            print(f"[skip-title] {slug}")
            continue
        if test_only:
            print(f"[would set] {slug} ({vid}): {new_title}")
            continue
        for attempt in range(3):
            try:
                yt.videos().update(
                    part="snippet",
                    body={"id": vid, "snippet": {
                        "title": new_title,
                        "description": info.get("description", ""),
                        "tags": info.get("tags", []),
                        "categoryId": "10",
                    }}).execute()
                print(f"[ok] {slug} ({vid}): {new_title}")
                break
            except Exception as e:
                print(f"[retry {attempt+1}] {slug}: {str(e)[:250]}")
    if test_only:
        print("TEST MODE - no changes made")

if __name__ == "__main__":
    import sys
    main(test_only="--test" in sys.argv)
