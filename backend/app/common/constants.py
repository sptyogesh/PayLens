"""Every threshold and limit used by the backend (constitution Principle XIV).

Change a value here, not in the code that uses it.
"""

from decimal import Decimal
from typing import Final

# --- Money (Principle III) ---
MONEY_PLACES: Final = Decimal("0.01")
RATE_PLACES: Final = Decimal("0.000001")

# --- PayPal Transaction Search (research R4) ---
PAYPAL_SANDBOX_BASE_URL: Final = "https://api-m.sandbox.paypal.com"
PAYPAL_WINDOW_DAYS: Final = 31
PAYPAL_PAGE_SIZE: Final = 500
PAYPAL_FIRST_PAGE: Final = 1
PAYPAL_MAX_PAGES_PER_WINDOW: Final = 50
PAYPAL_TOKEN_REFRESH_MARGIN_S: Final = 60

# --- Outbound HTTP (Principle VIII) ---
HTTP_TIMEOUT_S: Final = 10.0
HTTP_MAX_RETRIES: Final = 3
HTTP_BACKOFF_BASE_S: Final = 1.0
HTTP_RETRY_STATUSES: Final = frozenset({429, 500, 502, 503, 504})

# --- Event classification (research R2) ---
INCOME_EVENT_CODES: Final = frozenset(
    {
        "T0000", "T0001", "T0002", "T0003", "T0004", "T0005", "T0006",
        "T0007", "T0011", "T0012", "T0018", "T0019", "T0023",
    }
)  # fmt: skip
FEE_EVENT_CODES: Final = frozenset({"T0107"})
REFUND_EVENT_CODES: Final = frozenset({"T1201"})
REFUND_EVENT_PREFIX: Final = "T11"
WITHDRAWAL_EVENT_PREFIX: Final = "T04"
CONVERSION_EVENT_PREFIX: Final = "T02"
HOLD_EVENT_PREFIXES: Final = ("T15", "T21")

# --- Sync (FR-020 to FR-022, research R9) ---
SYNC_DEFAULT_DAYS: Final = 90
SYNC_LOCK_KEY: Final = 7_001_001
SYNC_STALE_AFTER_MINUTES: Final = 10

# --- Checkout /pay (FR-030 to FR-033, research R1) ---
CHECKOUT_CURRENCIES: Final = ("USD", "GBP", "EUR", "AUD")
CHECKOUT_MAX_AMOUNT: Final = Decimal("10000.00")
CHECKOUT_DESCRIPTION_MAX: Final = 127
CHECKOUT_RECONCILE_WINDOW_HOURS: Final = 72

# --- Rate limits (research R8): (requests, window seconds) per client IP ---
RATE_LIMIT_SYNC: Final = (3, 60)
RATE_LIMIT_PAY: Final = (10, 60)

# --- API ---
TRANSACTIONS_PAGE_DEFAULT: Final = 100
TRANSACTIONS_PAGE_MAX: Final = 200
LOCAL_FRONTEND_ORIGIN: Final = "http://localhost:3000"

# --- Clients ---
UNKNOWN_CLIENT_NAME: Final = "Unknown client"

# --- Demo seed (FR-040): synthetic fees, labelled "Demo seed" in the UI ---
SEED_FEE_PERCENT: Final = Decimal("0.044")
SEED_FEE_FIXED: Final = {
    "USD": Decimal("0.30"),
    "GBP": Decimal("0.20"),
    "EUR": Decimal("0.35"),
    "AUD": Decimal("0.30"),
}
SEED_ID_PREFIX: Final = "SEED-"
SEED_MONTHS: Final = 4

# --- Leakage and FX (002, plan section 10, research R1-R4) ---
INR: Final = "INR"
DISPLAY_TIME_ZONE: Final = "Asia/Kolkata"
SIMULATED_FX_SPREAD: Final = Decimal("0.03")  # simulated PayPal rate = mid x (1 - spread)
PERCENT_PLACES: Final = Decimal("0.01")
PERCENT_FACTOR: Final = Decimal(100)
FX_API_DEFAULT_URL: Final = "https://api.frankfurter.dev"
FX_PROVIDER: Final = "ecb"
FX_SOURCE_NAME: Final = "frankfurter_ecb"
FX_FAKE_SOURCE_NAME: Final = "fake"
FX_TIMEOUT_S: Final = 5.0
INR_RATE: Final = Decimal("1.000000")
MONTH_KEY_FORMAT: Final = "%Y-%m"  # "2026-11"
MONTH_LABEL_FORMAT: Final = "%b %Y"  # "Nov 2026"
