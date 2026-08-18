#!/usr/bin/env python3
"""Probe: upload a tiny private video to confirm the token and identify the channel."""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

d = json.load(open('/home/ubuntu/muzik/token.json'))
creds = Credentials(
    token=d['token'], refresh_token=d['refresh_token'], token_uri=d['token_uri'],
    client_id=d['client_id'], client_secret=d['client_secret'])
yt = build('youtube', 'v3', credentials=creds)

body = {
    'snippet': {'title': 'test probe 2', 'description': 'test'},
    'status': {'privacyStatus': 'private'},
}
req = yt.videos().insert(part='snippet,status', body=body,
                         media_body=MediaFileUpload('/home/ubuntu/muzik/test_upload.mp4'))
resp = req.execute()
print(json.dumps(resp, indent=1))
