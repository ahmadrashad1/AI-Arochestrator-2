from __future__ import annotations

from os import environ

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.base import store
from app.database.repositories.execution_repository import ExecutionRepository
from app.database.repositories.tenant_repository import TenantRepository
from app.database.repositories.usage_repository import UsageRepository
from app.database.repositories.llm_usage_repository import LLMUsageRepository
from app.database.repositories.tool_quota_repository import ToolQuotaRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.workflow_repository import WorkflowRepository
from app.database.repositories.workspace_repository import WorkspaceRepository
from app.database.session import get_session


def _use_database_backend() -> bool:
	return environ.get("REPO_BACKEND", "INMEMORY").upper() in ("DB", "SQL", "SQLALCHEMY")


def get_tenant_repository(session: Session | None = Depends(get_session)) -> TenantRepository:
	if not _use_database_backend():
		return TenantRepository(store)
	return TenantRepository(store, session=session)


def get_user_repository(session: Session | None = Depends(get_session)) -> UserRepository:
	if not _use_database_backend():
		return UserRepository(store)
	return UserRepository(store, session=session)


def get_workspace_repository(session: Session | None = Depends(get_session)) -> WorkspaceRepository:
	if not _use_database_backend():
		return WorkspaceRepository(store)
	return WorkspaceRepository(store, session=session)


def get_workflow_repository(session: Session | None = Depends(get_session)) -> WorkflowRepository:
	if not _use_database_backend():
		return WorkflowRepository(store)
	return WorkflowRepository(store, session=session)


def get_execution_repository(session: Session | None = Depends(get_session)) -> ExecutionRepository:
	if not _use_database_backend():
		return ExecutionRepository(store)
	return ExecutionRepository(store, session=session)


def get_usage_repository(session: Session | None = Depends(get_session)) -> UsageRepository:
	if not _use_database_backend():
		return UsageRepository(store)
	return UsageRepository(store, session=session)


def get_llm_usage_repository(session: Session | None = Depends(get_session)) -> LLMUsageRepository:
	if not _use_database_backend():
		return LLMUsageRepository(store)
	return LLMUsageRepository(store, session=session)


def get_tool_quota_repository(session: Session | None = Depends(get_session)) -> ToolQuotaRepository:
	if not _use_database_backend():
		return ToolQuotaRepository(store)
	return ToolQuotaRepository(store, session=session)

