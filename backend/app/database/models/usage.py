from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin


class Usage(TimestampMixin, Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class LLMUsage(TimestampMixin, Base):
    __tablename__ = "llm_usage"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=True)
    execution_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    tier: Mapped[str] = mapped_column(String(64), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
