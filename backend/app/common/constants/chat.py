"""Ask Your Money chat, periods and tools (003)."""

from typing import Final

from app.common.constants.leakage import SIMULATED_LABEL

# --- Ask Your Money chat (003, research R1-R2) ---
RATE_LIMIT_CHAT: Final = (10, 60)
LLM_DEFAULT_API_URL: Final = "https://api.anthropic.com"
LLM_DEFAULT_MODEL: Final = "claude-opus-5-5"
LLM_API_VERSION: Final = "2026-10-21"
LLM_TIMEOUT_S: Final = 20.0
LLM_MAX_TOKENS: Final = 4096
LLM_EFFORT: Final = "low"
LLM_MAX_TOOL_ROUNDS: Final = 4
LLM_TOOL_ERROR_MAX: Final = 300  # characters of a tool input error sent back to the LLM
CHAT_QUESTION_MAX: Final = 500
CHAT_HISTORY_MAX: Final = 6
CHAT_HISTORY_ITEM_MAX: Final = 2000
CHAT_STORED_CONTENT_MAX: Final = 4000
CHAT_TOOL_ROWS_MAX: Final = 20
GROUNDING_FREE_INTEGER_MAX: Final = 12
GROUNDING_CONTEXT_CHARS: Final = 40
# Free-text tool fields: their numbers (except years) are never accepted as grounded.
GROUNDING_TEXT_KEYS: Final = frozenset(
    {
        "client", "label", "key", "name", "paypal_transaction_id", "source", "leakage_status",
        "currency",
        # Timestamps: only their years are usable (005 review: hours/minutes are not data).
        "generated_at", "start", "end",
    }
)  # fmt: skip
GROUNDING_SIGN_LOOKBACK: Final = 2  # chars before a number checked for a minus ("-₹", " -")
GROUNDING_PREFIX_LOOKBACK: Final = 5  # chars before a number checked for "₹", "USD ", "Rs. "
CHAT_DEADLINE_S: Final = 30.0
CHAT_MIN_CALL_S: Final = 2.0
TAX_KEYWORDS: Final = (
    "tax", "gst", "tds", "itr", "44ada", "advance tax", "deduction", "income tax",
)  # fmt: skip
NOT_TAX_ADVICE: Final = "Prepared from user data — not tax advice. Confirm with a CA."

# --- Chat periods and tools (003 T002/T006, data-model.md) ---
MONTHS_IN_YEAR: Final = 12
QUARTER_MONTHS: Final = 3
FINANCIAL_YEAR_START_MONTH: Final = 4  # Indian financial year: 1 Apr - 31 Mar
LAST_3_MONTHS_BACK: Final = 2  # this month and the two before, same as the dashboard
NAMED_PERIOD_LABELS: Final = {
    "this_month": "This month",
    "last_month": "Last month",
    "this_quarter": "This quarter",
    "last_quarter": "Last quarter",
    "last_3_months": "Last 3 months",
    "this_financial_year": "This financial year",
    "last_financial_year": "Last financial year",
    "all_time": "All time",
}
PERIOD_RANGE_LABEL: Final = "{start} – {end}"  # "1 Jul 2026 – 30 Sep 2026"
PERIOD_NAMED_LABEL: Final = "{name} ({range})"  # "Last quarter (1 Jul 2026 – 30 Sep 2026)"
CHAT_TOOL_ROWS_DEFAULT: Final = 10
CHAT_CLIENT_FILTER_MAX: Final = 200
FIGURE_LABELS: Final = {
    "income": "Income (INR, mid-market)",
    "payments": "Payments",
    "fee_loss": "Fee loss",
    "fx_loss": f"FX loss ({SIMULATED_LABEL})",
    "total_leakage": "Total leakage",
    "leakage_percent": "Leakage %",
    "transactions": "Transactions found",
}
