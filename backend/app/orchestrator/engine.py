from __future__ import annotations

import json
from uuid import uuid4

from app.database.models.workflow import Workflow
from app.database.repositories.workflow_repository import WorkflowRepository
from app.orchestrator.execution_manager import ExecutionManager
from app.llm.router import llm_router
from app.workflows.config import WorkflowConfig, resolve_workflow_config
from shared.dto.workflow_requests import CreateWorkflowRequest, RunWorkflowRequest
from shared.schemas.workflow import WorkflowConfigUpdate


class WorkflowEngine:
    def __init__(self, workflow_repository: WorkflowRepository, execution_manager: ExecutionManager):
        self.workflow_repository = workflow_repository
        self.execution_manager = execution_manager

    def create_workflow(self, tenant_id: str, payload: CreateWorkflowRequest) -> Workflow:
        workflow = Workflow(
            id=f"workflow_{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            name=payload.name,
            description=payload.description,
            definition_json=json.dumps(payload.definition, separators=(",", ":")),
            status="draft",
        )
        return self.workflow_repository.create(workflow)

    def list_workflows(self, tenant_id: str) -> list[Workflow]:
        return self.workflow_repository.list_by_tenant(tenant_id)

    def get_workflow(self, tenant_id: str, workflow_id: str) -> Workflow | None:
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None or workflow.tenant_id != tenant_id:
            return None
        return workflow

    def get_workflow_config(self, tenant_id: str, workflow_id: str) -> WorkflowConfig | None:
        workflow = self.get_workflow(tenant_id, workflow_id)
        if workflow is None:
            return None
        raw_definition = json.loads(workflow.definition_json or "{}")
        return resolve_workflow_config(raw_definition)

    def update_workflow_config(self, tenant_id: str, workflow_id: str, payload: WorkflowConfigUpdate) -> Workflow | None:
        workflow = self.get_workflow(tenant_id, workflow_id)
        if workflow is None:
            return None

        current_definition = json.loads(workflow.definition_json or "{}")
        updated_definition = dict(current_definition)
        incoming = payload.model_dump(exclude_unset=True)
        for key, value in incoming.items():
            if value is None:
                continue
            if key == "metadata" and isinstance(value, dict):
                updated_definition.update(value)
            else:
                updated_definition[key] = value

        workflow.definition_json = json.dumps(updated_definition, separators=(",", ":"))
        return self.workflow_repository.update(workflow)

    def run_workflow(
        self,
        tenant_id: str,
        workflow_id: str,
        payload: RunWorkflowRequest,
        idempotency_key: str | None = None,
    ):
        llm_route = llm_router.select_route(payload.input_payload.get("llm_tier") if isinstance(payload.input_payload, dict) else None)
        return self.execution_manager.submit_execution(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            input_payload=payload.input_payload,
            idempotency_key=idempotency_key,
        )