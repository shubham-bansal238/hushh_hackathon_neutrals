import os
import json
from hushh_mcp.vault.json_vault import save_encrypted_json
import base64
import re
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
JSONS_DIR = os.path.join(os.path.dirname(__file__), "../jsons")
INPUT_FILE = os.path.join(JSONS_DIR, "relevant_emails.json")

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

def build_store_subject_query(store_keywords: dict) -> str:
    query_parts = []
    for store, keywords in store_keywords.items():
        for keyword in keywords:
            query_parts.append(f'(from:{store} "{keyword}")')
    return " OR ".join(query_parts)


def get_matching_message_ids(service, query: str, max_results=100) -> List[str]:
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    return [msg['id'] for msg in messages]

def extract_message_metadata(service, msg_id: str):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg['payload']['headers']
    metadata = {
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

    def decode_part(data):
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    def extract_body(payload):
        if payload.get('mimeType') == 'text/plain' and 'data' in payload.get('body', {}):
            return decode_part(payload['body']['data']), 'plain'
        elif payload.get('mimeType') == 'text/html' and 'data' in payload.get('body', {}):
            return decode_part(payload['body']['data']), 'html'
        elif 'parts' in payload:
            for part in payload['parts']:
                body, kind = extract_body(part)
                if body:
                    return body, kind
        return "", None

    body, kind = extract_body(msg['payload'])

    if kind == 'html':
        body = re.sub('<[^<]+?>', '', body)

    cleaned_body = re.sub(r'\s+', ' ', body).strip()
    metadata['body'] = cleaned_body or "[No body found]"

    return metadata

def main():
    os.makedirs(JSONS_DIR, exist_ok=True)

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
    if not service:
        print("❌ Google authentication failed.")
        return

    # Define stores and the keywords to look for in subject or body
    store_keywords = {
        "amazon.in": ["shipped"],
        "croma.com": ["invoice"],
        "noreply@flipkart.com": ["delivered", "invoice"]
    }
    

    # Gmail query: fetch by sender only
    query = build_store_subject_query(store_keywords)
    message_ids = get_matching_message_ids(service, query)
    print(f"🔍 Gmail returned {len(message_ids)} matching emails.")

    metadata_list = []
    for msg_id in message_ids:
        try:
            metadata = extract_message_metadata(service, msg_id)

            sender = metadata.get("from", "").lower()
            subject = metadata.get("subject", "").lower()
            body = metadata.get("body", "").lower()

            for store, keywords in store_keywords.items():
                if store in sender:
                    if any(kw in subject or kw in body for kw in keywords):
                        metadata_list.append(metadata)
                    break

        except Exception as e:
            print(f"⚠️ Error parsing message {msg_id}: {e}")

    # Save output
    save_encrypted_json(metadata_list, INPUT_FILE)
    print(f"✅ Filtered metadata saved to {INPUT_FILE} (encrypted)")

if __name__ == '__main__':
    main()
