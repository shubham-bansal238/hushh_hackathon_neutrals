import os
import json
from hushh_mcp.vault.json_vault import load_encrypted_json, save_encrypted_json
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from hushh_mcp.consent.token import validate_token
from hushh_mcp.constants import CONSENT_TOKEN_PATH
from hushh_mcp.types import ConsentScope
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
JSONS_DIR = os.path.join(os.path.dirname(__file__), "../jsons")
PRODUCTINFO_PATH = os.path.join(JSONS_DIR, "context.json")
OUTPUT_PATH = os.path.join(JSONS_DIR, "calendar_lastseen.json")


def load_consent_token():
    if not os.path.exists(CONSENT_TOKEN_PATH):
        return None
    with open(CONSENT_TOKEN_PATH, "r") as f:
        return f.read().strip()

def authenticate_google():
    if not os.path.exists("token.json"):
        print("⚠️ token.json missing. Run: python -m hushh_mcp.cli.authenticate_user")
        return None
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

def load_keywords(path=PRODUCTINFO_PATH) -> List[Dict]:
    return load_encrypted_json(path)

def fetch_calendar_events(service):
    start_time = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

def match_event(event: dict, keyword: Dict) -> bool:
    text = ((event.get("summary") or "") + " " + (event.get("description") or "")).lower()

    for context_word in keyword.get("context_keywords", []):
        if context_word.lower() in text:
            return True
    
    for alias in keyword.get("aliases", []):
        if alias.lower() in text:
            return True
    
    return False

def analyze_events(events: List[dict], keywords: List[Dict]):
    last_seen = {entry["id"]: None for entry in keywords}
    for event in events:
        date_str = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        if not date_str:
            continue

        try:
            event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            continue

        for keyword in keywords:
            if match_event(event, keyword):
                current = last_seen[keyword["id"]]
                if not current or event_date > current:
                    last_seen[keyword["id"]] = event_date

    return [
        {"id": k, "last_mentioned": v.date().isoformat() if v else None}
        for k, v in last_seen.items()
    ]

def save_result(data, path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    save_encrypted_json(data, path)

def main():
    # Consent verification
    token = load_consent_token()
    if not token:
        print("⚠️ No consent token. Run: python -m hushh_mcp.cli.authenticate_user")
        return
    try:
        validate_token(token, expected_scope=ConsentScope.FETCH_CALENDAR)
        print("✅ Consent token verified.")
    except Exception as e:
        print(f"❌ Consent token invalid or expired: {e}")
        return

    # Authenticate with Google Calendar
    service = authenticate_google()
    if not service:
        return

    # Load keywords (product info)
    keywords = load_keywords()

    # Fetch events and analyze matches
    events = fetch_calendar_events(service)
    result = analyze_events(events, keywords)

    # Save results
    save_result(result)
    print(f"✅ Keyword-date mapping saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
