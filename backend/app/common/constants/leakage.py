"""Leakage and FX (002, plan section 10)."""

from decimal import Decimal
from typing import Final

# --- Leakage and FX (002, plan section 10, research R1-R4) ---
INR: Final = "INR"
DISPLAY_TIME_ZONE: Final = "Asia/Kolkata"
SIMULATED_FX_SPREAD: Final = Decimal("0.03")  # simulated PayPal rate = mid x (1 - spread)
SIMULATED_LABEL: Final = "Simulated (sandbox)"  # the one label for the simulated FX rate
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
