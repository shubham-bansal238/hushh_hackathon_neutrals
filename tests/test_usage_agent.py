import pytest
from unittest.mock import patch
import hushh_mcp.agents.usage_agent as usage_agent

class TestUsageAgent:
    sample_master_data = {
        "products": [
            {
                "id": 1,
                "itemname": "Sample Product",
                "price_range": "800-1200",
                "confidence": 0.9,
                "chrome_browsing_matched_url_history": ["query1", "query2"],
                "calender_last_matched": "2023-07-01"
            }
        ],
        "driver_history_from_pc": {"some": "driver data"}
    }

    @patch("hushh_mcp.agents.usage_agent.load_encrypted_json")
    @patch("hushh_mcp.agents.usage_agent.call_gemini")
    def test_main_handles_bad_json(self, mock_call_gemini, mock_load):
        mock_load.return_value = self.sample_master_data
        mock_call_gemini.return_value = "not a json"

        with patch("builtins.print") as mock_print:
            usage_agent.main()

            calls = mock_print.call_args_list
            # Assert that "Failed to parse JSON for: Sample Product" was printed
            assert any("Failed to parse JSON for: Sample Product" in call.args[0] for call in calls)

            # Assert that "Raw response:" and the bad response appear as two separate print args
            assert any(call.args[0] == "Raw response:" and call.args[1] == "not a json" for call in calls)

    @patch("hushh_mcp.agents.usage_agent.load_encrypted_json")
    @patch("hushh_mcp.agents.usage_agent.call_gemini")
    def test_main_handles_no_response(self, mock_call_gemini, mock_load):
        mock_load.return_value = self.sample_master_data
        mock_call_gemini.return_value = None  # Simulate no response

        with patch("builtins.print") as mock_print:
            usage_agent.main()

            calls = mock_print.call_args_list
            # Check "No response for: Sample Product" printed
            assert any("No response for: Sample Product" in call.args[0] for call in calls)

    @patch("hushh_mcp.agents.usage_agent.load_encrypted_json")
    @patch("hushh_mcp.agents.usage_agent.call_gemini")
    @patch("hushh_mcp.agents.usage_agent.save_encrypted_json")
    def test_main_successful_status_parse(self, mock_save, mock_call_gemini, mock_load):
        mock_load.return_value = self.sample_master_data
        # Return valid JSON string with status
        mock_call_gemini.return_value = '{"id": "1", "status": "resell_candidate"}'

        usage_agent.main()

        # Check save_encrypted_json called once
        mock_save.assert_called_once()
        saved_data, saved_path = mock_save.call_args[0]

        # Validate updated status in saved data
        assert "products" in saved_data
        product = saved_data["products"][0]
        assert product["id"] == 1
        assert product["status"] == "resell_candidate"

        # Driver history preserved
        assert "driver_history_from_pc" in saved_data
        assert saved_data["driver_history_from_pc"] == self.sample_master_data["driver_history_from_pc"]

    @patch("hushh_mcp.agents.usage_agent.load_encrypted_json")
    def test_extract_json_valid_and_invalid(self, mock_load):
        # Valid JSON string
        valid_json = '{"id": 1, "status": "dont_sell"}'
        parsed = usage_agent.extract_json(valid_json)
        assert parsed == {"id": 1, "status": "dont_sell"}

        # Invalid JSON but with embedded JSON
        embedded_json = 'Some text before {"id": 2, "status": "uncertain"} some text after'
        parsed = usage_agent.extract_json(embedded_json)
        assert parsed == {"id": 2, "status": "uncertain"}

        # Completely invalid JSON
        invalid_json = 'No json here!'
        parsed = usage_agent.extract_json(invalid_json)
        assert parsed is None
