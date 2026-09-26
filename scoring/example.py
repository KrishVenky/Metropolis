"""
Phase 1 gate: hand-walk one borrower through the scoring formula and confirm
the output is sane and explainable.

NOTE: this is illustrative-parameter validation of the formula's mechanics,
NOT a live pull from a real Monad wallet. Pulling a real wallet's actual
Sablier stream requires calling the Monad RPC / an indexer, which this
session's network policy currently blocks (rpc.monad.xyz and the block
explorers were denied by the egress proxy). Once that access is available,
this script should be replaced with a real state read, block number
included, per the reproducibility rule. Never present the numbers below as
real borrower data.
"""

from model import Stream, ScoringInput, score

DAY = 24 * 60 * 60

# Illustrative stream: a non-cancelable, 90-day salary-style stream, 30 days
# into its schedule, a third already withdrawn.
stream = Stream(
    stream_id=1,
    sender="0xEMPLOYER_ILLUSTRATIVE",
    deposit_amount=9000.0,
    withdrawn_amount=3000.0,
    start_time=0,
    end_time=90 * DAY,
    cancelable=False,
    canceled=False,
)

inputs = ScoringInput(
    streams=[stream],
    requested_credit_line=4000.0,
    loan_term_seconds=60 * DAY,
    as_of_time=30 * DAY,
    block_number=0,  # illustrative only, not a real Monad block
)

result = score(inputs)

print("--- illustrative case: non-cancelable stream, ample coverage ---")
print(f"remaining_value:        {stream.remaining_value():.2f}")
print(f"runway_factor:          {stream.runway_factor(inputs.as_of_time, inputs.loan_term_seconds):.3f}")
print(f"risk_adjusted_income:   {result.risk_adjusted_income:.2f}")
print(f"coverage_ratio:         {result.coverage_ratio:.3f}")
print(f"tier:                   {result.tier.value}")
print(f"approved_line:          {result.approved_line:.2f}")

# Sanity: remaining_value = 9000 - 3000 = 6000
# runway_factor = min(1, 60d remaining / 60d loan_term) = 1.0 (60 days left of 90, loan term 60d)
# risk_adjusted_income = 6000 * 1.0 (non-cancelable) * 1.0 (runway) = 6000
# coverage_ratio = 6000 / 4000 = 1.5 -> FULL tier, boundary case, approved_line = 4000
assert abs(stream.remaining_value() - 6000.0) < 1e-9
assert abs(result.coverage_ratio - 1.5) < 1e-9
assert result.tier.value == "full"
assert abs(result.approved_line - 4000.0) < 1e-9
print("\nassertions passed: formula behaves as derived by hand.")

print("\n--- same stream, but cancelable and a bigger ask ---")
stream_cancelable = Stream(
    stream_id=2,
    sender="0xEMPLOYER_ILLUSTRATIVE",
    deposit_amount=9000.0,
    withdrawn_amount=3000.0,
    start_time=0,
    end_time=90 * DAY,
    cancelable=True,
    canceled=False,
)
inputs2 = ScoringInput(
    streams=[stream_cancelable],
    requested_credit_line=4000.0,
    loan_term_seconds=60 * DAY,
    as_of_time=30 * DAY,
    block_number=0,
)
result2 = score(inputs2)
# risk_adjusted_income = 6000 * 0.5 (cancelable haircut) * 1.0 = 3000
# coverage_ratio = 3000 / 4000 = 0.75 -> DECLINE (below 1.0)
print(f"risk_adjusted_income:   {result2.risk_adjusted_income:.2f}")
print(f"coverage_ratio:         {result2.coverage_ratio:.3f}")
print(f"tier:                   {result2.tier.value}")
print(f"approved_line:          {result2.approved_line:.2f}")
assert abs(result2.coverage_ratio - 0.75) < 1e-9
assert result2.tier.value == "decline"
assert result2.approved_line == 0.0
print("\nassertions passed: cancelability haircut correctly flips full -> decline"
      " for the same underlying cashflow, which is the whole point of the haircut.")
