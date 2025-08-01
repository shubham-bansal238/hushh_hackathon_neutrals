from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os, json, threading, datetime, time
from hushh_mcp.vault.json_vault import load_encrypted_json
from hushh_mcp.vault.json_vault import save_encrypted_json, load_encrypted_json

# Windows-specific imports
import pythoncom
import wmi

app = Flask(__name__)
CORS(app)  # allow Chrome extension to connect

JSONS_DIR = os.path.join(os.path.dirname(__file__), "jsons")
OUTPUT_FILE = os.path.join(JSONS_DIR, "history.json")
INPUT_FILE = os.path.join(JSONS_DIR, "context.json")
DRIVER_FILE = os.path.join(JSONS_DIR, "driver.json")
MASTER_DIR = os.path.join(JSONS_DIR, "usage.json")

@app.route("/context.json", methods=["GET"])
def get_context():
    try:
        data = load_encrypted_json(INPUT_FILE)
        return Response(json.dumps(data), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/usage.json", methods=["GET"])
def get_usage():
    try:
        data = load_encrypted_json(MASTER_DIR)
        return Response(json.dumps(data), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/save-history", methods=["POST"])
def save_history():
    new_data = request.json
    if not new_data:
        return jsonify({"error": "No data received"}), 400

    os.makedirs(JSONS_DIR, exist_ok=True)

    # Load existing history
    if os.path.exists(OUTPUT_FILE):
        try:
            history = load_encrypted_json(OUTPUT_FILE)
        except Exception:
            history = {}
    else:
        history = {}

    # Append new matches
    for pid, entry in new_data.items():
        if pid not in history:
            history[pid] = {"id": pid, "matched_queries": []}
        history[pid]["matched_queries"].extend(entry["matched_queries"])

    # Save back
    save_encrypted_json(history, OUTPUT_FILE)

    return jsonify({"status": "ok", "saved_to": OUTPUT_FILE})

# === Driver Monitor ===
def driver_monitor():
    pythoncom.CoInitialize()
    c = wmi.WMI()

    os.makedirs(JSONS_DIR, exist_ok=True)

    # Load existing driver log
    if os.path.exists(DRIVER_FILE):
        try:
            driver_log = load_encrypted_json(DRIVER_FILE)
        except Exception:
            driver_log = {}
    else:
        driver_log = {}

    watcher = c.watch_for(
        notification_type="Creation",
        wmi_class="Win32_PnPEntity"
    )

    print("📡 Driver monitor started (Windows only)")

    while True:
        try:
            device = watcher()
            name = device.Name or "Unknown Device"
            now = datetime.datetime.now().strftime("%d/%m/%Y")

            driver_log[name] = now

            save_encrypted_json(driver_log, DRIVER_FILE)

            print(f"✅ Driver activated: {name} on {now}")
        except Exception as e:
            print("❌ Driver watcher error:", e)
            time.sleep(5)

# Start driver monitoring in background
threading.Thread(target=driver_monitor, daemon=True).start()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
