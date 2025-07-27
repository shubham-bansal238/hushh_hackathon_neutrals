import os
import json
import uuid
import re
from tqdm import tqdm
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in environment")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Paths
BASE_DIR = os.path.dirname(__file__)
JSONS_DIR = os.path.join(BASE_DIR, "../jsons")
INPUT_FILE = os.path.join(JSONS_DIR, "sampledataforcost.json")
OUTPUT_FILE = os.path.join(JSONS_DIR, "value_of_product.json")

def build_prompt(product):
    return f"""
You are a resale valuation assistant for the Indian market (OLX, Cashify, Quikr, etc.) as of July 26, 2025.

Estimate a **realistic and conservative** price range for this second-hand product in INR. Use the product's name, original price, purchase date, and platform.

Guidelines:
- Indian electronics depreciate fast: steep drop in 1–3 years, flattening near 5+ years.
- Older items = more wear. Assume normal usage.
- Brand matters: flagships retain value better than mid-range.
- Prices on classifieds are lower than trade-in platforms.
- Avoid overpricing. Lean towards the lower safe bracket.
- Output must include: **price_range**, **confidence** ("high", "medium", or "low"), and **one-line reasoning**.
- Confidence depends on demand: low demand = low confidence, etc.

reasoning should be just one liner. and the output you will give me should be just in JSON, NOTHING ELSE. I WANT JUST THE JSON  
TODAY IS JULY 26, 2025. AND HAVE EMPHASIS ON THE INDIAN MARKET AND THE PURCHASE DATE FOR THE VALUE.  
ONLY return JSON in this format:  
{{
  "id": "{str(uuid.uuid4())[:12]}",
  "itemname": "{product['itemname']}",
  "price_range": "X to Y INR",
  "confidence": "high|medium|low",
  "reasoning": "one-line explanation"
}}  
Do not write anything else.  
Input product:  
{json.dumps(product, indent=2)}  
Overpricing leads to incorrect appraisals. Prioritize underpricing to avoid user dissatisfaction  
Pricing above this leads to unsold listings and user loss. Therefore, I choose the lowest safe bracket.  
less premium brand devices depreciate faster than premium ones. (specially in phone,headphone category)
"""

def extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]+?\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None

def call_gemini(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("❌ Gemini API call failed:", str(e))
        return None

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    if isinstance(products, dict):
        products = [products]

    output = []

    for product in tqdm(products, desc="Valuing products"):
        prompt = build_prompt(product)
        response_text = call_gemini(prompt)

        if not response_text:
            print(f"⚠️ No response for: {product['itemname']}")
            continue

        parsed = extract_json(response_text)
        if parsed:
            output.append(parsed)
        else:
            print(f"❌ Failed to parse JSON for: {product['itemname']}")
            print("Raw response:", response_text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Finished. {len(output)} valuations written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
