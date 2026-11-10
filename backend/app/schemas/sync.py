"""API models for POST /sync and GET /sync/last (contracts/http-api.md)."""

import uuid
from datetime import datetime, timedelta

from pydantic import AwareDatetime, BaseModel

from app.common.constants import SYNC_STALE_AFTER_MINUTES
from app.common.types import SyncOutcome, SyncTrigger
from app.models import SyncRun
from app.schemas.common import UtcDatetime

NO_NEW_DATA_HINT = (
    "No new payments found. New sandbox payments can take up to 3 hours to appear in PayPal."
)
STALE_RUN_ERROR = ("SYNC_INTERRUPTED", "The last sync did not finish. Please run it again.")


class SyncRequest(BaseModel):
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None


class PeriodOut(BaseModel):
    start: UtcDatetime
    end: UtcDatetime


class WindowsOut(BaseModel):
    total: int
    done: int


class CountsOut(BaseModel):
    added: int
    updated: int
    skipped: int
    flagged: int


class SyncErrorOut(BaseModel):
    code: str
    message: str


class SyncRunOut(BaseModel):
    id: uuid.UUID
    trigger: SyncTrigger
    period: PeriodOut
    started_at: UtcDatetime
    finished_at: UtcDatetime | None
    outcome: SyncOutcome
    windows: WindowsOut
    counts: CountsOut
    error: SyncErrorOut | None
    hint: str | None

    @classmethod
    def from_model(cls, run: SyncRun, now: datetime) -> "SyncRunOut":
        outcome, error = run.outcome, None
        if run.error_code and run.error_message:
            error = SyncErrorOut(code=run.error_code, message=run.error_message)
        stale_after = timedelta(minutes=SYNC_STALE_AFTER_MINUTES)
        if outcome is SyncOutcome.RUNNING and now - run.started_at > stale_after:
            outcome = SyncOutcome.FAILED
            error = SyncErrorOut(code=STALE_RUN_ERROR[0], message=STALE_RUN_ERROR[1])
        nothing_new = outcome is SyncOutcome.SUCCESS and run.added + run.updated == 0
        return cls(
            id=run.id,
            trigger=run.trigger,
            period=PeriodOut(start=run.period_start, end=run.period_end),
            started_at=run.started_at,
            finished_at=run.finished_at,
            outcome=outcome,
            windows=WindowsOut(total=run.windows_total, done=run.windows_done),
            counts=CountsOut(
                added=run.added, updated=run.updated, skipped=run.skipped, flagged=run.flagged
            ),
            error=error,
            hint=NO_NEW_DATA_HINT if nothing_new else None,
        )
