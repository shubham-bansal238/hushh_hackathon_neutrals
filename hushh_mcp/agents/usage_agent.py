import os
import json
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
INPUT_FILE = os.path.join(JSONS_DIR, "master.json")   # Input file
OUTPUT_FILE = os.path.join(JSONS_DIR, "usage.json")   # Output file

def build_prompt(product, driver_history):
    return f"""
You are a Product Usage and Resale Candidate Detection Agent.

For the given product, decide if its current status is one of:
- **in_use** → The product is clearly still in active daily use.  
- **resell_candidate** → The product is old, has issues, shows signs of repair/fixing, is unused for a long time, or has no strong signals of active use. Even if it is faulty or broken, consider it a resale candidate.  
- **uncertain** → When there is not enough evidence to decide confidently whether it is actively in use or a resale candidate.  

Rules:
- If there is **recent driver activity**, assume the product is actively in use.  
- If browsing history or calendar mentions the product with **repair/fixing keywords**, mark it as a **resell_candidate**.  
- If the product is old (several years), has no recent usage signals, or is lower-value but still functional, classify as **resell_candidate**.  
- If no clear evidence exists and the product is not very old, classify as **uncertain**.  
- Always favor practical resale logic (in Indian market context, even faulty items are resold with “needs fixing” tags).  

Return ONLY JSON in this format:
{{
  "id": "{product.get('id')}",
  "status": "in_use|resell_candidate|uncertain"
}}

Do not write anything else.

Product:
{json.dumps(product, indent=2)}

Driver history:
{json.dumps(driver_history, indent=2)}
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
    # Load master.json
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    products = master_data.get("products", [])
    driver_history = master_data.get("driver_history_from_pc", {})

    results = []

    for product in tqdm(products, desc="Checking product usage"):
        prompt = build_prompt(product, driver_history)
        response_text = call_gemini(prompt)

        if not response_text:
            print(f"⚠️ No response for: {product.get('itemname')}")
            product["status"] = "uncertain"
            results.append(product)
            continue

        parsed = extract_json(response_text)
        if parsed and "status" in parsed:
            product["status"] = parsed["status"]
        else:
            print(f"❌ Failed to parse JSON for: {product.get('itemname')}")
            print("Raw response:", response_text)
            product["status"] = "uncertain"

        results.append(product)

    # Keep driver_history_from_pc unchanged
    final_output = {
        "products": results,
        "driver_history_from_pc": driver_history
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Finished. Results written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
