import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

# File paths
JSONS_DIR = os.path.join(os.path.dirname(__file__), "../jsons")
INPUT_PATH = os.path.join(JSONS_DIR, "relevant_emails.json")
OUTPUT_PATH = os.path.join(JSONS_DIR, "productdetail.json")

# Platform detection keywords
PLATFORM_KEYWORDS = {
    "amazon": ["amazon.in", "amazon"],
    "croma": ["croma.com", "croma"]
}

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

def extract_amazon_data(email):
    body = clean_text(email["body"])
    subject = email.get("subject", "")
    date = format_date(email["date"])
    platform = "amazon"
    results = []

    # Modern format: bullet points with item, quantity, price
    def modern_regex(body):
        return re.findall(r"\*\s+(.+?)\s+Quantity:?[ ]*\d+\s+([\d,.]+)\s*INR", body)

    # Legacy format: bullet points with item, quantity, price separated
    def legacy_regex(body):
        items = re.findall(r"\*\s+(.+?)\s+Quantity", body)
        prices = re.findall(r"Quantity: ?\d+\s+([\d,.]+)\s*INR", body)
        return list(zip(items, prices)) if items and prices and len(items) == len(prices) else []

    # Shipment details: lines after 'Your Shipment Details'
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

    # Order summary: fallback for some summary emails
    def order_summary_regex(body):
        m = re.search(r"Order summary Item Subtotal: Rs\.([\d,.]+)", body)
        if m:
            return [(None, m.group(1))]
        return []

    # Subject fallback
    def subject_fallback(subject, body):
        match = re.search(r"Shipped: [\"“”']?(.+?)[\"“”']", subject)
        item = match.group(1).strip() if match else None
        price = extract_price(body)
        if item and price:
            return [(item, str(price))]
        return []

    # Try all strategies in order
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

    # If still nothing, try subject fallback
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

    # If still nothing, try to extract any price and use subject or fallback
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

    # If still nothing, fallback to a generic but non-null entry
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
    # Try to extract all items and prices from invoice format
    # Look for lines like: Item Description ... Qty. Rate Amount
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
        # Try fallback: Total Amount Paid
        m = re.search(r"Total Amount Paid: ([\d,.]+)", body)
        if m:
            price = int(float(m.group(1).replace(",", "")))
            results.append({
                "itemname": None,
                "price": price,
                "purchase_date": date,
                "platform": platform
            })
    # If still nothing, skip this email (do not add nulls)
    return results

    # For generic, skip (do not add nulls)
    return []

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

    # Remove duplicates: same itemname, price, purchase_date, platform
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

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_products, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
