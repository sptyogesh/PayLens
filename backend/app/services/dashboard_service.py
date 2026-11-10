"""Dashboard numbers for a period (FR-030 to FR-036). Totals come from the leakage engine."""

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.common.constants import MONTH_KEY_FORMAT, PERCENT_FACTOR, SIMULATED_FX_SPREAD
from app.common.dates import ist_date
from app.common.money import to_percent_string
from app.common.periods import PERIOD_LABELS, DashboardPeriod, resolve
from app.engine.leakage import (
    ELIGIBLE_KIND,
    ELIGIBLE_STATUS,
    LeakageRow,
    by_client,
    by_month,
    totals,
)
from app.models import Transaction
from app.schemas.dashboard import BreakdownRowOut, DashboardOut, DashboardPeriodOut, TotalsOut
from app.schemas.leakage import leakage_status, stored_result


def eligible_in_period(start: datetime | None, end: datetime | None) -> Select[Transaction]:
    query = select(Transaction).where(
        Transaction.kind == ELIGIBLE_KIND, Transaction.status == ELIGIBLE_STATUS
    )
    if start is not None:
        query = query.where(Transaction.occurred_at >= start)
    if end is not None:
        query = query.where(Transaction.occurred_at <= end)
    return query


def to_leakage_row(row: Transaction) -> LeakageRow | None:
    result = stored_result(row)
    if result is None:
        return None
    return LeakageRow(
        month=ist_date(row.occurred_at).strftime(MONTH_KEY_FORMAT),
        client_key=str(row.client_id),
        client_label=row.client.name,
        result=result,
    )


def get_dashboard(session: Session, period: DashboardPeriod, now: datetime) -> DashboardOut:
    start, end = resolve(period, now)
    transactions = list(session.scalars(eligible_in_period(start, end)))
    included = [(t, r) for t, r in ((t, to_leakage_row(t)) for t in transactions) if r is not None]
    rows = [r for _, r in included]
    statuses = [leakage_status(t) for t in transactions]
    return DashboardOut(
        period=DashboardPeriodOut(key=period, label=PERIOD_LABELS[period], start=start, end=end),
        totals=TotalsOut.of(totals(rows)) if rows else None,
        excluded_count=statuses.count("rate_unavailable"),
        not_calculated_count=statuses.count("not_calculated"),
        sources=sorted({t.source for t, _ in included}),
        simulated_spread_percent=to_percent_string(SIMULATED_FX_SPREAD * PERCENT_FACTOR),
        by_month=[BreakdownRowOut.of(g) for g in by_month(rows)],
        by_client=[BreakdownRowOut.of(g) for g in by_client(rows)],
    )
