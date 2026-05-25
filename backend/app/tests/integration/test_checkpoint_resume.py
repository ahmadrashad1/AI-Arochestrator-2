from __future__ import annotations

from pathlib import Path

from app.memory.short_term.checkpoint_store import CheckpointStore
from app.orchestrator.workflow_runner import WorkflowRunner


def test_checkpoint_resume_survives_restart(tmp_path: Path) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    runner = WorkflowRunner(CheckpointStore(checkpoint_dir))

    workflow_state = {
        "workflow_id": "workflow_phase3_resume",
        "tenant_id": "tenant_phase3",
        "current_step": "research",
        "status": "paused",
        "messages": ["draft plan"],
    }

    runner.save_checkpoint(workflow_state["workflow_id"], workflow_state)
    assert runner.load_checkpoint(workflow_state["workflow_id"]) == workflow_state

    restarted_runner = WorkflowRunner(CheckpointStore(checkpoint_dir))
    assert restarted_runner.load_checkpoint(workflow_state["workflow_id"]) == workflow_state
