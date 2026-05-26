from __future__ import annotations

from typing import Any

from app.agents.executor.execution_engine import execute_workflow_step
from app.agents.planner.planning_engine import build_plan
from app.agents.researcher.retrieval import gather_lead_context
from app.automations.lead_generation.scoring import score_lead
from app.automations.lead_generation.personalization import personalize_message
from app.observability.logging import log_execution_trace
from app.tools.communication.gmail_tool import run as send_gmail
from app.tools.crm.hubspot_tool import run as sync_hubspot
from app.tools.crm.salesforce_tool import run as sync_salesforce
from app.tools.productivity.airtable_tool import run as update_airtable
from app.tools.productivity.notion_tool import run as update_notion
from app.tools.productivity.sheets_tool import run as update_sheets


def execute_lead_generation(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    plan = state.get("plan") or build_plan(input_payload, state.get("llm_route", {}))
    research = gather_lead_context(input_payload)
    execution_result = execute_workflow_step(input_payload, plan, research)

    # Vertical-specific scoring and personalization live in the automation layer
    lead_score = score_lead(input_payload, research, plan)
    # attach lead_score to plan so personalization can reference it
    plan = dict(plan)
    plan["lead_score"] = lead_score
    message = personalize_message(input_payload, plan, research)

    outreach_payload = {
        "to": input_payload.get("email") or input_payload.get("prospect_email") or "prospect@example.com",
        "subject": execution_result["subject"],
        "body": message,
        "allow_send": True,
    }

    email_result = send_gmail(outreach_payload)
    crm_result = {
        "hubspot": sync_hubspot({"lead": input_payload, "plan": plan, "research": research}),
        "salesforce": sync_salesforce({"lead": input_payload, "plan": plan, "research": research}),
        "sheets": update_sheets({"lead": input_payload, "plan": plan}),
        "airtable": update_airtable({"lead": input_payload, "plan": plan}),
        "notion": update_notion({"lead": input_payload, "plan": plan}),
    }

    trace = list(state.get("trace", []))
    trace.append({"stage": "lead_generation", "plan": plan, "research": research, "email": email_result})
    log_execution_trace(
        "lead_generation.complete",
        workflow_id=state.get("workflow_id"),
        execution_id=state.get("execution_id"),
        lead_score=lead_score,
        subject=execution_result["subject"],
    )

    return {
        "status": "completed",
        "plan": plan,
        "research": research,
        "lead_score": lead_score,
        "personalization": message,
        "email_result": email_result,
        "crm_result": crm_result,
        "trace": trace,
        "output_payload": {
            "workflow_id": state.get("workflow_id"),
            "execution_id": state.get("execution_id"),
            "status": "completed",
            "plan": plan,
            "research": research,
            "lead_score": lead_score,
            "personalization": message,
            "email_result": email_result,
            "crm_result": crm_result,
            "llm_route": state.get("llm_route"),
            "summary": execution_result["summary"],
            "trace": trace,
        },
    }
