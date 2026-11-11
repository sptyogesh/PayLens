"""Required Tests P1–P8 for the sync coordinator (respx-mocked PayPal + real PostgreSQL)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import respx
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.common.http_client import make_client
from app.common.types import TransactionKind
from app.models import Transaction
from app.paypal import HttpPayPalGateway, TokenCache
from app.paypal.sync import run_sync
from tests.fixtures.paypal.search import page, row

BASE = "https://api-m.sandbox.paypal.com"
SEARCH = f"{BASE}/v1/reporting/transactions"
START = datetime(2026, 8, 1, tzinfo=UTC)


def gateway() -> HttpPayPalGateway:
    respx.post(f"{BASE}/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 3600})
    )
    client = make_client(BASE)
    return HttpPayPalGateway(client, TokenCache(client, "id", "secret"))


def ok(rows: list[dict[str, Any]], number: int = 1, total: int = 1) -> httpx.Response:
    return httpx.Response(200, json=page(rows, number, total))


def stored(factory: sessionmaker[Session]) -> list[Transaction]:
    with factory() as session:
        return list(
            session.scalars(select(Transaction).order_by(Transaction.paypal_transaction_id))
        )


def no_sleep(monkeypatch: Any) -> None:
    monkeypatch.setattr("app.common.http_client.time.sleep", lambda _s: None)


@respx.mock
def test_p1_75_days_makes_three_window_requests(session_factory: sessionmaker[Session]) -> None:
    route = respx.get(SEARCH).mock(return_value=ok([]))
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=75))
    assert route.call_count == 3
    assert (result.windows_total, result.windows_done) == (3, 3)


@respx.mock
def test_p2_all_pages_are_fetched(session_factory: sessionmaker[Session]) -> None:
    route = respx.get(SEARCH).mock(
        side_effect=[ok([row("A")], 1, 3), ok([row("B")], 2, 3), ok([row("C")], 3, 3)]
    )
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    assert route.call_count == 3
    assert [t.paypal_transaction_id for t in stored(session_factory)] == ["A", "B", "C"]
    assert result.added == 3


@respx.mock
def test_p3_running_twice_creates_no_duplicates(session_factory: sessionmaker[Session]) -> None:
    respx.get(SEARCH).mock(return_value=ok([row("A"), row("B")]))
    first = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    second = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    assert (first.added, second.added, second.updated) == (2, 0, 2)
    assert len(stored(session_factory)) == 2


@respx.mock
def test_p4_rate_limit_then_success(
    session_factory: sessionmaker[Session], monkeypatch: Any
) -> None:
    no_sleep(monkeypatch)
    respx.get(SEARCH).mock(side_effect=[httpx.Response(429), ok([row("A")])])
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    assert (result.error, result.added) == (None, 1)


@respx.mock
def test_p5_expired_token_is_refreshed(session_factory: sessionmaker[Session]) -> None:
    respx.get(SEARCH).mock(side_effect=[httpx.Response(401), ok([row("A")])])
    assert run_sync(session_factory, gateway(), START, START + timedelta(days=10)).added == 1


@respx.mock
def test_p6_failed_window_keeps_earlier_windows_only(
    session_factory: sessionmaker[Session], monkeypatch: Any
) -> None:
    no_sleep(monkeypatch)
    respx.get(SEARCH).mock(side_effect=[ok([row("A")]), *[httpx.Response(500)] * 4])
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=40))
    assert result.error is not None and result.error.code == "PAYPAL_UNAVAILABLE"
    assert (result.windows_done, result.added) == (1, 1)
    assert [t.paypal_transaction_id for t in stored(session_factory)] == ["A"]


@respx.mock
def test_p7_p8_fee_positive_and_non_payments_stored_but_skipped(
    session_factory: sessionmaker[Session],
) -> None:
    rows = [row("PAY", fee="-3.98"), row("WD", amount="-50.00", fee=None, code="T0400")]
    rows.append(row("RF", amount="-20.00", fee=None, code="T1107"))
    respx.get(SEARCH).mock(return_value=ok(rows))
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    assert (result.added, result.skipped) == (1, 2)
    by_id = {t.paypal_transaction_id: t for t in stored(session_factory)}
    assert str(by_id["PAY"].fee_amount) == "3.98"
    assert by_id["WD"].kind is TransactionKind.WITHDRAWAL
    assert by_id["RF"].kind is TransactionKind.REFUND


@respx.mock
def test_duplicate_id_in_a_page_keeps_income_row_and_flags(
    session_factory: sessionmaker[Session],
) -> None:
    rows = [row("X", amount="-1.00", fee=None, code="T0400"), row("X")]
    respx.get(SEARCH).mock(return_value=ok(rows))
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=10))
    assert (result.added, result.flagged) == (1, 1)
    assert stored(session_factory)[0].kind is TransactionKind.INCOME


@respx.mock
def test_empty_window_with_zero_pages(session_factory: sessionmaker[Session]) -> None:
    respx.get(SEARCH).mock(return_value=ok([], 1, 0))
    with session_factory() as session:
        before = session.scalar(select(func.count()).select_from(Transaction))
    result = run_sync(session_factory, gateway(), START, START + timedelta(days=5))
    assert (result.added, result.error, before) == (0, None, 0)
