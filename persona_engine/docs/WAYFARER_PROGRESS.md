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

M4 runtime integration:

```text
9e819a0aa02c607e53e566cafc1528380a4fd3ac
Implement M4 linear continuity clock
```

The phase-sized Python 3.11 integration run completed with:

```text
M4 targeted suite: 15 passed
Full suite: 258 passed, 1 skipped, 1 warning
```

The normal Python 3.11/3.12 Wayfarer CI is triggered by this documentation checkpoint and remains the final branch-level verification. The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

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

See `CONSISTENCY_LAYER.md`, `BELIEF_TIMESCALE_AUDIT.md`, `HOMEOSTASIS_ACCEPTANCE_GATE.md`, `ABLATION_STUDY_PLAN.md`, and `PRESSURE_SCENARIO_AUDIT.md`.

## Belief timescale audit

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. They are intentionally different timescales, not duplicate authorities. No direct interpretive-confidence to slow-belief assignment is permitted.

## M3 canonical continuity ledger and replay

**COMPLETE FOR THE CURRENT ROOT-EVENT CONTRACT.**

The old `event_log` remains a broad diagnostic journal. `continuity_event` stores only authority-eligible canonical lived-history events. The ledger is bound to the portable `.snp` `entity_uuid`, preserves source/authority/canonicality distinctions, validates sequence and import integrity, and uses SHA-256 only for deterministic checkpoints rather than a cryptographic event chain.

Canonical replay now validates the bundle before side effects, replays exogenous/root experiences through public character interfaces, skips derived state-transition records so consequences are not applied twice, and rejects renderer prose or other non-authority-eligible injections. Supported roots currently include user input and bounded audio/vision observations. Unsupported host-level roots are reported rather than silently claimed as complete.

Replay commit `d6ad2da2346fa28a17a87c9f931fda6d487c02d1` initially exposed a semantic-digest projection bug (`SensoriumProcessor.events` versus a nonexistent `.observations`). The repair commit `7ae8fd791731d8b7690da91dd76365cde82df2e4` was green on Python 3.11 and 3.12 at `255 passed, 1 skipped, 1 warning`.

M4 extends replay with canonical `time_advance` roots.

## M4 ContinuityClock

**FOUNDATION IMPLEMENTED.** See `CONTINUITY_CLOCK.md`.

Wayfarer now distinguishes authoritative subject elapsed time from legacy dynamics integration. An eight-hour shutdown advances the portable subject clock by the full eight hours. It does not execute 5,760 five-second simulation ticks and it does not pretend the old per-tick body/pressure constants are scientifically valid eight-hour dynamics.

`ContinuityClock` is persisted and monotonic. Backward wall-clock jumps advance subject time by zero and are recorded as corrections. Explicit host time advancement is supported through the public `CharacterAgent.advance_time()` interface. Meaningful elapsed intervals enter canonical continuity as `time_advance` root events and are replayable through the same public interface.

Pre-M4 body/pressure dynamics currently retain a clearly labeled `legacy_bounded_v1` compatibility integration budget of 1,000 seconds per catch-up. This is intentionally provisional. Real elapsed time is not truncated; only unvalidated legacy dynamics are capped.

Automatic wall-clock gaps smaller than the existing five-second dynamics quantum update the clock but do not create standalone canonical stopwatch events. Explicit advances and backward-clock corrections can still be recorded. `engine.timestep` remains a processing/work index and is no longer treated as elapsed time.

M4 deliberately does **not** infer loneliness, attachment change, relationship cooling, sleep, routines, or off-screen narrative from elapsed duration. Those effects require separate evidence that Wayfarer cannot produce the needed longitudinal behavior without them.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## M19 ablation split and early MVI checkpoint

Minimum character and minimum renderer are separate studies. Study A holds renderer fixed while stripping character machinery. Study B holds character machinery fixed while reducing renderer capability. Combine them only after main effects are understood.

The sequence has been intentionally changed: begin an **early character-side MVI baseline immediately after the minimal M4 clock**, before richer memory, homeostasis, or Society Lab mechanisms accumulate. This baseline is diagnostic, not a declaration that the current system is minimal. Its job is to determine what current machinery already contributes and where longitudinal behavior actually fails.

## Current research rule

Do not ask which cognitive subsystem sounds missing. Ask:

> What longitudinal behavior can Wayfarer not yet produce or preserve, and what is the smallest causal mechanism that fixes it?

New mechanisms remain provisional until observable longitudinal behavior or ablation evidence justifies them.

## Immediate next actions

1. Confirm normal Python 3.11/3.12 CI is green for the M4 branch state.
2. Build the first character-side MVI baseline harness with a fixed deterministic renderer and explicit existing-subsystem ablations.
3. Measure identity/decision/relationship/memory/time continuity under those ablations before implementing richer autobiographical memory or affective homeostasis.
4. Use the first MVI findings to choose the next mechanism based on an observed longitudinal deficit rather than roadmap momentum.
5. Run the manual two-Ollama-model renderer-swap probe when suitable local models are available, but do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
