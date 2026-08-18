#!/usr/bin/env python3
"""Upload samples_v2 files to Drive via the Data API client (reliable)."""
import json
import os

import google.oauth2.credentials
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

TOKEN = "/home/ubuntu/muzik/token.json"
ARCHIVE_ID = "1qccnkOh5A0oXsOaIKF0h06L2vXk2F2qL"
FOLDER_ID = "1pzL8KJJ-QKhu1WmuM--vr0tcNLy7Qgg0"  # existing (octet-stream
# placeholder name); we'll trash it and use a proper folder

creds = google.oauth2.credentials.Credentials(**json.load(open(TOKEN)))
yt = googleapiclient.discovery.build("drive", "v3", credentials=creds)


def main():
    # ensure proper folder exists
    q = (f"mimeType='application/vnd.google-apps.folder' and "
         f"name='samples_v2' and '{ARCHIVE_ID}' in parents and "
         f"trashed=false")
    r = yt.files().list(q=q, fields="files(id)").execute()
    if r.get("files"):
        folder_id = r["files"][0]["id"]
    else:
        folder_id = yt.files().create(
            body={"name": "samples_v2",
                  "mimeType": "application/vnd.google-apps.folder",
                  "parents": [ARCHIVE_ID]},
            fields="id").execute()["id"]
    print("folder:", folder_id)

    files = [
        ("lofi_v2.mp3", "audio/mpeg"),
        ("sleep_v2.mp3", "audio/mpeg"),
        ("KALITE_RAPORU_V2.md", "text/markdown"),
        ("comparison_lofi.png", "image/png"),
        ("comparison_sleep.png", "image/png"),
    ]
    base = "/home/ubuntu/drive_package/samples_v2"
    for name, ct in files:
        path = f"{base}/{name}"
        media = MediaFileUpload(path, mimetype=ct, resumable=False)
        meta = yt.files().create(
            body={"name": name, "parents": [folder_id]},
            media_body=media, fields="id,name,size").execute()
        print("uploaded", meta.get("name"), meta.get("id"), meta.get("size"))


if __name__ == "__main__":
    main()
