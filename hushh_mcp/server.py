from flask import request, jsonify
from hushh_mcp.cli.authenticate_user import grant_consent_flow, revoke_consent, ConsentScope, CONSENT_TOKEN_PATH, DEFAULT_CONSENT_TOKEN_EXPIRY_MS, issue_token
import json
import os
from flask import Flask, request, jsonify, send_from_directory, Response, redirect, session, url_for
from flask_cors import CORS
import os, json, threading, datetime, time
from hushh_mcp.vault.json_vault import load_encrypted_json, save_encrypted_json
import pythoncom
import wmi
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')


# Consent status endpoint
@app.route('/consent/status', methods=['GET'])
def consent_status():
    if not os.path.exists(CONSENT_TOKEN_PATH):
        return jsonify({
            "gmail": False,
            "calendar": False,
            "browser_history": False,
            "driver": False
        })
    with open(CONSENT_TOKEN_PATH) as f:
        data = json.load(f)
    return jsonify({
        "gmail": str(ConsentScope.FETCH_EMAIL) in data,
        "calendar": str(ConsentScope.FETCH_CALENDAR) in data,
        "browser_history": str(ConsentScope.FETCH_BROWSER_HISTORY) in data,
        "driver": str(ConsentScope.FETCH_DRIVER) in data
    })

