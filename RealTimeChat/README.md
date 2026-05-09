# RealTimeChat — real‑time chat (InfoSec demo project)
Author: Burkhoniddin Khaitkulov (kb12362)

This is a small **real‑time chat** built for the AUCA **Information Security** course. It demonstrates:

- **WebSocket messaging** via Socket.IO (instant updates in multiple tabs)
- a tiny **REST API** that can inject messages into the live chat (easy to show in Postman)
- **SQLite persistence** for chat history
- a few practical **security hardenings** and an **nginx reverse‑proxy** setup

---

## What you can demo

- **Join / leave updates**
- **Typing indicator**
- **Chat history** (latest messages are fetched on join)
- **REST → WebSocket bridge**: sending a message through `POST /api/send` appears live for everyone

---

## Endpoints

- **`GET /`**: web UI
- **`GET /history`**: last 50 messages as JSON
- **`POST /api/send`**: send a message through the REST API
- **`POST /clear`**: clear stored message history (demo/admin)

---

## REST examples

### `POST /api/send`

```json
{
  "username": "Postman",
  "text": "Hello from REST!"
}
```

Response:

```json
{ "status": "ok" }
```

### `GET /history`
Example response:

```json
[
  { "username": "Alice", "text": "Hello", "ts": "2025-01-01 12:00:00" }
]
```

---

## Protecting `/clear` (recommended for demo)

By default, `POST /clear` works without auth to keep local demos simple.
If you set `ADMIN_TOKEN`, the endpoint requires it.

```bash
export ADMIN_TOKEN="demo123"
```

Then call:

```bash
curl -X POST http://localhost:5001/clear -H "X-Admin-Token: demo123"
```

---

## Security notes (what was improved)

- **XSS mitigation in UI**: messages are rendered with `innerText` (not `innerHTML`)
- **Input validation**: empty messages and very long payloads are rejected
- **SQL injection prevention**: SQLite writes use parameterized queries
- **CORS tightening for Socket.IO**: default origins are limited to localhost (can be overridden via `SOCKETIO_CORS_ALLOWED_ORIGINS`)

---

## Local run

Create venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run:

```bash
python app.py
```

Open:
- `http://localhost:5001` (direct)
- `http://localhost:8080` (through nginx, if configured)

---

## nginx reverse proxy (example)

This is an example config for local usage on `http://localhost:8080`:

```nginx
http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    upstream chat_backend {
        server 127.0.0.1:5001;
    }

    server {
        listen       8080;
        server_name  localhost;

        location /socket.io/ {
            proxy_pass http://chat_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
            proxy_read_timeout 60s;
        }

        location / {
            proxy_pass http://chat_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }
    }
}
```

---

## WebSocket events (Socket.IO)

Client → server:
- `newuser` (string username)
- `chat` (`{ "username": "...", "text": "..." }`)
- `typing` (`{ "username": "...", "typing": true|false }`)
- `exituser` (string username)

Server → clients:
- `update` (string)
- `chat` (message object)
- `typing` (typing object)

---

## Project layout

```
RealTimeChat/
├── app.py
├── db/__init__.py
├── static/
│   ├── code.js
│   └── style.css
├── templates/index.html
├── chat.db
├── requirements.txt
└── README.md
```

