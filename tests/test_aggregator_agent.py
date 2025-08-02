import pytest
from unittest.mock import patch
import hushh_mcp.agents.aggregator_agent as master_builder

def test_load_json_with_file_and_no_file(monkeypatch):
    # Patch load_encrypted_json to return some data
    monkeypatch.setattr(master_builder, "load_encrypted_json", lambda path: {"key": "value"})

    # Patch os.path.exists to True
    monkeypatch.setattr(master_builder.os.path, "exists", lambda path: True)
    result = master_builder.load_json("dummy_path", default={"default": True})
    assert result == {"key": "value"}

    # Patch os.path.exists to False
    monkeypatch.setattr(master_builder.os.path, "exists", lambda path: False)
    result = master_builder.load_json("non_existent_path", default={"default": True})
    assert result == {"default": True}

    # Patch load_encrypted_json to raise Exception
    def raise_exc(path):
        raise Exception("fail")
    monkeypatch.setattr(master_builder.os.path, "exists", lambda path: True)
    monkeypatch.setattr(master_builder, "load_encrypted_json", raise_exc)
    result = master_builder.load_json("dummy_path", default={"default": True})
    assert result == {"default": True}


def test_main_aggregation(monkeypatch):
    monkeypatch.setattr(master_builder.os.path, "exists", lambda path: True)

    def load_side_effect(path):
        if path == master_builder.PRODUCT_FILE:
            return [{"id": 1, "itemname": "Prod1", "price": 1000, "purchase_date": "2023-01-01"}]
        elif path == master_builder.RESALE_FILE:
            return [{"id": 1, "price_range": "800-1200", "confidence": 0.9}]
        elif path == master_builder.HISTORY_FILE:
            return {"1": {"matched_queries": ["query1", "query2"]}}
        elif path == master_builder.CALENDAR_FILE:
            return {"1": {"last_mentioned": "2023-07-01"}}
        elif path == master_builder.DRIVER_FILE:
            return {"some": "driver data"}
        return None

    monkeypatch.setattr(master_builder, "load_encrypted_json", load_side_effect)

    saved = {}
    def fake_save(data, path):
        saved['data'] = data
        saved['path'] = path

    monkeypatch.setattr(master_builder, "save_encrypted_json", fake_save)

    master_builder.main()

    assert saved['path'] == master_builder.OUTPUT_FILE
    output_data = saved['data']

    assert "products" in output_data
    assert isinstance(output_data["products"], list)
    assert "driver_history_from_pc" in output_data

    product = output_data["products"][0]
    assert product["id"] == 1
    assert product["itemname"] == "Prod1"
    assert product["price_range"] == "800-1200"
    assert product["confidence"] == 0.9
    assert product["chrome_browsing_matched_url_history"] == ["query1", "query2"]
    assert product["calender_last_matched"] == "2023-07-01"
