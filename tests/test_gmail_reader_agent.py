import os
import base64
import pytest
from datetime import datetime
from hushh_mcp.agents import gmail_reader_agent


@pytest.fixture
def mock_consent_token_file(tmp_path, monkeypatch):
    token_file = tmp_path / "consent_token.json"
    token_file.write_text("abc123")
    
    # Patch the function that opens the file, not the constant
    def mock_load_consent_token():
        return token_file.read_text().strip()

    monkeypatch.setattr(gmail_reader_agent, "load_consent_token", mock_load_consent_token)
    return token_file


def test_load_consent_token(mock_consent_token_file):
    token = gmail_reader_agent.load_consent_token()
    assert token == "abc123"


def test_build_store_subject_query():
    store_keywords = {
        "amazon.in": ["shipped"],
        "croma.com": ["invoice"],
    }
    query = gmail_reader_agent.build_store_subject_query(store_keywords)
    assert 'from:amazon.in' in query
    assert '"shipped"' in query
    assert 'from:croma.com' in query
    assert '"invoice"' in query


def test_extract_message_metadata(monkeypatch):
    dummy_msg = {
        "payload": {
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(b"Hello world").decode()
            },
            "headers": [
                {"name": "From", "value": "example@store.com"},
                {"name": "Subject", "value": "Your Order"},
                {"name": "Date", "value": "Fri, 1 Aug 2025 12:00:00 GMT"}
            ]
        },
        "internalDate": str(int(datetime.now().timestamp() * 1000))
    }

    class DummyService:
        def users(self): return self
        def messages(self): return self
        def get(self, userId, id, format): return self
        def execute(self): return dummy_msg

    metadata = gmail_reader_agent.extract_message_metadata(DummyService(), "dummy-id")
    assert metadata["from"] == "example@store.com"
    assert metadata["subject"] == "Your Order"
    assert "Hello world" in metadata["body"]


def test_main(monkeypatch):
    monkeypatch.setattr(gmail_reader_agent, "load_consent_token", lambda: "valid-token")
    monkeypatch.setattr(gmail_reader_agent, "validate_token", lambda token, expected_scope: {"user": "test-user"})
    monkeypatch.setattr(gmail_reader_agent, "authenticate_google", lambda: "mock-service")
    monkeypatch.setattr(gmail_reader_agent, "get_matching_message_ids", lambda service, query: ["id1"])

    def mock_extract(service, msg_id):
        return {
            "id": msg_id,
            "from": "noreply@flipkart.com",
            "subject": "Your item has been delivered",
            "body": "Delivered to your address."
        }

    monkeypatch.setattr(gmail_reader_agent, "extract_message_metadata", mock_extract)

    captured = {}

    def fake_save(data, path):
        captured["data"] = data
        captured["path"] = path

    monkeypatch.setattr(gmail_reader_agent, "save_encrypted_json", fake_save)

    gmail_reader_agent.main()
    assert len(captured["data"]) == 1
    assert "flipkart" in captured["data"][0]["from"]
