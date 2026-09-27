<p align="center">
  <img src="assets/logo.png" width="120" alt="Concordat logo">
</p>

# Concordat

Real-time, onchain-native undercollateralized credit — built for Monad
Metropolis 2026, Track 01 (Onchain Finance & Trading).

Prior undercollateralized credit protocols (Goldfinch, Maple) failed on
underwriting, not blockchain limits: covenant checks ran monthly against
static, self-reported data, so risk drifted for weeks before anyone
noticed. Concordat prices and monitors credit against real, live, onchain
income (Sablier streams on Monad mainnet), continuously — which only works
because Monad's ~400ms finality makes constant re-scoring cheap enough to
actually run.

## What's here

| Path | What it is |
|---|---|
| [`BUILDLOG.md`](BUILDLOG.md) | The full build record: every data source verified against its own primary source (not a search result), every threshold stated and reasoned about, every bug caught and how, block-number-logged live runs against real Monad mainnet state. Start here to see the work, not just the result. |
| [`scoring/model.py`](scoring/model.py) | The deterministic underwriting formula. No LLM makes or influences a credit decision anywhere in this project — same inputs always produce the same score. |
| [`scoring/monitor.py`](scoring/monitor.py) | The live monitoring mechanism: polls Monad mainnet directly, reads block number and timestamp atomically, reruns the formula. |
| [`scoring/phase1_gate_live.py`](scoring/phase1_gate_live.py) | The formula run against one real, live Sablier stream on Monad mainnet — not illustrative parameters. |
| [`web/index.html`](web/index.html) | The live demo. Single file, no build step, no server — reads Monad mainnet directly in your browser and runs the identical formula client-side. |
| [`GTM.md`](GTM.md) | Go-to-market and demand validation, grounded in real onchain data (not a persona) — including the honest, unrounded size of the addressable cohort today. |

## Run the demo

```
open web/index.html
```

That's it — no server, no build, no API key. It calls
`https://rpc.monad.xyz` directly from your browser (Monad's public RPC,
CORS-open) and reads Sablier Lockup
(`0x82723c1FfEc9D43de5fA80b25dA8Df99Afd470BA`) on Monad mainnet live. Try
a different real stream ID or change the requested credit line / loan term
and watch the tier recompute against real chain state.

A hosted copy (once GitHub Pages is enabled on this repo) will also be
available at the repo's Pages URL — see
`.github/workflows/deploy-pages.yml`.

## Run the scoring formula directly

```
cd scoring
python3 phase1_gate_live.py   # real stream, hand-derived assertions
python3 monitor.py 23 1000000000000000000000000 2592000   # live poll, any stream id
```

## The formula, one paragraph

Each Sablier stream is treated as a receivable (asset-based
lending / receivables-factoring framing, not an invented model): its
remaining value (`deposit − withdrawn`, zeroed if canceled) is haircut by
cancelability (0.5x if the sender can revoke it) and by runway
(`min(1, remaining_duration / loan_term)`), summed into a risk-adjusted
income figure. Below 1.0x coverage of the requested line, the request is
declined outright (an eligibility floor, not a smaller line). At or above
1.0x, the approved line is `min(requested, risk_adjusted_income / 1.5)` —
continuous, not tiered, because continuous re-scoring is the entire point:
static safety margins are what this project exists to replace. Full
derivation, every threshold's reasoning, and a bug that was caught and
fixed mid-build are in `BUILDLOG.md`.

## Known open items

- **Phase 2's "visible score change" gate is mechanism-verified but not
  yet observed against an organic real event.** All 26 real streams on
  this Sablier deployment were checked across 3.26 hours of real Monad
  chain time with zero state changes — a genuine negative result on a
  young, thin market, not a broken mechanism. See `BUILDLOG.md`, Phase 2.
- Kintsu/aPriori staking yield was explicitly scoped out of v1 (contract
  addresses not verifiable to this project's standard within budget) —
  Sablier alone is the income signal for this build.

## Track

Track 01, Onchain Finance & Trading, Monad Metropolis 2026.
