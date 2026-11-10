"""Sync coordinator: windows → pages → classify/map → upsert, committing per window.

A failure in window k keeps windows 1..k-1 and rolls window k back in full (FR-018, Test P6).
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.common.constants import PAYPAL_FIRST_PAGE, PAYPAL_MAX_PAGES_PER_WINDOW, PAYPAL_WINDOW_DAYS
from app.common.dates import split_windows
from app.common.errors import AppError, PayPalError
from app.paypal.classify import counts_as_income
from app.paypal.dto import SearchRow, TransactionUpsert
from app.paypal.gateway import PayPalGateway
from app.paypal.mapper import from_search_row
from app.paypal.upsert import upsert_transaction

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]
STORE_FAILED_MESSAGE = "PayLens could not save the synced payments. Please try again."
BAD_DATA_MESSAGE = "PayPal returned transaction data in an unexpected format."
HANDLED_ERRORS = (AppError, SQLAlchemyError, ValueError)


@dataclass
class SyncResult:
    windows_total: int = 0
    windows_done: int = 0
    added: int = 0
    updated: int = 0
    skipped: int = 0
    flagged: int = 0
    truncated: bool = False
    error: AppError | None = None
    seen_ids: set[str] = field(default_factory=set)


def select_rows(rows: list[SearchRow], result: SyncResult) -> list[TransactionUpsert]:
    """Map rows. A transaction ID seen twice keeps the income row (research R5)."""
    chosen: dict[str, TransactionUpsert] = {}
    for row in rows:
        dto = from_search_row(row.detail, row.raw)
        tx_id = dto.paypal_transaction_id
        if tx_id in result.seen_ids:  # already stored by an earlier window in this run
            result.flagged += 1
            continue
        previous = chosen.get(tx_id)
        if previous is not None:
            result.flagged += 1
            logger.warning("Duplicate transaction ID in sync (event %s)", dto.event_code)
            if not counts_as_income(dto.kind, dto.status):
                continue
        chosen[tx_id] = dto
    return list(chosen.values())


def store(session: Session, dtos: list[TransactionUpsert], result: SyncResult) -> None:
    for dto in dtos:
        outcome = upsert_transaction(session, dto)
        result.seen_ids.add(dto.paypal_transaction_id)
        result.flagged += dto.flag_reason is not None
        if not counts_as_income(dto.kind, dto.status):
            result.skipped += 1
        elif outcome == "added":
            result.added += 1
        else:
            result.updated += 1


def sync_window(
    session: Session, gateway: PayPalGateway, window: tuple[datetime, datetime], result: SyncResult
) -> None:
    page, rows = PAYPAL_FIRST_PAGE, []
    while True:
        search = gateway.search_transactions(window[0], window[1], page)
        rows.extend(search.rows)
        if page >= search.total_pages:
            break
        if page >= PAYPAL_MAX_PAGES_PER_WINDOW:
            result.truncated = True
            break
        page += 1
    store(session, select_rows(rows, result), result)


def window_error(error: Exception) -> AppError:
    """The safe, coded error recorded for a failed window (earlier windows stay stored)."""
    if isinstance(error, AppError):
        return error
    if isinstance(error, SQLAlchemyError):
        return AppError(STORE_FAILED_MESSAGE, code="SYNC_STORE_FAILED")
    return PayPalError(BAD_DATA_MESSAGE, code="PAYPAL_REJECTED")  # bad JSON or field values


def run_sync(
    session_factory: SessionFactory,
    gateway: PayPalGateway,
    start: datetime,
    end: datetime,
    result: SyncResult | None = None,
) -> SyncResult:
    """Sync window by window into `result` (pass one in to keep it if an unexpected error is
    re-raised). Known failures stop the run and are recorded in `result.error`."""
    windows = split_windows(start, end, PAYPAL_WINDOW_DAYS)
    result = SyncResult() if result is None else result
    result.windows_total = len(windows)
    for window in windows:
        with session_factory() as session:
            snapshot = (result.added, result.updated, result.skipped, result.flagged)
            try:
                sync_window(session, gateway, window, result)
                session.commit()
            except Exception as error:
                session.rollback()
                result.added, result.updated, result.skipped, result.flagged = snapshot
                if not isinstance(error, HANDLED_ERRORS):
                    raise
                result.error = window_error(error)
                logger.error("Sync window failed: %s (%s)", result.error.code, type(error).__name__)
                return result
        result.windows_done += 1
    return result
