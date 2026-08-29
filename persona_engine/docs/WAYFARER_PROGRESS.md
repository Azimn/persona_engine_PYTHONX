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
6763456c08408d5ea2a0e7733518810ad41feea0
Let self-adopted commitments constrain later conduct
```

The commitment phase-sized Python 3.11 integration run completed with:

```text
Focused commitment/history/replay/clock tests: 19 passed
Full suite: 275 passed, 1 skipped, 1 warning
```

The preceding restart/repair history checkpoint was verified by normal Wayfarer CI on both Python 3.11 and 3.12 at `270 passed, 1 skipped, 1 warning`. This documentation update is intended to trigger normal two-version CI for the committed commitment-constraint state. The remaining known warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

## Baseline history

The untouched pre-Wayfarer documentation claimed `171 passed, 1 skipped`; clean execution actually found Python 3.11 at `177 passed, 2 failed, 1 skipped` and Python 3.12 at `178 passed, 1 failed, 1 skipped`. Those failures remain preserved as baseline history rather than being rewritten away.

## M0

**COMPLETE for deterministic/offline evidence.** Durable architecture/handoff docs, two-version CI, simulator evidence, and deterministic Pretorius session/state evidence exist. A local-model transcript remains useful but optional.

## M1

**COMPLETE.** Canonicality fails closed. Renderer speech, private cognition, interpretive beliefs, UI/avatar/voice output are noncanonical. Renderer choice is not identity. Ontology is character-owned rather than hard-coded globally.

## M2

**ARCHITECTURAL FOUNDATION COMPLETE.** Wayfarer has permanent `entity_uuid`, deterministic versioned v1-to-v2 normalization, structured substrate-neutral self-model claims, authored phenotype namespaces separated from lived state, unknown-field preservation, progressive fidelity levels 1 through 5, and a machine-readable v2 schema companion.

MatrAIx interoperability is frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, with 1,290 dimensions. Import/export is lossless. Unmapped dimensions default to preserve-only unsupported rather than guessed native semantics.

## Consistency/validation phase

**IMPLEMENTED AND GREEN.** `ValidationRequest` / `ValidationResult` define the renderer-consistency seam. Soft issues sanitize locally. Hard issues receive one bounded constrained regeneration and deterministic offline fallback if still invalid. Critical issues use deterministic identity-safe fallback immediately.

High arousal no longer automatically means identity boundary. Semantic conduct follows resistance type. Raw renderer wording and punctuation no longer mutate pressure state; post-expression effects consume the resolved semantic decision instead.

Deterministic renderer-swap tests hold character history/input fixed while varying surface language and compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics. A manual two-Ollama-model probe exists at `tools/renderer_swap_probe.py`.

## Belief timescale audit

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. They are intentionally different timescales, not duplicate authorities. No direct interpretive-confidence to slow-belief assignment is permitted.

## M3 canonical continuity ledger and replay

**COMPLETE FOR THE CURRENT ROOT-EVENT CONTRACT.**

The old `event_log` remains a broad diagnostic journal. `continuity_event` stores only authority-eligible canonical lived-history events. The ledger is bound to the portable `.snp` `entity_uuid`, preserves source/authority/canonicality distinctions, validates sequence and import integrity, and uses SHA-256 only for deterministic checkpoints rather than a cryptographic event chain.

Canonical replay validates the bundle before side effects, replays exogenous/root experiences through public character interfaces, skips derived records to avoid double application, and rejects renderer prose or other non-authority-eligible injections. Supported roots now include user input, bounded audio/vision observations, M4 `time_advance`, and explicit self-adopted `commitment_adopted` events. Unsupported host-level roots are reported rather than silently claimed as complete.

The replay repair was verified on Python 3.11 and 3.12, with Python 3.11 at `255 passed, 1 skipped, 1 warning` before M4.

## M4 ContinuityClock

**FOUNDATION IMPLEMENTED.** See `CONTINUITY_CLOCK.md`.

Wayfarer distinguishes authoritative subject elapsed time from legacy dynamics integration. An eight-hour shutdown advances the portable subject clock by the full eight hours. It does not execute 5,760 five-second simulation ticks and it does not pretend pre-M4 body/pressure constants are validated eight-hour dynamics.

`ContinuityClock` is persisted and monotonic. Backward wall-clock jumps advance subject time by zero and are recorded as corrections. Explicit host time advancement is supported through `CharacterAgent.advance_time()`. Meaningful elapsed intervals enter canonical continuity as replayable `time_advance` roots.

Legacy dynamics currently retain a clearly labeled `legacy_bounded_v1` compatibility integration budget of 1,000 seconds per catch-up. Real elapsed time is not truncated; only unvalidated legacy dynamics are capped. Automatic wall gaps below the existing five-second dynamics quantum update the clock but do not create standalone canonical stopwatch events.

M4 deliberately does **not** infer loneliness, attachment change, relationship cooling, sleep, routines, or off-screen narrative from elapsed duration. Those effects require separate longitudinal evidence.

The M4 phase-sized run reached `258 passed, 1 skipped, 1 warning` on Python 3.11.

## Early MVI Study A

**FIRST CHARACTER-SIDE BASELINE CAPTURED.** See `tools/mvi_character_baseline.py` and `evidence/mvi/EARLY_CHARACTER_BASELINE.md`.

Renderer, cartridge, user ID, scenario order, and explicit 2-hour/8-hour time gaps are held fixed. Initial clean-seam ablations are memory retrieval, interpretation, symbols, habits, body dynamics, and the combined condition. There is deliberately no synthetic lifelikeness score.

### First finding: body sampling was masquerading as psychology

The first run appeared to show body dynamics changing 4 of 10 decisions and 6 risk buckets, but disabling body dynamics also removed 399 memories. Inspection found that persistent body states were emitted as new sensorium events every five-second compatibility step; each duplicate event could change pressure and create another autobiographical memory.

That was corrected at the event-semantic level. `SensoriumProcessor` now emits body-derived sensorium when a meaningful threshold/state changes, not every time the same condition is polled. Recovery followed by later re-entry is a new event; simply remaining depleted is not.

After the fix, the exact same MVI scenario reports zero decision, risk-bucket, relationship, or pressure divergence for all five clean individual ablations. Body-off now changes only three memories rather than 399. The earlier apparent body importance was sampling-frequency amplification, not evidence that body dynamics were load-bearing for conduct.

### Second finding: retrieved history was not participating in conduct

The corrected baseline showed `memory_retrieval_off` removed 30 retrievals while leaving decision, risk, relationship, pressure, final memory count, and semantic digest unchanged. Inspection confirmed the engine retrieved memories before conduct resolution but used them primarily in workspace/rendering rather than the decision itself.

Wayfarer now has a deliberately small `HistoryDecisionEvidence` adapter. It activates only when the current request concerns trust/commitment/cooperation, the current relationship still carries unresolved conflict, and retrieval finds sufficiently salient unresolved relationship history.

When active, it may qualify an otherwise ordinary response as `qualified_response`. It does not mutate trust or relationship state, does not create another memory store, and does not outrank identity or explicit resistance rules.

The fixed `history-dependent-conduct-v1` probe holds current trust, guardedness, and unresolved conflict constant. With relevant unresolved history the character selects `qualified_response`; without that history it selects `respond`. Relationship state remains equal after normal appraisal. Unresolved history survives restart and still qualifies conduct. If genuine repair occurs before restart, the old episode remains in biography but no longer constrains later trust/cooperation conduct because the current relationship is no longer unresolved.

The restart/repair history tests were verified on Python 3.11 and 3.12 at `270 passed, 1 skipped, 1 warning`.

### Third finding: persistent intentions did not function as commitments

The pre-fix `commitment-gap-v1` probe gave the existing intention machinery its strongest reasonable opportunity: a high-priority self-adopted diagnostic intention was persisted, the process restarted, and the character then received a request that conflicted with that intention. The intention survived and was selected, but conduct was identical to the no-intention control: `respond` in both cases.

That isolated the missing property as causal participation, not storage. Wayfarer therefore did **not** add a second `CommitmentLedger`.

`Intention` now has optional typed commitment metadata, and `IntentionQueue` exposes active commitment constraints independently of ordinary intention priority. V1 supports only the demonstrated `non_disclosure` behavior. An explicit semantic self-decision API may adopt such a commitment. Conversational text and renderer speech cannot create it implicitly.

`CommitmentDecisionEvidence` checks whether a later disclosure request matches the active commitment target. If so, an otherwise ordinary `respond` or history-qualified response becomes `decline`. Identity/resistance policy still outranks the commitment constraint, so a simultaneous identity violation remains `protect_boundary` rather than being misclassified as commitment behavior.

Commitment adoption is canonical `self_commitment_authority` state and a replay root. The stable replay digest includes typed commitments without volatile priority or timestamp fields.

The fixed `commitment-constraint-v1` probe shows:

```text
explicit self-adoption: self_decision
survives restart:       yes
with commitment:        decline
without commitment:     respond
```

Evidence is preserved in `evidence/mvi/COMMITMENT_GAP.md`, `evidence/mvi/COMMITMENT_CONSTRAINT.md`, and their JSON companions.

No beneficiary model, fulfillment/breach state, promise-language parser, reciprocity model, or general commitment ontology has been added. Those remain unearned until a longitudinal failure requires them.

## Current MVI interpretation

The present Study-A baseline does **not** justify deleting interpretation, symbols, habits, or body dynamics. It says only that the current fixed scenario does not expose a conduct contribution from them. Those mechanisms remain provisional until targeted longitudinal scenarios or human-visible evidence show their value.

Memory has one bounded conduct path because a concrete failure demonstrated the need. Commitment has one bounded conduct path because a separate concrete failure demonstrated the need. Both reuse existing state rather than multiplying authorities.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## Current research rule

Do not ask which cognitive subsystem sounds missing. Ask:

> What longitudinal behavior can Wayfarer not yet produce or preserve, and what is the smallest causal mechanism that fixes it?

New mechanisms remain provisional until observable longitudinal behavior or ablation evidence justifies them.

## Immediate next actions

1. Confirm normal Python 3.11/3.12 CI is green for the committed minimal commitment state.
2. Probe interlocutor handoff as a minimum continuity property: does one `entity_uuid` retain shared biography/character-owned state when the active interlocutor changes, while relationship state remains actor-specific?
3. If current `user_id` persistence already produces the correct split, add nothing. If it instead partitions the individual itself, isolate the smallest persistence-key/relationship-boundary correction rather than creating a multi-agent social architecture.
4. Continue targeted MVI scenarios for interpretation, habits, symbols, and body only where a longitudinal behavior gives them something concrete to explain.
5. Run the manual two-Ollama-model renderer-swap probe when suitable local models are available; do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
