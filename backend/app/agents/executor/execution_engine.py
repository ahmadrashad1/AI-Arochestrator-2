from __future__ import annotations

from typing import Any

from app.agents.planner.planning_engine import personalize_message


def execute_workflow_step(input_payload: dict[str, Any], plan: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    subject = f"{plan['objective'].title()} for {input_payload.get('company') or 'a prospect'}"
    return {
        "subject": subject,
        "lead_score": plan["lead_score"],
        "personalization": personalize_message(input_payload, plan, research),
        "summary": f"Prepared outreach for {input_payload.get('company') or 'lead'}",
    }
