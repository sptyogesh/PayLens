"""005 review: timestamps and Indian amount words must not ground invented summary numbers."""

from app.ai.grounding import allowed_from_content, ungrounded_numbers

CONTENT = {
    "generated_at": "2026-11-10T08:47:12.345678Z",
    "period": {"label": "Last 3 months", "start": "2026-08-31T18:30:00Z", "end": None},
    "totals": {"total_leakage_inr": {"amount": "4.10", "currency": "INR"}},
}


def test_timestamp_parts_and_amount_words_are_not_free() -> None:
    allowed = allowed_from_content(CONTENT, [])
    answer = "Leakage was 47% of income, about 12 lakh rupees, FX loss INR 18."
    assert set(ungrounded_numbers(answer, allowed)) == {"47", "12", "18"}
    assert ungrounded_numbers("It costs 5 crore or 3k or Rs 7.", allowed) == ["5", "3", "7"]


def test_real_values_and_years_still_pass() -> None:
    allowed = allowed_from_content(CONTENT, [])
    assert ungrounded_numbers("In 2026 leakage was INR 4.10 over 3 months.", allowed) == []
