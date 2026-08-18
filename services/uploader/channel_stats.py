#!/usr/bin/env python3
"""Fetch channel stats + statuses of previously-failed video IDs."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(**json.load(open('/home/ubuntu/muzik/token.json')))
yt = build('youtube', 'v3', credentials=creds)

# Channel stats
ch = yt.channels().list(part='snippet,statistics,brandingSettings', mine=True).execute()
for it in ch.get('items', []):
    s = it['snippet']
    st = it.get('statistics', {})
    print(f"Channel: {s['title']} (@{s.get('customUrl','?')})")
    print(f"subs={st.get('subscriberCount')} videos={st.get('videoCount')} views={st.get('viewCount')}")
    print(f"desc: {s['description'][:150]}")

# Check previously-failed IDs
ids = ['0HsNDDc75Iw', 'nB1n614FLFw', '6U7fmpvF-8E', '_qyXefhPlvc',
       'zsTLoOxyDdM', '-lTJELz_Z0I', '2D67ja7lvic', 'yN8UhwAvFy0',
       'js6VDeVzrLg', '4O_-0WVDizc', '1VlX1nzK3kI', 'WUA7CI2XDrM',
       'U-6zbqutEn0', 'xErtGeEr6Go', '7c4TjbsFBSo', 'qrtphYgvpo8',
       'rOrDP5V_AZs', 'WSux1ixYNRs', 'Z8VUwZ7F378', '0A78FEJ6W1M']
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    r = yt.videos().list(part='snippet,status,statistics,contentDetails', id=','.join(batch)).execute()
    for it in r.get('items', []):
        s = it['snippet']
        st = it.get('statistics', {})
        c = it.get('contentDetails', {}).get('uploadStatus', '?')
        dur = it.get('contentDetails', {}).get('duration', '?')
        print(f"{it['id']} | {s['title'][:60]} | {c} | {dur} | views={st.get('viewCount',0)} likes={st.get('likeCount',0)}")

# All public videos with stats (for feedback loop JSON)
all_vids = []
try:
    upl = yt.channels().list(part='contentDetails', mine=True).execute()
    up_id = upl['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    nxt = None
    while True:
        pi = yt.playlistItems().list(part='snippet', playlistId=up_id, maxResults=50, pageToken=nxt).execute()
        vids = [it['snippet']['resourceId']['videoId'] for it in pi.get('items', [])]
        nxt = pi.get('nextPageToken')
        if not vids:
            break
        for i in range(0, len(vids), 50):
            r = yt.videos().list(part='snippet,statistics,contentDetails', id=','.join(vids[i:i+50])).execute()
            for it in r.get('items', []):
                st = it.get('statistics', {})
                pub = it['snippet'].get('publishedAt', '')
                all_vids.append({
                    'id': it['id'], 'title': it['snippet'].get('title', ''),
                    'publishedAt': pub, 'views': int(st.get('viewCount') or 0),
                    'likes': int(st.get('likeCount') or 0),
                    'comments': int(st.get('commentCount') or 0),
                    'duration': it.get('contentDetails', {}).get('duration', ''),
                })
        if not nxt:
            break
except Exception as e:
    print(f"all_vids fetch error: {e}")

out = {
    'channel': None, 'videos': all_vids,
    'fetched_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
}
for it in ch.get('items', []):
    out['channel'] = it.get('statistics', {})
fn = '/home/ubuntu/muzik/research/daily_stats.json'
os.makedirs(os.path.dirname(fn), exist_ok=True)
json.dump(out, open(fn, 'w'), ensure_ascii=False, indent=2)
print(f"daily stats saved to {fn} ({len(all_vids)} videos)")

# Geo: check analytics not available for 3rd party without oauth analytics scope; skip.
