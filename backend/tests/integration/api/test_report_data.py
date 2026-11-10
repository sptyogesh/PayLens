"""Report data equals GET /dashboard and GET /fira for the same period (005 FR-002, T002)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm import Session, sessionmaker

from app.ai.tools.fira_status import FiraStatusInput, fira_status
from app.common.constants import (
    NOT_TAX_ADVICE,
)
from app.common.periods import DashboardPeriod, NamedPeriod
from app.fakes.llm_fake import FakeLlm
from app.reports.labels import (
    REPORT_NOTE_SEED,
)
from app.services.report_service import build_report_data
from tests.fixtures.report import NOW, seed_demo_with_firas

DASHBOARD_KEYS = ("period", "totals", "by_month", "by_client", "excluded_count")


@pytest.mark.parametrize("period", list(DashboardPeriod))
def test_report_numbers_equal_the_dashboard(
    api: TestClient, session_factory: sessionmaker[Session], tmp_path: Path, period: str
) -> None:
    seed_demo_with_firas(session_factory, tmp_path)
    with freeze_time(NOW), session_factory() as session:
        dashboard = api.get("/dashboard", params={"period": period}).json()
        data = build_report_data(session, FakeLlm(), DashboardPeriod(period), NOW)
    body = data.model_dump(mode="json")
    for key in DASHBOARD_KEYS:
        assert body[key] == dashboard[key]
    assert body["not_calculated_count"] == dashboard["not_calculated_count"]
    assert body["simulated_spread_percent"] == dashboard["simulated_spread_percent"]
    assert body["disclaimer"] == NOT_TAX_ADVICE
    assert (REPORT_NOTE_SEED in body["notes"]) == ("demo_seed" in dashboard["sources"])
    assert body["generated_at"] == "2026-11-10T06:00:00Z"


def test_all_time_fira_equals_the_fira_page(
    api: TestClient, session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    seed_demo_with_firas(session_factory, tmp_path)
    listed = api.get("/fira").json()
    with session_factory() as session:
        data = build_report_data(session, FakeLlm(), DashboardPeriod.ALL_TIME, NOW)
    fira = data.fira.model_dump(mode="json")
    assert (fira["uploaded"], fira["matched"], fira["needs_review"]) == (21, 19, 2)
    assert fira["missing"] == listed["summary"]["missing_payments"] == 3
    expected = [
        {k: item[k] for k in ("date", "client", "paypal_transaction_id", "gross")}
        for item in listed["missing"]
    ]
    assert fira["missing_payments"] == expected
    assert data.gross_by_currency and all(g.currency != "INR" for g in data.gross_by_currency)
    assert data.summary.source == "ai"


def test_period_fira_equals_the_chat_tool(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    seed_demo_with_firas(session_factory, tmp_path)
    with session_factory() as session:
        data = build_report_data(session, FakeLlm(), DashboardPeriod.LAST_3_MONTHS, NOW)
        tool = fira_status(session, FiraStatusInput(period=NamedPeriod.LAST_3_MONTHS), NOW).content
    counts = (data.fira.matched, data.fira.needs_review, data.fira.missing)
    assert counts == (tool["matched_count"], tool["needs_review_count"], tool["missing_count"])
    ids = [p.paypal_transaction_id for p in data.fira.missing_payments]
    assert ids == [p["paypal_transaction_id"] for p in tool["missing"]]


def test_empty_database_has_no_totals(db_session: Session) -> None:
    data = build_report_data(db_session, FakeLlm(), DashboardPeriod.THIS_MONTH, NOW)
    assert data.totals is None and data.by_month == [] and data.gross_by_currency == []
    assert data.fira.uploaded == 0 and data.fira.missing_payments == []
    assert data.summary.source == "ai" and REPORT_NOTE_SEED not in data.notes
