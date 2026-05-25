from __future__ import annotations

from pathlib import Path

from app.memory.short_term.checkpoint_store import CheckpointStore
from app.orchestrator.workflow_runner import WorkflowRunner


def test_graph_checkpoint_resume_after_approval(tmp_path: Path) -> None:
    runner = WorkflowRunner(CheckpointStore(tmp_path / "checkpoints"))
    workflow_id = "workflow_graph_resume"
    execution_id = "execution_graph_resume"

    paused_plan = runner.build_execution_plan(
        workflow_id,
        execution_id,
        {"approval_required": True},
        {"graph_name": "customer_support"},
    )
    assert paused_plan["output_payload"]["status"] == "paused"

    checkpoint = runner.load_checkpoint(workflow_id)
    assert checkpoint is not None
    checkpoint["graph_state"]["input_payload"]["approved"] = True
    runner.save_checkpoint(workflow_id, checkpoint)

    resumed_state = runner.resume_from_checkpoint(workflow_id)
    assert resumed_state is not None
    assert resumed_state["status"] == "completed"
    assert resumed_state["approved"] is True
    assert "validation" in resumed_state["visited_nodes"]
