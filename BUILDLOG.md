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

Sizing (revised — see "correction" below for what changed and why):

```
coverage_ratio < 1.0   -> DECLINE, approved_line = 0
                           (eligibility screen, binary: risk-adjusted income
                            can't even nominally cover the ask)

coverage_ratio >= 1.0  -> approved_line = min(requested_credit_line,
                                               risk_adjusted_income / 1.5)
                           tier = FULL if approved_line == requested_credit_line
                                  else TIGHTENED
                           (margin-adjusted advance, continuous: the line is
                            always sized so the AMOUNT ACTUALLY APPROVED is
                            covered at a 1.5x margin, never more than what
                            was asked)
```

#### Correction made during confirmation (worth recording, not hiding)

The first version of this formula set `approved_line = risk_adjusted_income`
directly in the 1.0-1.5 coverage band. That's wrong: since
`risk_adjusted_income = coverage_ratio * requested_credit_line`, for any
coverage ratio in that band `risk_adjusted_income >= requested_credit_line`
— meaning the "tightened" tier was silently approving *more* than the ask,
never less. Caught this when asked to actually push back on the thresholds
rather than rubber-stamp them.

The fix also changed the shape of the model, not just capped the bug:
tiering was replaced with (1) a binary eligibility floor at coverage ratio
1.0, exactly as real ABL practice screens receivables in/out of the
borrowing base at all, and (2) a continuous margin-adjusted advance for
everything eligible, rather than a second discrete tier. This is also a
better fit for the thesis: continuous re-scoring is supposed to be what
lets Concordat run without Goldfinch/Maple's large static safety margins,
so the sizing function should itself be continuous, not snap between fixed
buckets with a hard boundary that has to be defended on its own.

1.0 and 1.5 are unchanged as the two threshold numbers (see rationale
below) — the correction was in how they're used, not their values.

### Thresholds — stated as deliberate choices, confirmed with the user

- **Cancelability haircut = 0.5x.** Chosen as a defensible midpoint: a
  cancelable stream's remaining value counts at half. Considered 0.25x
  (stricter) and 0x (exclude entirely) and rejected both — 0x throws away
  real signal from long-running cancelable streams that have never been
  canceled, 0.25x had no principled anchor beyond "more conservative."
- **Target margin = 1.5x.** Confirmed, not revised — divisor applied to
  risk-adjusted income to size the approved line. Chosen over 2.0x (too
  conservative for a demo, most streams wouldn't clear it for their full
  ask) and 1.0x (no safety margin — a wallet whose risk-adjusted income
  exactly equals the approved amount has zero room for the stream
  running dry before the loan matures, which is the exact failure mode
  this project exists to avoid).
- **Eligibility floor = 1.0x coverage.** Confirmed, not revised — below
  nominal 1:1 coverage, the income literally cannot cover the line even
  before the margin is applied, so this is a hard binary floor: not
  bankable at all, not a smaller line.
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

Three illustrative cases (explicitly labeled illustrative, not real
borrower data — see below) confirm the formula's mechanics:

1. Non-cancelable stream, $9000 deposit / $3000 withdrawn, 30 days into a
   90-day schedule, $4000 ask, 60-day loan term → coverage ratio exactly
   1.5, tier FULL, approved line $4000.
2. Identical stream but cancelable and a $4000 ask → risk-adjusted income
   halves to $3000, coverage ratio 0.75, below the eligibility floor ->
   DECLINE, approved line $0. Same underlying cashflow, opposite outcome,
   purely because it's not guaranteed — the haircut doing its actual job.
3. Same non-cancelable stream but a $5000 ask → coverage ratio 1.2,
   eligible (>= 1.0) but below the 1.5x target margin -> TIGHTENED,
   approved line sized down to $4000 (min($5000, $6000/1.5)) — correctly
   below the ask, which is what the earlier buggy version failed to do.

All assertions pass (`python3 scoring/example.py`).

### Network blocker — resolved (2026-09-26)

`rpc.monad.xyz` was denied by this environment's egress proxy; user added
it to the environment's allowed domains. `www.monadexplorer.com` and
`docs.monad.xyz` remain blocked, but weren't needed once direct RPC
access worked — every fact below came from `eth_call`/`eth_getLogs`
against `rpc.monad.xyz` plus `eth_getCode`/`eth_blockNumber` to confirm
liveness, not from either blocked host.

### Phase 1 gate, re-run against a real live stream (2026-09-26)

Confirmed the SablierLockup contract has real bytecode at
`0x82723c1ffec9d43de5fa80b25da8df99afd470ba` (`eth_getCode` non-empty),
chain id `0x8f` (143) via `eth_chainId`.

`eth_getLogs` on Monad mainnet is rate-limited to a 100-block range per
call, which makes scanning for stream-creation events from genesis
impractical within budget. Used a cheaper path instead: called the
contract's own `nextStreamId()` view function, which returned `27` —
meaning only streams 1-26 exist on this deployment so far. Enumerated all
26 directly via `ownerOf`, `getSender`, `getDepositedAmount`,
`getWithdrawnAmount`, `getStartTime`, `getEndTime`, `isCancelable`,
`wasCanceled`, `isDepleted` (selectors computed locally via Keccak-256,
not guessed from an ABI file, and cross-checked against known Sablier
Lockup function names).

