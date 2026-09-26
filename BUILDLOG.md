# Concordat — Build Log

## Phase 0 — verification (2026-09-26)

### What's confirmed live on Monad mainnet (verified against primary sources, not search blogs)

- **Monad mainnet**: live since Nov 24, 2025.
- **Sablier**: CONFIRMED via Sablier's own SDK changelog on GitHub
  (github.com/sablier-labs/sdk, CHANGELOG.md) — Monad added as a supported
  chain in v1.5.0 (2025-11-10), wrapper contract checksum fix in v2.0.0
  (2026-01-23), Monad testnet removed in v3.0.0 (2026-03-18) while mainnet
  support was retained. This is a primary source, not a search result.
- **Aave v3**: CONFIRMED via multiple reports of a formal Aave DAO
  governance deployment (12 assets, GHO, Chainlink Smart Value Recapture
  from day one). High confidence despite not hitting aave.com directly —
  this was a governance action, not a marketing claim.
- **Curvance**: reported live at mainnet launch with cbBTC markets
  ($20M+ TVL), sourced from Monad's own blog (blog.monad.xyz).
- **Kintsu (sMON)** and **aPriori (aprMON)**: both real, live liquid
  staking protocols on Monad, but NOT verified to project standard.
  docs.kintsu.xyz, apriori-docs.gitbook.io, and docs.sablier.com are all
  blocked by this session's network egress proxy, and neither project has
  a discoverable public GitHub contracts repo. Could not confirm exact
  contract addresses or view functions from a primary source within a
  reasonable number of calls.
- **Euler**: reported deployed to Monad, but only via aggregator
  blog claims, not Euler's own docs. Not verified to standard.
- **Blend on Monad**: this is a neobank/deposit-routing stack that routes
  into Aave/Morpho, not an independent lending market. Not the same
  project as Blend Capital (Stellar). Not a distinct primitive.
- **Superfluid**: NOT confirmed on Monad. Their historical deployment
  list (Polygon, Gnosis, Arbitrum, Optimism, Avalanche, BSC) doesn't
  include Monad in any source found.

### Decision: real vs synthetic demo cohort

**Decision: real cohort, Sablier only for v1.** Kintsu/aPriori staking
yield is dropped from v1 scope rather than guessed at or mocked, per rule
#2 (nothing mocked) and rule #5 (verify against own docs, not search
results) — since neither could be verified to standard within budget.
This can be revisited later if their contract addresses get confirmed
directly off the Monad block explorer (a primary source), but that is
out of scope for now.

**Reasoning:** Sablier is the strongest real, verifiable, live income
signal on Monad mainnet. A wallet's Sablier stream (recipient, deposit
amount, rate per second, amount withdrawn) is a queryable onchain object
readable directly via RPC/contract calls, with no subgraph or blocked
docs site dependency. It directly represents a recurring income stream
(streamed payments/salary), which is exactly the cashflow signal this
thesis needs for underwriting.

### Assumption logged

Demo cohort = real Monad mainnet wallets with active Sablier streams.
No fabricated wallet history. If a suitable real cohort of streams
cannot be found with enough volume/duration to be interesting, the
fallback is a clearly-labeled synthetic cohort — never presented as
real — decided and stated before Phase 1 scoring work begins, not
silently.

## Phase 1 — scoring model (2026-09-26)

### Decision: Sablier is the primary income signal, not a fallback

