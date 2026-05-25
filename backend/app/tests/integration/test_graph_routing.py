from __future__ import annotations

from app.graphs.graph_registry import graph_registry


def test_lead_generation_graph_routes_through_expected_nodes() -> None:
    graph = graph_registry.resolve({"graph_name": "lead_generation"}, {"research_query": "best leads"})
    state = graph.run(
        {
            "workflow_id": "workflow_graph_routing",
            "execution_id": "execution_graph_routing",
            "input_payload": {"research_query": "best leads"},
        }
    )

    assert state["graph_name"] == "lead_generation"
    assert state["status"] == "completed"
    assert state["visited_nodes"][:4] == ["planning", "routing", "retrieval", "memory"]
    assert "validation" in state["visited_nodes"]
