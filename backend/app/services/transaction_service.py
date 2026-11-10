"""Read transactions for the list (FR-023): newest first, filterable by kind and source."""

from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.common.types import TransactionKind, TransactionSource
from app.models import Transaction

KindFilter = Literal["income", "all"]


def filtered(kind: KindFilter, source: TransactionSource | None) -> Select[Transaction]:
    query = select(Transaction)
    if kind == "income":
        query = query.where(Transaction.kind == TransactionKind.INCOME)
    if source is not None:
        query = query.where(Transaction.source == source)
    return query


def list_transactions(
    session: Session,
    page: tuple[int, int],
    kind: KindFilter = "income",
    source: TransactionSource | None = None,
) -> tuple[list[Transaction], int]:
    limit, offset = page
    query = filtered(kind, source)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.scalars(
        query.order_by(Transaction.occurred_at.desc(), Transaction.id).limit(limit).offset(offset)
    )
    return list(rows), total
