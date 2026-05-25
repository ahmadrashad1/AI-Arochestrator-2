from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.agents.executor.execution_engine import execute_workflow_step
from app.agents.planner.planning_engine import build_plan
from app.agents.researcher.retrieval import gather_lead_context
from app.tools.registry import run_tool


GraphState = dict[str, Any]
AgentPrimitive = Callable[[GraphState], GraphState]


@dataclass(slots=True)
class AgentContext:
    workflow_id: str | None = None
    execution_id: str | None = None
    input_payload: dict[str, Any] = field(default_factory=dict)
    workflow_definition: dict[str, Any] = field(default_factory=dict)
    llm_route: dict[str, Any] = field(default_factory=dict)
    graph_name: str = "automation"


def _input_payload(state: GraphState) -> dict[str, Any]:
    payload = state.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def planner_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    plan = build_plan(input_payload, state.get("llm_route", {}))
    state["plan"] = plan
    return state


def research_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    state["research"] = gather_lead_context(input_payload)
    return state


def retriever_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    query = input_payload.get("knowledge_query") or input_payload.get("research_query") or input_payload.get("goal") or "knowledge"
    state["retrieved_context"] = {
        "query": query,
        "documents": [f"Retrieved knowledge for {query}"],
    }
    return state


def validator_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    if not isinstance(state.get("input_payload"), dict):
        state["status"] = "failed"
        state["error"] = "input_payload must be a mapping"
        state["next_node"] = "fallback"
        return state

    state["validation"] = {
        "ok": True,
        "tools_allowed": list(state.get("workflow_definition", {}).get("tools", [])),
    }
    if input_payload.get("approval_required"):
        state["next_node"] = "approval"
    elif input_payload.get("tool_request") or input_payload.get("tool_name"):
        state["next_node"] = "tool_execution"
    else:
        state["next_node"] = "executor"
    return state


def executor_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    if state.get("graph_name") == "lead_generation" or state.get("workflow_definition", {}).get("workflow_type") == "sales":
        execution_result = execute_workflow_step(input_payload, state.get("plan", {}), state.get("research", {}))
        state.update(execution_result)
        state["next_node"] = None
        state["status"] = "completed"
        return state

    state["output_payload"] = {
        "workflow_id": state.get("workflow_id"),
        "execution_id": state.get("execution_id"),
        "status": "completed",
        "summary": state.get("plan", {}).get("objective", "Workflow complete"),
        "llm_route": state.get("llm_route"),
    }
    state["status"] = "completed"
    state["next_node"] = None
    return state


def memory_primitive(state: GraphState) -> GraphState:
    memory = state.setdefault("memory", [])
    memory.append({"step": state.get("current_node"), "summary": state.get("research", {}).get("summary") or state.get("retrieved_context", {}).get("query")})
    return state


def router_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    if input_payload.get("approval_required"):
        state["next_node"] = "approval"
    elif input_payload.get("research_query") or input_payload.get("knowledge_query"):
        state["next_node"] = "research"
    elif input_payload.get("tool_request") or input_payload.get("tool_name"):
        state["next_node"] = "tool_execution"
    else:
        state["next_node"] = "validation"
    return state


def tool_executor_primitive(state: GraphState) -> GraphState:
    input_payload = _input_payload(state)
    tool_request = input_payload.get("tool_request") if isinstance(input_payload.get("tool_request"), dict) else None
    tool_name = input_payload.get("tool_name") or (tool_request.get("tool_name") if tool_request else None)
    tool_input = input_payload.get("tool_input") or (tool_request.get("input_payload") if tool_request else input_payload)
    if not tool_name:
        state["status"] = "completed"
        state["next_node"] = None
        return state

    result = run_tool(tool_name, tool_input)
    state["tool_result"] = result
    state["output_payload"] = {
        "workflow_id": state.get("workflow_id"),
        "execution_id": state.get("execution_id"),
        "status": "completed",
        "tool_name": tool_name,
        "tool_result": result,
        "llm_route": state.get("llm_route"),
    }
    state["status"] = "completed"
    state["next_node"] = None
    return state
