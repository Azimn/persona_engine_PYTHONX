# Epistemic Proposition Experiment

Status: **EXPERIMENTAL BRANCH ONLY**

Branch: `wayfarer-adjacent-research-phase`

Production Phase D actual-model requests, scoring, and runtime remain frozen on `wayfarer`. This experiment must not be merged into the production turn loop before the frozen actual-model collection is captured or deliberately re-versioned.

## The demonstrated architecture gap

Wayfarer currently has three neighboring representations with intentionally different authority:

1. `MemoryUnit` can preserve first-person experience such as `I heard you say: the bridge is closed`, with a `USER_TOLD` source.
2. `InterpretiveBelief` can preserve a bounded, turn-local, noncanonical subjective reading grounded in visible evidence.
3. `WorldAuthority` owns objective host/world facts.

`BeliefLedger` is explicitly reserved for slow cartridge-defined developmental beliefs and is not an arbitrary semantic claim store.

There is therefore no durable typed owner for:

> Given the evidence available to me, what do I currently believe, doubt, or remain uncertain about?

This is distinct from both `someone told me X` and `X is objectively true`.

## Minimum candidate contract

`persona_engine/core/epistemic.py` prototypes the missing contract without wiring it into the production turn loop.

The candidate has four small concepts:

- `EpistemicEvidence`: immutable evidence about one atomic proposition;
- `EpistemicProposition`: the subject's current stance;
- `EpistemicRevision`: a returned causal certificate describing a current-state change;
- `EpistemicLedger`: current proposition state plus evidence records for experimental evaluation.

The current stance vocabulary is deliberately categorical:

- `unknown`;
- `tentative`;
- `believed`;
- `disbelieved`.

This is not an emotion model, personality model, or truth engine.

## Authority boundaries

Recording testimony does **not** change a proposition automatically.

Recording testimony does **not** create a `WorldFact`.

The ledger does not parse natural language.

The ledger does not assign reliability based on source type.

The ledger does not derive trust weights from the relationship system.

The ledger does not let a model inference become objective truth.

A current stance changes only through an explicit typed `revise(...)` operation. The revision must cite known evidence belonging to the same proposition unless the stance is `unknown`.

This separation is intentional. A later experiment can determine how relationship trust, direct observation, World Authority, corroboration, contradiction, and model inference should contribute to revision. Those rules should not be guessed into the storage layer.

## Evidence classes

The experimental provenance vocabulary is:

- `testimony`;
- `observation`;
- `world_authority`;
- `model_inference`;
- `self_inference`.

These are provenance classes only. Their names do not encode an automatic reliability hierarchy.

## Temporal semantics

Evidence records can optionally carry `claim_valid_from` and `claim_valid_until`. This permits later experiments involving statements that were once correct but became outdated without requiring a temporal graph database.

An invalid interval fails closed.

No automatic time-expiration rule is currently implemented. The temporal fields are evidence metadata until an experiment earns a resolver policy.

## First-person representation

The ledger provides a deterministic internal/debug projection:

- `I currently believe X.`
- `I currently lean toward X, but I am not certain.`
- `I currently do not believe X.`
- `I do not currently have a settled belief about X.`

This supports Wayfarer's first-person subject framing without granting generated prose authority. The projection is derived from typed state. It is **not** automatically renderer-visible. A future renderer integration must still pass through the least-privilege disclosure boundary.

## Current low-resource issue

The experimental class retains local evidence records so the contract can be tested in isolation. That is not yet the intended lifetime storage architecture.

A production integration should prefer:

- canonical continuity for durable evidence history;
- a compact current proposition projection;
- only the active evidence references necessary for present causal behavior;
- cold reconstruction where demonstrated safe.

This follows the same semantic-residency principle already used by Wayfarer memory. We should not create an ever-growing second autobiography inside current state.

## Required experiments before production integration

The prototype must first prove basic invariants on Python 3.11 and 3.12 and against the full deterministic suite.

After that, a runtime integration must freeze and test at least these cases before gaining production status:

1. **Testimony versus truth:** Alice says X. Wayfarer remembers Alice said X, but World Authority does not become X and current belief does not silently become X.
2. **Tentative belief:** a validated semantic decision can adopt a tentative stance with explicit evidence provenance.
3. **Correction:** later evidence can reverse the current stance while preserving the original evidence unchanged.
4. **Contradictory sources:** conflicting testimony can result in uncertainty rather than forced selection.
5. **Objective confirmation:** a visible World Authority fact can support a proposition without erasing prior contradictory testimony.
6. **Model-derived knowledge:** a stronger renderer/cognitive model may contribute an inference with provider/model provenance, but it remains inference until separately verified.
7. **Temporal update:** a claim can be historically valid and currently outdated without rewriting history.
8. **Restart/replay:** current proposition state must reconstruct from causal roots rather than depend only on an opaque snapshot.
9. **Cross-model swap:** a smaller model must receive the same current proposition state and provenance that a stronger model left behind.
10. **Resource plateau:** current epistemic state must not grow linearly merely because biography grows.

## Explicit non-goals for this phase

Do not add a graph database.

Do not add an OCEAN/Big Five layer.

Do not parse arbitrary user prose directly into beliefs.

Do not create universal trust-to-belief equations yet.

Do not let the renderer revise epistemic state directly.

Do not expose all evidence to the renderer by default.

Do not merge this experimental module into production solely because its unit tests pass.

## Decision criterion

The experiment earns further integration only if it demonstrably lets Wayfarer preserve the distinction among:

> what happened to me,
> what I was told,
> what I inferred,
> what the world authority establishes,
> and what I currently believe.

It must do so with less complexity than an equivalent graph/agent-memory architecture and without weakening existing authority, replay, first-person, or low-resource contracts.
