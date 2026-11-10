"""Review fixes: database errors, bad JSON and /pay races during a sync never crash the run."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.common.http_client import make_client
from app.models import Transaction
from app.paypal import HttpPayPalGateway, SyncResult, TokenCache, run_sync
from app.paypal.dto import TransactionUpsert
from app.paypal.upsert import UpsertResult, upsert_transaction
from tests.fixtures.paypal.search import page, row

BASE = "https://api-m.sandbox.paypal.com"
SEARCH = f"{BASE}/v1/reporting/transactions"
START = datetime(2026, 8, 1, tzinfo=UTC)
TWO_WINDOWS = START + timedelta(days=40)


def gateway() -> HttpPayPalGateway:
    respx.post(f"{BASE}/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 3600})
    )
    client = make_client(BASE)
    return HttpPayPalGateway(client, TokenCache(client, "id", "secret"))


def ok(rows: list[dict[str, Any]]) -> httpx.Response:
    return httpx.Response(200, json=page(rows, 1, 1))


def stored_ids(factory: sessionmaker[Session]) -> list[str]:
    with factory() as session:
        query = select(Transaction.paypal_transaction_id).order_by(Transaction.occurred_at)
        return [str(tx_id) for tx_id in session.scalars(query)]


@respx.mock
def test_database_error_in_a_window_keeps_earlier_windows(
    session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_upsert(session: Session, dto: TransactionUpsert) -> UpsertResult:
        if dto.paypal_transaction_id == "B":
            raise OperationalError("INSERT", {}, Exception("connection lost"))
        return upsert_transaction(session, dto)

    monkeypatch.setattr("app.paypal.sync.upsert_transaction", failing_upsert)
    respx.get(SEARCH).mock(side_effect=[ok([row("A")]), ok([row("B")])])
    result = run_sync(session_factory, gateway(), START, TWO_WINDOWS)
    assert result.error is not None and result.error.code == "SYNC_STORE_FAILED"
    assert "connection lost" not in result.error.message
    assert (result.windows_done, result.added) == (1, 1)
    assert stored_ids(session_factory) == ["A"]


@respx.mock
def test_non_json_page_is_a_rejected_window(session_factory: sessionmaker[Session]) -> None:
    bad = httpx.Response(200, content=b"<html>oops</html>")
    respx.get(SEARCH).mock(side_effect=[ok([row("A")]), bad])
    result = run_sync(session_factory, gateway(), START, TWO_WINDOWS)
    assert result.error is not None and result.error.code == "PAYPAL_REJECTED"
    assert (result.windows_done, result.added) == (1, 1)


@respx.mock
def test_value_error_while_mapping_is_a_rejected_window(
    session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    def bad_select(*_args: object) -> list[TransactionUpsert]:
        raise ValueError("bad amount")

    monkeypatch.setattr("app.paypal.sync.select_rows", bad_select)
    respx.get(SEARCH).mock(return_value=ok([row("A")]))
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=5))
    assert result.error is not None and result.error.code == "PAYPAL_REJECTED"
    assert (result.windows_done, result.added) == (0, 0)


@respx.mock
def test_unexpected_error_restores_window_counts_and_reraises(
    session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_upsert(session: Session, dto: TransactionUpsert) -> UpsertResult:
        if dto.paypal_transaction_id == "C":
            raise RuntimeError("bug")
        return upsert_transaction(session, dto)

    monkeypatch.setattr("app.paypal.sync.upsert_transaction", broken_upsert)
    respx.get(SEARCH).mock(side_effect=[ok([row("A")]), ok([row("B"), row("C")])])
    result = SyncResult()
    with pytest.raises(RuntimeError):
        run_sync(session_factory, gateway(), START, TWO_WINDOWS, result)
    assert (result.windows_done, result.added, result.error) == (1, 1, None)
