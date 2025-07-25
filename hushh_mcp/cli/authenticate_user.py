import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from hushh_mcp.constants import (
    ConsentScope,
    CONSENT_TOKEN_PATH,
    GMAIL_TOKEN_PATH,
    DEFAULT_CONSENT_TOKEN_EXPIRY_MS,
)
from hushh_mcp.consent.token import issue_token, revoke_token

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

def authenticate_user():
    creds = None
    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), GOOGLE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, GOOGLE_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds

def get_user_email(creds):
    if creds.id_token and "email" in creds.id_token:
        return creds.id_token["email"]

    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    return user_info.get("email", "unknown")

def revoke_consent(scope: ConsentScope):
    if not os.path.exists(CONSENT_TOKEN_PATH):
        print("⚠️ No consent token file found.")
        return

    with open(CONSENT_TOKEN_PATH, "r") as f:
        data = json.load(f)

    if str(scope) not in data:
        print(f"⚠️ No token found for scope: {scope}")
        return

    token_data = data.pop(str(scope))
    try:
        revoke_token(token_data["token"])
        print(f"❌ Revoked consent for scope: {scope}")
    except Exception as e:
        print(f"⚠️ Error revoking token: {e}")

    if data:
        with open(CONSENT_TOKEN_PATH, "w") as f:
            json.dump(data, f, indent=2)
    else:
        os.remove(CONSENT_TOKEN_PATH)
        print("🗑️ All consent tokens removed.")

def grant_consent_flow():
    creds = authenticate_user()
    user_email = get_user_email(creds)
    print(f"\n✅ Authenticated as: {user_email}")

    print("\nWhat do you consent to share with agents?")
    print("1. Only Gmail (readonly)")
    print("2. Only Calendar (readonly)")
    print("3. Both Gmail and Calendar")
    print("4. None (exit)")
    consent_choice = input("Choose [1/2/3/4]: ").strip()

    if os.path.exists(CONSENT_TOKEN_PATH):
        with open(CONSENT_TOKEN_PATH) as f:
            existing = json.load(f)
    else:
        existing = {}

    if consent_choice == "1":
        token = issue_token(user_id=user_email, agent_id="gmail_reader_agent", scope=ConsentScope.FETCH_EMAIL, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
        existing[str(ConsentScope.FETCH_EMAIL)] = token.dict()
    elif consent_choice == "2":
        token = issue_token(user_id=user_email, agent_id="calendar_reader_agent", scope=ConsentScope.FETCH_CALENDAR, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
        existing[str(ConsentScope.FETCH_CALENDAR)] = token.dict()
    elif consent_choice == "3":
        token1 = issue_token(user_id=user_email, agent_id="gmail_reader_agent", scope=ConsentScope.FETCH_EMAIL, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
        token2 = issue_token(user_id=user_email, agent_id="calendar_reader_agent", scope=ConsentScope.FETCH_CALENDAR, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
        existing[str(ConsentScope.FETCH_EMAIL)] = token1.dict()
        existing[str(ConsentScope.FETCH_CALENDAR)] = token2.dict()
    else:
        print("❌ No data shared. Exiting.")
        return

    with open(CONSENT_TOKEN_PATH, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"✅ Consent token(s) saved to: {CONSENT_TOKEN_PATH}")

def revoke_consent_flow():
    print("\nWhich consent do you want to revoke?")
    print("1. Gmail only")
    print("2. Calendar only")
    print("3. Both")
    revoke_choice = input("Choose [1/2/3]: ").strip()

    if revoke_choice == "1":
        revoke_consent(ConsentScope.FETCH_EMAIL)
    elif revoke_choice == "2":
        revoke_consent(ConsentScope.FETCH_CALENDAR)
    elif revoke_choice == "3":
        revoke_consent(ConsentScope.FETCH_EMAIL)
        revoke_consent(ConsentScope.FETCH_CALENDAR)
    else:
        print("❌ Invalid option.")

def main():
    print("🔐 Personal Data Agent Setup")
    print("1. Authenticate with Google")
    print("2. Grant Consent")
    print("3. Revoke Consent")
    choice = input("Choose [1/2/3]: ").strip()

    if choice == "1":
        creds = authenticate_user()
        email = get_user_email(creds)
        print(f"✅ Authenticated as: {email}")
    elif choice == "2":
        grant_consent_flow()
    elif choice == "3":
        revoke_consent_flow()
    else:
        print("❌ Invalid main choice.")

if __name__ == "__main__":
    main()
