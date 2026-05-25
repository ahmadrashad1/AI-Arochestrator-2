from __future__ import annotations

from fastapi import Depends

from app.database.repositories import (
	get_execution_repository,
	get_workflow_repository,
)
from app.orchestrator.engine import WorkflowEngine
from app.orchestrator.execution_manager import ExecutionManager
from app.orchestrator.workflow_runner import WorkflowRunner


def get_workflow_runner() -> WorkflowRunner:
	return WorkflowRunner()


def get_execution_manager(
	execution_repository=Depends(get_execution_repository),
	workflow_repository=Depends(get_workflow_repository),
	runner: WorkflowRunner = Depends(get_workflow_runner),
) -> ExecutionManager:
	return ExecutionManager(
		execution_repository=execution_repository,
		workflow_repository=workflow_repository,
		runner=runner,
	)


def get_workflow_engine(
	workflow_repository=Depends(get_workflow_repository),
	execution_manager: ExecutionManager = Depends(get_execution_manager),
) -> WorkflowEngine:
	return WorkflowEngine(
		workflow_repository=workflow_repository,
		execution_manager=execution_manager,
	)