# Belief Timescale Audit

This audit answers a specific Wayfarer question before affective homeostasis and personality development are allowed to depend on belief state: are `current interpretive beliefs` and the slower `BeliefLedger` accidentally two competing implementations of the same concept?

## Finding

They are two structures, but they are intentionally different timescales and authorities rather than duplicate stores.

### Fast interpretive belief

Implemented by `InterpretiveBelief` / `InterpretationEngine`.

Properties:

- formed per turn from currently visible evidence,
- explicitly noncanonical,
- source-traced through `source_ids` and `support_keys`,
- biased by current pressures and relationship posture,
- deterministic and disposable,
- intended to answer: **how does the character currently read what is happening?**

It must not silently update the slow ledger.

### Slow consolidated belief

Implemented by `BeliefLedger` / `BeliefRecord`.

Properties:

- cartridge-defined dimensions,
- persistent across turns and restarts,
- changed through explicit evidence-count/consolidation rules,
- bounded by min/max/fixed semantics,
- subject to slow decay where configured,
- intended to answer: **what relatively durable learned position has accumulated?**

It must not be recomputed from each conversational impression.

## Required boundary

The architecture should remain:

```text
visible evidence
    -> InterpretiveBelief (fast, subjective, noncanonical)
    -> memory/evidence events
    -> explicit consolidation rule
    -> BeliefLedger (slow, persistent)
```

There is no direct assignment path from `InterpretiveBelief.confidence` to a `BeliefRecord.value`.

Current contract tests already verify that generating interpretive beliefs and even running a dream pass does not mutate the slow ledger when no qualifying consolidation evidence exists.

## Naming risk

Both structures use the word `belief`, which is semantically defensible but easy for a future contributor or coding agent to conflate. Documentation and APIs should therefore use the phrases **interpretive belief** and **consolidated belief** consistently.

Do not introduce a third generic `belief_state` container.

## Dependency rule for M7/M8

A new subsystem must state which timescale it consumes.

Affective homeostasis may consume current interpretive beliefs as appraisal input, but it may not treat them as durable truth.

Personality development may consume consolidated evidence and slow beliefs, but it may not promote a single turn-level interpretation directly into a trait change.

If a proposed feature cannot identify the belief timescale it reads, the feature is not ready to merge.
