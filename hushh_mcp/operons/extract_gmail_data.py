from typing import Any, Dict

def extract_gmail_data(service: Any, msg_id: str) -> Dict:
    """
    Extracts metadata from a Gmail message using the Gmail API.
    Returns a dict with subject, sender, and snippet.
    """
    message = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
    headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
    return {
        'subject': headers.get('Subject'),
        'from': headers.get('From'),
        'snippet': message.get('snippet')
    }
