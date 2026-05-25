from __future__ import annotations

from app.automations.actions.send_email import run as send_email


def test_send_email_action_queues_message() -> None:
    result = send_email({"to": "lead@example.com", "subject": "Hello", "body": "Hi", "allow_send": True})

    assert result["action"] == "send_email"
    assert result["tool"] == "communication.gmail"
    assert result["status"] == "queued"
