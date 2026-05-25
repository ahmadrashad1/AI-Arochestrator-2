"""End-to-end example: build a workflow that requests a tool execution,
spin up the worker loop to process the tool job, and print the result.

Usage: run from the repository root with PYTHONPATH pointing to backend
  python backend/scripts/e2e_tool_workflow.py
"""
from __future__ import annotations

import time
import uuid

from app.memory.short_term.checkpoint_store import CheckpointStore
from app.orchestrator.workflow_runner import WorkflowRunner
from app.workers.tool_worker import process_tool_jobs


class CapturingRunner:
    def __init__(self):
        self.results: dict[str, any] = {}

    def run_tool(self, payload: dict) -> any:
        # payload expected to contain execution_id and input_payload
        exec_id = payload.get("execution_id")
        inp = payload.get("input_payload")
        # call into tool registry via regular import to allow configurable sandboxing
        from app.tools.registry import run_tool

        tool_name = payload.get("tool_name")
        res = run_tool(tool_name, inp, timeout_seconds=10, sandbox=False)
        if exec_id:
            self.results[exec_id] = res
        return res


def main():
    runner = WorkflowRunner(checkpoint_store=CheckpointStore(".e2e_checkpoints"))
    capture = CapturingRunner()

    workflow_id = f"e2e-{uuid.uuid4().hex[:8]}"
    execution_id = f"exec-{uuid.uuid4().hex[:8]}"

    input_payload = {
        "tool_request": {"tool_name": "echo", "input_payload": {"hello": "world"}}
    }

    print("Building execution plan and publishing tool request...")
    plan = runner.build_execution_plan(workflow_id, execution_id, input_payload)
    print("Saved plan to checkpoint:", plan)

    # Process tool jobs until our execution_id has a result or timeout
    deadline = time.time() + 10
    while time.time() < deadline:
        processed = process_tool_jobs(runner=capture)
        if execution_id in capture.results:
            print("Tool execution result:", capture.results[execution_id])
            return
        if processed == 0:
            time.sleep(0.1)

    print("Timed out waiting for tool execution")


if __name__ == "__main__":
    main()
