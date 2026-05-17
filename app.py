import os
import requests
from flask import Flask, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_BASE  = "https://app.gptmaker.ai/v2"
WORKSPACE = "3D7DF166862E102CF9F8267EBF57EF45"
AGENT_ID  = "3F336FF8479AC092E19EB6E2FF34077D"


def auth_headers():
    token = os.environ.get("GPTMAKER_TOKEN", "")
    return {"Authorization": f"Bearer {token}"}


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/logo_tomagaleads.png")
def logo():
    return send_from_directory(".", "logo_tomagaleads.png")


@app.route("/reset", methods=["GET", "POST"])
def reset():
    h = auth_headers()
    token = h["Authorization"].replace("Bearer ", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "GPTMAKER_TOKEN not set"}), 500

    # Listar chats ativos do widget da filIPPa
    r = requests.get(
        f"{API_BASE}/chat",
        params={"workspaceId": WORKSPACE},
        headers=h,
        timeout=10,
    )
    if not r.ok:
        return jsonify({"ok": False, "error": f"GPTMaker API error: {r.status_code}"}), 502

    chats = r.json()
    active = [
        c for c in chats
        if c.get("agentId") == AGENT_ID
        and c.get("type") == "WIDGET"
        and not c.get("finished")
    ]

    if not active:
        return jsonify({"ok": True, "message": "no active chat to reset"})

    # Chat mais recente
    active.sort(key=lambda x: x.get("time", 0), reverse=True)
    chat_id = active[0]["id"]

    # Apagar todas as mensagens (mantém o chat, limpa o histórico)
    d = requests.delete(
        f"{API_BASE}/chat/{chat_id}/messages",
        headers=h,
        timeout=10,
    )

    return jsonify({"ok": d.ok, "chatId": chat_id, "status": d.status_code})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
