from __future__ import annotations

from typing import Any

from app.memory.short_term.checkpoint_store import CheckpointStore
from app.orchestrator.event_bus import event_bus
from app.llm.router import llm_router
from app.graphs.graph_registry import graph_registry


class WorkflowRunner:
    def __init__(self, checkpoint_store: CheckpointStore | None = None):
        self.checkpoint_store = checkpoint_store or CheckpointStore()

    def save_checkpoint(self, workflow_id: str, state: dict[str, Any]) -> None:
        self.checkpoint_store.save(workflow_id, state)

    def load_checkpoint(self, workflow_id: str) -> dict[str, Any] | None:
        return self.checkpoint_store.load(workflow_id)

    def build_execution_output(
        self,
        workflow_id: str,
        execution_id: str,
        input_payload: dict[str, Any],
        workflow_definition: dict[str, Any] | None = None,
        existing_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        route = llm_router.select_route(input_payload.get("llm_tier") if isinstance(input_payload, dict) else None)
        graph = graph_registry.resolve(workflow_definition or {}, input_payload)
        state = graph.run(
            existing_state
            or {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "input_payload": input_payload,
                "workflow_definition": workflow_definition or {},
                "llm_route": route.to_dict(),
            }
        )
        state.setdefault("workflow_id", workflow_id)
        state.setdefault("execution_id", execution_id)
        state.setdefault("llm_route", route.to_dict())
        state.setdefault("summary", f"Workflow {workflow_id} completed")
        return state

    def build_execution_plan(
        self,
        workflow_id: str,
        execution_id: str,
        input_payload: dict[str, Any],
        workflow_definition: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = workflow_definition or {}
        output_payload = self.build_execution_output(workflow_id, execution_id, input_payload, context)
        plan = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "output_payload": output_payload,
            "graph_state": output_payload,
            "input_payload": input_payload,
            "workflow_definition": context,
            "llm_route": output_payload.get("llm_route"),
        }
        self.save_checkpoint(workflow_id, plan)
        # If the workflow requests a tool execution, enqueue it for workers.
        try:
            tool_req = input_payload.get("tool_request") if isinstance(input_payload, dict) else None
            if tool_req:
                event_bus.publish(
                    "tool.execution.requested",
                    {
                        "execution_id": execution_id,
                        "tool_name": tool_req.get("tool_name") if isinstance(tool_req, dict) else None,
                        "input_payload": tool_req.get("input_payload") if isinstance(tool_req, dict) else input_payload,
                    },
                )
        except Exception:
            pass

        return plan

    def resume_from_checkpoint(self, workflow_id: str) -> dict[str, Any] | None:
        checkpoint = self.load_checkpoint(workflow_id)
        if checkpoint is None:
            return None

        input_payload = checkpoint.get("input_payload", {}) if isinstance(checkpoint, dict) else {}
        workflow_definition = checkpoint.get("workflow_definition", {}) if isinstance(checkpoint, dict) else {}
        existing_state = checkpoint.get("graph_state") if isinstance(checkpoint, dict) else None
        if not isinstance(input_payload, dict):
            input_payload = {}
        if not isinstance(workflow_definition, dict):
            workflow_definition = {}
        if not isinstance(existing_state, dict):
            existing_state = None

        return self.build_execution_output(
            checkpoint.get("workflow_id", workflow_id),
            checkpoint.get("execution_id", f"execution_{workflow_id}"),
            input_payload,
            workflow_definition,
            existing_state=existing_state,
        )
