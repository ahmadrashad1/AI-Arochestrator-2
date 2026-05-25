from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from app.core.security import hash_password
from app.database.models.execution import Execution
from app.database.models.integration import Integration
from app.database.models.tenant import Tenant
from app.database.models.usage import Usage
from app.database.models.user import User
from app.database.models.workflow import Workflow
from app.database.models.workspace import Workspace
from app.database.repositories.execution_repository import ExecutionRepository
from app.database.repositories.integration_repository import IntegrationRepository
from app.database.repositories.tenant_repository import TenantRepository
from app.database.repositories.usage_repository import UsageRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.workflow_repository import WorkflowRepository
from app.database.repositories.workspace_repository import WorkspaceRepository
from app.database.session import create_session_factory


def _upgrade_sqlite_database(database_url: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[4] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def test_repository_crud_round_trip(tmp_path: Path) -> None:
    database_file = tmp_path / "crud.db"
    database_url = f"sqlite+pysqlite:///{database_file}"
    _upgrade_sqlite_database(database_url)

    session_factory = create_session_factory(database_url)

    with session_factory() as session:
        tenant_repository = TenantRepository(session=session)
        user_repository = UserRepository(session=session)
        workspace_repository = WorkspaceRepository(session=session)
        workflow_repository = WorkflowRepository(session=session)
        execution_repository = ExecutionRepository(session=session)
        integration_repository = IntegrationRepository(session=session)
        usage_repository = UsageRepository(session=session)

        tenant = tenant_repository.create(Tenant(id="tenant_phase3", name="Phase 3 Tenant", plan="growth"))
        assert tenant_repository.get_by_id(tenant.id) is not None

        user = user_repository.create(
            User(
                id="user_phase3",
                tenant_id=tenant.id,
                email="phase3@example.com",
                password_hash=hash_password("password123"),
                role="admin",
                full_name="Phase Three User",
            )
        )
        user.full_name = "Updated User"
        updated_user = user_repository.update(user)
        assert updated_user.full_name == "Updated User"
        assert user_repository.authenticate("phase3@example.com", "password123") is not None

        workspace = workspace_repository.create(Workspace(id="workspace_phase3", tenant_id=tenant.id, name="Phase 3 Workspace"))
        assert workspace_repository.count_by_tenant(tenant.id) == 1
        workspace.name = "Updated Workspace"
        assert workspace_repository.update(workspace).name == "Updated Workspace"

        workflow = workflow_repository.create(
            Workflow(id="workflow_phase3", tenant_id=tenant.id, name="Phase 3 Workflow", description="Test workflow")
        )
        workflow.status = "active"
        assert workflow_repository.update(workflow).status == "active"

        execution = execution_repository.create(
            Execution(
                id="execution_phase3",
                tenant_id=tenant.id,
                workflow_id=workflow.id,
                status="running",
                input_payload_json="{\"lead\": \"Acme\"}",
            )
        )
        execution.status = "completed"
        execution.output_payload_json = "{\"sent\": true}"
        assert execution_repository.update(execution).status == "completed"
        assert execution_repository.list_by_workflow(workflow.id)[0].id == execution.id

        integration = integration_repository.create(
            Integration(
                id="integration_phase3",
                tenant_id=tenant.id,
                provider="stripe",
                name="Billing Integration",
                external_account_id="acct_123",
            )
        )
        assert integration_repository.list_by_tenant(tenant.id)[0].id == integration.id

        usage = usage_repository.create(
            Usage(id="usage_phase3", tenant_id=tenant.id, metric_name="workflow_runs", amount=1)
        )
        assert usage_repository.list_by_tenant(tenant.id)[0].id == usage.id

        user_repository.delete(user.id)
        workspace_repository.delete(workspace.id)
        workflow_repository.delete(workflow.id)
        execution_repository.delete(execution.id)

        assert user_repository.get_by_id(user.id) is None
        assert workspace_repository.get_by_id(workspace.id) is None
        assert workflow_repository.get_by_id(workflow.id) is None
        assert execution_repository.get_by_id(execution.id) is None
