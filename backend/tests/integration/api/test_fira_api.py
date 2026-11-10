"""POST /fira/upload, GET /fira and fira_status on /transactions (004 contracts; fake LLM)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm import Session, sessionmaker

from app.common.constants import FIRA_MAX_BYTES
from app.config import get_settings
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.llm_fake import FakeLlm
from app.services.refresh_service import safe_refresh
from scripts.generate_fira_samples import generate
from scripts.seed_demo import seed
from tests.fixtures.fira import fira_pdf

PDF = {"content-type": "application/pdf"}
NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)


def post(api: TestClient, body: bytes, name: str = "fira.pdf", **headers: str) -> dict[str, object]:
    response = api.post("/fira/upload", params={"file_name": name}, content=body, headers=headers)
    assert response.status_code == 200, response.text
    result: dict[str, object] = response.json()
    return result


def outcome(body: dict[str, object]) -> object:
    result = body["result"]
    assert isinstance(result, dict)
    return result["outcome"]


def test_upload_returns_result_and_summary(api: TestClient) -> None:
    body = post(api, fira_pdf(), **PDF)
    result = body["result"]
    assert isinstance(result, dict)
    assert result["outcome"] == "stored" and result["status"] == "no_match"
    assert result["file_name"] == "fira.pdf" and result["fira_id"]
    assert body["summary"] == {
        "matched": 0,
        "needs_review": 0,
        "no_match": 1,
        "missing_payments": 0,
    }


def test_duplicate_and_rejections_are_outcomes(api: TestClient, fake_llm: FakeLlm) -> None:
    post(api, fira_pdf(), **PDF)
    calls = len(fake_llm.requests)
    assert outcome(post(api, fira_pdf(), **PDF)) == "duplicate"
    rejected = [
        post(api, b"plain text", **PDF),
        post(api, fira_pdf(reference_no="X"), **{"content-type": "text/plain"}),
        post(api, b"%PDF-" + b"0" * (FIRA_MAX_BYTES + 10), **PDF),
        post(api, fira_pdf(reference_no="Y"), "fira.docx", **PDF),
    ]
    assert all(outcome(r) == "rejected" for r in rejected)
    assert len(fake_llm.requests) == calls  # E6: no AI call for rejected or duplicate files


def test_missing_or_blank_file_name_is_422(api: TestClient) -> None:
    assert api.post("/fira/upload", content=fira_pdf(), headers=PDF).status_code == 422
    blank = api.post("/fira/upload", params={"file_name": "  "}, content=b"%PDF-", headers=PDF)
    assert blank.status_code == 422
    assert blank.json()["error"]["code"] == "VALIDATION_ERROR"


def test_failed_extraction_is_200_failed(api: TestClient) -> None:
    result = post(api, fira_pdf(fake_mode="non_json"), **PDF)["result"]
    assert isinstance(result, dict) and result["outcome"] == "failed"
    assert api.get("/fira").json()["items"] == []


def test_sample_firas_give_the_expected_split(
    api: TestClient,
    session_factory: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")  # 21 uploads in one go, as in E2E
    get_settings.cache_clear()
    with freeze_time(NOW), session_factory() as session:
        seed(session)
        session.commit()
    safe_refresh(session_factory, FakeFxGateway())
    missing_before = api.get("/fira").json()["summary"]["missing_payments"]
    assert missing_before == 24
    for path in generate(tmp_path, NOW):
        post(api, path.read_bytes(), path.name, **PDF)
    listed = api.get("/fira").json()
    assert listed["summary"] == {
        "matched": 19,
        "needs_review": 2,
        "no_match": 0,
        "missing_payments": 3,
    }
    review = {i["reference_no"]: i for i in listed["items"] if i["status"] == "needs_review"}
    assert set(review) == {"SEED-0020", "SEED-0021"}
    assert (review["SEED-0020"]["score"], review["SEED-0021"]["score"]) == (75, 60)
    assert review["SEED-0020"]["matches"][0]["paypal_transaction_id"] == "SEED-0020"
    missing = sorted(m["paypal_transaction_id"] for m in listed["missing"])
    assert missing == ["SEED-0022", "SEED-0023", "SEED-0024"]
    item = next(i for i in listed["items"] if i["reference_no"] == "SEED-0001")
    assert item["foreign_amount"] == {"amount": "1200.00", "currency": "USD"}
    assert item["inr_amount"] == {"amount": "100800.00", "currency": "INR"}
    assert item["remittance_date"] and item["purpose_code"] == "P0802"
    rows = api.get("/transactions", params={"limit": 50}).json()["items"]
    statuses = {r["paypal_transaction_id"]: r["fira_status"] for r in rows}
    assert list(statuses.values()).count("matched") == 19
    assert statuses["SEED-0021"] == "needs_review" and statuses["SEED-0024"] == "missing"


def test_sync_sets_fira_status_on_new_rows(api: TestClient) -> None:
    api.post("/sync")
    rows = api.get("/transactions", params={"kind": "all", "limit": 50}).json()["items"]
    income = [r for r in rows if r["kind"] == "income" and r["status"] == "completed"]
    others = [r for r in rows if r not in income]
    assert income and all(r["fira_status"] == "missing" for r in income)
    assert all(r["fira_status"] is None for r in others)
