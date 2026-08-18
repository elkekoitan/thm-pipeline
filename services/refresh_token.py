#!/usr/bin/env python3
"""Refresh the YouTube Data API access token."""
import json, requests

P = '/home/ubuntu/muzik/token.json'
t = json.load(open(P))
r = requests.post(t['token_uri'], data={
    'grant_type': 'refresh_token',
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
}, timeout=30)
d = r.json()
if 'access_token' in d:
    t['token'] = d['access_token']
    json.dump(t, open(P, 'w'), indent=1)
    print('token refreshed OK')
else:
    print('FAILED:', r.status_code, d)
