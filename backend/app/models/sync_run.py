"""sync_runs table: one row per sync attempt (data-model.md)."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import SyncOutcome, SyncTrigger
from app.models.base import Base, IdMixin, pg_enum


class SyncRun(IdMixin, Base):
    __tablename__ = "sync_runs"

    trigger: Mapped[SyncTrigger] = mapped_column(pg_enum(SyncTrigger, "sync_trigger"))
    period_start: Mapped[datetime]
    period_end: Mapped[datetime]
    started_at: Mapped[datetime] = mapped_column(index=True)
    finished_at: Mapped[datetime | None]
    outcome: Mapped[SyncOutcome] = mapped_column(pg_enum(SyncOutcome, "sync_outcome"))
    windows_total: Mapped[int] = mapped_column(default=0)
    windows_done: Mapped[int] = mapped_column(default=0)
    added: Mapped[int] = mapped_column(default=0)
    updated: Mapped[int] = mapped_column(default=0)
    skipped: Mapped[int] = mapped_column(default=0)
    flagged: Mapped[int] = mapped_column(default=0)
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(String(500))
