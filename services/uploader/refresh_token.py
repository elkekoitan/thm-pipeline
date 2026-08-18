import json
from google.oauth2.credentials import Credentials

TOKEN = '/home/ubuntu/muzik/token.json'
creds = Credentials(**json.load(open(TOKEN)))
print('before: valid =', creds.valid, '| expired =', creds.expired)
from google.auth.transport.requests import Request
creds.refresh(Request())
d = {
    'token': creds.token, 'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri, 'client_id': creds.client_id,
    'client_secret': creds.client_secret, 'scopes': list(creds.scopes),
}
json.dump(d, open(TOKEN, 'w'), indent=2)
print('after: valid =', creds.valid)
