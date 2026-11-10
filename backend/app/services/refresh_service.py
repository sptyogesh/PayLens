"""Recompute what derives from transactions after sync, seed and /pay (002 FR-020, 004 FR-007).

Leakage first, then the FIRA rematch. Each step logs its own failure and never raises.
"""

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.fx import FxGateway
from app.services.fira_rematch import safe_rematch
from app.services.leakage_service import RecalcSummary, safe_recalculate


def safe_refresh(factory: Callable[[], Session], fx: FxGateway) -> RecalcSummary | None:
    """Returns the leakage summary (None when leakage failed); the rematch result is stored."""
    summary = safe_recalculate(factory, fx)
    safe_rematch(factory)
    return summary
