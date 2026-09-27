# Concordat — Go-to-market & demand validation

## The first user, specifically

Not "crypto traders." The first user is **a contributor or grantee being
paid through a Sablier stream by a Monad-native project, DAO, or grant
program**, who wants liquidity against income they've already earned but
that hasn't finished vesting, without selling the position outright and
losing the upside.

This isn't a hypothetical persona. It's already happening on this exact
deployment: stream 23 and stream 24 on Sablier Lockup (Monad mainnet,
`0x82723c1FfEc9D43de5fA80b25dA8Df99Afd470BA`) are two identical-shaped
streams from the same sender (`0xb996c591fda11d3e67b8fad59a82d75d4349defe`)
to two different recipients, both created in the same transaction window,
same start/end, same deposit size — a real payroll-shaped disbursement, not
a one-off. Whoever runs that sender wallet is already paying more than one
person this way, on Monad, today. That's the first outreach list, not a
guess at one.

## Why this market doesn't already exist yet

Two real, separable reasons, not one narrative:

1. **Streaming income onchain is itself new at meaningful scale.** Sablier
   and similar primitives only became economical for routine, small-value
   payments (contributor pay, grants, not just large vesting cliffs) once a
   chain existed where continuous, granular payment streams don't cost more
   in gas than the payments themselves. That's a very recent condition —
   Monad mainnet has been live since November 2025, and Sablier's own
   Monad deployment has processed 26 total streams as of this build,
   confirmed directly onchain (see `BUILDLOG.md`, Phase 0/1). This is an
   early market by any honest measure, not an exaggerated one.

2. **Prior undercollateralized lenders weren't built to use it even where
   it existed.** Goldfinch and Maple underwrote against off-chain,
   self-reported financials with monthly-cadence covenant checks — because
   that was the only kind of signal available to them, and continuous
   re-scoring wasn't cheap enough to run as infrastructure. Both failed on
   the same pattern: risk drifted for weeks before anyone with reporting
   access noticed. Concordat's underwriting formula (see `scoring/model.py`
   and `BUILDLOG.md`) only works as *continuous* underwriting — no static
   safety margin baked in, sized instead against a real-time coverage ratio
   — because Monad's ~400ms blocks make re-scoring against live chain state
   cheap enough to actually run continuously. That combination (a real
   verifiable income primitive + a chain fast enough to monitor it
   constantly) is what didn't exist together before now.

## Evidence of real usage today, stated precisely

As of the block checked during this build (Sablier Lockup v4.0.0, Monad
mainnet, `nextStreamId()` = 27):

- **26 total streams exist.** Of those:
  - **9** were created by the contract's own deployer address
    (`0xf26994e6af0b95cca8dfa22a0bc25e1f38a54c42`, matches the deployment
    broadcast's origin) to a single fixed test recipient — almost
    certainly Sablier's own post-deploy smoke tests, not organic usage.
    Excluded from any usage claim below.
  - **14** are self-funded (sender address equals recipient address) —
    self-vesting or lockup patterns, not third-party income. Real activity,
    but not the "someone else pays me" signal this product underwrites.
  - **3** are genuine third-party streams: one sender funding one
    unrelated recipient (stream 11), and one sender funding two different
    recipients identically (streams 23/24) — the payroll-shaped pattern
    above.

Stated plainly: the addressable, underwritable cohort on Monad today is
**3 real third-party income relationships, across 2 distinct paying
wallets**. This is a thin market. It is not being inflated into something
it isn't — the honest number is the credible number, and it's the number
this scoring engine actually reads live, not a projection.

## Path forward — concrete, not aspirational

Given the size of the current cohort, the near-term plan is direct outreach
to the payer side, not a broad marketing motion:

1. **Identify the sender behind streams 23/24** (already streaming to
   multiple recipients — the strongest existing signal of a repeatable,
   ongoing payment relationship) and the sender behind stream 11, and reach
   out directly to understand who they are and whether their recipients
   would want liquidity against unvested balance. This is a two-conversation
   outreach list, not a hypothetical ICP.
2. **Target Monad-native grant programs and DAOs** already considering or
   piloting streaming payroll/grants — the Monad Foundation's own grant
   disbursement is a natural first integration conversation, since
   Concordat's underwriting is agnostic to who the sender is as long as the
   stream is real and onchain.
3. **Track growth against the verified baseline, not a vanity metric.**
   Target: grow from 3 to 15+ genuine third-party income relationships
   (same definition used above — sender distinct from recipient, excluding
   deployer test activity) within the first quarter after the hackathon,
   measured the same way this build measured it: read directly off
   `SablierLockup` on Monad mainnet, not self-reported.
4. **Expand the income-signal set only once the first is proven.**
   Kintsu/aPriori staking yield was explicitly scoped out of this build
   (see `BUILDLOG.md`, Phase 0/1) rather than guessed at. The right time to
   add a second signal type is after Sablier-based credit lines are live
   with real borrowers, not before — adding sources multiplies integration
   and audit surface before there's a single proven user.

No fundraising commitments or named partners are claimed here that aren't
already verifiable onchain — the outreach list above is literally the two
wallets already paying people this way on Monad mainnet, not a
speculative persona.
