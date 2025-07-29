import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# ------------------ CONFIG ------------------
JSONS_DIR = os.path.join(os.path.dirname(__file__), "../jsons")
INPUT_PATH = os.path.join(JSONS_DIR, "relevant_emails.json")
OUTPUT_PATH = os.path.join(JSONS_DIR, "productdetail.json")

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in environment")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------ PLATFORM DETECTION ------------------
PLATFORM_KEYWORDS = {
    "amazon": ["amazon.in", "amazon"],
    "croma": ["croma.com", "croma"]
}

# ------------------ HELPERS ------------------
def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()

def format_date(date_str):
    try:
        return datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return None

def detect_platform(email):
    sender = email.get("from", "").lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        if any(kw in sender for kw in keywords):
            return platform
    return None

def extract_price(text):
    patterns = [
        r"Total\s+([\d,]+)\s+INR",
        r"Rs\.?\s?([\d,]+(?:\.\d{2})?)",
        r"₹\s?([\d,]+(?:\.\d{2})?)",
        r"Total Amount Paid: ([\d,]+\.\d{2})"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(float(match.group(1).replace(",", "")))
    return None

# ------------------ AMAZON & CROMA EXTRACTORS ------------------
def extract_amazon_data(email):
    body = clean_text(email["body"])
    subject = email.get("subject", "")
    date = format_date(email["date"])
    platform = "amazon"
    results = []

    def modern_regex(body):
        return re.findall(r"\*\s+(.+?)\s+Quantity:?[ ]*\d+\s+([\d,.]+)\s*INR", body)

    def legacy_regex(body):
        items = re.findall(r"\*\s+(.+?)\s+Quantity", body)
        prices = re.findall(r"Quantity: ?\d+\s+([\d,.]+)\s*INR", body)
        return list(zip(items, prices)) if items and prices and len(items) == len(prices) else []

    def shipment_details_regex(body):
        if "Your Shipment Details" in body:
            section = body.split("Your Shipment Details", 1)[1]
            lines = [l.strip() for l in section.splitlines() if l.strip() and not l.lower().startswith("http")]
            found = []
            for line in lines:
                m = re.match(r"(.+?)\s+Rs\.?\s?([\d,.]+)", line)
                if m:
                    found.append(m.groups())
            return found
        return []

    def order_summary_regex(body):
        m = re.search(r"Order summary Item Subtotal: Rs\.([\d,.]+)", body)
        if m:
            return [(None, m.group(1))]
        return []

    def subject_fallback(subject, body):
        match = re.search(r"Shipped: [\"“”']?(.+?)[\"“”']", subject)
        item = match.group(1).strip() if match else None
        price = extract_price(body)
        if item and price:
            return [(item, str(price))]
        return []

    strategies = [modern_regex, legacy_regex, shipment_details_regex, order_summary_regex]
    for strat in strategies:
        found = strat(body)
        for item, price in found:
            if item is not None and price:
                try:
                    price_val = int(float(price.replace(",", "")))
                except Exception:
                    price_val = None
                results.append({
                    "itemname": item.strip() if item else None,
                    "price": price_val,
                    "purchase_date": date,
                    "platform": platform
                })
        if results:
            break

    if not results:
        found = subject_fallback(subject, body)
        for item, price in found:
            try:
                price_val = int(float(price.replace(",", "")))
            except Exception:
                price_val = None
            results.append({
                "itemname": item.strip() if item else None,
                "price": price_val,
                "purchase_date": date,
                "platform": platform
            })

    if not results:
        price = extract_price(body)
        item = subject or body[:50]
        if price:
            results.append({
                "itemname": item.strip() if item else None,
                "price": price,
                "purchase_date": date,
                "platform": platform
            })

    if not results:
        results.append({
            "itemname": subject or "Unknown Product",
            "price": 0,
            "purchase_date": date,
            "platform": platform
        })
    return results

def extract_croma_data(email):
    body = clean_text(email["body"])
    date = format_date(email["date"])
    platform = "croma"
    results = []

    invoice_items = re.findall(r"Item Description\s*Tax Code\s*Qty\.\s*Rate\s*Amount\s*(\d+)\s+(.+?)\s+\S+\s+(\d+\.\d+)\s+(\d+\.\d+)", body, re.DOTALL)
    if invoice_items:
        for qty, item, rate, amount in invoice_items:
            results.append({
                "itemname": item.strip(),
                "price": int(float(amount)),
                "purchase_date": date,
                "platform": platform
            })
    else:
        m = re.search(r"Total Amount Paid: ([\d,.]+)", body)
        if m:
            price = int(float(m.group(1).replace(",", "")))
            results.append({
                "itemname": None,
                "price": price,
                "purchase_date": date,
                "platform": platform
            })
    return results

# ------------------ MAIN LOGIC ------------------
def parse_email(email):
    platform = detect_platform(email)
    if platform == "amazon":
        return extract_amazon_data(email)
    elif platform == "croma":
        return extract_croma_data(email)
    else:
        return []

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        emails = json.load(f)

    all_products = []
    for email in emails:
        parsed = parse_email(email)
        all_products.extend(parsed)

    # Deduplicate
    seen = set()
    unique_products = []
    for prod in all_products:
        key = (
            prod.get("itemname"),
            prod.get("price"),
            prod.get("purchase_date"),
            prod.get("platform")
        )
        if key not in seen:
            seen.add(key)
            unique_products.append(prod)

    # ------------------ PROMPT FOR GEMINI ------------------
    prompt = f"""
You will be provided with a JSON array of purchase data. Each object in the array represents an item with details such as "itemname", "price", "purchase_date", and "platform".

Your task is to identify and return ONLY the items from this list that are electronic devices or require electricity to function. This explicitly includes items that:
* Plug into an electrical outlet.
* Are powered by internal batteries (rechargeable or disposable).
* Are components essential for an electronic device to operate

Exclude items that are:
* Protective covers or cases for electronic devices (e.g., phone cases).
* Non-electronic accessories or tools, even if they are used with electronic devices. charger cables, adapters, or connectors
* Books, clothing, or food items.

Return the identified items as a JSON array, and nothing else.
ONLY JSON format is acceptable.
Do not include any additional text or explanations. not even ```json or ``` at the start or end.

Here is the purchase data:
{json.dumps(unique_products, indent=2, ensure_ascii=False)}
"""

    # Send to Gemini
    response = model.generate_content(prompt)
    gemini_result = response.text.strip()

    # Parse Gemini response to Python list
    try:
        filtered_items = json.loads(gemini_result)
    except json.JSONDecodeError:
        raise ValueError("Gemini did not return valid JSON")

    # Add IDs AFTER filtering
    final_with_ids = []
    for idx, prod in enumerate(filtered_items, start=1):
        ordered_prod = {
            "id": idx,
            "itemname": prod.get("itemname"),
            "price": prod.get("price"),
            "purchase_date": prod.get("purchase_date"),
            "platform": prod.get("platform")
        }
        final_with_ids.append(ordered_prod)

    # Save final result
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_with_ids, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
