# Ensemble Causal Architecture Checkpoint

Date: 2026-09-03

Branch: `ensemble`

Verified code checkpoint: `29a6d29c19ed1d5c530513629cbaa1846ff444fa`

GitHub Actions run: `33778972790`

## Verification

The checkpoint completed successfully on Python 3.11 and Python 3.12.

Python 3.11 reported:

```text
Full deterministic suite: 466 passed, 1 skipped, 2 warnings
Focused Ensemble architecture suite: 60 passed
Ensemble evaluation entry points: passed
Deterministic offline Scene Lab smoke: passed
```

The two warnings are existing FastAPI/Starlette/anyio dependency deprecations. They are not behavioral test failures.

## What this checkpoint demonstrates

### Candidate ecology is subordinate to live subject authority

Normal `CharacterAgent` integration binds `EnsembleLLMRenderer` to `EngineAuthorityCandidateGate`.

The renderer may generate and surface-rank several expressive realizations, but each candidate must first pass the live `InteriorEngine` consistency authority using the current:

- forbidden self claims;
- resolved semantic decision;
- selected memory evidence;
- recall contract;
- current interpretation state;
- world state;
- deception ledger.

A regression deliberately removes a forbidden self claim from the renderer-side `ExpressionRequest` and supplies an invalid model candidate containing that claim. The candidate is still rejected because the gate reads the live engine identity rather than trusting renderer-local reconstruction.

Standalone renderer/evaluation use remains portable and falls back to request-reconstructed candidate validation. The final engine consistency pass remains a second boundary after selection.

### Epistemic state is subject-scoped

`CharacterAgent` stores `EpistemicLedger` state through UUID-scoped `subject_state` persistence.

Regression coverage demonstrates that:

- evidence and current belief survive restart;
- the same permanent subject sees the same belief across different interlocutor `user_id` streams;
- later contradictory evidence can revise the current stance without deleting prior evidence;
- testimony does not automatically become belief;
- model inference does not automatically become belief;
- testimony/model inference do not create world-authority facts.

This checkpoint verifies snapshot persistence across restart and interlocutor streams. It does not yet claim that epistemic revisions have a dedicated canonical continuity-event replay schema independent of snapshot state.

### Subject belief can influence interpretation without becoming world truth

`InterpretationEngine` can receive a read-only `subject_epistemic` source family from the UUID-scoped epistemic ledger.

Only non-UNKNOWN propositions are projected. A proposition is admitted to a turn only when it is lexically relevant to the current visible topic.

The resulting `InterpretiveBelief`:

- remains `canonical=False`;
- carries source id `subject_epistemic:<proposition_key>`;
- carries the subject proposition confidence;
- does not create a corresponding `WorldAuthority` proposition;
- does not activate on unrelated topics;
- does not activate when testimony has been recorded but no explicit belief revision has occurred;
- survives restart and interlocutor change because the source ledger belongs to the subject UUID.

The ordinary turn may still record `user_text` in World Authority as hidden input evidence. That is distinct from promoting the subject's epistemic proposition into world truth.

### Subject-relative appraisal has a causal consumer

Typed semantic events can produce subject-relative appraisal based on current relationship context and explicit goal/identity/control parameters.

The appraisal changes episodic memory salience and bounded existing pressure vessels. Controlled tests demonstrate that the same typed event can leave different lived traces in different subject contexts while the event record itself remains unchanged.

### Host delivery has a causal consumer

Speech delivery receipts distinguish intended renderer output from what the host actually delivered.

Partial or failed delivery can become the subject's episodic lived experience. Regression coverage verifies that an interrupted subject retains the delivered prefix and interruption while the undelivered remainder is absent from that lived memory after restart.

### Scene Lab exercises the public composition

The deterministic offline Scene Lab smoke completes through the public agent API with:

- multiple actors;
- actor-specific visibility;
- server truth separated from visible context;
- movement;
- speech input;
- host delivery;
- interruption-aware delivery receipts;
- lived delivery writeback.

## What this checkpoint does not demonstrate

No claim is made yet that Ensemble improves perceived character quality with a real language model.

Specifically unverified at this checkpoint:

- Qwen/Gemma candidate quality;
- reduced stiffness or repetition under actual model generation;
- improved human recognizability;
- better cross-model identity preservation than single-shot Wayfarer rendering;
- long-horizon social effects of subject-relative appraisal;
- recipient-side relationship consequences based on delivered rather than intended speech;
- dedicated canonical event replay for epistemic revisions;
- whether more persistent agenda fields are necessary.

Those are empirical questions for the next collection phase, not reasons to add more mechanisms preemptively.

## Next gate

Return to matched actual-model testing when the local Ollama environment is available.

The next implementation change should be earned by a demonstrated failure in those collections or in a controlled situated experiment. The architecture should not accumulate another speculative subsystem before that evidence exists.
