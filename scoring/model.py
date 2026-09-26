"""
Concordat credit-line scoring model.

Deterministic borrowing-base model against Sablier Lockup streams. No LLM
involvement anywhere in this module. Same inputs always produce the same
output. See BUILDLOG.md for the formula's derivation and the reasoning
behind every threshold below.

Framework this resembles: asset-based lending / receivables factoring
underwriting. A Sablier stream is treated as a receivable; credit is
extended against a borrowing base (advance rate x eligible collateral
value), with the advance rate haircut by receivable quality (cancelability,
aging/runway) the same way an ABL facility haircuts receivables by dilution
risk and concentration.
"""

from dataclasses import dataclass, field
from enum import Enum


CANCELABLE_HAIRCUT = 0.5     # cancelable stream's remaining value counts at 50%
NON_CANCELABLE_HAIRCUT = 1.0

FULL_APPROVAL_CR = 1.5       # coverage ratio >= this -> full requested line
DECLINE_CR = 1.0             # coverage ratio < this -> decline


class Tier(str, Enum):
    FULL = "full"
    TIGHTENED = "tightened"
    DECLINE = "decline"


@dataclass
class Stream:
    """One Sablier Lockup stream, as read from onchain state."""
    stream_id: int
    sender: str
    deposit_amount: float
    withdrawn_amount: float
    start_time: int          # unix seconds
    end_time: int             # unix seconds
    cancelable: bool
    canceled: bool

    def remaining_value(self) -> float:
        """Undrawn principal still owed to the recipient, in stream units."""
        if self.canceled:
            # Unvested principal already returned to the sender on cancellation.
            return 0.0
        return max(0.0, self.deposit_amount - self.withdrawn_amount)

    def remaining_duration(self, as_of_time: int) -> int:
        return max(0, self.end_time - as_of_time)

    def cancelability_factor(self) -> float:
        return CANCELABLE_HAIRCUT if self.cancelable else NON_CANCELABLE_HAIRCUT

    def runway_factor(self, as_of_time: int, loan_term_seconds: int) -> float:
        """Fraction of the loan term the stream is actually still running for."""
        if loan_term_seconds <= 0:
            return 0.0
        return min(1.0, self.remaining_duration(as_of_time) / loan_term_seconds)

    def risk_adjusted_value(self, as_of_time: int, loan_term_seconds: int) -> float:
        return (
            self.remaining_value()
            * self.cancelability_factor()
            * self.runway_factor(as_of_time, loan_term_seconds)
        )


@dataclass
class ScoringInput:
    streams: list[Stream]
    requested_credit_line: float
    loan_term_seconds: int
    as_of_time: int           # unix seconds the score is computed at
    block_number: int         # Monad block this state was read at


@dataclass
class ScoringResult:
    risk_adjusted_income: float
    coverage_ratio: float
    tier: Tier
    approved_line: float
    as_of_time: int
    block_number: int
    inputs: ScoringInput = field(repr=False)


def score(inputs: ScoringInput) -> ScoringResult:
    risk_adjusted_income = sum(
        s.risk_adjusted_value(inputs.as_of_time, inputs.loan_term_seconds)
        for s in inputs.streams
    )

    if inputs.requested_credit_line <= 0:
        coverage_ratio = 0.0
    else:
        coverage_ratio = risk_adjusted_income / inputs.requested_credit_line

    if coverage_ratio >= FULL_APPROVAL_CR:
        tier = Tier.FULL
        approved_line = inputs.requested_credit_line
    elif coverage_ratio >= DECLINE_CR:
        tier = Tier.TIGHTENED
        # Size the line down to what is actually 1:1 covered by risk-adjusted
        # income rather than extending the full ask at an inadequate margin.
        approved_line = risk_adjusted_income
    else:
        tier = Tier.DECLINE
        approved_line = 0.0

    return ScoringResult(
        risk_adjusted_income=risk_adjusted_income,
        coverage_ratio=coverage_ratio,
        tier=tier,
        approved_line=approved_line,
        as_of_time=inputs.as_of_time,
        block_number=inputs.block_number,
        inputs=inputs,
    )


def income_volatility(monthly_income_history: list[float]) -> float | None:
    """
    Coefficient of variation (stdev / mean) across a wallet's historical
    monthly income from completed streams. Standard dispersion measure used
    in variable-income underwriting (e.g. self-employed income averaging
    under conventional mortgage guidelines, which discounts high-CV income).

    Returns None if there isn't enough history to compute it (< 2 points) -
    never a guessed default.
    """
    n = len(monthly_income_history)
    if n < 2:
        return None
    mean = sum(monthly_income_history) / n
    if mean == 0:
        return None
    variance = sum((x - mean) ** 2 for x in monthly_income_history) / n
    stdev = variance ** 0.5
    return stdev / mean
