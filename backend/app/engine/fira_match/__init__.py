"""FIRA matching engine (Phase 1A plan section 11, research R3). Import from here only.

Pure: no database, network or files. Decimal only.

Children: `types` (validated inputs/outputs and reason texts), `score` (one pair's score and
status), `weekly` (one ISO week's payments summed against a FIRA), `match` (greedy assignment of
all FIRAs, one payment per FIRA, then payment statuses).
"""

from app.engine.fira_match.match import Candidate, match_all, rank_candidates
from app.engine.fira_match.score import (
    failed_reason,
    reference_equal,
    score_pair,
    status_for,
    within_pct,
)
from app.engine.fira_match.types import (
    REASON_AMOUNT,
    REASON_DATE,
    REASON_NO_CURRENCY,
    REASON_REFERENCE,
    REASON_SEPARATOR,
    REASON_TAKEN,
    REASON_WEEKLY,
    FiraCandidate,
    FiraOutcome,
    FiraStatus,
    MatchKind,
    MatchResult,
    PaymentCandidate,
    PaymentStatus,
    ScoreBreakdown,
)
from app.engine.fira_match.weekly import weekly_match

__all__ = [
    "REASON_AMOUNT",
    "REASON_DATE",
    "REASON_NO_CURRENCY",
    "REASON_REFERENCE",
    "REASON_SEPARATOR",
    "REASON_TAKEN",
    "REASON_WEEKLY",
    "Candidate",
    "FiraCandidate",
    "FiraOutcome",
    "FiraStatus",
    "MatchKind",
    "MatchResult",
    "PaymentCandidate",
    "PaymentStatus",
    "ScoreBreakdown",
    "failed_reason",
    "match_all",
    "rank_candidates",
    "reference_equal",
    "score_pair",
    "status_for",
    "weekly_match",
    "within_pct",
]
