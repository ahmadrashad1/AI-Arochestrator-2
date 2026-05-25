from __future__ import annotations

from typing import Any

from app.memory.short_term.checkpoint_store import CheckpointStore
from app.orchestrator.event_bus import event_bus
from app.llm.router import llm_router


class WorkflowRunner:
    def __init__(self, checkpoint_store: CheckpointStore | None = None):
        self.checkpoint_store = checkpoint_store or CheckpointStore()

    def save_checkpoint(self, workflow_id: str, state: dict[str, Any]) -> None:
        self.checkpoint_store.save(workflow_id, state)

    def load_checkpoint(self, workflow_id: str) -> dict[str, Any] | None:
        return self.checkpoint_store.load(workflow_id)

    def build_execution_output(self, workflow_id: str, execution_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        route = llm_router.select_route(input_payload.get("llm_tier") if isinstance(input_payload, dict) else None)
        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": "completed",
            "input_payload": input_payload,
            "llm_route": route.to_dict(),
            "summary": f"Workflow {workflow_id} completed",
        }

    def build_execution_plan(
        self,
        workflow_id: str,
        execution_id: str,
        input_payload: dict[str, Any],
    ) -> dict[str, Any]:
        output_payload = self.build_execution_output(workflow_id, execution_id, input_payload)
        plan = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "output_payload": output_payload,
            "input_payload": input_payload,
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
