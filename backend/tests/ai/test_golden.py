"""G1-G10 golden questions (constitution, spec SC-001): real tools + DB, fake LLM.

Each answer must come from the expected tool and contain the exact amount strings that tool
returns for the same period; the "Based on" figures must carry the same values.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.ai.tools import run_tool
from app.common.periods import DashboardPeriod
from app.schemas.chat import ChatOut
from app.services.dashboard_service import get_dashboard
from tests.ai.support import NOW, ask

Content = dict[str, Any]


def tool(session: Session, name: str, **arguments: Any) -> Content:
    return run_tool(session, name, arguments, NOW).content


def assert_grounded(out: ChatOut, tool_name: str, amounts: list[str]) -> None:
    assert out.outcome == "answered", out.answer
    assert out.tools_used == [tool_name]
    assert amounts and all(amount in out.answer for amount in amounts)
    assert out.periods and out.periods[0] in out.answer
    assert "INR" in out.answer


def figure_values(out: ChatOut) -> set[str]:
    return {figure.value for figure in out.figures}


def test_g1_fx_loss_last_quarter(seeded: Session) -> None:
    expected = tool(seeded, "fee_summary", period="last_quarter")
    out = ask(seeded, "How much FX loss last quarter?")
    assert_grounded(out, "fee_summary", [f"₹{expected['fx_loss_inr']}"])
    assert expected["fx_loss_inr"] in figure_values(out)
    assert "Simulated (sandbox)" in out.answer
    assert out.periods == ["Last quarter (1 Jul 2026 – 30 Sep 2026)"]


def test_g2_income_by_month(seeded: Session) -> None:
    expected = tool(seeded, "income_summary", period="last_3_months", group_by="month")
    out = ask(seeded, "Show my income by month for the last 3 months")
    months = [f"₹{group['income_inr']}" for group in expected["groups"]]
    assert len(months) == 3
    assert_grounded(out, "income_summary", [f"₹{expected['income_inr']}", *months])


def test_g3_top_client_by_fees(seeded: Session) -> None:
    expected = tool(seeded, "fee_summary", period="last_3_months", group_by="client")
    out = ask(seeded, "Which client costs me the most in fees?")
    top = expected["groups"][0]
    assert_grounded(out, "fee_summary", [f"₹{top['total_leakage_inr']}"])
    assert top["label"] == "Ava Stone" and f"for {top['label']}" in out.answer
    assert out.answer.index(top["total_leakage_inr"]) < out.answer.index(
        expected["groups"][1]["total_leakage_inr"]
    )


def test_g4_income_this_financial_year(seeded: Session) -> None:
    expected = tool(seeded, "income_summary", period="this_financial_year")
    out = ask(seeded, "What is my income this financial year?")
    assert_grounded(out, "income_summary", [f"₹{expected['income_inr']}"])
    assert expected["payment_count"] == 8
    assert {expected["income_inr"], "8"} <= figure_values(out)


def test_g5_largest_payment(seeded: Session) -> None:
    expected = tool(seeded, "get_transactions", period="all_time", sort="largest_leakage", limit=1)
    out = ask(seeded, "What was my largest payment ever?")
    item = expected["items"][0]
    assert item["gross"] == {"amount": "2200.00", "currency": "USD"}
    assert_grounded(out, "get_transactions", ["USD 2200.00", f"₹{item['total_leakage_inr']}"])


def test_g6_leakage_percent_all_time_matches_dashboard(seeded: Session) -> None:
    dashboard = get_dashboard(seeded, DashboardPeriod.ALL_TIME, NOW)
    assert dashboard.totals is not None and dashboard.totals.leakage_percent is not None
    out = ask(seeded, "What is my leakage % all time?")
    assert_grounded(out, "fee_summary", [dashboard.totals.leakage_percent])
    assert dashboard.totals.leakage_percent in figure_values(out)


def test_g7_fee_loss_last_month(seeded: Session) -> None:
    expected = tool(seeded, "fee_summary", period="last_month")
    out = ask(seeded, "How much fee loss last month?")
    assert_grounded(out, "fee_summary", [f"₹{expected['fee_loss_inr']}"])
    assert expected["payment_count"] == 1


def test_g8_income_by_currency(seeded: Session) -> None:
    expected = tool(seeded, "income_summary", period="all_time", group_by="currency")
    out = ask(seeded, "What is my income by currency all time?")
    gross = [f"{m['currency']} {m['amount']}" for m in expected["gross_by_currency"]]
    assert len(gross) == 3
    assert_grounded(out, "income_summary", gross)


def test_g9_transactions_for_a_client(seeded: Session) -> None:
    expected = tool(seeded, "get_transactions", period="all_time", client="Ben Lee")
    out = ask(seeded, 'List all time transactions for "Ben Lee"')
    gross = [f"GBP {item['gross']['amount']}" for item in expected["items"]]
    assert expected["total_count"] == 3
    assert_grounded(out, "get_transactions", gross)


def test_g10_total_leakage_this_quarter(seeded: Session) -> None:
    expected = tool(seeded, "fee_summary", period="this_quarter")
    out = ask(seeded, "What is my total leakage this quarter?")
    assert_grounded(out, "fee_summary", [f"₹{expected['total_leakage_inr']}"])
    assert expected["total_leakage_inr"] in figure_values(out)


def test_golden_last_3_months_fee_loss_matches_dashboard(seeded: Session) -> None:
    dashboard = get_dashboard(seeded, DashboardPeriod.LAST_3_MONTHS, NOW)
    assert dashboard.totals is not None
    out = ask(seeded, "What were my fees in the last 3 months?")
    assert_grounded(out, "fee_summary", [f"₹{dashboard.totals.fee_loss_inr.amount}"])
