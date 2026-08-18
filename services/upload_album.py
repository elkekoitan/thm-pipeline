#!/usr/bin/env python3
"""Upload the 7 SEVEN COLORS album videos (+ optional thumbnails) to the
Turhan Hamza Müzik YouTube channel using the OAuth token in token.json."""
import json
import os
import sys
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ALBUM = "/home/ubuntu/muzik/album"
TOKEN = "/home/ubuntu/muzik/token.json"
LOG = "/home/ubuntu/muzik/upload_log.json"

TRACKS = [
    ("01_whisper_dark",
     "Whisper Dark (Official Video) | SEVEN COLORS Album",
     "Dark alt-pop with whispery vocals, minimalist synths and deep sub-bass drops. Track 1 of the SEVEN COLORS album by TH Music. "
     "Genre: dark alternative pop. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Whisper Dark,dark pop,alt pop,Billie Eilish style,alternative pop,music video,THMusic,album 2026"),
    ("02_daglarda_ses",
     "Dağlarda Ses (Official Video) | SEVEN COLORS Album",
     "Epic Anatolian rock with baglama, violins and thundering drums. Track 2 of the SEVEN COLORS album by TH Music. "
     "Genre: Anatolian rock / folk rock. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Dagluda Ses,Anatolian rock,Anadolu rock,Baris Manco style,folk rock,epic,Turkish rock,music video"),
    ("03_dancefloor_fever",
     "Dancefloor Fever (Official Video) | SEVEN COLORS Album",
     "Bright, euphoric dance-pop with glittering synths and steel drums. Track 3 of the SEVEN COLORS album by TH Music. "
     "Genre: dance-pop. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Dancefloor Fever,dance pop,Turkish pop,dance music,party,summer hit,music video,THMusic"),
    ("04_neon_istanbul",
     "Neon İstanbul (Official Video) | SEVEN COLORS Album",
     "Retro-futuristic synthwave over modern trap drums, a neon night drive through the city. Track 4 of the SEVEN COLORS album by TH Music. "
     "Genre: synthwave / retro electro. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Neon Istanbul,synthwave,retro,synth pop,electronic,neon,80s,music video"),
    ("05_vahsi_orman",
     "Vahşi Orman (Official Video) | SEVEN COLORS Album",
     "Raw hard rock with screaming guitars, pounding drums and an explosive guitar solo. Track 5 of the SEVEN COLORS album by TH Music. "
     "Genre: hard rock. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Vahsi Orman,hard rock,rock music,guitar solo,epic rock,heavy,music video,THMusic"),
    ("06_ruya_bahcesi",
     "Rüya Bahçesi (Official Video) | SEVEN COLORS Album",
     "Dreamy indie folk with acoustic guitar, piano and soft vocals that bloom into a string-soaked finale. Track 6 of the SEVEN COLORS album by TH Music. "
     "Genre: indie folk / acoustic. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Ruya Bahcesi,indie folk,acoustic,dream pop,folk music,chill,music video,THMusic"),
    ("07_yildiz_savascisi",
     "Yıldız Savaşçısı (Official Video) | SEVEN COLORS Album",
     "Bombastic trap fusion with 808 bass, sharp hi-hats and a final drop to close the album. Track 7 of the SEVEN COLORS album by TH Music. "
     "Genre: trap / hip-hop fusion. Listen to the full album on this channel @THMusic-n1x",
     "TH Music,Seven Colors,Yildiz Savascisi,trap,hip hop,808,trap beat,Turkish trap,rap,music video,THMusic"),
]


def creds():
    d = json.load(open(TOKEN))
    return Credentials(
        token=d["token"], refresh_token=d["refresh_token"], token_uri=d["token_uri"],
        client_id=d["client_id"], client_secret=d["client_secret"])


def main():
    # resume support
    done = {}
    if os.path.exists(LOG):
        done = json.load(open(LOG))

    yt = build("youtube", "v3", credentials=creds())

    for slug, title, desc, tags in TRACKS:
        if slug in done:
            print(f"[skip] {slug} -> {done[slug]['id']}")
            continue
        video = os.path.join(ALBUM, f"{slug}_video.mp4")
        if not os.path.exists(video):
            print(f"[missing] {video}")
            continue
        body = {
            "snippet": {
                "title": title,
                "description": desc,
                "tags": [t.strip() for t in tags.split(",")],
                "categoryId": "10",
            },
            "status": {"privacyStatus": "public", "embeddable": True,
                       "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(video, mimetype="video/mp4", resumable=True)
        for attempt in range(5):
            try:
                req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
                resp = req.execute()
                vid = resp["id"]
                print(f"[ok] {slug} -> https://www.youtube.com/watch?v={vid}")
                done[slug] = {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", "title": title}
                json.dump(done, open(LOG, "w"), indent=1, ensure_ascii=False)
                break
            except Exception as e:
                print(f"[retry {attempt+1}] {slug}: {str(e)[:200]}")
                time.sleep(10 * (attempt + 1))
        else:
            print(f"[FAILED] {slug}")
    print("DONE. Results saved to", LOG)
    for s, v in done.items():
        print(v["url"])


if __name__ == "__main__":
    main()
