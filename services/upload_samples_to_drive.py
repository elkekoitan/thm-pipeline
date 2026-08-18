#!/usr/bin/env python3
"""Upload samples_v2 files to Drive under THM_Offical_Uretim_Arsivi using gws CLI."""
import json
import subprocess
import sys

ARCHIVE_NAME = "THM_Offical_Uretim_Arsivi"
FOLDER_NAME = "samples_v2"


def gws(args):
    r = subprocess.run(["gws"] + args, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print("ERR:", r.stdout[:500], r.stderr[:500])
        return None


def main():
    # find archive folder
    q = (f"mimeType='application/vnd.google-apps.folder' and "
         f"name='{ARCHIVE_NAME}' and trashed=false")
    res = gws(["drive", "files", "list", "--params",
               json.dumps({"q": q, "fields": "files(id,name)"})])
    if not res or not res.get("files"):
        print("archive folder not found")
        sys.exit(1)
    archive_id = res["files"][0]["id"]
    print("archive:", archive_id)

    # find or create samples_v2 subfolder
    folder_id = "1pzL8KJJ-QKhu1WmuM--vr0tcNLy7Qgg0"
    print("folder:", folder_id)

    files = [
        "/home/ubuntu/drive_package/samples_v2/lofi_v2.mp3",
        "/home/ubuntu/drive_package/samples_v2/sleep_v2.mp3",
        "/home/ubuntu/drive_package/samples_v2/KALITE_RAPORU_V2.md",
        "/home/ubuntu/drive_package/samples_v2/comparison_lofi.png",
        "/home/ubuntu/drive_package/samples_v2/comparison_sleep.png",
    ]
    for f in files:
        ct = ("audio/mpeg" if f.endswith(".mp3")
              else "text/markdown" if f.endswith(".md")
              else "image/png")
        res = gws(["drive", "files", "create", "--params",
                   json.dumps({"fileId": f"create_{f.split('/')[-1]}"}),
                   "--json", json.dumps({"name": f.split("/")[-1],
                                         "parents": [folder_id]}),
                   "--upload", f, "--upload-content-type", ct])
        if res:
            print("uploaded", f.split("/")[-1], res.get("id"))
        else:
            print("FAILED", f)


if __name__ == "__main__":
    main()
