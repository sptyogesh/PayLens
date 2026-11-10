"""A2 and FR-030 to FR-036: GET /dashboard."""

import re
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.common.types import TransactionKind, TransactionSource, TransactionStatus
from app.fakes.fx_fake import FakeFxGateway
from app.services.leakage_service import recalculate_leakage
from tests.fixtures.rows import add_client, add_tx

MONEY = re.compile(r"^-?\d+\.\d{2}$")
NOW = "2026-11-10 06:00:00"
NOV, SEP, JUN = (datetime(2026, m, 6, 6, 30, tzinfo=UTC) for m in (11, 9, 6))


def seed(session: Session) -> None:
    ava, ben = add_client(session), add_client(session, "Ben Lee", "GBP")
    add_tx(session, ava, "NOV", occurred_at=NOV)
    add_tx(session, ben, "SEP", occurred_at=SEP, gross="200.00", fee="9.00")
    add_tx(session, ava, "JUN", occurred_at=JUN, source=TransactionSource.DEMO_SEED)
    add_tx(session, ava, "WD", occurred_at=NOV, kind=TransactionKind.WITHDRAWAL)
    add_tx(session, ava, "PEND", occurred_at=NOV, status=TransactionStatus.PENDING)
    recalculate_leakage(session, FakeFxGateway())
    session.commit()


def money(body: dict[str, object], key: str) -> Decimal:
    value = body[key]
    assert isinstance(value, dict) and value["currency"] == "INR" and MONEY.match(value["amount"])
    return Decimal(value["amount"])


@freeze_time(NOW)
def test_a2_default_period_is_last_3_months(api: TestClient, db_session: Session) -> None:
    seed(db_session)
    body = api.get("/dashboard").json()
    assert body["period"]["key"] == "last_3_months"
    assert body["period"]["start"] == "2026-08-31T18:30:00Z"
    totals = body["totals"]
    assert totals["payment_count"] == 2
    assert money(totals, "income_inr") == Decimal("84000.00") + Decimal("21300.00")
    assert body["sources"] == ["paypal_sandbox"]
    assert body["paypal_rate_simulated"] is True
    assert body["simulated_spread_percent"] == "3.00"


@freeze_time(NOW)
def test_periods_change_the_totals(api: TestClient, db_session: Session) -> None:
    seed(db_session)
    counts = {
        p: api.get("/dashboard", params={"period": p}).json() for p in ("this_month", "all_time")
    }
    assert counts["this_month"]["totals"]["payment_count"] == 1
    assert counts["all_time"]["totals"]["payment_count"] == 3
    assert counts["all_time"]["sources"] == ["demo_seed", "paypal_sandbox"]
    assert counts["all_time"]["period"]["start"] is None


@freeze_time(NOW)
def test_breakdowns_add_up_to_totals(api: TestClient, db_session: Session) -> None:
    seed(db_session)
    body = api.get("/dashboard", params={"period": "all_time"}).json()
    for field in ("income_inr", "fee_loss_inr", "fx_loss_inr", "total_leakage_inr"):
        for rows in (body["by_month"], body["by_client"]):
            assert sum(money(r["totals"], field) for r in rows) == money(body["totals"], field)
    assert [r["key"] for r in body["by_month"]] == ["2026-11", "2026-09", "2026-06"]
    assert [r["label"] for r in body["by_client"]] == ["Ava Stone", "Ben Lee"]


@freeze_time(NOW)
def test_empty_period_has_no_totals(api: TestClient) -> None:
    body = api.get("/dashboard", params={"period": "this_month"}).json()
    assert (body["totals"], body["excluded_count"], body["by_month"]) == (None, 0, [])


@freeze_time(NOW)
def test_rate_unavailable_rows_are_counted_not_summed(api: TestClient, db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "NOV", occurred_at=NOV)
    recalculate_leakage(db_session, FakeFxGateway(unavailable=True))
    db_session.commit()
    body = api.get("/dashboard").json()
    assert (body["totals"], body["excluded_count"]) == (None, 1)
    assert body["sources"] == []  # nothing included, so no source is claimed


def test_unknown_period_is_422(api: TestClient) -> None:
    response = api.get("/dashboard", params={"period": "forever"})
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_ERROR")


@freeze_time(NOW)
def test_a2_card_values_match_section_10(api: TestClient, db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "NOV", occurred_at=NOV)
    recalculate_leakage(db_session, FakeFxGateway())
    db_session.commit()
    totals = api.get("/dashboard").json()["totals"]
    assert money(totals, "fee_loss_inr") == Decimal("3696.00")  # 44 x 84
    assert money(totals, "fx_loss_inr") == Decimal("2409.12")  # 956 x (84 - 81.48)
    assert money(totals, "total_leakage_inr") == Decimal("6105.12")
    assert totals["leakage_percent"] == "7.27"


@freeze_time(NOW)
def test_ist_month_boundary(api: TestClient, db_session: Session) -> None:
    client = add_client(db_session)
    add_tx(db_session, client, "IN", occurred_at=datetime(2026, 10, 31, 19, 0, tzinfo=UTC))
    add_tx(db_session, client, "OUT", occurred_at=datetime(2026, 10, 31, 18, 29, tzinfo=UTC))
    recalculate_leakage(db_session, FakeFxGateway())
    db_session.commit()
    this_month = api.get("/dashboard", params={"period": "this_month"}).json()
    assert this_month["totals"]["payment_count"] == 1
    months = api.get("/dashboard", params={"period": "all_time"}).json()["by_month"]
    assert [(m["key"], m["totals"]["payment_count"]) for m in months] == [
        ("2026-11", 1),
        ("2026-10", 1),
    ]


@freeze_time(NOW)
def test_invalid_rows_are_not_called_rate_unavailable(api: TestClient, db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "BAD", occurred_at=NOV, gross="40.00", fee="50.00")
    recalculate_leakage(db_session, FakeFxGateway())
    db_session.commit()
    body = api.get("/dashboard").json()
    assert (body["excluded_count"], body["not_calculated_count"]) == (0, 1)
    assert (body["totals"], body["sources"]) == (None, [])
