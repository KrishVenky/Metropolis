"""
Phase 1 gate, run against REAL onchain state (not illustrative parameters).

Stream 23 on Sablier Lockup, Monad mainnet (chain id 143):
  contract:  0x82723c1ffec9d43de5fa80b25da8df99afd470ba
  sender:    0xb996c591fda11d3e67b8fad59a82d75d4349defe   (third-party payer,
             not a self-funded stream - the sender also funds stream 24 to a
             different recipient, i.e. a real one-to-many payroll pattern)
  recipient: 0x77a89c51f106d6cd547542a3a83fe73cb4459135
  asset:     0x350035555e10d9afaf1566aaebfced5ba6c27777 (symbol CHOG, 18 decimals)

All values below were read directly via eth_call against Monad mainnet RPC
(https://rpc.monad.xyz), pinned to block 108166208 (unix timestamp
1790421803), and cross-checked twice (an unpinned scan across streams 1-26,
then re-read pinned to this exact block). Nothing here is fabricated or
illustrative.
"""

from model import Stream, ScoringInput, score

BLOCK_NUMBER = 108_166_208
BLOCK_TIMESTAMP = 1790421803

stream = Stream(
    stream_id=23,
    sender="0xb996c591fda11d3e67b8fad59a82d75d4349defe",
    deposit_amount=5_000_000e18,      # 5,000,000 CHOG, 18 decimals
    withdrawn_amount=500_000e18,       # 500,000 CHOG withdrawn so far
    start_time=1782135900,
    end_time=1841727600,
    cancelable=True,
    canceled=False,
)

# Illustrative ask, not part of the onchain data: this scoring run tests the
# formula against a real stream for a hypothetical credit line request, the
# same way the demo will size a request against whatever stream a real
# borrower actually presents.
REQUESTED_CREDIT_LINE = 1_000_000e18   # 1,000,000 CHOG-denominated ask
LOAN_TERM_SECONDS = 30 * 24 * 60 * 60  # 30-day loan term

inputs = ScoringInput(
    streams=[stream],
    requested_credit_line=REQUESTED_CREDIT_LINE,
    loan_term_seconds=LOAN_TERM_SECONDS,
    as_of_time=BLOCK_TIMESTAMP,
    block_number=BLOCK_NUMBER,
)

result = score(inputs)

remaining_value = stream.remaining_value()
runway = stream.runway_factor(BLOCK_TIMESTAMP, LOAN_TERM_SECONDS)
cancelability = stream.cancelability_factor()

print(f"block_number:            {result.block_number}")
print(f"as_of_time (unix):       {result.as_of_time}")
print(f"remaining_value (CHOG):  {remaining_value / 1e18:,.0f}")
print(f"cancelability_factor:    {cancelability}")
print(f"runway_factor:           {runway:.4f}")
print(f"risk_adjusted_income:    {result.risk_adjusted_income / 1e18:,.0f} CHOG")
print(f"requested_credit_line:   {REQUESTED_CREDIT_LINE / 1e18:,.0f} CHOG")
print(f"coverage_ratio:          {result.coverage_ratio:.4f}")
print(f"tier:                    {result.tier.value}")
print(f"approved_line:           {result.approved_line / 1e18:,.0f} CHOG")

# Hand-derived sanity check, same arithmetic the model runs:
# remaining_value = 5,000,000 - 500,000 = 4,500,000 CHOG
# cancelable -> haircut 0.5x
# stream ends 1841727600, as_of 1790421803 -> remaining_duration = 51,305,797s
#   loan_term = 30d = 2,592,000s -> runway_factor = min(1, 51305797/2592000) = 1.0
# risk_adjusted_income = 4,500,000 * 0.5 * 1.0 = 2,250,000 CHOG
# coverage_ratio = 2,250,000 / 1,000,000 = 2.25 -> eligible, and 2.25 >= 1.5 target margin
# approved_line = min(1,000,000, 2,250,000/1.5) = min(1,000,000, 1,500,000) = 1,000,000 -> FULL
def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1.0)

# float64 has ~15-17 significant digits; at ~1e24 magnitude an absolute
# tolerance of 1 is meaningless, so these checks use relative tolerance.
assert close(remaining_value, 4_500_000e18)
assert cancelability == 0.5
assert abs(runway - 1.0) < 1e-9
assert close(result.risk_adjusted_income, 2_250_000e18)
assert abs(result.coverage_ratio - 2.25) < 1e-9
assert result.tier.value == "full"
assert close(result.approved_line, 1_000_000e18)
print("\nassertions passed: real stream, real haircuts, sane and explainable output.")
