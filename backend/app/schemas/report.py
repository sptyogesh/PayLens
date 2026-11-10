"""GET /report/data: the exact data the CA report PDF is built from (005 contracts/http-api.md).

Every value except `summary.text` (when the source is "ai") is computed by code. The dashboard
parts reuse the GET /dashboard models, so both screens show the same numbers.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import MoneyOut, UtcDatetime
from app.schemas.dashboard import BreakdownRowOut, DashboardPeriodOut, TotalsOut

SummarySource = Literal["ai", "code"]


class ReportMissingPayment(BaseModel):
    date: date
    client: str
    paypal_transaction_id: str
    gross: MoneyOut


class ReportFira(BaseModel):
    """FIRA status of the eligible payments in the period; `uploaded` counts every FIRA stored."""

    uploaded: int
    matched: int
    needs_review: int
    missing: int
    missing_payments: list[ReportMissingPayment]


class ReportSummary(BaseModel):
    text: str
    source: SummarySource


class ReportFigures(BaseModel):
    """Everything in the report except the summary (this is what the LLM is shown)."""

    period: DashboardPeriodOut
    generated_at: UtcDatetime
    totals: TotalsOut | None
    gross_by_currency: list[MoneyOut]
    by_month: list[BreakdownRowOut]
    by_client: list[BreakdownRowOut]
    excluded_count: int
    not_calculated_count: int
    simulated_spread_percent: str
    fira: ReportFira
    notes: list[str]
    disclaimer: str


class ReportData(ReportFigures):
    summary: ReportSummary
