import pytest
import json
from hushh_mcp.agents import cost_agent


# Sample product data used in tests
@pytest.fixture
def sample_product():
    return {
        "id": "123",
        "itemname": "Redmi Note 10",
        "original_price": 12000,
        "purchase_date": "2022-03-10",
        "platform": "Flipkart"
    }

# Sample response in expected JSON format from Gemini
@pytest.fixture
def sample_response_json():
    return {
        "price_range": "4000 to 5000 INR",
        "confidence": "medium",
        "reasoning": "Mid-range phones lose value quickly after 2+ years of use"
    }

# ✅ TEST: cost_agent.build_prompt
def test_build_prompt_contains_fields(sample_product):
    prompt = cost_agent.build_prompt(sample_product)
    assert "Redmi Note 10" in prompt
    assert "12000" in prompt
    assert "Flipkart" in prompt
    assert "2022" in prompt  # ensure purchase year is present

# ✅ TEST: cost_agent.extract_json (valid JSON only)
def test_extract_json_valid():
    text = """
    {
      "price_range": "4000 to 5000 INR",
      "confidence": "medium",
      "reasoning": "Mid-range phones lose value quickly"
    }
    """
    result = cost_agent.extract_json(text)
    assert isinstance(result, dict)
    assert result["confidence"] == "medium"

# ✅ TEST: cost_agent.extract_json (extract JSON from noisy text)
def test_extract_json_from_wrapped_text():
    text = """
    Here's your valuation:
    {
      "price_range": "8000 to 10000 INR",
      "confidence": "high",
      "reasoning": "Flagship device retains good resale value"
    }
    Thanks!
    """
    result = cost_agent.extract_json(text)
    assert isinstance(result, dict)
    assert result["confidence"] == "high"

# ✅ TEST: cost_agent.extract_json (invalid input)
def test_extract_json_invalid():
    bad_json = "This isn't JSON at all"
    assert cost_agent.extract_json(bad_json) is None

# ✅ TEST: cost_agent.call_gemini
def test_call_gemini_success(monkeypatch):
    class DummyModel:
        def generate_content(self, prompt):
            class DummyResponse:
                text = """
                {
                  "price_range": "5000 to 6000 INR",
                  "confidence": "medium",
                  "reasoning": "Popular phone but now outdated"
                }
                """
            return DummyResponse()

    monkeypatch.setattr(cost_agent, "model", DummyModel())
    result = cost_agent.call_gemini("dummy prompt")
    assert "5000 to 6000 INR" in result

# ✅ TEST: cost_agent.main (entire flow with mocks)
def test_main_flow(monkeypatch, tmp_path, sample_product, sample_response_json):
    # Prepare dummy paths
    input_path = tmp_path / "productdetail.json"
    output_path = tmp_path / "resale_cost.json"

    # Override constants
    monkeypatch.setattr(cost_agent, "INPUT_FILE", str(input_path))
    monkeypatch.setattr(cost_agent, "OUTPUT_FILE", str(output_path))

    # Mock dependencies
    def fake_load(path):
        return [sample_product]

    def fake_save(data, path):
        with open(path, "w") as f:
            json.dump(data, f)

    def fake_call_gemini(prompt):
        return json.dumps(sample_response_json)

    monkeypatch.setattr(cost_agent, "load_encrypted_json", fake_load)
    monkeypatch.setattr(cost_agent, "save_encrypted_json", fake_save)
    monkeypatch.setattr(cost_agent, "call_gemini", fake_call_gemini)

    # Run main()
    cost_agent.main()

    # Verify output file
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
        assert data[0]["id"] == "123"
        assert "price_range" in data[0]
