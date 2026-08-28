# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. New ChatGPT, Codex, Claude Code, or human development sessions should read this file before inferring project state from older chat history.

Last updated: 2026-08-28

## Current branch

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline merely to make it current.

## Latest verified checkpoint

M3 runtime integration:

```text
ef0aaec89d48eb77ab760b310fd162f502e8a3c4
Bind engine persistence to canonical continuity ledger
```

M3 documentation/verification checkpoint:

```text
3a2a9381fb86a61c2b019c46be266574606fd4db
Wayfarer CI run 33220191426
Python 3.11: 250 passed, 1 skipped, 1 warning
Python 3.12: success
```

The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

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

High arousal no longer automatically means identity boundary. Semantic conduct follows resistance type: character refusal, challenge, withdraw/go quiet, deflect, or redirect. Raw renderer wording and punctuation no longer mutate pressure state; post-expression effects consume the resolved semantic decision instead.

Deterministic renderer-swap tests now hold character history/input fixed while varying surface language and compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics. A manual two-Ollama-model probe exists at `tools/renderer_swap_probe.py`.

See `CONSISTENCY_LAYER.md`, `BELIEF_TIMESCALE_AUDIT.md`, `HOMEOSTASIS_ACCEPTANCE_GATE.md`, `ABLATION_STUDY_PLAN.md`, and `PRESSURE_SCENARIO_AUDIT.md`.

## Belief timescale audit

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. They are intentionally different timescales, not duplicate authorities. No direct interpretive-confidence to slow-belief assignment is permitted.

## M3 canonical continuity ledger

**STORAGE/INTEGRITY FOUNDATION COMPLETE AND GREEN. REPLAY EXPANSION REMAINS.**

The old `event_log` remains a broad diagnostic journal. The new `continuity_event` table stores only authority-eligible canonical lived-history events.

Implemented:

- permanent `.snp` `entity_uuid` binding as canonical `subject_uuid`,
- deterministic compatibility UUID for legacy direct callers,
- monotonic per-subject/per-epoch canonical sequence,
- event UUID,
- continuity epoch field,
- subject time and wall time stored separately,
- source actor/class and authority class,
- visibility, event type, canonicality, causal-parent field, payload schema, and lossless payload,
- user input authority represented as `reported_input`, not World Authority truth,
- accepted World Authority action resolution admitted while rejected proposals remain diagnostic,
- renderer/private-cognition/interpretive/UI/avatar/voice events excluded from canonical continuity,
- deterministic checkpoint digest at latest canonical sequence,
- SQLite integrity check,
- sequence-gap and malformed-event validation,
- schema-versioned event-tail export,
- subject/epoch/canonicality/contiguous-sequence validated import,
- unknown payload-field preservation,
- explicit idempotent legacy backfill with deterministic UUIDv5 identifiers,
- engine checkpoints recorded during normal persistence,
- dedicated `CONTINUITY_LEDGER.md` threat-model and authority documentation.

No previous-event cryptographic chain is required by the current local single-owner threat model. SHA-256 is a checkpoint fingerprint, not a blockchain mechanism. Stronger tamper evidence remains optional for a future untrusted-sync or hostile-custody profile.

Imported event tails are validated and stored but are not yet executed against runtime state. That is the remaining M3 replay/application work.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## M19 ablation split

Minimum character and minimum renderer are separate studies. Study A holds renderer fixed while stripping character machinery. Study B holds character machinery fixed while reducing renderer capability. Combine them only after main effects are understood.

## Long-silence status

Wayfarer has an eight-hour persisted wall-clock advance plus process restart test. It verifies continuity and bounded somatic catch-up. The remaining limitation belongs to M4: pre-M4 catch-up caps long gaps at 200 five-second cycles, so it is not yet a full semantic representation of elapsed subject time.

## Immediate next actions

Continue M3 with canonical replay/application rather than redesigning storage. Replay must consume canonical continuity events, preserve authority distinctions, reject noncanonical injected events, and never replay renderer prose as causal input. Initially replay exogenous/root events and treat derived state-transition records as verification evidence rather than applying them twice.

After replay stabilizes, M4 should introduce explicit ContinuityClock elapsed-time semantics so long absences are represented as elapsed human-like time without executing every missing second.

Run the manual two-Ollama-model renderer-swap probe when suitable local models are available and preserve its output as evidence, but do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
