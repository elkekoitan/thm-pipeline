#!/usr/bin/env python3
"""Channel cleanup: delete all videos except the most-viewed (Fuego en la Calle).

Kotası 10,000/gün, her silme ~1600 → max 6 silme/gün. Her çalıştırma kalan
kota dahilinde 6'ya kadar siler ve ilerlemeyi delete_log.json'a yazar.
Sonsuz döngü yok: bir çalıştırmada max 6.

usage: python3 cleanup_channel.py
"""
import json
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/muzik/token.json"
QUEUE = "/home/ubuntu/muzik/delete_queue.json"
LOG = "/home/ubuntu/muzik/delete_log.json"
MAX_PER_RUN = 6


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

    with open(QUEUE) as f:
        queue = json.load(f)
    done = []
    if __import__("os").path.exists(LOG):
        with open(LOG) as f:
            done = json.load(f)
    remaining = [i for i in queue if i not in done]
    print(f"[queue] {len(remaining)} remaining of {len(queue)}")

    for vid in remaining[:MAX_PER_RUN]:
        try:
            yt.videos().delete(id=vid).execute()
            done.append(vid)
            with open(LOG, "w") as f:
                json.dump(done, f)
            print(f"[deleted] {vid}")
        except Exception as e:
            err = str(e)
            if "uploadLimitExceeded" in err or "quotaExceeded" in err \
                    or "dailyLimitExceeded" in err:
                print("[LIMIT] quota exhausted; re-run tomorrow")
                return
            if '404' in err or 'notFound' in err or 'not be found' in err:
                done.append(vid)
                with open(LOG, "w") as f:
                    json.dump(done, f)
                print(f"[notfound→done] {vid}")
            else:
                print(f"[ERROR] {vid}: {err[:200]}")
        time.sleep(3)

    remaining2 = [i for i in queue if i not in done]
    if remaining2:
        print(f"[NOTE] {len(remaining2)} more to delete — re-run tomorrow")
    else:
        print("[DONE] channel cleanup complete")


if __name__ == "__main__":
    main()
