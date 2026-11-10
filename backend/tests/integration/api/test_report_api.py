"""GET /report.pdf and GET /report/data (005 contracts): headers, SC-001, fallback, limits."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_llm
from app.common.constants import (
    NOT_TAX_ADVICE,
    RATE_LIMIT_REPORT,
    REPORT_NO_PAYMENTS,
)
from app.fakes.llm_fake import FakeLlm
from app.fakes.llm_fake_report import ReportMode
from app.reports.labels import (
    REPORT_NO_FIRAS,
    REPORT_SUMMARY_AI_HEADING,
    REPORT_SUMMARY_CODE_HEADING,
)
from app.schemas.report import ReportData
from tests.fixtures.pdf_text import pdf_text
from tests.fixtures.report import NOW, seed_demo_with_firas
from tests.fixtures.report_checks import missing_from_pdf, numbers_not_in_data


def fetch(api: TestClient, period: str) -> tuple[ReportData, str]:
    with freeze_time(NOW):
        data = ReportData.model_validate(api.get("/report/data", params={"period": period}).json())
        response = api.get("/report.pdf", params={"period": period})
    assert response.status_code == 200, response.text
    return data, pdf_text(response.content)


def test_pdf_headers_and_file_name(api: TestClient) -> None:
    with freeze_time(NOW):
        response = api.get("/report.pdf", params={"period": "all_time"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    disposition = response.headers["content-disposition"]
    assert disposition == 'attachment; filename="paylens-ca-report-all_time-2026-11-10.pdf"'
    assert response.content.startswith(b"%PDF-")


def test_default_period_is_last_3_months(api: TestClient) -> None:
    with freeze_time(NOW):
        body = api.get("/report/data").json()
        name = api.get("/report.pdf").headers["content-disposition"]
    assert body["period"]["key"] == "last_3_months" and "last_3_months" in name


@pytest.mark.parametrize("period", ["last_3_months", "all_time"])
def test_every_number_both_ways(
    api: TestClient, session_factory: sessionmaker[Session], tmp_path: Path, period: str
) -> None:
    seed_demo_with_firas(session_factory, tmp_path)
    data, text = fetch(api, period)
    assert data.totals is not None and data.summary.source == "ai"
    assert missing_from_pdf(data, text) == []
    assert numbers_not_in_data(data, text) == []
    assert NOT_TAX_ADVICE in text and "Simulated (sandbox)" in text
    assert all(note in text for note in data.notes)
    assert f"{REPORT_SUMMARY_AI_HEADING} For " in text and "₹" in data.summary.text
    assert data.summary.text.replace("₹", "INR ") in text
    assert f"Payments missing a FIRA {data.fira.missing}" in text
    assert f"Payments {data.totals.payment_count}" in text


def test_empty_period_still_downloads(api: TestClient) -> None:
    data, text = fetch(api, "this_month")
    assert data.totals is None
    assert REPORT_NO_PAYMENTS in text and REPORT_NO_FIRAS in text and NOT_TAX_ADVICE in text
    assert "By month" not in text


@pytest.mark.parametrize("mode", ["fail", "invent"])
def test_ai_problem_uses_code_summary_and_pdf_renders(
    api: TestClient, session_factory: sessionmaker[Session], tmp_path: Path, mode: ReportMode
) -> None:
    seed_demo_with_firas(session_factory, tmp_path)
    assert isinstance(api.app, FastAPI)
    api.app.dependency_overrides[get_llm] = lambda: FakeLlm(report_mode=mode)
    data, text = fetch(api, "all_time")
    assert data.summary.source == "code" and "99,999.99" not in text
    assert f"{REPORT_SUMMARY_CODE_HEADING} {data.summary.text}" in text
    assert REPORT_SUMMARY_AI_HEADING not in text
    assert numbers_not_in_data(data, text) == []


@pytest.mark.parametrize("path", ["/report.pdf", "/report/data"])
def test_unknown_period_is_422(api: TestClient, path: str) -> None:
    response = api.get(path, params={"period": "last_year"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_report_is_rate_limited(api: TestClient) -> None:
    limit = RATE_LIMIT_REPORT[0]
    paths = ["/report/data", "/report.pdf"] * limit
    statuses = [api.get(path).status_code for path in paths[: limit + 1]]
    assert statuses == [200] * limit + [429]
    assert api.get("/report.pdf").json()["error"]["code"] == "RATE_LIMITED"
