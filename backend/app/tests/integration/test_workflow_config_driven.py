from __future__ import annotations

from app.graphs.graph_registry import graph_registry
from app.workflows.config import WorkflowConfig, resolve_workflow_config


def test_workflow_config_parser_normalizes_templates() -> None:
    resolved = resolve_workflow_config(
        {
            "workflow_type": "Support",
            "graph_name": "support",
            "steps": ["planner", "retriever", "validator", "executor"],
            "tools": ["browser.search", "communication.slack"],
        },
        {"tenant_label": "company_2"},
    )

    assert resolved.workflow_type == "support"
    assert resolved.graph_name == "support"
    assert resolved.resolved_steps(["planner"]) == ["planner", "retriever", "validator", "executor"]

    config = WorkflowConfig.from_dict(
        {
            "workflow_type": "Support",
            "graph_name": "support",
            "steps": ["planner", "retriever", "validator", "executor"],
            "tools": ["browser.search", "communication.slack"],
            "tenant_label": "company_2",
        }
    )

    assert config.workflow_type == "support"
    assert config.graph_name == "support"
    assert config.resolved_steps(["planner"]) == ["planner", "retriever", "validator", "executor"]
    assert config.metadata["tenant_label"] == "company_2"


def test_config_driven_workflow_uses_shared_primitives() -> None:
    workflow_definition = {
        "workflow_type": "support",
        "steps": ["planner", "retriever", "validator", "executor"],
        "tools": ["browser.search", "communication.slack"],
    }
    graph = graph_registry.resolve(workflow_definition, {"knowledge_query": "refund policy"})

    state = graph.run(
        {
            "workflow_id": "workflow_config_support",
            "execution_id": "execution_config_support",
            "workflow_definition": workflow_definition,
            "input_payload": {"knowledge_query": "refund policy"},
        }
    )

    assert state["graph_name"] == "support"
    assert state["status"] == "completed"
    assert state["visited_nodes"] == ["planner", "retriever", "validator", "executor"]
    assert state["workflow_config"]["tools"] == ["browser.search", "communication.slack"]
    assert state["output_payload"]["status"] == "completed"
