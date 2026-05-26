from __future__ import annotations

from typing import Any


def personalize_message(input_payload: dict[str, Any], plan: dict[str, Any], research: dict[str, Any]) -> str:
    name = input_payload.get("name") or input_payload.get("prospect_name") or "there"
    company = input_payload.get("company") or (research or {}).get("company") or "your team"
    lead_score = plan.get("lead_score") if isinstance(plan, dict) else None
    score_text = f"Your lead score is {lead_score} out of 100, which makes this a good fit for outreach.\n\n" if lead_score is not None else ""
    return (
        f"Hi {name},\n\n"
        f"I reviewed {company} and put together a short note based on {plan.get('objective')}. "
        f"{score_text}"
        "If you’d like, I can share the rest of the workflow details."
    )
