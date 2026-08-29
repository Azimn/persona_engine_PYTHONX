# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. New ChatGPT, Codex, Claude Code, or human development sessions should read this file before inferring project state from older chat history.

Last updated: 2026-08-29

## Current branch

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline merely to make it current.

## Latest implemented checkpoint

Current runtime/evidence head before this documentation update:

```text
bbe03c427c86019786a4b28a0cdcbf283a196c45
Keep one subject on one timeline across interlocutors
```

The latest phase-sized Python 3.11 integration run completed with:

```text
Focused clock/continuity tests: 14 passed
Full suite: 281 passed, 1 skipped, 1 warning
```

The immediately preceding subject-ordering state was also verified by normal Wayfarer CI on both Python 3.11 and 3.12. This documentation commit is intended to trigger normal two-version CI against the committed subject-clock repair. The remaining known warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

## Baseline history

The untouched pre-Wayfarer documentation claimed `171 passed, 1 skipped`; clean execution actually found Python 3.11 at `177 passed, 2 failed, 1 skipped` and Python 3.12 at `178 passed, 1 failed, 1 skipped`. Those failures remain preserved as baseline history rather than being rewritten away.

## Architectural direction

Wayfarer is being developed by a minimum-mechanism rule. The target is not maximum subsystem count. The target is the smallest substrate that can preserve a recognizable, portable simulated individual across time, interlocutors, renderers, and eventually hardware/runtime changes.

Richness should arise from combinations of a few causal state families rather than from many overlapping planners. A mechanism is added or generalized only after a controlled longitudinal test demonstrates a behavior the current system cannot produce or preserve.

The current operational question is:

> What longitudinal behavior can Wayfarer not yet produce or preserve, and what is the smallest causal mechanism that fixes it?

## M0

**COMPLETE for deterministic/offline evidence.** Durable architecture/handoff docs, two-version CI, simulator evidence, and deterministic Pretorius session/state evidence exist. A local-model transcript remains useful but optional.

## M1

**COMPLETE.** Canonicality fails closed. Renderer speech, private cognition, interpretive beliefs, UI/avatar/voice output are noncanonical. Renderer choice is not identity. Ontology is character-owned rather than hard-coded globally.

## M2

**ARCHITECTURAL FOUNDATION COMPLETE.** Wayfarer has permanent `entity_uuid`, deterministic versioned v1-to-v2 normalization, structured substrate-neutral self-model claims, authored phenotype namespaces separated from lived state, unknown-field preservation, progressive fidelity levels 1 through 5, and a machine-readable v2 schema companion.

MatrAIx interoperability is frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, with 1,290 dimensions. Import/export is lossless. Unmapped dimensions default to preserve-only unsupported rather than guessed native semantics.

## Consistency and renderer boundary

**IMPLEMENTED AND GREEN.** `ValidationRequest` / `ValidationResult` define the renderer-consistency seam. Soft issues sanitize locally. Hard issues receive one bounded constrained regeneration and deterministic offline fallback if still invalid. Critical issues use deterministic identity-safe fallback immediately.

High arousal no longer automatically means identity boundary. Semantic conduct follows resistance type. Raw renderer wording and punctuation do not mutate pressure state; post-expression effects consume the resolved semantic decision instead.

Deterministic renderer-swap tests hold character history/input fixed while varying surface language and compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics. A manual two-Ollama-model probe exists at `tools/renderer_swap_probe.py`.

## Belief timescales

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. They are intentionally different timescales, not duplicate authorities. No direct interpretive-confidence to slow-belief assignment is permitted.

## M3 canonical continuity ledger and replay

**COMPLETE FOR THE CURRENT ROOT-EVENT CONTRACT.**

The old `event_log` remains a broad diagnostic journal. `continuity_event` stores only authority-eligible canonical lived-history events and is bound to the portable `.snp` `entity_uuid`. Canonical replay validates bundles before side effects, replays supported exogenous/root experiences through public character interfaces, skips derived records to avoid double application, and rejects renderer prose or other non-authority-eligible injections.

Supported roots include user input, bounded audio/vision observations, M4 `time_advance`, and explicit self-adopted `commitment_adopted` events. Unsupported host-level roots are reported rather than silently claimed as complete.

