import unittest
from unittest.mock import patch, MagicMock
from hushh_mcp.agents import receipt_agent  # Correct import

class TestEmailParser(unittest.TestCase):
    @patch("hushh_mcp.agents.receipt_agent.load_encrypted_json")
    @patch("hushh_mcp.agents.receipt_agent.save_encrypted_json")
    @patch("hushh_mcp.agents.receipt_agent.model.generate_content")
    def test_main_runs_and_filters(self, mock_generate_content, mock_save_json, mock_load_json):
        # Mock input JSON data for load_encrypted_json
        mock_load_json.return_value = [
            {
                "from": "order-update@amazon.in",
                "body": "<html>Order Details: Item XYZ Rs. 1500</html>",
                "subject": "Your Amazon order",
                "date": "Wed, 01 Jan 2023 10:00:00"
            }
        ]

        # Mock Gemini API response to only keep electronics
        gemini_response = '[{"itemname": "Item XYZ", "price": 1500, "purchase_date": "2023-01-01", "platform": "amazon"}]'
        mock_generate_content.return_value = MagicMock(text=gemini_response)

        # Run main should parse emails, call Gemini, and save output
        receipt_agent.main()

        # Check load_encrypted_json called once with input file path
        mock_load_json.assert_called_once_with(receipt_agent.INPUT_PATH)

        # Check that Gemini generate_content was called (once, here)
        self.assertTrue(mock_generate_content.called)

        # Check save_encrypted_json called once with output path
        mock_save_json.assert_called_once()
        args, kwargs = mock_save_json.call_args
        self.assertEqual(args[1], receipt_agent.OUTPUT_PATH)

        # Check that saved data contains expected filtered product keys
        saved_data = args[0]
        self.assertIsInstance(saved_data, list)
        self.assertGreater(len(saved_data), 0)
        self.assertIn("itemname", saved_data[0])
        self.assertIn("price", saved_data[0])
        self.assertIn("purchase_date", saved_data[0])
        self.assertIn("platform", saved_data[0])

if __name__ == "__main__":
    unittest.main()
