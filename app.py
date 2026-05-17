import os
import requests
from flask import Flask, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WORKSPACE = "3D7DF166862E102CF9F8267EBF57EF45"
AGENT_ID  = "3F336FF8479AC092E19EB6E2FF34077D"

# Possíveis bases de URL da API GPTMaker
API_BASES = [
    "https://app.gptmaker.ai/v2",
    "https://api.gptmaker.ai/v2",
    "https://app.gptmaker.ai/api/v2",
]


def auth_headers():
    token = os.environ.get("GPTMAKER_TOKEN", "")
    return {"Authorization": f"Bearer {token}"}


def find_chats():
    """Tenta vários endpoints até obter os chats com sucesso."""
    h = auth_headers()
    url_patterns = [
        ("{base}/workspace/{ws}/chats", {}),
        ("{base}/chat", {"workspaceId": WORKSPACE}),
        ("{base}/chats", {"workspaceId": WORKSPACE}),
    ]
    for base in API_BASES:
        for pattern, params in url_patterns:
            url = pattern.format(base=base, ws=WORKSPACE)
            try:
                r = requests.get(url, params=params, headers=h, timeout=8)
                if r.ok:
                    data = r.json()
                    if isinstance(data, list):
                        return data, url
                    if isinstance(data, dict) and "data" in data:
                        return data["data"], url
            except Exception:
                continue
    return None, None


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/logo_tomagaleads.png")
def logo():
    return send_from_directory(".", "logo_tomagaleads.png")


@app.route("/debug")
def debug():
    """Endpoint de diagnóstico — remove depois do evento."""
    h = auth_headers()
    token = h["Authorization"].replace("Bearer ", "")
    results = {"token_set": bool(token.strip()), "attempts": []}

    for base in API_BASES:
        url = f"{base}/workspace/{WORKSPACE}/chats"
        try:
            r = requests.get(url, headers=h, timeout=5)
            results["attempts"].append({"url": url, "status": r.status_code})
        except Exception as e:
            results["attempts"].append({"url": url, "error": str(e)})

    return jsonify(results)


@app.route("/reset", methods=["GET", "POST"])
def reset():
    h = auth_headers()
    token = h["Authorization"].replace("Bearer ", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "GPTMAKER_TOKEN not set"}), 500

    chats, working_url = find_chats()
    if chats is None:
        return jsonify({"ok": False, "error": "Could not reach GPTMaker API"}), 502

    # Filtrar chats WIDGET da filIPPa
    widget_chats = [
        c for c in chats
        if c.get("agentId") == AGENT_ID and c.get("type") == "WIDGET"
    ]

    if not widget_chats:
        return jsonify({"ok": True, "message": "no widget chat found"})

    # Mais recente
    widget_chats.sort(key=lambda x: x.get("time", 0), reverse=True)
    chat_id = widget_chats[0]["id"]

    # Extrair base da URL que funcionou
    base = working_url.split("/workspace")[0].split("/chat")[0]
    delete_url = f"{base}/chat/{chat_id}/messages"

    d = requests.delete(delete_url, headers=h, timeout=10)
    return jsonify({"ok": d.ok, "chatId": chat_id, "deleteStatus": d.status_code, "apiBase": base})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
