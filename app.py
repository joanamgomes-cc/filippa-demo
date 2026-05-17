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

    # Listar todos os chats WIDGET da filIPPa (endpoint correto)
    r = requests.get(
        f"{API_BASE}/workspace/{WORKSPACE}/chats",
        headers=h,
        timeout=10,
    )
    if not r.ok:
        return jsonify({"ok": False, "error": f"GPTMaker API error: {r.status_code}"}), 502

    chats = r.json()

    # Filtrar chats do widget da filIPPa (sem filtro de finished — apagar o mais recente)
    widget_chats = [
        c for c in chats
        if c.get("agentId") == AGENT_ID
        and c.get("type") == "WIDGET"
    ]

    if not widget_chats:
        return jsonify({"ok": True, "message": "no widget chat found"})

    # Chat mais recente pelo timestamp
    widget_chats.sort(key=lambda x: x.get("time", 0), reverse=True)
    chat_id = widget_chats[0]["id"]

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
