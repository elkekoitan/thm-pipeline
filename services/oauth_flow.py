#!/usr/bin/env python3
"""OAuth 2.0 flow for YouTube upload authorization.

Step 1: run with `url` -> prints authorization URL (open in browser).
Step 2: run with `code <AUTH_CODE>` -> exchanges code, saves token to token.json.
"""
import json
import sys
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

CRED_FILE = "/home/ubuntu/muzik/oauth_credentials.json"
TOKEN_FILE = "/home/ubuntu/muzik/token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]
REDIRECT = "urn:ietf:wg:oauth:2.0:oob"
STATE_FILE = "/home/ubuntu/muzik/oauth_state.json"

if __name__ == "__main__":
    with open(CRED_FILE) as f:
        client_config = json.load(f)

    if sys.argv[1] == "url":
        flow = Flow.from_client_config(client_config, SCOPES, redirect_uri=REDIRECT)
        # Force PKCE off to match a code_challenge-less authorization URL,
        # and disable autogenerate (which was generating a verifier only at
        # authorization_url time, losing it between runs).
        flow.code_verifier = None
        flow.autogenerate_code_verifier = False
        url, state = flow.authorization_url(prompt="consent")
        with open(STATE_FILE, "w") as f:
            json.dump({"state": state, "verifier": flow.code_verifier}, f)
        print("AUTH_URL:", url)
    elif sys.argv[1] == "code":
        code = sys.argv[2]
        saved = json.load(open(STATE_FILE))
        flow = Flow.from_client_config(
            client_config, SCOPES, redirect_uri=REDIRECT,
            state=saved["state"],
            code_verifier=saved.get("verifier"),
            autogenerate_code_verifier=False,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }, f)
        print("TOKEN SAVED. expires_in:", creds.expiry)
        # quick test: whoami
        from googleapiclient.discovery import build
        yt = build("youtube", "v3", credentials=creds)
        me = yt.channels().list(part="snippet", mine=True).execute()
        for c in me["items"]:
            print("CHANNEL:", c["snippet"]["title"], c["id"])
