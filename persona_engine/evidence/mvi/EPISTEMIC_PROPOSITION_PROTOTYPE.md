# Epistemic Proposition Prototype Verification

Date: 2026-09-02
Experimental code checkpoint: `073aa4c8dc7883f6a02bb82306ca942632ddc31d`
Workflow run: `33683939210`
Production runtime remains unchanged by this experiment.

## Result

The isolated typed epistemic representation is mechanically viable and does not regress the existing deterministic suite.

Focused prototype verification:

```text
Python 3.11: 6 passed
Python 3.12: 6 passed
```

Full experimental branch suite:

```text
Python 3.11: 385 passed, 1 skipped, 1 warning
Python 3.12: 385 passed, 1 skipped, 1 warning
```

The six extra tests are experimental epistemic regressions. Production `wayfarer` still has the previously verified 379-test runtime inventory.

## Demonstrated invariants

### Testimony is not truth

Recording testimony creates `EpistemicEvidence` only. It does not create an objective `WorldFact` and it does not silently create a current belief.

### Belief revision is explicit

A current `tentative`, `believed`, or `disbelieved` stance requires an explicit typed revision and at least one known evidence reference for the same proposition.

### Correction does not rewrite history

A later contradictory/corrective evidence item can support a revision from `believed` to `disbelieved` while the original supporting evidence remains byte-for-semantics unchanged in the ledger.

### Cross-proposition evidence fails closed

A proposition cannot cite evidence recorded for another proposition key.

### Model inference retains provenance and uncertainty

The prototype can preserve a `model_inference` evidence source and a tentative current state across serialization without promoting the inference to objective truth.

### Temporal metadata fails closed when malformed

Evidence with a `claim_valid_until` earlier than `claim_valid_from` is rejected.

### First-person status is derived, not generated

Typed state deterministically projects to first-person internal statements such as:

`I currently believe X.`

`I currently lean toward X, but I am not certain.`

`I currently do not believe X.`

The text has no authority over the state that produced it.

## What this verification does not establish

This checkpoint does not justify production integration.

It does not establish:

- natural-language proposition extraction;
- automatic testimony weighting;
- relationship-trust-to-belief equations;
- contradiction resolution policy;
- World Authority confirmation policy;
- canonical revision event/replay semantics;
- active/cold evidence residency;
- renderer disclosure policy for acquired knowledge;
- user-visible improvement;
- cross-model continuity improvement.

Those remain separate experiments.

## Architectural decision after this checkpoint

Do not merge the module into the production turn loop merely because its data contract is green.

The next epistemic experiment should focus on causal integration and replay with an explicit typed semantic input, not automatic free-form language parsing. A production implementation should keep durable evidence in canonical continuity and retain only causally necessary current proposition state/evidence references resident where possible.
