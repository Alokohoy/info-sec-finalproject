import os

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import db

app = Flask(__name__)

_cors = os.getenv(
    "SOCKETIO_CORS_ALLOWED_ORIGINS",
    "http://localhost:5001,http://127.0.0.1:5001,http://localhost:8080,http://127.0.0.1:8080",
)
socketio = SocketIO(
    app,
    cors_allowed_origins=[o.strip() for o in _cors.split(",") if o.strip()],
)

db.init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/history")
def history():
    return jsonify(db.latest_messages()[::-1])


@app.route("/clear", methods=["POST"])
def clear_history():
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token:
        presented = (
            request.headers.get("X-Admin-Token")
            or request.args.get("token")
            or (request.get_json(silent=True) or {}).get("token")
        )
        if presented != admin_token:
            return jsonify({"error": "forbidden"}), 403
    db.clear_messages()
    return ("", 204)


@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json(force=True, silent=True) or {}

    username = data.get("username", "API_User")
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text field is required"}), 400

    if len(text) > 500:
        return jsonify({"error": "text too long"}), 400

    db.save_message(username, text)
    socketio.emit("chat", {"username": username, "text": text})

    return jsonify({"status": "ok"}), 201



@socketio.on("newuser")
def on_newuser(username):
    socketio.emit("update", f"{username} joined")


@socketio.on("chat")
def on_chat(data):
    username = data.get("username", "Anonymous")
    text = data.get("text", "")

    if not text.strip():
        return

    if len(text) > 500:
        return

    db.save_message(username, text)
    socketio.emit("chat", {"username": username, "text": text})


@socketio.on("exituser")
def on_exit(username):
    socketio.emit("update", f"{username} left")


@socketio.on("typing")
def on_typing(data):
    socketio.emit("typing", data)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
