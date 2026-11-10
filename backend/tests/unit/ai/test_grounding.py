"""Grounding check (FR-004, research R2): numbers must come from tool results."""

from app.ai.grounding import allowed_numbers, normalise, ungrounded_numbers
from app.ai.types import Figure, ToolResult

PERIOD = "Last quarter (1 Jul 2026 – 30 Sep 2026)"


def result(**content: object) -> ToolResult:
    figure = Figure(label="Leakage %", kind="percent", value="7.30", currency=None, period=PERIOD)
    return ToolResult(
        name="fee_summary",
        content={"period": {"label": PERIOD, "start_date": "2026-07-01"}, **content},
        has_data=True,
        figures=[figure],
        period_label=PERIOD,
    )


def allowed(question: str = "How much FX loss?") -> set[str]:
    tool = result(fx_loss_inr="126678.93", payment_count=18, rows=[{"gross": "-500.40"}])
    return allowed_numbers([tool], question, [PERIOD])


def test_normalise_drops_commas_and_trailing_zeros() -> None:
    assert normalise("1,26,678.93") == "126678.93"
    assert normalise("7.30") == "7.3"
    assert normalise("38,000.00") == "38000"
    assert normalise("07") == "7"
    assert normalise("0.50") == "0.5"


def test_en_in_formatted_amount_matches_the_tool_string() -> None:
    assert ungrounded_numbers("FX loss was ₹1,26,678.93 in INR.", allowed()) == []


def test_western_grouping_matches_but_a_truncated_amount_does_not() -> None:
    assert ungrounded_numbers("About ₹126,678.93.", allowed()) == []
    assert ungrounded_numbers("About ₹126678.", allowed()) == ["126678"]  # review: no integer part


def test_invented_number_is_flagged() -> None:
    assert ungrounded_numbers("Your income was ₹99,999.99.", allowed()) == ["99999.99"]


def test_rounded_number_is_flagged_because_rounding_is_calculation() -> None:
    assert ungrounded_numbers("Roughly ₹1,26,679.", allowed()) == ["126679"]


def test_years_dates_and_short_years_are_allowed() -> None:
    text = "From 1 Jul 2026 to 30 Sep 2026 (FY 2026-26), starting 2026-07-01."
    assert ungrounded_numbers(text, allowed()) == []


def test_small_counts_are_free_but_larger_ones_are_not() -> None:
    assert ungrounded_numbers("Over 3 months and 12 clients.", allowed()) == []
    assert ungrounded_numbers("Over 13 months.", allowed()) == ["13"]


def test_percent_and_counts_from_tools_match() -> None:
    assert ungrounded_numbers("Leakage was 7.30% (7.3%) across 18 payments.", allowed()) == []


def test_negative_values_and_nested_rows_are_allowed() -> None:
    assert ungrounded_numbers("An FX gain of ₹500.40.", allowed()) == []


def test_numbers_in_the_question_are_allowed() -> None:
    assert ungrounded_numbers("Payments above 5000 rupees", allowed("above 5000?")) == []


def test_text_without_numbers_is_grounded() -> None:
    assert ungrounded_numbers("The data is not available.", set()) == []
