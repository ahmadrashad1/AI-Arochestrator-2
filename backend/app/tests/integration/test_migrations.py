from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy import inspect


def test_initial_migration_creates_core_tables(tmp_path: Path) -> None:
    database_file = tmp_path / "phase3.db"
    database_url = f"sqlite+pysqlite:///{database_file}"

    config = Config(str(Path(__file__).resolve().parents[4] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"tenants", "users", "workspaces", "workflows", "executions", "integrations", "usage_records"}.issubset(tables)

    user_fks = inspector.get_foreign_keys("users")
    assert any(fk["referred_table"] == "tenants" for fk in user_fks)

    execution_fks = inspector.get_foreign_keys("executions")
    assert {fk["referred_table"] for fk in execution_fks} == {"tenants", "workflows"}
