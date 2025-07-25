import os
import json
from datetime import datetime
from typing import List
from hushh_mcp.consent.token import validate_token
from hushh_mcp.constants import CONSENT_TOKEN_PATH
from hushh_mcp.types import ConsentScope
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def load_consent_token():
    if not os.path.exists(CONSENT_TOKEN_PATH):
        return None
    with open(CONSENT_TOKEN_PATH, 'r') as f:
        return f.read().strip()

def authenticate_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        print("run: python -m hushh_mcp.cli.authenticate_user")
        return
    return build('gmail', 'v1', credentials=creds)

def build_query(stores: List[str], subjects: List[str]) -> str:
    store_query = " OR ".join([f"from:{s}" for s in stores])
    subject_query = " OR ".join([f"subject:{s}" for s in subjects])
    return f"({store_query}) ({subject_query})"

def get_matching_message_ids(service, query: str, max_results=50) -> List[str]:
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    return [msg['id'] for msg in messages]

def extract_message_metadata(service, msg_id: str):
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
    headers = msg['payload']['headers']
    metadata = {
        'snippet': msg.get('snippet'),
        'id': msg_id,
        'timestamp': int(msg.get('internalDate', '0')) // 1000
    }
    for header in headers:
        if header['name'].lower() == 'from':
            metadata['from'] = header['value']
        elif header['name'].lower() == 'subject':
            metadata['subject'] = header['value']
        elif header['name'].lower() == 'date':
            metadata['date'] = header['value']
    return metadata

def main():
    # Verify Consent
    token = load_consent_token()
    if not token:
        print("⚠️  No consent token found. Run: python -m hushh_mcp.cli.authenticate_user")
        return
    try:
        consent = validate_token(token, expected_scope=ConsentScope.FETCH_EMAIL)
        print(f"✅ Consent verified.")
    except Exception as e:
        print(f"❌ Consent token invalid or expired: {e}")
        return

    # Authenticate Google
    service = authenticate_google()

    # Define queries
    stores = ["nic.in", "iiser"]
    subjects = ["result", "jee", "main", "b.tech"]
    query = build_query(stores, subjects)

    # Fetch messages
    message_ids = get_matching_message_ids(service, query)
    print(f"🔍 Found {len(message_ids)} matching emails.")

    # Extract metadata
    metadata_list = []
    for msg_id in message_ids:
        try:
            metadata = extract_message_metadata(service, msg_id)
            metadata_list.append(metadata)
        except Exception as e:
            print(f"⚠️ Error parsing message {msg_id}: {e}")

    # Save
    with open('emails_extracted.json', 'w') as f:
        json.dump(metadata_list, f, indent=2)
    print("✅ Metadata saved to emails_extracted.json")

if __name__ == '__main__':
    main()