Per direction: Sablier streams are closer to real recurring income than
staking yield, and it's the signal that can actually change in a way
worth monitoring (Phase 2's whole point). Kintsu/aPriori are dropped from
scope entirely for now, not revisited as prep work. If Phase 1's formula
needs a second income type to prove it generalizes, that's a small
bounded add later, decided then.

### Confirmed contract data (verified byte-exact from primary source)

Fetched `deployments/lockup/v4.0/broadcasts/monad.json` directly from
`sablier-labs/sdk` on GitHub via `curl` + `python3 json.load` (not a
WebFetch summary, which is model-generated prose and cannot be trusted for
exact hex addresses — confirmed this the hard way after WebFetch's first
summary of the same file corrupted an address's apparent length before
byte-exact reparsing confirmed 42-char / 20-byte addresses).

Chain id in the broadcast file: `143` (Monad mainnet, cross-confirmed
against the public chain id 143 = Monad, independent of Sablier's own
data).

- `SablierLockup`: `0x82723c1ffec9d43de5fa80b25da8df99afd470ba`
- `SablierBatchLockup`: `0xb02d463f531c3eb1a92b18b9d4756e9d03ab2562`
- `LockupHelpers`: `0xc86b56250d2758f30d09b3420d9ec5b646244c7c`
- `LockupMath`: `0x6c873bce27aa6ca803ef7013f05d1802ab6995b6`
- `LockupNFTDescriptor`: `0x37ba02a35861f7254fae733e3a7cadd96d9d32a2`

`SablierLockup` is the one the scoring model reads from: it holds
per-stream `depositAmount`, `withdrawnAmount`, start/end time, and
cancelable/canceled status.

### Framework: asset-based lending / receivables factoring, not a novel model

A Sablier stream is treated as a receivable: a verified, contractual
future cashflow. Credit is extended against a borrowing base (`advance
rate x eligible collateral value`), the same structure banks use for
accounts-receivable lines of credit. The advance rate is a haircut
schedule keyed to receivable quality — this is standard ABL underwriting
practice (dilution reserves, aging schedules, concentration limits), not
an invented number. The cancelability haircut specifically mirrors the
Basel Credit Conversion Factor treatment of unconditionally-cancelable
vs. committed exposures (cancelable commitments get a much lower CCF).

### Formula

For each stream `i` held by a wallet:

```
remaining_value_i     = 0                                  if canceled
                       = deposit_amount_i - withdrawn_amount_i   otherwise

cancelability_factor_i = 0.5   if stream is sender-cancelable
                        = 1.0   if not

runway_factor_i = min(1, remaining_duration_i / loan_term_seconds)

risk_adjusted_value_i = remaining_value_i * cancelability_factor_i * runway_factor_i
```

Coverage ratio for the wallet:

```
risk_adjusted_income = sum(risk_adjusted_value_i for all active streams)
coverage_ratio        = risk_adjusted_income / requested_credit_line
```

Tiering:

```
coverage_ratio >= 1.5   -> FULL approval, approved_line = requested_credit_line
1.0 <= coverage_ratio < 1.5 -> TIGHTENED, approved_line = risk_adjusted_income
                                (sized down to what is actually 1:1 covered,
                                 rather than extending the full ask at an
                                 inadequate safety margin)
coverage_ratio < 1.0    -> DECLINE, approved_line = 0
```

### Thresholds — stated as deliberate choices, confirmed with the user

- **Cancelability haircut = 0.5x.** Chosen as a defensible midpoint: a
  cancelable stream's remaining value counts at half. Considered 0.25x
  (stricter) and 0x (exclude entirely) and rejected both — 0x throws away
  real signal from long-running cancelable streams that have never been
  canceled, 0.25x had no principled anchor beyond "more conservative."
- **Full-approval threshold = 1.5x coverage.** Chosen over 2.0x (too
  conservative for a demo, most streams wouldn't clear it) and 1.0x (no
  safety margin — a wallet whose income exactly equals the ask on paper
  has zero room for the stream running dry before the loan matures).
- **Decline threshold = 1.0x coverage.** Below nominal 1:1 coverage, the
  income literally cannot cover the line even before any haircut is
  applied further downstream (e.g. before repayment / interest), so this
  is a hard floor, not a judgment call.
- **Concentration (single-sender / HHI) haircut: skipped for v1.** Most
  cohort wallets will have one sender (one employer-style stream), so
  this term would be an inert constant multiplier on the wallets we
  actually have. Revisit if a real multi-sender wallet shows up in the
  cohort — this is a known, stated simplification, not an oversight.

### Volatility measure (for wallets with multiple historical streams)

Coefficient of variation (`stdev / mean`) across a wallet's realized
monthly income from completed streams — the same dispersion measure used
in self-employed/variable income averaging under conventional mortgage
underwriting (income history is averaged over ~2 years and discounted for
high variance). Returns `None`, not a guessed default, when a wallet has
fewer than 2 historical streams to compute it from.

### Gate: hand-walked in `scoring/example.py`

Two illustrative cases (explicitly labeled illustrative, not real
borrower data — see below) confirm the formula's mechanics:

1. Non-cancelable stream, $9000 deposit / $3000 withdrawn, 30 days into a
   90-day schedule, $4000 ask, 60-day loan term → coverage ratio exactly
   1.5, tier FULL, approved line $4000.
2. Identical stream but cancelable → risk-adjusted income halves,
   coverage ratio drops to 0.75, tier flips to DECLINE. This is the
   formula doing its actual job: the same underlying cashflow is treated
   very differently based on whether it's guaranteed.

Both assertions pass (`python3 scoring/example.py`).

### Blocker: this session's network policy blocks live Monad RPC and every block explorer tried

`rpc.monad.xyz`, `www.monadexplorer.com`, and `docs.monad.xyz` are all
denied by this environment's egress proxy (allowlist-based, deny by
default — confirmed via the proxy's own status endpoint, not guessed).
Only certain hosts (GitHub, raw.githubusercontent.com) are reachable
directly; the WebFetch/WebSearch tools have a separate, broader backend
that could reach some but not all of the needed hosts.

This means the Phase 1 gate above was validated with illustrative
parameters, not a live wallet — clearly labeled as such in
`scoring/example.py` and never presented as real. Pulling one real
wallet's actual stream state (for Phase 1's true gate and for Phase 2's
live monitoring) requires either:
1. Broadening this environment's network access to include
   `rpc.monad.xyz` (or an allowed RPC provider) via the environment's
   Network settings, or
2. The user supplying a real stream's parameters (recipient, stream id,
   block number) pulled from their own tooling, which this scoring module
   can then run against directly and deterministically.

Flagging this now rather than proceeding into Phase 2 (live monitoring)
on top of an unverified live-data path.
