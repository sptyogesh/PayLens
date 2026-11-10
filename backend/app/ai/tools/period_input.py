"""The period every chat tool accepts: a named period or explicit IST dates (FR-003)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.constants import CHAT_EARLIEST_DATE, CHAT_LATEST_DATE
from app.common.periods import (
    DEFAULT_NAMED_PERIOD,
    NamedPeriod,
    ResolvedPeriod,
    resolve_dates,
    resolve_named,
)


class PeriodInput(BaseModel):
    """Either `period`, or both `start` and `end`; neither means the last 3 months."""

    model_config = ConfigDict(extra="forbid")

    period: NamedPeriod | None = Field(
        default=None,
        description="Named period in India time. Calendar quarters; financial year is 1 Apr-31 Mar."
        " Leave empty when giving start and end. Default: last_3_months.",
    )
    start: date | None = Field(
        default=None, description="First day (YYYY-MM-DD, India time). Requires end."
    )
    end: date | None = Field(
        default=None, description="Last day, inclusive (YYYY-MM-DD, India time). Requires start."
    )

    @field_validator("start", "end")
    @classmethod
    def within_supported_range(cls, value: date | None) -> date | None:
        """Far-past or far-future dates would overflow datetime arithmetic; reject them."""
        if value is not None and not CHAT_EARLIEST_DATE <= value <= CHAT_LATEST_DATE:
            raise ValueError(f"dates must be between {CHAT_EARLIEST_DATE} and {CHAT_LATEST_DATE}")
        return value

    @model_validator(mode="after")
    def one_way_to_give_the_period(self) -> "PeriodInput":
        has_start, has_end = self.start is not None, self.end is not None
        if self.period is not None and (has_start or has_end):
            raise ValueError("give either period or start and end, not both")
        if has_start != has_end:
            raise ValueError("start and end must be given together")
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must not be after end")
        return self

    def resolve(self, now: datetime) -> ResolvedPeriod:
        if self.start is not None and self.end is not None:
            return resolve_dates(self.start, self.end, now)
        return resolve_named(self.period or DEFAULT_NAMED_PERIOD, now)


class PeriodOut(BaseModel):
    """The resolved period, repeated in every tool result so the answer can state it."""

    label: str
    start_date: date | None
    end_date: date | None

    @classmethod
    def of(cls, resolved: ResolvedPeriod) -> "PeriodOut":
        return cls(label=resolved.label, start_date=resolved.start_date, end_date=resolved.end_date)
