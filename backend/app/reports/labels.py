"""User-facing texts of the CA report (005): headings, empty states and data notes.

Kept apart from app/common/constants.py (size limit); change the wording here.
"""

from typing import Final

from app.common.constants import SIMULATED_LABEL

REPORT_TITLE: Final = "PayLens CA report"
REPORT_SUMMARY_AI_HEADING: Final = "Summary (AI-written from the figures below)"
REPORT_SUMMARY_CODE_HEADING: Final = "Summary"
REPORT_NO_FIRAS: Final = "No FIRAs uploaded yet."
REPORT_NOTE_SANDBOX: Final = "Sandbox data: payments come from the PayPal sandbox, not real money."
REPORT_NOTE_SIMULATED: Final = (
    f"FX loss uses a {SIMULATED_LABEL} PayPal rate: the ECB mid-market rate minus {{spread}}%."
)
REPORT_NOTE_ECB: Final = "Income in INR uses ECB reference rates via Frankfurter (mid-market)."
REPORT_NOTE_SEED: Final = "Some rows are demo seed data, labelled demo_seed, with synthetic fees."
REPORT_NOTE_EXCLUDED: Final = (
    "Payments without an exchange rate or with a fee above the gross are counted below but not"
    " included in the totals."
)
REPORT_NOTE_UNPRINTABLE: Final = (
    'Some names use characters the PDF font cannot show; they are printed as "?".'
)
