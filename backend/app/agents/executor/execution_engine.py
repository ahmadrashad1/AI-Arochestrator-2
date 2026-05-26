from __future__ import annotations

from typing import Any

def execute_workflow_step(input_payload: dict[str, Any], plan: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    """Generic executor: prepare subject and summary. Do NOT include vertical-specific logic."""
    subject = f"{plan['objective'].title()} for {input_payload.get('company') or 'a prospect'}"
    return {
        "subject": subject,
        "summary": f"Prepared outreach for {input_payload.get('company') or 'lead'}",
    }