Picked **stream 23** for the gate: sender `0xb996c591fda11d3e67b8fad59a82d75d4349defe`
funding recipient `0x77a89c51f106d6cd547542a3a83fe73cb4459135` — a genuine
third-party stream (the same sender also funds stream 24 to a different
recipient, i.e. a real one-to-many payroll-shaped pattern, not a
self-funded test stream). Asset: `0x350035555e10d9afaf1566aaebfced5ba6c27777`
(symbol `CHOG`, 18 decimals, read from the token contract directly).

All values pinned to block **108,166,208** (unix timestamp 1,790,421,803)
and re-read at that exact block after the initial unpinned scan, to
confirm reproducibility — same block, same numbers, both times:

- deposited: 5,000,000 CHOG
- withdrawn: 500,000 CHOG
- cancelable: true, not canceled
- start/end: 1,782,135,900 / 1,841,727,600

Run in `scoring/phase1_gate_live.py` against a $1,000,000-CHOG-equivalent
illustrative credit ask (the ask itself isn't onchain data — a real
borrower's requested line is an input to underwriting, not a fact to
verify — but every number describing the stream backing it is real):

- remaining_value = 4,500,000 CHOG
- cancelability haircut = 0.5x (stream is sender-cancelable)
- runway_factor = 1.0 (stream runs well past the 30-day loan term)
- risk_adjusted_income = 2,250,000 CHOG
- coverage_ratio = 2.25 → eligible and clears the 1.5x target margin
- tier = FULL, approved_line = 1,000,000 CHOG (the full ask)

Output is sane and explainable: a real, third-party, cancelable stream
with 90% of its value still unclaimed comfortably backs a line at half
its nominal remaining value. Gate passed — Phase 1 is done.

Also worth recording: computed the eight ABI function selectors used
above locally via Keccak-256 (`pip install pycryptodome`, allowed through
the environment's package-registry allowlist even while RPC access was
still blocked) rather than trusting a fetched ABI file, since a wrong
selector would silently either revert or, worse, hit an unrelated
function — same "verify against the primary source, not something
fetched" discipline as Phase 0's contract-address check.

## Phase 2 — real-time monitoring mechanism (2026-09-26)

### Mechanism: `scoring/monitor.py`

Polls `rpc.monad.xyz` directly for a given stream's current state, reads
the block number and timestamp from the same `eth_call`, and re-runs the
Phase 1 formula on it. No LLM in the loop. Every poll is independently
reproducible: same block, same output.

### Finding: this RPC node cannot serve arbitrary historical state — retention window slides forward continuously

Original plan was to find the exact historical block where stream 6 (a
real, already-canceled stream from the Phase 1 enumeration) flipped from
active to canceled, via binary search on `wasCanceled(6)` across block
history, and show the score snapping to zero right at that block — a
real, verified, non-staged state transition.

This failed, and it's worth recording exactly how, because the first
version of the search silently produced a wrong answer rather than an
obvious error. Old blocks return JSON-RPC error `-32602`, `"Block
requested not found ... querying historical state that is not
available"` — but my first `was_canceled_at()` helper treated *any*
non-`result` response (both real "not canceled" and "state pruned,
can't tell") as `False`. That made a monotonic-boolean binary search
converge on a plausible-looking but meaningless boundary. Caught it only
by re-querying the two boundary blocks directly and seeing the raw JSON-RPC
error instead of trusting the search's own output — the same "verify
before you write it down" instinct as the Phase 1 WebFetch address
mangling.

Re-ran a bisection for the actual availability boundary itself, and its
own endpoints changed answers between the search and the follow-up
verification a few dozen seconds later. That's not a bug in the search —
it means the retention window is a *sliding* cutoff, not a fixed archive
depth: a block that was still queryable partway through the search had
already aged out by the time it was re-checked. There is no stable
history on this endpoint to reconstruct the past from.

Consequence for Phase 2's design, and it's actually the right consequence
for this thesis, not just a workaround: monitoring here can only be
**forward-looking, poll-from-now**, never retrospective reconstruction.
That's stated as a real infrastructure constraint discovered during
verification, not chosen for narrative convenience — but it also happens
to be exactly the shape the pitch already argues for (continuous
re-scoring going forward, not a periodic look-back).

### Live verification of the polling mechanism

Ran `monitor.py` against stream 23 at block 108,205,082 (t=1,790,433,540):
same formula, same real stream, output identical in shape to the Phase 1
gate (coverage ratio 2.25, FULL, approved line unchanged) — confirms the
poll path itself (RPC round-trip, block+timestamp read, rescoring) works
correctly against live state, not just the one-shot Phase 1 script.

Then re-enumerated all 26 streams (same view calls as Phase 1) and diffed
against the Phase 1 snapshot (block 108,166,208, t=1,790,421,803). Block
timestamps put **11,746 seconds (3.26 hours) of real Monad chain time**
between the two snapshots (38,904 blocks, ~0.30s/block — consistent with
Monad's advertised block time, measured directly, not assumed).

**Result: no diffs.** None of `deposited`, `withdrawn`, `canceled`, or
`depleted` changed on any of the 26 streams across that 3.26-hour window.
This is a genuine negative result, not a failed test — real income
streams on a two-month-old deployment with 26 total streams don't churn
every few hours, and manufacturing a fake diff to report here would
violate rule #2 as directly as fabricating a wallet's history would.

### Open question for the user: how to close the "visible score change" gate

The mechanism is real and verified working. What's missing is a real,
non-staged instance of it actually catching a change, because none has
organically occurred in the observation window available so far. Not
continuing to poll speculatively — that's open-ended and the budget rule
says to stop and ask rather than keep searching with no clear resolution.
