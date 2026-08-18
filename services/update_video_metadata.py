#!/usr/bin/env python3
"""Retrofit metadata: add year (2026) + genre keywords to existing video titles.

Per research findings, search traffic is driven by genre + year keywords in
titles and descriptions. This updates priority top-performing videos.
"""
import json
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = 'token.json'
DRY = '--dry' in sys.argv

creds = Credentials.from_authorized_user_file(TOKEN, ['https://www.googleapis.com/auth/youtube'])
yt = build('youtube', 'v3', credentials=creds)

# id -> new title / description additions
UPDATES = [
    # Latin (strongest performer)
    ('twtdaD-zeDI', 'Fuego en la Calle (Official Video) — Latin Reggaeton 2026 | THM Official', None),
    # Album 2 ECHOES OF A CITY
    ('tG9cXWHNyHA', 'Rooftop Runners (Official Video) — Turkish Alt Rock 2026 | ECHOES OF A CITY | THM Official', None),
    ('PYfdnPjpWAM', 'Rain on Rooftop (Official Video) — Atmospheric Chill 2026 | ECHOES OF A CITY | THM Official', None),
    ('aGrM2G8cL0I', 'Midnight Ferryman (Official Video) — Dark Jazz Noir 2026 | ECHOES OF A CITY | THM Official', None),
    ('S2heAfaZKdg', "Clockmaker's Daughter (Official Video) — Cinematic Indie 2026 | ECHOES OF A CITY | THM Official", None),
    ('Gv8-tdGayFc', 'Last Train (Official Video) — Melancholic Piano Ballad 2026 | ECHOES OF A CITY | THM Official', None),
    # Album 1 THE GENEROUS (v2 videos, will also be replaced with new Higgsfield scenes later)
    ('CYyVpMnXhuE', 'Neon Istanbul (Official Video) — Synthwave 2026 | THE GENEROUS | THM Official', None),
    ('gIz3HFirzqw', 'Dancefloor Fever (Official Video) — Nu-Disco Funk 2026 | THE GENEROUS | THM Official', None),
    ('2E9z_HftZEc', 'Whisper Dark (Official Video) — Dark Ambient 2026 | THE GENEROUS | THM Official', None),
    ('eDJhvJLtuOE', 'Voice in Mountains (Official Video) — Epic Folk 2026 | THE GENEROUS | THM Official', None),
    ('6R_agjD8UmM', 'Wild Forest (Official Video) — Cinematic Adventure 2026 | THE GENEROUS | THM Official', None),
    ('vX7j95QPDrU', 'Dream Garden (Official Video) — Dream Pop 2026 | THE GENEROUS | THM Official', None),
    ('5L75uVb48Xk', 'Star Warrior (Official Video) — Epic Orchestral 2026 | THE GENEROUS | THM Official', None),
]

# Genre keywords to add to descriptions
DESC_ADD = (
    '\n\n#music2026 #2026 #newmusic #officialvideo #THMOfficial\n'
    'Listen to the full album playlist on the channel. Subscribe for weekly releases.'
)

def main():
    done = 0
    for vid, title, desc in UPDATES:
        try:
            cur = yt.videos().list(part='snippet', id=vid).execute()
            if not cur['items']:
                print(f'[missing] {vid} — not found, skipping')
                continue
            snip = dict(cur['items'][0]['snippet'])
            new_desc = (snip['description'] or '') + DESC_ADD
            body = {'id': vid, 'snippet': {**snip, 'title': title, 'description': new_desc}}
            if DRY:
                print(f'[dry] {vid} -> {title}')
            else:
                yt.videos().update(part='snippet', body=body).execute()
                print(f'[ok] {vid} -> {title}')
            done += 1
        except Exception as e:
            print(f'[err] {vid}: {e}')
    print(f'{done}/{len(UPDATES)} updated' + (' (dry run)' if DRY else ''))

if __name__ == '__main__':
    main()
