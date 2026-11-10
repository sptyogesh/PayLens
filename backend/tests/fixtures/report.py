"""Builders for CA report tests: ReportData by hand, and demo seed + uploaded sample FIRAs."""

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from freezegun import freeze_time
from sqlalchemy.orm import Session, sessionmaker

from app.common.constants import NOT_TAX_ADVICE
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.llm_fake import FakeLlm
from app.schemas.report import ReportData, ReportFigures
from app.services.fira_service import upload
from app.services.refresh_service import safe_refresh
from scripts.generate_fira_samples import generate
from scripts.seed_demo import seed

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)  # 11:30 IST


def totals(count: int = 2, income: str = "168000.00", fx: str = "5040.00") -> dict[str, Any]:
    return {
        "payment_count": count,
        "income_inr": {"amount": income, "currency": "INR"},
        "fee_loss_inr": {"amount": "7392.00", "currency": "INR"},
        "fx_loss_inr": {"amount": fx, "currency": "INR"},
        "total_leakage_inr": {"amount": "12432.00", "currency": "INR"},
        "leakage_percent": "7.40",
    }


def row(key: str, label: str, **overrides: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "totals": totals(**overrides)}


def figures(**overrides: Any) -> ReportFigures:
    """Two USD payments in Nov 2026, one missing a FIRA."""
    values: dict[str, Any] = {
        "period": {
            "key": "this_month",
            "label": "This month",
            "start": "2026-10-31T18:30:00Z",
            "end": "2026-11-10T06:00:00Z",
        },
        "generated_at": "2026-11-10T06:00:00Z",
        "totals": totals(),
        "gross_by_currency": [{"amount": "2000.00", "currency": "USD"}],
        "by_month": [row("2026-11", "Nov 2026")],
        "by_client": [row("c1", "Ava Stone")],
        "excluded_count": 1,
        "not_calculated_count": 0,
        "simulated_spread_percent": "3.00",
        "fira": {
            "uploaded": 1,
            "matched": 1,
            "needs_review": 0,
            "missing": 1,
            "missing_payments": [
                {
                    "date": date(2026, 11, 4).isoformat(),
                    "client": "Ava Stone",
                    "paypal_transaction_id": "TX-2",
                    "gross": {"amount": "1000.00", "currency": "USD"},
                }
            ],
        },
        "notes": ["Sandbox data.", "Simulated (sandbox) rate: 3.00% below mid."],
        "disclaimer": NOT_TAX_ADVICE,
    }
    values.update(overrides)
    return ReportFigures.model_validate(values)


def report(source: str = "code", text: str = "Summary text.", **overrides: Any) -> ReportData:
    base = figures(**overrides).model_dump(mode="json")
    return ReportData.model_validate({**base, "summary": {"text": text, "source": source}})


def seed_demo_with_firas(factory: sessionmaker[Session], tmp_path: Path) -> None:
    """Demo seed (24 payments) with leakage, then the 21 sample FIRAs uploaded (19 matched,
    2 needs review, 3 missing), as on the FIRA page."""
    with freeze_time(NOW), factory() as session:
        seed(session)
        session.commit()
    safe_refresh(factory, FakeFxGateway())
    llm = FakeLlm()
    for path in generate(tmp_path, NOW):
        upload(factory, llm, path.name, path.read_bytes())
