"""GET /transactions: newest first, every row carries its source label (FR-023, FR-050)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.constants import TRANSACTIONS_PAGE_DEFAULT, TRANSACTIONS_PAGE_MAX
from app.common.types import TransactionSource
from app.db import get_session
from app.schemas.transaction import TransactionListOut, TransactionOut
from app.services.transaction_service import KindFilter, list_transactions

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def get_transactions(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=TRANSACTIONS_PAGE_MAX)] = TRANSACTIONS_PAGE_DEFAULT,
    offset: Annotated[int, Query(ge=0)] = 0,
    kind: KindFilter = "income",
    source: TransactionSource | None = None,
) -> TransactionListOut:
    rows, total = list_transactions(session, (limit, offset), kind, source)
    items = [TransactionOut.from_model(row) for row in rows]
    return TransactionListOut(items=items, total=total, limit=limit, offset=offset)
