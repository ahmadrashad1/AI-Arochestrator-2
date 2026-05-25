from __future__ import annotations

from app.graphs.graph_registry import graph_registry


def test_graph_validation_failure_uses_fallback_path() -> None:
    graph = graph_registry.resolve({"graph_name": "automation"}, None)
    state = graph.run(
        {
            "workflow_id": "workflow_graph_recovery",
            "execution_id": "execution_graph_recovery",
            "input_payload": "invalid-payload",
        }
    )

    assert state["status"] == "completed"
    assert state["fallback"]["reason"] == "input_payload must be a mapping"
    assert state["output_payload"]["fallback"] is True