# Generate consent token endpoint
@app.route('/consent/generate-token', methods=['POST'])
def generate_consent_token():
    req = request.get_json()
    token_type = req.get('type')
    # For demo, use a fixed user_id; in production, get from session
    user_id = 'demo_user'  # Replace with session user
    agent_map = {
        'gmail': (ConsentScope.FETCH_EMAIL, 'gmail_reader_agent'),
        'calendar': (ConsentScope.FETCH_CALENDAR, 'calendar_reader_agent'),
        'browser_history': (ConsentScope.FETCH_BROWSER_HISTORY, 'history_agent'),
        'driver': (ConsentScope.FETCH_DRIVER, 'driver_agent')
    }
    if token_type not in agent_map:
        return jsonify({"error": "Invalid type"}), 400
    scope, agent_id = agent_map[token_type]
    token = issue_token(user_id=user_id, agent_id=agent_id, scope=scope, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
    if os.path.exists(CONSENT_TOKEN_PATH):
        with open(CONSENT_TOKEN_PATH) as f:
            existing = json.load(f)
    else:
        existing = {}
    existing[str(scope)] = token.dict()
    with open(CONSENT_TOKEN_PATH, "w") as f:
        json.dump(existing, f, indent=2)
    return jsonify({"success": True})

# Revoke consent token endpoint
@app.route('/consent/revoke-token', methods=['POST'])
def revoke_consent_token():
    req = request.get_json()
    token_type = req.get('type')
    agent_map = {
        'gmail': ConsentScope.FETCH_EMAIL,
        'calendar': ConsentScope.FETCH_CALENDAR,
        'browser_history': ConsentScope.FETCH_BROWSER_HISTORY,
        'driver': ConsentScope.FETCH_DRIVER
    }
    if token_type not in agent_map:
        return jsonify({"error": "Invalid type"}), 400
    scope = agent_map[token_type]
    revoke_consent(scope)
    return jsonify({"success": True})


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# Products API endpoints
@app.route("/products", methods=["GET"])
def get_products():
    try:
        data = load_encrypted_json(os.path.join(JSONS_DIR, "usage.json"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Logout endpoint
@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/auth/google')
def auth_google():
    flow = Flow.from_client_secrets_file(
        'hushh_mcp/credentials.json',
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/auth/google/callback')
def auth_google_callback():
    import threading
    import subprocess

    def run_agent_pipeline():
        agent_cmds = [
            ["python", "-m", "hushh_mcp.agents.gmail_reader_agent"],
            ["python", "-m", "hushh_mcp.agents.receipt_agent"],
            ["python", "-m", "hushh_mcp.agents.context_agent"],
            ["python", "-m", "hushh_mcp.agents.cost_agent"],
            ["python", "-m", "hushh_mcp.agents.calender_reader_agent"],
            ["python", "-m", "hushh_mcp.agents.aggregator_agent"],
            ["python", "-m", "hushh_mcp.agents.usage_agent"]
        ]
        for cmd in agent_cmds:
            agent_name = cmd[-1].split(".")[-1]
            print(f"Running agent: {agent_name}")
            try:
                # Wait for each agent to finish before starting the next
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"{agent_name} completed successfully.")
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"{agent_name} failed. Stopping pipeline.")
                print(e.stdout)
                print(e.stderr)
                break

    state = session.get('state')
    flow = Flow.from_client_secrets_file(
        'hushh_mcp/credentials.json',
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=state
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    # Save credentials to token.json for later use (restoring previous behavior)
    with open("token.json", "w") as token_file:
        token_file.write(credentials.to_json())

    request_session = google_requests.Request()
    id_info = id_token.verify_oauth2_token(
        credentials._id_token,
        request_session,
        GOOGLE_CLIENT_ID
    )
    # Store user info in session
    session['user'] = {
        'email': id_info.get('email'),
        'name': id_info.get('name'),
        'picture': id_info.get('picture')
    }

    # Auto-grant consent tokens for mail, calendar, browser, driver
    user_id = id_info.get('email') or 'demo_user'
    from hushh_mcp.constants import ConsentScope, CONSENT_TOKEN_PATH, DEFAULT_CONSENT_TOKEN_EXPIRY_MS
    from hushh_mcp.cli.authenticate_user import issue_token
    agent_map = {
        'gmail_reader_agent': ConsentScope.FETCH_EMAIL,
        'calendar_reader_agent': ConsentScope.FETCH_CALENDAR,
        'history_agent': ConsentScope.FETCH_BROWSER_HISTORY,
        'driver_agent': ConsentScope.FETCH_DRIVER
    }
    if os.path.exists(CONSENT_TOKEN_PATH):
        with open(CONSENT_TOKEN_PATH) as f:
            existing = json.load(f)
    else:
        existing = {}
    for agent_id, scope in agent_map.items():
        token = issue_token(user_id=user_id, agent_id=agent_id, scope=scope, expires_in_ms=DEFAULT_CONSENT_TOKEN_EXPIRY_MS)
        existing[str(scope)] = token.dict()
    with open(CONSENT_TOKEN_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    # Only run agent pipeline if usage.json does not exist
    usage_path = os.path.join(JSONS_DIR, "usage.json")
    if not os.path.exists(usage_path):
        threading.Thread(target=run_agent_pipeline, daemon=True).start()

    # Schedule pipeline to run every 7 days automatically
    def schedule_pipeline():
        import time
        while True:
            try:
                # Only run pipeline if usage.json does not exist
                if not os.path.exists(usage_path):
                    threading.Thread(target=run_agent_pipeline, daemon=True).start()
            except Exception as e:
                print("Scheduled pipeline error:", e)
            time.sleep(7 * 24 * 60 * 60)  # 7 days in seconds

    # Start scheduler thread only once (on first login)
    if not hasattr(app, "_pipeline_scheduler_started"):
        app._pipeline_scheduler_started = True
        threading.Thread(target=schedule_pipeline, daemon=True).start()

    # Redirect to frontend (adjust URL as needed)
    return redirect('http://localhost:8080/')

@app.route('/auth/user')
def get_authenticated_user():
    user = session.get('user')
    if user:
        return jsonify(user)
    return jsonify({'error': 'Not authenticated'}), 401

@app.route("/products/update-status", methods=["POST"])
def update_product_status():
    req = request.get_json()
    id = req.get("id")
    new_status = req.get("newStatus")
    if id is None or new_status is None:
        return jsonify({"error": "Missing id or newStatus"}), 400
    try:
        data = load_encrypted_json(os.path.join(JSONS_DIR, "usage.json"))
        products = data.get("products", [])
        idx = next((i for i, p in enumerate(products) if p.get("id") == id), None)
        if idx is None:
            return jsonify({"error": "Product not found"}), 404
        products[idx]["status"] = new_status
        data["products"] = products
        save_encrypted_json(data, os.path.join(JSONS_DIR, "usage.json"))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
  # allow Chrome extension to connect

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
    # Consent enforcement for browser history
    if not os.path.exists(CONSENT_TOKEN_PATH):
        save_encrypted_json(None, OUTPUT_FILE)
        return jsonify({"status": "no consent", "saved_to": OUTPUT_FILE})
    with open(CONSENT_TOKEN_PATH) as f:
        data = json.load(f)
    if str(ConsentScope.FETCH_BROWSER_HISTORY) not in data:
        save_encrypted_json(None, OUTPUT_FILE)
        return jsonify({"status": "no consent", "saved_to": OUTPUT_FILE})

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
            if driver_log is None:
                driver_log = {}
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
            # Consent enforcement for driver logging
            if not os.path.exists(CONSENT_TOKEN_PATH):
                save_encrypted_json(None, DRIVER_FILE)
                time.sleep(5)
                continue
            with open(CONSENT_TOKEN_PATH) as f:
                data = json.load(f)
            if str(ConsentScope.FETCH_DRIVER) not in data:
                save_encrypted_json(None, DRIVER_FILE)
                time.sleep(5)
                continue

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
