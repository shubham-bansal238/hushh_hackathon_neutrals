import os
import json
import json
from hushh_mcp.vault.json_vault import load_encrypted_json, save_encrypted_json
import time
from dotenv import load_dotenv
from tqdm import tqdm
from groq import Groq

# Load API key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set in environment")

# Initialize Groq client
client = Groq(api_key=api_key)

# Model choice
MODEL = "llama3-70b-8192"

# Paths
JSONS_DIR = os.path.join(os.path.dirname(__file__), "../jsons")
INPUT_FILE = os.path.join(JSONS_DIR, "productdetail.json")
OUTPUT_FILE = os.path.join(JSONS_DIR, "context.json")

def build_prompt(product):
    return f"""Given this item metadata:
{{
  "id": {product['id']},
  "price": "{product['price']}",
  "item": "{product['itemname']}",
  "purchase_date": "{product['purchase_date']}"
}}

Generate:
1. A canonical product name
2. A list of aliases and common names this product might be referred to as
3. A list of usage context keywords — verbs, tasks, related software that indicate how people commonly use this item

Output strictly in JSON format with keys:
id, price, canonical_name, aliases, context_keywords
DONT WRITE ANYTHING ELSE OTHER THAN THE JSON. I ONLY WANT JSON AS YOUR OUTPUT.
"""

def call_groq(prompt):
    return client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        temperature=0.3,
    )

def main():
    items = load_encrypted_json(INPUT_FILE)


    output = []
    for product in tqdm(items, desc="Processing items"):
        prompt = build_prompt(product)
        response = call_groq(prompt)

        # response.choices[0].message.content should be valid JSON
        raw = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(raw)
            output.append(parsed)
        except json.JSONDecodeError:
            print(f"❌ Failed to parse product ID {product['id']}:")
            print(raw)
            continue

    save_encrypted_json(output, OUTPUT_FILE)

    print(f"\n✅ Output written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
