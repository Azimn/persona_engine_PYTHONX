# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. New ChatGPT, Codex, Claude Code, or human development sessions should read this file before inferring state from older chat history.

Last updated: 2026-08-28

## Branch and baseline

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline merely to make it current.

The untouched pre-Wayfarer documentation claimed `171 passed, 1 skipped`; clean execution actually found Python 3.11 at `177 passed, 2 failed, 1 skipped` and Python 3.12 at `178 passed, 1 failed, 1 skipped`. Those failures remain preserved as baseline history.

## Latest fully verified pre-M3 checkpoint

Consistency/runtime checkpoint was verified in Wayfarer CI run `33219784195`:

```text
Python 3.11: 239 passed, 1 skipped, 1 warning
Python 3.12: success
```

The warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

## Latest M3 runtime commit

```text
ef0aaec89d48eb77ab760b310fd162f502e8a3c4
Bind engine persistence to canonical continuity ledger
```

The M3 targeted integration workflow completed successfully before pushing this commit. This documentation update triggers the full Python 3.11/3.12 Wayfarer suite against the integrated M3 branch.

## M0 baseline/project memory

**Status: COMPLETE for deterministic/offline evidence.**

Wayfarer has durable architecture/handoff documentation, two-version CI, deterministic simulator evidence, and a captured deterministic Pretorius session/state package. A local-model evidence transcript remains useful but does not block development.

## M1 ownership/authority

**Status: COMPLETE.**

Canonicality fails closed. Renderer speech, private cognition, interpretive beliefs, UI/avatar/voice output are noncanonical. Renderer choice is not identity. `InteriorEngine` does not consult `identity.model_name`. Ontology is character-owned rather than hard-coded as universally human or universally non-AI.

## M2 `.snp` v2 and interoperability phenotype

**Status: ARCHITECTURAL FOUNDATION COMPLETE.**

Wayfarer has permanent `entity_uuid`, deterministic versioned v1-to-v2 normalization, structured substrate-neutral self-model claims, authored phenotype namespaces separated from lived state, unknown-field preservation, progressive fidelity levels 1 through 5, and a machine-readable v2 schema companion.

MatrAIx interoperability is frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, with 1,290 dimensions. Import/export is lossless. Exact, approximate, one-to-many, many-to-one, unsupported, and preserve-only-unmapped behavior are explicit.

## Consistency/validation phase pulled forward

**Status: IMPLEMENTED AND GREEN.**

`ValidationRequest` / `ValidationResult` define the renderer-consistency seam. Severity is explicit: soft issues sanitize locally; hard issues receive one bounded constrained regeneration and deterministic offline fallback if still invalid; critical issues use deterministic identity-safe fallback immediately.

The semantic decision policy now separates arousal from meaning. High risk may constrain expression but does not automatically imply an identity boundary. `character_refusal -> protect_boundary`, `challenge -> challenge`, `go_quiet -> withdraw`, `deflect -> deflect`, and `shift_topic -> redirect`.

Raw rendered wording no longer writes character pressure state. Post-expression effects consume resolved semantic decisions instead of punctuation or word choice. Deterministic renderer-swap tests now compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics across different surface realizations. A manual two-Ollama-model probe is available at `tools/renderer_swap_probe.py`.

See `CONSISTENCY_LAYER.md`, `BELIEF_TIMESCALE_AUDIT.md`, `HOMEOSTASIS_ACCEPTANCE_GATE.md`, `ABLATION_STUDY_PLAN.md`, and `PRESSURE_SCENARIO_AUDIT.md`.

## M3 canonical continuity ledger

**Status: STORAGE/INTEGRITY FOUNDATION IMPLEMENTED; REPLAY EXPANSION REMAINS.**

The existing broad `event_log` is retained as a diagnostic journal. A new `continuity_event` table records only events admitted by Wayfarer's fail-closed canonicality policy.

Implemented:

- [x] Permanent `subject_uuid` keying, bound to `.snp` `entity_uuid` by `InteriorEngine`.
- [x] Deterministic compatibility UUID for direct legacy callers lacking portable identity.
- [x] Monotonic per-subject/per-epoch canonical sequence.
- [x] Event UUID.
- [x] `continuity_epoch` field reserved for later handoff/branch semantics.
- [x] Subject time and wall time stored separately. M3 v1 subject time is existing engine timestep; M4 will replace/extend it with ContinuityClock semantics.
- [x] Source actor, source class, authority class, visibility, event type, canonicality, causal-parent field, payload schema, and lossless payload.
- [x] User input is `reported_input`, not World Authority truth.
- [x] Accepted World Authority action resolution is canonical; rejected proposals remain diagnostic.
- [x] Renderer output, private cognition, interpretive beliefs, UI/avatar/voice output stay out of canonical continuity.
- [x] Deterministic state checkpoint digest at latest canonical sequence.
- [x] SQLite integrity check.
- [x] Sequence-gap and malformed-event integrity report.
- [x] Schema-versioned event-tail export.
- [x] Subject/epoch/canonicality/contiguous-sequence validated import.
- [x] Unknown payload-field preservation.
- [x] Explicit idempotent legacy-event backfill using deterministic UUIDv5 for admitted legacy rows.
- [x] Engine `_persist()` records state checkpoints.
- [x] Dedicated `CONTINUITY_LEDGER.md` documents the threat model and authority semantics.

Design remains intentionally non-blockchain. SHA-256 is used for deterministic state checkpoint fingerprints, not a previous-event cryptographic chain. Stronger tamper evidence remains optional for a future untrusted-sync/hostile-custody profile.

M3 still needs replay/application work after the event contract proves stable. Imported event tails are validated and stored but are not automatically executed against runtime state yet.

## Belief timescales

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. No direct interpretive-confidence to slow-belief assignment is permitted.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity begins with minimal shared profiles plus sensitivity/identifiability testing. M8 homeostatic variables require explicit owners, update/decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## M19 ablation split

Minimum character and minimum renderer are separate experiments. Study A holds renderer fixed while removing character machinery. Study B holds character machinery fixed while reducing renderer capability. Combine them only after main effects are understood.

## Long-silence status

Wayfarer now has an eight-hour persisted wall-clock advance plus process restart scenario. It verifies continuity and bounded somatic catch-up. The remaining structural limitation belongs to M4: current pre-M4 catch-up caps long gaps at 200 five-second cycles, so it does not yet represent the full elapsed interval semantically.

## Immediate next actions

First, record the full Python 3.11/3.12 CI result for `ef0aaec...` plus this documentation checkpoint.

Then continue M3 with replay/application rather than redesigning the storage contract. Replay should consume canonical continuity events, preserve authority distinctions, reject noncanonical injected events, and compare deterministic state/checkpoint results where an event family is currently replayable. Do not attempt to replay renderer prose.

After M3 replay is stable, M4 should introduce explicit ContinuityClock elapsed-time semantics so long absences are represented as elapsed human-like time without executing every missing second.

Run the manual two-Ollama-model renderer-swap probe when suitable local models are available and preserve its output as evidence, but do not make local-model availability a CI dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Do not guess from stale chat context. Repository documentation is part of the implementation contract.