The original M3 `sequence` remains a per-interlocutor stream ordinal because existing replay/export/checkpoint/integrity behavior depends on that contract. A later controlled Alice/Bob/Alice probe showed that one `subject_uuid` could therefore contain canonical input stream sequences `1, 1, 4`, leaving the subject's total biography without one explicit order.

Wayfarer did not replace or reinterpret the mature v1 stream field. It added one storage-level `subject_sequence` ordinal across `(subject_uuid, continuity_epoch)`. Existing databases deterministically backfill this value by recorded wall time and insertion order. Subject-wide readers use `subject_sequence`; v1 export deliberately omits it so the established interchange shape remains unchanged until a subject-wide portability experiment earns a versioned external representation.

The fixed `subject-history-ordering-v2` probe preserved stream input sequences `1, 1, 4` while assigning input roots subject ordinals `1, 4, 7`. Across all nine canonical events in that scenario, `subject_sequence` was exactly `1..9`. One additional integer therefore gives the individual one unambiguous biography without replacing per-interlocutor replay machinery.

The subject-order integration reached `280 passed, 1 skipped, 1 warning` on Python 3.11 and the committed state was subsequently green on normal Python 3.11 and 3.12 CI.

## M4 ContinuityClock

**FOUNDATION IMPLEMENTED AND SUBJECT-OWNED ACROSS INTERLOCUTORS.** See `CONTINUITY_CLOCK.md` and `evidence/mvi/SUBJECT_CLOCK_OWNERSHIP.md`.

Wayfarer distinguishes authoritative subject elapsed time from legacy dynamics integration. An eight-hour shutdown advances the portable subject clock by the full eight hours. It does not execute 5,760 five-second simulation ticks and it does not pretend pre-M4 body/pressure constants are validated eight-hour dynamics.

`ContinuityClock` is persisted and monotonic. Backward wall-clock jumps advance subject time by zero and are recorded as corrections. Explicit host time advancement is supported through `CharacterAgent.advance_time()`. Meaningful elapsed intervals enter canonical continuity as replayable `time_advance` roots.

Legacy dynamics retain a clearly labeled `legacy_bounded_v1` compatibility integration budget of 1,000 seconds per catch-up. Real elapsed time is not truncated; only unvalidated legacy dynamics are capped. Automatic wall gaps below the existing five-second dynamics quantum update the clock but do not create standalone canonical stopwatch events.

A cross-interlocutor ownership probe exposed a separate persistence defect. Alice advanced the same subject by exactly `28,800` seconds. Alice restart read `28,800` and canonical subject history read `28,800`, but Bob opened the same `entity_uuid` from the same database and read `0`. The clock arithmetic was correct; the snapshot was simply partitioned by `user_id`.

The minimum repair keeps existing per-interlocutor snapshots intact and adds startup reconciliation from canonical subject `time_advance` history. If canonical subject elapsed time is ahead of the local snapshot, the local `ContinuityClock` moves upward to that subject time. It never moves backward and it infers no psychology from duration.

The fixed `subject-clock-ownership-v1` probe now reports Alice `28,800`, Alice restart `28,800`, Bob `28,800`, same subject UUID, and `subject_clock_is_shared_across_interlocutors`.

M4 still deliberately does **not** infer loneliness, attachment change, relationship cooling, sleep, routines, or off-screen narrative from elapsed duration. Those effects require separate longitudinal evidence.

## Early MVI Study A

**FIRST CHARACTER-SIDE BASELINE CAPTURED.** See `tools/mvi_character_baseline.py` and `evidence/mvi/EARLY_CHARACTER_BASELINE.md`.

Renderer, cartridge, user ID, scenario order, and explicit 2-hour/8-hour time gaps are held fixed. Initial clean-seam ablations are memory retrieval, interpretation, symbols, habits, body dynamics, and the combined condition. There is deliberately no synthetic lifelikeness score.

The first baseline initially made body dynamics appear important because persistent body states were being re-emitted as new sensorium events every five-second compatibility step. That duplicated autobiographical memories and pressure effects. `SensoriumProcessor` now emits body-derived sensorium only on meaningful threshold/state changes. After that correction, the same baseline showed zero decision, risk-bucket, relationship, or pressure divergence for the five individual clean ablations. Body-off changed only three memories rather than 399. The earlier effect was sampling-frequency amplification, not evidence that body dynamics were load-bearing for conduct.

