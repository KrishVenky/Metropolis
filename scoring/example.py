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
# coverage_ratio = 6000 / 4000 = 1.5 -> exactly clears TARGET_MARGIN, FULL, approved_line = 4000
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

print("\n--- non-cancelable stream, eligible but below target margin: TIGHTENED ---")
stream_thin = Stream(
    stream_id=3,
    sender="0xEMPLOYER_ILLUSTRATIVE",
    deposit_amount=9000.0,
    withdrawn_amount=3000.0,
    start_time=0,
    end_time=90 * DAY,
    cancelable=False,
    canceled=False,
)
inputs3 = ScoringInput(
    streams=[stream_thin],
    requested_credit_line=5000.0,  # bigger ask against the same $6000 remaining value
    loan_term_seconds=60 * DAY,
    as_of_time=30 * DAY,
    block_number=0,
)
result3 = score(inputs3)
# risk_adjusted_income = 6000 (no haircuts, non-cancelable, full runway)
# coverage_ratio = 6000 / 5000 = 1.2 -> eligible (>=1.0) but below TARGET_MARGIN (1.5)
# approved_line = min(5000, 6000 / 1.5) = min(5000, 4000) = 4000, i.e. sized DOWN below the ask
print(f"risk_adjusted_income:   {result3.risk_adjusted_income:.2f}")
print(f"coverage_ratio:         {result3.coverage_ratio:.3f}")
print(f"tier:                   {result3.tier.value}")
print(f"approved_line:          {result3.approved_line:.2f}")
assert abs(result3.coverage_ratio - 1.2) < 1e-9
assert result3.tier.value == "tightened"
assert abs(result3.approved_line - 4000.0) < 1e-9
assert result3.approved_line < inputs3.requested_credit_line
print("\nassertions passed: TIGHTENED now correctly sizes the line BELOW the ask"
      " (4000 < 5000 requested), fixing the earlier bug where it could exceed the ask.")
