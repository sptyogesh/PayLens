"""Fee and FX loss. FX uses the Simulated (sandbox) PayPal rate; a negative loss is a gain."""

from typing import Final

from reportlab.platypus import Paragraph

from app.common.constants import SIMULATED_LABEL
from app.reports.format import is_gain, money, percent, without_sign
from app.reports.styles import HEADING, Flowable, key_values
from app.schemas.report import ReportData

HEADING_TEXT: Final = "Fee and FX loss"
FEE: Final = "PayPal fee loss"
FX_LOSS: Final = f"FX loss ({SIMULATED_LABEL})"
FX_GAIN: Final = f"FX gain ({SIMULATED_LABEL})"
TOTAL: Final = "Total leakage"
PERCENT: Final = "Leakage % of income"


def leakage(data: ReportData) -> list[Flowable]:
    totals = data.totals
    if totals is None:
        return []
    fx = totals.fx_loss_inr
    pairs = [
        (FEE, money(totals.fee_loss_inr)),
        (FX_GAIN, money(without_sign(fx))) if is_gain(fx) else (FX_LOSS, money(fx)),
        (TOTAL, money(totals.total_leakage_inr)),
        (PERCENT, percent(totals.leakage_percent)),
    ]
    return [Paragraph(HEADING_TEXT, HEADING), key_values(pairs)]
