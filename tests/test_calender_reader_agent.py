import os
import pytest
from datetime import datetime, timedelta, timezone
from hushh_mcp.agents import calender_reader_agent


@pytest.fixture
def mock_keywords():
    return [
        {"id": "1", "context_keywords": ["meeting", "review"], "aliases": ["sync", "catch-up"]},
        {"id": "2", "context_keywords": ["launch"], "aliases": ["rollout"]}
    ]


@pytest.fixture
def dummy_events():
    now = datetime.now(timezone.utc)
    return [
        {
            "summary": "Product sync",
            "description": "Weekly catch-up",
            "start": {"dateTime": (now - timedelta(days=1)).isoformat()}
        },
        {
            "summary": "Launch discussion",
            "description": "Big rollout event",
            "start": {"date": (now - timedelta(days=5)).date().isoformat()}
        },
        {
            "summary": "Unrelated event",
            "description": "No match here",
            "start": {"date": (now - timedelta(days=10)).date().isoformat()}
        }
    ]


def test_match_event_found(mock_keywords):
    event = {
        "summary": "Project Catch-Up",
        "description": "Discussion meeting"
    }
    assert calender_reader_agent.match_event(event, mock_keywords[0]) is True


def test_match_event_not_found(mock_keywords):
    event = {
        "summary": "Some random event",
        "description": "No keywords"
    }
    assert calender_reader_agent.match_event(event, mock_keywords[0]) is False


def test_analyze_events(dummy_events, mock_keywords):
    result = calender_reader_agent.analyze_events(dummy_events, mock_keywords)
    ids = [r["id"] for r in result]
    assert "1" in ids and "2" in ids
    for r in result:
        if r["id"] == "1":
            assert r["last_mentioned"] is not None
        if r["id"] == "2":
            assert r["last_mentioned"] is not None


def test_load_consent_token(tmp_path, monkeypatch):
    token_file = tmp_path / "consent_token.json"
    token_file.write_text("test-token")
    
    monkeypatch.setattr(calender_reader_agent, "CONSENT_TOKEN_PATH", str(token_file))
    token = calender_reader_agent.load_consent_token()
    
    assert token == "test-token"


def test_load_keywords(monkeypatch):
    fake_keywords = [{"id": "x", "context_keywords": ["test"], "aliases": []}]
    monkeypatch.setattr(calender_reader_agent, "load_encrypted_json", lambda path: fake_keywords)

    result = calender_reader_agent.load_keywords("dummy-path.json")
    assert result == fake_keywords


def test_save_result(tmp_path, monkeypatch):
    saved_data = {}

    def fake_save(data, path):
        saved_data["data"] = data
        saved_data["path"] = path

    monkeypatch.setattr(calender_reader_agent, "save_encrypted_json", fake_save)

    path = tmp_path / "calendar_lastseen.json"
    data = [{"id": "1", "last_mentioned": "2025-08-01"}]
    calender_reader_agent.save_result(data, path)

    assert saved_data["data"] == data
    assert saved_data["path"] == path


def test_main(monkeypatch, dummy_events, mock_keywords):
    monkeypatch.setattr(calender_reader_agent, "load_consent_token", lambda: "valid-token")
    monkeypatch.setattr(calender_reader_agent, "validate_token", lambda token, expected_scope: True)
    monkeypatch.setattr(calender_reader_agent, "authenticate_google", lambda: "mock-service")
    monkeypatch.setattr(calender_reader_agent, "load_keywords", lambda: mock_keywords)
    monkeypatch.setattr(calender_reader_agent, "fetch_calendar_events", lambda service: dummy_events)

    captured_result = {}

    def fake_save(data, path):
        captured_result["data"] = data
        captured_result["path"] = path

    monkeypatch.setattr(calender_reader_agent, "save_encrypted_json", fake_save)

    calender_reader_agent.main()

    assert len(captured_result["data"]) == 2
    assert all("id" in item and "last_mentioned" in item for item in captured_result["data"])
