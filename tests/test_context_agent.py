import pytest
import json
from unittest.mock import MagicMock
from hushh_mcp.agents import context_agent

# Sample product data for testing
@pytest.fixture
def sample_product():
    return {
        "id": 101,
        "price": "15000",
        "itemname": "iPhone 12",
        "purchase_date": "2023-01-15"
    }

# Sample valid JSON response from Groq API
@pytest.fixture
def sample_response_json():
    return {
        "id": 101,
        "price": "15000",
        "canonical_name": "Apple iPhone 12",
        "aliases": ["iPhone12", "Apple Phone 12"],
        "context_keywords": ["calling", "photography", "apps"]
    }

# --------- TEST: build_prompt() ---------
def test_build_prompt_contains_fields(sample_product):
    prompt = context_agent.build_prompt(sample_product)
    assert f'"id": {sample_product["id"]}' in prompt
    assert sample_product["price"] in prompt
    assert sample_product["itemname"] in prompt
    assert sample_product["purchase_date"] in prompt
    # The prompt should request JSON output only
    assert "ONLY WANT JSON" in prompt or "DONT WRITE ANYTHING ELSE" in prompt

# --------- TEST: call_groq() ---------
def test_call_groq_returns_response(monkeypatch):
    dummy_response = MagicMock()
    dummy_response.choices = [MagicMock()]
    dummy_response.choices[0].message.content = '{"id":101,"price":"15000"}'

    # Patch the client.chat.completions.create method to return dummy_response
    monkeypatch.setattr(context_agent.client.chat.completions, "create", lambda **kwargs: dummy_response)

    prompt = "dummy prompt"
    response = context_agent.call_groq(prompt)
    assert hasattr(response, "choices")
    assert response.choices[0].message.content == '{"id":101,"price":"15000"}'

# --------- TEST: main() ---------
def test_main_flow(monkeypatch, tmp_path, sample_product, sample_response_json):
    # Prepare dummy input and output file paths
    input_file = tmp_path / "productdetail.json"
    output_file = tmp_path / "context.json"

    # Override constants to use test tmp directory
    monkeypatch.setattr(context_agent, "INPUT_FILE", str(input_file))
    monkeypatch.setattr(context_agent, "OUTPUT_FILE", str(output_file))

    # Write sample product to input file using the encrypted load/save mocks
    def fake_load(path):
        return [sample_product]

    def fake_save(data, path):
        with open(path, "w") as f:
            json.dump(data, f)

    # Fake Groq call returns valid JSON string of sample_response_json
    def fake_call_groq(prompt):
        class DummyResp:
            choices = [MagicMock()]
            choices[0].message.content = json.dumps(sample_response_json)
        return DummyResp()

    monkeypatch.setattr(context_agent, "load_encrypted_json", fake_load)
    monkeypatch.setattr(context_agent, "save_encrypted_json", fake_save)
    monkeypatch.setattr(context_agent, "call_groq", fake_call_groq)

    # Run main
    context_agent.main()

    # Verify output file created and content correct
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert data[0]["id"] == sample_product["id"]
        assert "canonical_name" in data[0]
        assert "aliases" in data[0]
        assert "context_keywords" in data[0]

# --------- TEST: main() with invalid JSON from Groq ---------
def test_main_invalid_json(monkeypatch, tmp_path, sample_product):
    input_file = tmp_path / "productdetail.json"
    output_file = tmp_path / "context.json"

    monkeypatch.setattr(context_agent, "INPUT_FILE", str(input_file))
    monkeypatch.setattr(context_agent, "OUTPUT_FILE", str(output_file))

    def fake_load(path):
        return [sample_product]

    def fake_save(data, path):
        with open(path, "w") as f:
            json.dump(data, f)

    # Groq returns invalid JSON string
    def fake_call_groq(prompt):
        class DummyResp:
            choices = [MagicMock()]
            choices[0].message.content = "Not a JSON string"
        return DummyResp()

    monkeypatch.setattr(context_agent, "load_encrypted_json", fake_load)
    monkeypatch.setattr(context_agent, "save_encrypted_json", fake_save)
    monkeypatch.setattr(context_agent, "call_groq", fake_call_groq)

    # Run main, expect no crash and empty output
    context_agent.main()

    # Output file should exist and be empty list since parsing failed
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
        assert data == []
