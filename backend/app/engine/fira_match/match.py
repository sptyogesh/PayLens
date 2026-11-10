"""Match all FIRAs to payments (research R3): score, greedy one payment per FIRA, weekly check."""

from collections.abc import Sequence
from typing import NamedTuple

from app.common.constants import FIRA_REVIEW_MIN
from app.engine.fira_match.score import failed_reason, score_pair, status_for
from app.engine.fira_match.types import (
    REASON_NO_CURRENCY,
    REASON_TAKEN,
    REASON_WEEKLY,
    FiraCandidate,
    FiraOutcome,
    MatchResult,
    PaymentCandidate,
    PaymentStatus,
    ScoreBreakdown,
)
from app.engine.fira_match.weekly import weekly_match


class Candidate(NamedTuple):
    """One scored same-currency payment for a FIRA."""

    breakdown: ScoreBreakdown
    payment: PaymentCandidate


def rank_candidates(fira: FiraCandidate, payments: Sequence[PaymentCandidate]) -> list[Candidate]:
    """Same-currency payments, best first: score desc, then closest date, then payment key."""
    scored = [
        Candidate(score_pair(fira, payment), payment)
        for payment in payments
        if payment.currency == fira.currency
    ]
    return sorted(
        scored,
        key=lambda c: (
            -c.breakdown.total,
            abs((fira.date - c.payment.date).days),
            c.payment.payment_key,
        ),
    )


def _best_total(ranked: list[Candidate]) -> int:
    return ranked[0].breakdown.total if ranked else 0


def _direct(fira: FiraCandidate, top: Candidate, taken: dict[str, str]) -> FiraOutcome:
    """Link the top candidate when free; otherwise needs review because a better FIRA has it."""
    total = top.breakdown.total
    key = top.payment.payment_key
    if key in taken:
        return FiraOutcome(
            fira_key=fira.fira_key,
            status="needs_review",
            score=total,
            reason=REASON_TAKEN,
            payment_keys=[],
            kind=None,
        )
    taken[key] = fira.fira_key
    status = status_for(total)
    reason = None if status == "matched" else failed_reason(top.breakdown)
    return FiraOutcome(
        fira_key=fira.fira_key,
        status=status,
        score=total,
        reason=reason,
        payment_keys=[key],
        kind="direct",
    )


def _fallback(
    fira: FiraCandidate,
    ranked: list[Candidate],
    payments: Sequence[PaymentCandidate],
    taken: dict[str, str],
) -> FiraOutcome:
    """Weekly sum-match on still-free payments, else no match with the reason of what failed."""
    score = _best_total(ranked)
    free = [payment for payment in payments if payment.payment_key not in taken]
    keys = weekly_match(fira, free)
    if keys is not None:
        taken.update(dict.fromkeys(keys, fira.fira_key))
        return FiraOutcome(
            fira_key=fira.fira_key,
            status="needs_review",
            score=score,
            reason=REASON_WEEKLY,
            payment_keys=keys,
            kind="weekly",
        )
    reason = failed_reason(ranked[0].breakdown) if ranked else REASON_NO_CURRENCY
    return FiraOutcome(
        fira_key=fira.fira_key,
        status="no_match",
        score=score,
        reason=reason,
        payment_keys=[],
        kind=None,
    )


def _payment_statuses(
    payments: Sequence[PaymentCandidate], outcomes: Sequence[FiraOutcome]
) -> dict[str, PaymentStatus]:
    linked: dict[str, PaymentStatus] = {}
    for outcome in outcomes:
        if outcome.status != "no_match":
            linked.update(dict.fromkeys(outcome.payment_keys, outcome.status))
    keys = sorted(payment.payment_key for payment in payments)
    return {key: linked.get(key, "missing") for key in keys}


def match_all(firas: Sequence[FiraCandidate], payments: Sequence[PaymentCandidate]) -> MatchResult:
    """Match every FIRA (FR-004..FR-007). Output FIRAs keep input order; payments sorted by key.

    Direct links are assigned greedily by best score desc, then upload order (F11); FIRAs below
    the review minimum then try the weekly sum-match in upload order (F12).
    """
    ranked = {fira.fira_key: rank_candidates(fira, payments) for fira in firas}
    by_strength = sorted(firas, key=lambda f: (-_best_total(ranked[f.fira_key]), f.order))
    taken: dict[str, str] = {}
    outcomes: dict[str, FiraOutcome] = {}
    for fira in by_strength:
        options = ranked[fira.fira_key]
        if options and options[0].breakdown.total >= FIRA_REVIEW_MIN:
            outcomes[fira.fira_key] = _direct(fira, options[0], taken)
    for fira in sorted(firas, key=lambda f: f.order):
        if fira.fira_key not in outcomes:
            outcomes[fira.fira_key] = _fallback(fira, ranked[fira.fira_key], payments, taken)
    ordered = [outcomes[fira.fira_key] for fira in firas]
    return MatchResult(firas=ordered, payments=_payment_statuses(payments, ordered))
