"""CA report data (005 FR-002): the dashboard numbers, gross by currency, FIRA status and notes.

Every number comes from the services behind GET /dashboard and GET /fira; the LLM only writes
the summary (ai/report_summary.py), which is grounded against this data or replaced by code.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.llm import LlmClient
from app.ai.report_summary import write_summary
from app.common.constants import (
    NOT_TAX_ADVICE,
)
from app.common.dates import ensure_utc, ist_date
from app.common.periods import DashboardPeriod, resolve
from app.common.types import FiraStatus, TransactionSource
from app.engine.leakage import gross_by_currency
from app.models import FiraDocument, Transaction
from app.reports.format import is_printable
from app.reports.labels import (
    REPORT_NOTE_ECB,
    REPORT_NOTE_EXCLUDED,
    REPORT_NOTE_SANDBOX,
    REPORT_NOTE_SEED,
    REPORT_NOTE_SIMULATED,
    REPORT_NOTE_UNPRINTABLE,
)
from app.schemas.common import MoneyOut
from app.schemas.dashboard import DashboardOut
from app.schemas.report import ReportData, ReportFigures, ReportFira, ReportMissingPayment
from app.services.dashboard_service import dashboard_from
from app.services.fira_query import payment_fira_status
from app.services.leakage_query import collect, eligible_in_range


def missing_payment(row: Transaction) -> ReportMissingPayment:
    return ReportMissingPayment(
        date=ist_date(row.occurred_at),
        client=row.client.name,
        paypal_transaction_id=row.paypal_transaction_id,
        gross=MoneyOut.of(row.gross_amount, row.currency),
    )


def fira_part(session: Session, start: datetime | None) -> ReportFira:
    """FIRA status of the eligible payments in the period (same rows as the dashboard)."""
    rows = list(session.scalars(eligible_in_range(start, None)))
    statuses = [payment_fira_status(row) for row in rows]
    pairs = zip(rows, statuses, strict=True)
    missing = [row for row, status in pairs if status is FiraStatus.MISSING]
    return ReportFira(
        uploaded=session.scalar(select(func.count()).select_from(FiraDocument)) or 0,
        matched=statuses.count(FiraStatus.MATCHED),
        needs_review=statuses.count(FiraStatus.NEEDS_REVIEW),
        missing=len(missing),
        missing_payments=[missing_payment(row) for row in missing],
    )


def notes_for(dashboard: DashboardOut) -> list[str]:
    """Data notes (Principle VII): always sandbox, simulated rate and ECB; the rest when true."""
    notes = [
        REPORT_NOTE_SANDBOX,
        REPORT_NOTE_SIMULATED.format(spread=dashboard.simulated_spread_percent),
        REPORT_NOTE_ECB,
    ]
    if TransactionSource.DEMO_SEED in dashboard.sources:
        notes.append(REPORT_NOTE_SEED)
    if dashboard.excluded_count or dashboard.not_calculated_count:
        notes.append(REPORT_NOTE_EXCLUDED)
    return notes


def build_figures(session: Session, period: DashboardPeriod, now: datetime) -> ReportFigures:
    start, _ = resolve(period, now)
    data = collect(session, start, None)
    dashboard = dashboard_from(data, period, now)
    return ReportFigures(
        period=dashboard.period,
        generated_at=ensure_utc(now),
        totals=dashboard.totals,
        gross_by_currency=[MoneyOut.from_money(m) for m in gross_by_currency(data.rows)],
        by_month=dashboard.by_month,
        by_client=dashboard.by_client,
        excluded_count=dashboard.excluded_count,
        not_calculated_count=dashboard.not_calculated_count,
        simulated_spread_percent=dashboard.simulated_spread_percent,
        fira=fira_part(session, start),
        notes=notes_for(dashboard),
        disclaimer=NOT_TAX_ADVICE,
    )


def build_report_data(
    session: Session, llm: LlmClient, period: DashboardPeriod, now: datetime
) -> ReportData:
    figures = build_figures(session, period, now)
    names = [row.label for row in figures.by_client]
    names += [payment.client for payment in figures.fira.missing_payments]
    if not all(is_printable(name) for name in names):
        figures = figures.model_copy(update={"notes": [*figures.notes, REPORT_NOTE_UNPRINTABLE]})
    summary = write_summary(llm, figures)
    return ReportData.model_validate({**figures.model_dump(), "summary": summary.model_dump()})
