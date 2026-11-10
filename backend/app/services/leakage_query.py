"""Eligible payments and their stored leakage for any time range (003 plan, reusable).

Used by the dashboard, the chat tools and (later) the CA report, so every screen counts the same
rows the same way. Read-only.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.common.constants import MONTH_KEY_FORMAT
from app.common.dates import ist_date
from app.common.types import Money, TransactionSource
from app.engine.leakage import ELIGIBLE_KIND, ELIGIBLE_STATUS, LeakageRow
from app.models import Transaction
from app.schemas.leakage import leakage_status, stored_result


@dataclass(frozen=True)
class CollectedItem:
    """One included payment: the stored transaction and its calculated leakage row."""

    transaction: Transaction
    row: LeakageRow


@dataclass(frozen=True)
class Collected:
    transactions: list[Transaction]  # every eligible payment in the range, newest first
    items: list[CollectedItem]  # those with calculated leakage (the ones that are summed)
    excluded_count: int  # rate unavailable
    not_calculated_count: int  # fee greater than gross
    sources: list[TransactionSource]  # sources of included rows only

    @property
    def rows(self) -> list[LeakageRow]:
        return [item.row for item in self.items]


def eligible_in_range(start: datetime | None, end: datetime | None) -> Select[Transaction]:
    """Completed income with start <= occurred_at < end; a None bound is open."""
    query = select(Transaction).where(
        Transaction.kind == ELIGIBLE_KIND, Transaction.status == ELIGIBLE_STATUS
    )
    if start is not None:
        query = query.where(Transaction.occurred_at >= start)
    if end is not None:
        query = query.where(Transaction.occurred_at < end)
    return query.order_by(Transaction.occurred_at.desc(), Transaction.id)


def to_leakage_row(row: Transaction) -> LeakageRow | None:
    result = stored_result(row)
    if result is None:
        return None
    return LeakageRow(
        month=ist_date(row.occurred_at).strftime(MONTH_KEY_FORMAT),
        client_key=str(row.client_id),
        client_label=row.client.name,
        result=result,
        gross=Money(amount=row.gross_amount, currency=row.currency),
    )


def collect(session: Session, start: datetime | None, end: datetime | None) -> Collected:
    transactions = list(session.scalars(eligible_in_range(start, end)))
    items = [
        CollectedItem(transaction=t, row=r)
        for t, r in ((t, to_leakage_row(t)) for t in transactions)
        if r is not None
    ]
    statuses = [leakage_status(t) for t in transactions]
    return Collected(
        transactions=transactions,
        items=items,
        excluded_count=statuses.count("rate_unavailable"),
        not_calculated_count=statuses.count("not_calculated"),
        sources=sorted({item.transaction.source for item in items}),
    )
