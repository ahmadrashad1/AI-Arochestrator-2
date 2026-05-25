from __future__ import annotations

import json
import os
import smtplib
import sqlite3
import threading
from datetime import datetime, timezone
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

try:
    import psycopg
except Exception:  # pragma: no cover - optional in local images
    psycopg = None  # type: ignore


DB_URL = os.getenv("ALERT_WEBHOOK_DB_URL", "sqlite:////workspace/data/alert_notifications.db")
SLACK_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_SLACK_URL", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_DISCORD_URL", "").strip()
EMAIL_TO = os.getenv("ALERT_WEBHOOK_EMAIL_TO", "").strip()
EMAIL_FROM = os.getenv("ALERT_WEBHOOK_EMAIL_FROM", "alerts@localhost").strip()
SMTP_HOST = os.getenv("ALERT_WEBHOOK_SMTP_HOST", "").strip()
SMTP_PORT = int((os.getenv("ALERT_WEBHOOK_SMTP_PORT", "587") or "587").strip())
SMTP_USERNAME = os.getenv("ALERT_WEBHOOK_SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("ALERT_WEBHOOK_SMTP_PASSWORD", "").strip()
SMTP_USE_TLS = os.getenv("ALERT_WEBHOOK_SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}

DB_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sqlite_path() -> Path:
    return Path(DB_URL.removeprefix("sqlite:///"))


def _connect_sqlite() -> sqlite3.Connection:
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_postgres() -> Any:
    if psycopg is None:
        raise RuntimeError("psycopg is required for PostgreSQL-backed alert storage")
    return psycopg.connect(DB_URL)


def get_connection() -> Any:
    if DB_URL.startswith("sqlite:///"):
        return _connect_sqlite()
    if DB_URL.startswith("postgresql://") or DB_URL.startswith("postgres://"):
        return _connect_postgres()
    raise ValueError(f"Unsupported ALERT_WEBHOOK_DB_URL: {DB_URL}")


def initialize_store() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS alert_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        path TEXT NOT NULL,
        payload_json TEXT NOT NULL
    )
    """ if DB_URL.startswith("sqlite:///") else """
    CREATE TABLE IF NOT EXISTS alert_notifications (
        id BIGSERIAL PRIMARY KEY,
        received_at TEXT NOT NULL,
        path TEXT NOT NULL,
        payload_json TEXT NOT NULL
    )
    """

    with DB_LOCK:
        conn = get_connection()
        try:
            with conn:
                conn.execute(schema)
        finally:
            conn.close()


def insert_record(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = {"received_at": utc_now(), "path": path, "payload": payload}
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    with DB_LOCK:
        conn = get_connection()
        try:
            if DB_URL.startswith("sqlite:///"):
                with conn:
                    cursor = conn.execute(
                        "INSERT INTO alert_notifications (received_at, path, payload_json) VALUES (?, ?, ?)",
                        (record["received_at"], path, payload_json),
                    )
                    record["id"] = cursor.lastrowid
            else:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO alert_notifications (received_at, path, payload_json) VALUES (%s, %s, %s) RETURNING id",
                            (record["received_at"], path, payload_json),
                        )
                        record["id"] = cursor.fetchone()[0]
        finally:
            conn.close()

    return record


def fetch_records(limit: int) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    query = "SELECT id, received_at, path, payload_json FROM alert_notifications ORDER BY id DESC LIMIT ?" if DB_URL.startswith("sqlite:///") else "SELECT id, received_at, path, payload_json FROM alert_notifications ORDER BY id DESC LIMIT %s"

    with DB_LOCK:
        conn = get_connection()
        try:
            cursor = conn.execute(query, (limit,))
            rows = cursor.fetchall()
        finally:
            conn.close()

    items: list[dict[str, Any]] = []
    for row in rows[::-1]:
        payload_text = row[3] if isinstance(row, tuple) else row["payload_json"]
        payload: Any
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            payload = {"raw": payload_text}

        items.append(
            {
                "id": row[0] if isinstance(row, tuple) else row["id"],
                "received_at": row[1] if isinstance(row, tuple) else row["received_at"],
                "path": row[2] if isinstance(row, tuple) else row["path"],
                "payload": payload,
            }
        )

    return items


def extract_alert_summary(payload: dict[str, Any]) -> str:
    alerts = payload.get("alerts")
    if isinstance(alerts, list) and alerts:
        first = alerts[0]
        if isinstance(first, dict):
            labels = first.get("labels", {})
            if isinstance(labels, dict) and labels.get("alertname"):
                return str(labels["alertname"])
    labels = payload.get("labels")
    if isinstance(labels, dict) and labels.get("alertname"):
        return str(labels["alertname"])
    return "alert"


def post_webhook(url: str, body: dict[str, Any]) -> None:
    if not url:
        return

    request = Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        response.read()


def forward_to_slack(record: dict[str, Any]) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    payload = record["payload"]
    summary = extract_alert_summary(payload)
    body = {
        "text": f"Alert received: {summary}",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {"title": "Received At", "value": record["received_at"], "short": True},
                    {"title": "Path", "value": record["path"], "short": True},
                ],
            }
        ],
    }
    post_webhook(SLACK_WEBHOOK_URL, body)


def forward_to_discord(record: dict[str, Any]) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    payload = record["payload"]
    summary = extract_alert_summary(payload)
    body = {
        "content": f"Alert received: {summary}",
        "embeds": [
            {
                "title": "Alert Notification",
                "color": 15158332,
                "fields": [
                    {"name": "Received At", "value": record["received_at"], "inline": True},
                    {"name": "Path", "value": record["path"], "inline": True},
                ],
            }
        ],
    }
    post_webhook(DISCORD_WEBHOOK_URL, body)


def forward_to_email(record: dict[str, Any]) -> None:
    if not EMAIL_TO or not SMTP_HOST:
        return

    payload = record["payload"]
    summary = extract_alert_summary(payload)
    message = EmailMessage()
    message["Subject"] = f"[Alertmanager] {summary}"
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.set_content(json.dumps(record, indent=2, sort_keys=True))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USERNAME:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)


class AlertWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        response_body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b""

        try:
            payload = json.loads(raw_body.decode("utf-8") or "[]")
        except json.JSONDecodeError:
            payload = {"raw": raw_body.decode("utf-8", errors="replace")}

        if isinstance(payload, list):
            envelope: dict[str, Any] = {"alerts": payload}
        elif isinstance(payload, dict):
            envelope = payload
        else:
            envelope = {"raw": payload}

        record = insert_record(self.path, envelope)

        print(json.dumps(record, indent=2, sort_keys=True), flush=True)

        try:
            forward_to_slack(record)
        except Exception as exc:  # pragma: no cover - network optional
            print(json.dumps({"forwarding": "slack", "error": str(exc)}), flush=True)

        try:
            forward_to_discord(record)
        except Exception as exc:  # pragma: no cover - network optional
            print(json.dumps({"forwarding": "discord", "error": str(exc)}), flush=True)

        try:
            forward_to_email(record)
        except Exception as exc:  # pragma: no cover - network optional
            print(json.dumps({"forwarding": "email", "error": str(exc)}), flush=True)

        self._send_json(200, {"status": "ok", "id": record.get("id")})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if parsed.path == "/alerts":
            params = parse_qs(parsed.query)
            try:
                limit = int(params.get("limit", ["20"])[0])
            except ValueError:
                limit = 20
            records = fetch_records(limit)
            self._send_json(200, {"count": len(records), "items": records, "store_backend": DB_URL})
            return

        self._send_json(200, {"service": "alert-webhook", "store_backend": DB_URL})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main() -> None:
    initialize_store()
    server = ThreadingHTTPServer(("0.0.0.0", 5001), AlertWebhookHandler)
    print("alert webhook listening on :5001", flush=True)
    print(json.dumps({"store_backend": DB_URL}, sort_keys=True), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
