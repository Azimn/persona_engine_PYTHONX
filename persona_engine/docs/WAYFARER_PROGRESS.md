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
374ed18599c8037a16b8d2714dff90872dc6022c
Let relevant lived history qualify present conduct
```

The phase-sized Python 3.11 integration run completed with:

```text
Focused history/MVI/sensorium tests: 10 passed
Full suite: 268 passed, 1 skipped, 1 warning
```

A normal Python 3.11/3.12 Wayfarer CI run should be treated as the final branch-level verification after documentation updates. The remaining known warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

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

Canonical replay validates the bundle before side effects, replays exogenous/root experiences through public character interfaces, skips derived records to avoid double application, and rejects renderer prose or other non-authority-eligible injections. Supported roots include user input, bounded audio/vision observations, and M4 `time_advance` events. Unsupported host-level roots are reported rather than silently claimed as complete.

The replay repair was verified on Python 3.11 and 3.12, with Python 3.11 at `255 passed, 1 skipped, 1 warning` before M4.

## M4 ContinuityClock

**FOUNDATION IMPLEMENTED.** See `CONTINUITY_CLOCK.md`.

Wayfarer distinguishes authoritative subject elapsed time from legacy dynamics integration. An eight-hour shutdown advances the portable subject clock by the full eight hours. It does not execute 5,760 five-second simulation ticks and it does not pretend pre-M4 body/pressure constants are validated eight-hour dynamics.

`ContinuityClock` is persisted and monotonic. Backward wall-clock jumps advance subject time by zero and are recorded as corrections. Explicit host time advancement is supported through `CharacterAgent.advance_time()`. Meaningful elapsed intervals enter canonical continuity as replayable `time_advance` roots.

Legacy dynamics currently retain a clearly labeled `legacy_bounded_v1` compatibility integration budget of 1,000 seconds per catch-up. Real elapsed time is not truncated; only unvalidated legacy dynamics are capped. Automatic wall gaps below the existing five-second dynamics quantum update the clock but do not create standalone canonical stopwatch events.

M4 deliberately does **not** infer loneliness, attachment change, relationship cooling, sleep, routines, or off-screen narrative from elapsed duration. Those effects require separate longitudinal evidence.

The M4 phase-sized run reached `258 passed, 1 skipped, 1 warning` on Python 3.11.

## Early MVI Study A

**FIRST CHARACTER-SIDE BASELINE CAPTURED.** See:

- `tools/mvi_character_baseline.py`
- `evidence/mvi/EARLY_CHARACTER_BASELINE.md`
- `evidence/mvi/early_character_baseline.json`

Renderer, cartridge, user ID, scenario order, and explicit 2-hour/8-hour time gaps are held fixed. Initial clean-seam ablations are memory retrieval, interpretation, symbols, habits, body dynamics, and the combined condition. There is deliberately no synthetic lifelikeness score.

### First finding: body sampling was masquerading as psychology

The first run appeared to show body dynamics changing 4 of 10 decisions and 6 risk buckets, but disabling body dynamics also removed 399 memories. Inspection found that persistent body states were emitted as new sensorium events every five-second compatibility step; each duplicate event could change pressure and create another autobiographical memory.

That was corrected at the event-semantic level. `SensoriumProcessor` now emits body-derived sensorium when a meaningful threshold/state changes, not every time the same condition is polled. Recovery followed by later re-entry is a new event; simply remaining depleted is not.

After the fix, the exact same MVI scenario reports zero decision, risk-bucket, relationship, or pressure divergence for all five clean individual ablations. Body-off now changes only three memories rather than 399. This means the earlier apparent body importance was sampling-frequency amplification, not evidence that body dynamics were load-bearing for conduct.

### Second finding: retrieved history was not participating in conduct

The corrected baseline showed `memory_retrieval_off` removed 30 retrievals while leaving decision, risk, relationship, pressure, final memory count, and semantic digest unchanged. Inspection confirmed the engine retrieved memories before conduct resolution but used them primarily in workspace/rendering rather than the decision itself.

Wayfarer now has a deliberately small `HistoryDecisionEvidence` adapter. It activates only when:

1. the current request concerns trust, commitment, or cooperation,
2. the current relationship still carries unresolved conflict,
3. retrieval finds sufficiently salient unresolved relationship history.

When active, it may qualify an otherwise ordinary response as `qualified_response`. It does not mutate trust or relationship state, does not create another memory store, and does not outrank identity or explicit resistance rules.

The fixed `history-dependent-conduct-v1` probe holds current trust, guardedness, and unresolved conflict constant. With relevant unresolved history the character selects `qualified_response`; without that history it selects `respond`. Relationship state remains equal after normal appraisal. Evidence is preserved in `evidence/mvi/HISTORY_DEPENDENT_CONDUCT.md` and `history_dependent_conduct.json`.

Resolved old conflict does not stay active merely because the episode remains in autobiographical memory; the adapter also requires current unresolved relationship state.

## Current MVI interpretation

The present Study-A baseline does **not** justify deleting interpretation, symbols, habits, or body dynamics. It says only that this fixed scenario does not expose a conduct contribution from them. Those mechanisms remain provisional until targeted longitudinal scenarios or human-visible evidence show their value.

Memory now has one deliberately bounded conduct path because a concrete longitudinal failure demonstrated the need for it. This is the intended Wayfarer development pattern.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## Current research rule

Do not ask which cognitive subsystem sounds missing. Ask:

> What longitudinal behavior can Wayfarer not yet produce or preserve, and what is the smallest causal mechanism that fixes it?

New mechanisms remain provisional until observable longitudinal behavior or ablation evidence justifies them.

## Immediate next actions

1. Confirm normal Python 3.11/3.12 CI is green for the integrated M4 + early-MVI + history-conduct branch state.
2. Audit the next candidate longitudinal behavior rather than automatically implementing richer memory/homeostasis. The current leading candidate is durable commitment behavior across time/restart because no explicit canonical commitment mechanism has yet been demonstrated.
3. If a commitment probe shows existing intention/open-loop machinery already preserves the required behavior, do not add a commitment subsystem.
4. If it fails, define the smallest semantic commitment representation that exists before renderer speech and can survive replay/restart without granting renderer text canonical write authority.
5. Continue targeted MVI scenarios for interpretation, habits, symbols, and body only where a longitudinal behavior gives them something concrete to explain.
6. Run the manual two-Ollama-model renderer-swap probe when suitable local models are available; do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
