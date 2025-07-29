import os
import json

# Paths
BASE_DIR = os.path.dirname(__file__)
JSONS_DIR = os.path.join(BASE_DIR, "../jsons")

PRODUCT_FILE = os.path.join(JSONS_DIR, "productdetail.json")
RESALE_FILE = os.path.join(JSONS_DIR, "resale_cost.json")
HISTORY_FILE = os.path.join(JSONS_DIR, "history.json")
CALENDAR_FILE = os.path.join(JSONS_DIR, "calendar_lastseen.json")
DRIVER_FILE = os.path.join(JSONS_DIR, "driver.json")
OUTPUT_FILE = os.path.join(JSONS_DIR, "master.json")

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # Load all JSONs
    products = load_json(PRODUCT_FILE, [])
    resale = load_json(RESALE_FILE, [])
    history = load_json(HISTORY_FILE, {})
    calendar = load_json(CALENDAR_FILE, {})
    driver = load_json(DRIVER_FILE, {})

    # Convert resale list -> dict keyed by id
    resale_map = {str(item["id"]): item for item in resale}
    # history.json already dict keyed by id
    # calendar_lastseen.json assumed dict keyed by id

    master_data = []

    for product in products:
        pid = str(product["id"])
        resale_info = resale_map.get(pid, {})
        history_info = history.get(pid, {})
        calendar_info = calendar.get(pid, {})

        consolidated = {
            "id": product["id"],
            "itemname": product.get("itemname"),
            "purchase_price": product.get("price"),
            "purchase_date": product.get("purchase_date"),
            "price_range": resale_info.get("price_range"),
            "confidence": resale_info.get("confidence"),
            "chrome_browsing_matched_url_history": history_info.get("matched_queries", None),
            "calender_last_matched": calendar_info.get("last_mentioned", None)
        }

        master_data.append(consolidated)

    # Add driver history at the end of the JSON
    output = {
        "products": master_data,
        "driver_history_from_pc": driver
    }

    # Save to master.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Master JSON created at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
