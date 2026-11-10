"""Fake LLM branch for the CA report summary (005 research): copies numbers from the JSON.

`report_mode` on FakeLlm picks the path tests need: "ok" (grounded summary), "fail" (AI down)
or "invent" (a number that is not in the report, so the code summary must be used).
"""

import json
from typing import Any, Final, Literal

from app.ai.llm import LlmRequest
from app.common.constants import REPORT_DATA_MARKER, SIMULATED_LABEL
from app.common.errors import LlmUnavailableError

ReportMode = Literal["ok", "fail", "invent"]
INVENTED: Final = "Your income was ₹99,999.99 in INR."
EMPTY: Final = "There are no payments in {label}."
TOTALS: Final = (
    "For {label}, in INR: {count} payments, income ₹{income}, fee loss ₹{fee} and FX loss"
    f" ₹{{fx}} at a {SIMULATED_LABEL} PayPal rate."
)
LEAKAGE: Final = "Total leakage was ₹{total}."
FIRA: Final = "{missing} payments are missing a FIRA."


def report_data(request: LlmRequest) -> dict[str, Any] | None:
    """The report JSON when this is a report-summary request, else None."""
    first = request.messages[0]["content"] if request.messages else None
    if not isinstance(first, str) or not first.startswith(REPORT_DATA_MARKER):
        return None
    data = json.loads(first.removeprefix(REPORT_DATA_MARKER))
    return data if isinstance(data, dict) else None


def report_summary_text(data: dict[str, Any], mode: ReportMode) -> str:
    if mode == "fail":
        raise LlmUnavailableError("Fake LLM is down.")
    if mode == "invent":
        return INVENTED
    label = data["period"]["label"]
    totals = data["totals"]
    if totals is None:
        return EMPTY.format(label=label)
    parts = [
        TOTALS.format(
            label=label,
            count=totals["payment_count"],
            income=totals["income_inr"]["amount"],
            fee=totals["fee_loss_inr"]["amount"],
            fx=totals["fx_loss_inr"]["amount"],
        ),
        LEAKAGE.format(total=totals["total_leakage_inr"]["amount"]),
        FIRA.format(missing=data["fira"]["missing"]),
    ]
    return " ".join(parts)