A second baseline finding showed that memory retrieval could remove 30 retrievals without changing decision, risk, relationship, pressure, final memory count, or semantic digest. Wayfarer therefore added a deliberately small `HistoryDecisionEvidence` adapter. It activates only for relevant trust/commitment/cooperation requests when current relationship state still carries unresolved conflict and sufficiently salient unresolved relationship history is actually retrieved. It may qualify an ordinary `respond` as `qualified_response`, but it does not mutate trust, create another memory store, or outrank identity/resistance policy. Unresolved history survives restart and can still constrain conduct; genuine repair leaves the episode biographical while removing its present constraint.

The restart/repair history tests were verified on Python 3.11 and 3.12 at `270 passed, 1 skipped, 1 warning`.

## Minimal commitment behavior

The pre-fix commitment probe demonstrated that the existing persistent `IntentionQueue` already stored self-adopted intentions across restart, but those intentions did not affect later conflicting conduct. That isolated the missing property as causal participation, not storage.

Wayfarer therefore did **not** add a `CommitmentLedger`. `Intention` gained optional typed commitment metadata and `IntentionQueue` exposes active commitment constraints independently of ordinary intention priority. V1 supports only the demonstrated `non_disclosure` behavior. Explicit semantic self-decision can adopt it; conversational text and renderer speech cannot.

`CommitmentDecisionEvidence` converts an otherwise ordinary `respond` or history-qualified response to `decline` when a matching active non-disclosure commitment exists. Identity/resistance policy still outranks this constraint. Commitment adoption is canonical `self_commitment_authority` state and a replay root.

The fixed commitment probe shows explicit self-adoption, restart survival, `decline` with the commitment and `respond` without it. No beneficiary model, fulfillment/breach state, promise-language parser, reciprocity model, or general commitment ontology has been added.

## Subject ownership across interlocutors

A continuing individual now demonstrates three distinct subject-level continuity properties while preserving actor-specific relationship state.

`entity_uuid` remains the same across Alice and Bob. Relationship trust/familiarity remain actor-specific. A self-adopted commitment made while Alice is present is restored from subject canonical history when Bob becomes active. Canonical events have one global `subject_sequence` while retaining their old per-interlocutor stream sequence. `ContinuityClock` reconciles to the latest canonical subject time rather than forking the individual's timeline when the interlocutor changes.

These repairs do not create a multi-agent cognition layer. They establish ownership boundaries. The important distinction is becoming: some state belongs to the continuing subject, some belongs to a particular relationship, and the existence of a `user_id` must not silently decide which is which.

## Current MVI interpretation

The present Study-A baseline does **not** justify deleting interpretation, symbols, habits, or body dynamics. It says only that the current fixed scenario does not expose a conduct contribution from them. Those mechanisms remain provisional until targeted longitudinal scenarios or human-visible evidence show their value.

Memory has one bounded conduct path because a concrete failure demonstrated the need. Commitment has one bounded conduct path because a separate concrete failure demonstrated the need. Subject biography order and subject time each gained only the smallest ownership primitive required by controlled cross-interlocutor failures.

This is intentional. Perceived behavioral complexity should emerge from intersections among a small number of independent causal facts rather than from duplicated planners or decorative state.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## Immediate next actions

1. Let this documentation commit verify the committed subject-clock repair under normal Python 3.11 and 3.12 Wayfarer CI.
2. Probe one additional unambiguously character-owned developmental state, preferably an earned trait, across an Alice/Bob interlocutor switch.
3. If that state is also partitioned by `user_id`, treat the repeated ownership failures as evidence for one small explicit persistence ownership rule rather than adding another one-off restoration method.
4. Keep relationship state actor-specific and do not globalize mixed or ambiguous families such as memories, pressures, symbols, world state, or body state without separate evidence.
5. Continue targeted MVI scenarios for interpretation, habits, symbols, and body only where a longitudinal behavior gives them something concrete to explain.
6. Run the manual two-Ollama-model renderer-swap probe when suitable local models are available; do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
