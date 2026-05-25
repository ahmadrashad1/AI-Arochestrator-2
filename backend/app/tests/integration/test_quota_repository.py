from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.database.connection import get_engine
from app.database.models.base import Base
from app.database.models.tool_quota import ToolQuota
from app.database.repositories.tool_quota_repository import ToolQuotaRepository


def test_tool_quota_persists_across_sessions(tmp_path: Path) -> None:
    db_path = tmp_path / "quotas.db"
    engine = get_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with Session() as session:
        repo = ToolQuotaRepository(session=session)
        repo.upsert(ToolQuota(tool_name="echo", executions_limit=5, cpu_seconds_limit=12.5, used_executions=1, used_cpu_seconds=0.5))

    with Session() as session:
        repo = ToolQuotaRepository(session=session)
        quota = repo.get_by_tool_name("echo")
        assert quota is not None
        assert quota.executions_limit == 5
        assert quota.used_executions == 1
        assert quota.cpu_seconds_limit == 12.5
