# Intrinsic Motivation

Intrinsic motivation is a bounded bridge between existing organism state and
situated action. It is not a second cognitive engine.

The generic intrinsic module owns want activation and neglect, deterministic
utility scoring, and generation of one immutable `IntrinsicProposal`. A
proposal is a candidate influence, not an accepted action. The situated
synthesis and canonical action resolver decide whether it becomes the turn's
single `ActionDecision`.

Cartridges own what the character wants, which activities pursue each want,
their effort and pressure affinities, a proposed action kind, and stable
performance-tendency IDs. Character prose remains in cartridge expression
data rather than in the proposal or engine.

Activities may reference a validated `[performance_tendencies.<id>]` table.
These tables contain bounded stance, certainty/directness deltas, channel
modes, response latency, concealment bias, and supplementary-channel choices.
The ID is never treated as a stance or prose instruction by core code.

Want levels and neglect counters are bounded persisted lived state. Character
identity and motive definitions remain immutable cartridge data.

Selection uses:

```text
want activation
+ bounded neglect
+ activity utility
+ matching pressure
+ restlessness-weighted novelty
+ small persistence bonus
- energy shortfall
```

Ties resolve by stable activity ID. Proposal generation may update bounded
neglect evidence, but it does not change current activity or satisfy the want.
Those changes occur only after synthesis accepts the proposal and an objective
`ActionCompletion` is recorded. The completion pipeline records its outcome,
subjective experience, first-person memory, and action evidence for habits.
Generated prose never becomes the action or its outcome.

The records use bounded scalars, stable string IDs, arrays, and mappings so the
mechanism can be reproduced with fixed-size tables in a later C99 host.
