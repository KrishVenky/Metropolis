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

## Phase 1 — scoring model

Not started.
