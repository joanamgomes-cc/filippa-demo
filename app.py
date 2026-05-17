import os
import requests
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_BASE  = "https://api.gptmaker.ai/v2"
WORKSPACE = "3D7DF166862E102CF9F8267EBF57EF45"
AGENT_ID  = "3F3420317413E0DB63473ECAA4960D4B"


def auth_headers():
    token = os.environ.get("GPTMAKER_TOKEN", "")
    return {"Authorization": f"Bearer {token}"}


def get_latest_widget_chat():
    h = auth_headers()
    r = requests.get(f"{API_BASE}/workspace/{WORKSPACE}/chats", headers=h, timeout=10)
    if not r.ok:
        return None
    chats = r.json()
    widget_chats = [
        c for c in chats
        if c.get("agentId") == AGENT_ID and c.get("type") == "WIDGET"
    ]
    if not widget_chats:
        return None
    widget_chats.sort(key=lambda x: x.get("time", 0), reverse=True)
    return widget_chats[0]["id"]


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/logo_tomagaleads.png")
def logo():
    return send_from_directory(".", "logo_tomagaleads.png")


@app.route("/reset", methods=["GET", "POST"])
def reset():
    h = auth_headers()
    if not h["Authorization"].replace("Bearer ", "").strip():
        return jsonify({"ok": False, "error": "GPTMAKER_TOKEN not set"}), 500

    chat_id = get_latest_widget_chat()
    if not chat_id:
        return jsonify({"ok": True, "message": "no widget chat found"})

    d = requests.delete(f"{API_BASE}/chat/{chat_id}/messages", headers=h, timeout=10)
    return jsonify({"ok": d.ok, "chatId": chat_id, "status": d.status_code})


@app.route("/send", methods=["POST"])
def send():
    h = auth_headers()
    if not h["Authorization"].replace("Bearer ", "").strip():
        return jsonify({"ok": False, "error": "GPTMAKER_TOKEN not set"}), 500

    body = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "no message provided"}), 400

    chat_id = get_latest_widget_chat()
    if not chat_id:
        return jsonify({"ok": False, "error": "no active widget chat"}), 404

    r = requests.post(
        f"{API_BASE}/chat/{chat_id}/send-message",
        headers={**h, "Content-Type": "application/json"},
        json={"message": message},
        timeout=10,
    )
    return jsonify({"ok": r.ok, "chatId": chat_id, "status": r.status_code})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
