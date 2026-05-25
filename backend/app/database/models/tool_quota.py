from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin


class ToolQuota(TimestampMixin, Base):
    __tablename__ = "tool_quotas"

    tool_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    executions_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_seconds_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    used_executions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_cpu_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
