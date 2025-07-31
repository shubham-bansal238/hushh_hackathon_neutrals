from typing import Any, List

def fetch_calendar_events(service: Any) -> List[dict]:
    """
    Fetches calendar events using a Google Calendar API service instance.
    Returns a list of event dicts.
    """
    events_result = service.events().list(calendarId='primary', singleEvents=True, orderBy='startTime').execute()
    return events_result.get('items', [])
