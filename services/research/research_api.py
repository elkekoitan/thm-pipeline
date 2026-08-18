#!/usr/bin/env python3
"""THM research API client — reads token.json with Google credential keys and runs YouTube Data API research queries.

Usage:
  python3 research_api.py search "lofi sleep music" --duration long --order viewCount --out raw.json [--quota-budget 200]
  python3 research_api.py channels --ids <comma-separated channel ids> --out channels.json
  python3 research_api.py uploads <channel_id> --out uploads.json [--max 100]
"""
import json, sys, argparse, os, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

MUSIC_DIR = "/home/ubuntu/muzik"
TOKEN_PATH = os.path.join(MUSIC_DIR, "token.json")

creds = Credentials(**json.load(open(TOKEN_PATH)))
yt = build('youtube', 'v3', credentials=creds)

def safe_execute(req):
    for _ in range(3):
        try:
            return req.execute()
        except Exception as e:
            if 'quotaExceeded' in str(e) or 'uploadLimitExceeded' in str(e):
                raise
            time.sleep(2)
    return req.execute()

def cmd_search(args):
    req = yt.search().list(part='snippet', q=args.q, type='video',
                           videoDuration=args.duration, order=args.order,
                           maxResults=min(50, args.max))
    res = safe_execute(req)
    items = res.get('items', [])
    vids = []
    ids = [it.get('id', {}).get('videoId') for it in items if it.get('id', {}).get('videoId')]
    for i in range(0, len(ids), 50):
        r = safe_execute(yt.videos().list(part='snippet,statistics,contentDetails', id=','.join(ids[i:i+50])))
        vids.extend(r.get('items', []))
    print(f"results: {len(items)} (quota: search 100/call + {len(vids)} videos.list)")
    for v in vids[:args.max]:
        s = v['statistics']
        print(f"{v['id']} | {int(s.get('viewCount',0)):,} views | {v['snippet'].get('channelTitle','')[:32]:34s} | {v['snippet'].get('publishedAt','')[:10]} | {v['snippet'].get('title','')[:65]}")
    out = {'items': items, 'videos': vids}
    json.dump(out, open(args.out, 'w'))

def cmd_channels(args):
    ids = args.ids.split(',')
    req = yt.channels().list(part='snippet,statistics,brandingSettings', id=','.join(ids))
    res = safe_execute(req)
    print(f"channels: {len(res.get('items', []))}")
    for c in res.get('items', []):
        s = c['statistics']
        print(f"{c['id']} | {c['snippet']['title'][:40]:42s} | subs={s.get('subscriberCount')} views={s.get('viewCount')} videos={s.get('videoCount')}")
    json.dump(res, open(args.out, 'w'))

def cmd_uploads(args):
    req = yt.playlists().list(part='snippet', channelId=args.channel_id, maxResults=1)
    pl = safe_execute(req)
    pid = None
    for p in pl.get('items', []):
        if p['snippet']['title'] == 'Uploads':
            pid = p['id']; break
    if not pid:
        raise SystemExit('uploads playlist not found')
    items = []
    nxt = None
    while len(items) < args.max:
        req = yt.playlistItems().list(part='snippet', playlistId=pid, maxResults=50, pageToken=nxt)
        res = safe_execute(req)
        items.extend(res.get('items', []))
        nxt = res.get('nextPageToken')
        if not nxt:
            break
    # stats
    ids = [i['snippet']['resourceId']['videoId'] for i in items[:args.max]]
    vids = []
    for i in range(0, len(ids), 50):
        r = safe_execute(yt.videos().list(part='snippet,statistics,contentDetails', id=','.join(ids[i:i+50])))
        vids.extend(r.get('items', []))
    out = {'items': items[:args.max], 'stats': vids}
    print(f"videos: {len(vids)}")
    for v in vids[:30]:
        s = v['statistics']
        print(f"{v['id']} | {v['snippet']['title'][:60]:62s} | views={s.get('viewCount')} likes={s.get('likeCount')} pub={v['snippet']['publishedAt'][:10]}")
    json.dump(out, open(args.out, 'w'))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')
    a = sub.add_parser('search'); a.add_argument('q'); a.add_argument('--duration', default='any')
    a.add_argument('--order', default='viewCount'); a.add_argument('--out', default='/home/ubuntu/muzik/research/category/raw.json')
    a.add_argument('--max', type=int, default=25)
    b = sub.add_parser('channels'); b.add_argument('--ids', required=True)
    b.add_argument('--out', default='/home/ubuntu/muzik/research/category/raw_channels.json')
    c = sub.add_parser('uploads'); c.add_argument('channel_id')
    c.add_argument('--out', default='/home/ubuntu/muzik/research/category/raw_uploads.json'); c.add_argument('--max', type=int, default=100)
    args = p.parse_args()
    {'search': cmd_search, 'channels': cmd_channels, 'uploads': cmd_uploads}[args.cmd](args)
