"""fira_status chat tool (004 US3): counts, lists, golden answer naming the missing payments."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ai.tools import TOOL_DEFINITIONS, run_tool
from app.common.dates import utc_now
from app.fakes.llm_fake import choose_tool
from app.models import FiraDocStatus, FiraDocument
from app.services.fira_rematch import rematch
from tests.ai.support import NOW, ask


def add_fira(session: Session, reference: str, amount: str, on: date) -> None:
    session.add(
        FiraDocument(
            file_name=f"{reference}.pdf",
            file_hash=reference.ljust(64, "0"),
            extracted_json={},
            foreign_amount=Decimal(amount),
            currency="USD",
            remittance_date=on,
            reference_no=reference,
            status=FiraDocStatus.NO_MATCH,
            uploaded_at=utc_now(),
        )
    )
    session.flush()


def with_firas(seeded: Session) -> Session:
    add_fira(seeded, "NOV", "1000.00", date(2026, 11, 6))  # exact → matched
    add_fira(seeded, "JUL", "1545.00", date(2026, 7, 5))  # 3% off → needs review
    rematch(seeded)
    return seeded


def test_tool_is_registered_with_a_period_input() -> None:
    names = [definition["name"] for definition in TOOL_DEFINITIONS]
    assert "fira_status" in names
    assert choose_tool("Which payments are missing a FIRA?") == ("fira_status", {})
    assert choose_tool("FIRA status last quarter") == ("fira_status", {"period": "last_quarter"})


def test_counts_and_lists_default_to_all_time(seeded: Session) -> None:
    result = run_tool(with_firas(seeded), "fira_status", {}, NOW)
    content = result.content
    assert (content["matched_count"], content["needs_review_count"], content["missing_count"]) == (
        1,
        1,
        7,
    )
    assert content["period"]["label"].startswith("All time")
    assert [i["paypal_transaction_id"] for i in content["needs_review"]] == ["JUL"]
    assert len(content["missing"]) == 7 and content["has_data"] is True
    assert content["missing"][0] == {
        "date": "2026-10-06",
        "client": "Ben Lee",
        "gross": {"amount": "640.00", "currency": "GBP"},
        "paypal_transaction_id": "OCT",
    }
    assert [(f.label, f.value) for f in result.figures] == [
        ("Matched", "1"),
        ("Needs review", "1"),
        ("Missing", "7"),
    ]


def test_period_without_payments_has_no_data(seeded: Session) -> None:
    result = run_tool(seeded, "fira_status", {"start": "2025-01-01", "end": "2025-01-31"}, NOW)
    assert result.has_data is False and result.figures == []


def test_golden_answer_lists_exactly_the_missing_payments(seeded: Session) -> None:
    session = with_firas(seeded)
    expected = run_tool(session, "fira_status", {}, NOW).content["missing"]
    out = ask(session, "Which payments are missing a FIRA?")
    assert out.outcome == "answered", out.answer
    assert out.tools_used == ["fira_status"]
    missing_part = out.answer.split("Missing a FIRA: ", 1)[1].split(" Needs review:", 1)[0]
    lines = missing_part.rstrip(".").split("; ")
    assert lines == [
        f"{i['date']} {i['client']} {i['gross']['currency']} {i['gross']['amount']}"
        for i in expected
    ]
    assert "1000.00" not in missing_part and "1500.00" not in missing_part  # NOV, JUL excluded
