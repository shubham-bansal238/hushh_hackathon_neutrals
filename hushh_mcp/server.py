from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json

app = Flask(__name__)
CORS(app)  # allow Chrome extension to connect

JSONS_DIR = os.path.join(os.path.dirname(__file__), "jsons")
OUTPUT_FILE = os.path.join(JSONS_DIR, "history.json")
INPUT_FILE = os.path.join(JSONS_DIR, "groq_output.json")

@app.route("/groq_output.json", methods=["GET"])
def get_groq_output():
    return send_from_directory(JSONS_DIR, "groq_output.json")

@app.route("/save-history", methods=["POST"])
def save_history():
    new_data = request.json
    if not new_data:
        return jsonify({"error": "No data received"}), 400

    os.makedirs(JSONS_DIR, exist_ok=True)

    # Load existing history
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    # Append new matches
    for pid, entry in new_data.items():
        if pid not in history:
            history[pid] = {"id": pid, "matched_queries": []}
        history[pid]["matched_queries"].extend(entry["matched_queries"])

    # Save back
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return jsonify({"status": "ok", "saved_to": OUTPUT_FILE})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
