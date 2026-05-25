from __future__ import annotations

from app.graphs.graph_registry import graph_registry


def test_customer_support_graph_pauses_for_approval() -> None:
    graph = graph_registry.resolve({"graph_name": "customer_support"}, {"approval_required": True})
    state = graph.run(
        {
            "workflow_id": "workflow_approval",
            "execution_id": "execution_approval",
            "input_payload": {"approval_required": True},
        }
    )

    assert state["status"] == "paused"
    assert state["pause_reason"] == "approval required"
    assert state["current_node"] == "approval"
