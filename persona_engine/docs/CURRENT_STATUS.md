# Project Wayfarer Current Status

Project Wayfarer is the active development line of `Azimn/persona_engine_PYTHONX` on the `wayfarer` branch.

The frozen pre-Wayfarer comparison point remains `main` at commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`. Do not use `main` documentation as current Wayfarer status.

PythonX remains the reference implementation and experimental laboratory. The long-term objective is not to make Python the minimum runtime. The objective is to discover and validate the minimum semantics required to preserve one portable, believable individual, then project those stabilized contracts into lower-resource runtimes including a future P99/C99-compatible implementation.

## Project definition

Wayfarer is a portable synthetic-individual architecture.

The authoritative character is not the LLM. The individual is represented by authored character data plus lived continuity state, including identity constraints, biography, relationships, memories, commitments, beliefs, affective state, developmental history, time, and causally traceable consequences.

A language model may provide semantic interpretation, proposal generation, or linguistic realization, but model replacement must not silently replace the individual's identity or lived trajectory.

The same individual is intended eventually to inhabit multiple hosts and renderer tiers, including deterministic/no-model rendering, small local models, larger local models, frontier models, games, phone/edge interfaces, and constrained runtimes.

## Current verification state

The ordered M1 runtime pass completed successfully in GitHub Actions run `33174272164` and pushed the two runtime commits only after compilation, targeted tests, and the complete Python 3.11 suite passed.

```text
Renderer/identity targeted tests: 7 passed
M1 ontology + renderer + engine targeted tests: 21 passed
Full Python 3.11 suite: 198 passed, 1 skipped, 1 warning in 3.47s
```

The normal Wayfarer CI matrix on Python 3.11 and 3.12 remains the branch-level verification authority. Check the most recent run after the current documentation/cleanup commits before quoting a newer exact result.

The standard local command is:

```bash
python -m pytest persona_engine/tests -q
```

## Frozen baseline finding

Historical documentation said `171 passed, 1 skipped`, but the untouched pre-Wayfarer code contained more tests.

Clean GitHub Actions runs of the frozen baseline found:

- Python 3.11: `177 passed, 2 failed, 1 skipped, 1 warning`
- Python 3.12: `178 passed, 1 failed, 1 skipped, 1 warning`

The shared failure was a stale validator test seam: the test patched `renderer.generate`, while active expression routing had moved to `renderer.generate_expression`. Wayfarer corrected the test so invalid output is injected through the live production path.

The detailed frozen record is in `WAYFARER_BASELINE.md`.

## Completed Wayfarer foundation

- Dedicated `wayfarer` development branch.
- GitHub Actions CI on Python 3.11 and 3.12.
- `WAYFARER_MASTER_PLAN.md` detailed roadmap.
- `WAYFARER_PROGRESS.md` live operational tracker.
- `WAYFARER_CHARTER.md` project definition.
- `AI_DEVELOPER_HANDOFF.md` multi-agent/multi-developer handoff rules.
- `AUTHORITY_MATRIX.md` state-ownership rules.
- `WAYFARER_BASELINE.md` frozen before-state and verification evidence.
- Root `AGENTS.md` instructions for Codex and other AI coding tools.

## M1 ownership and authority repair: runtime complete

### Production-path validator coverage

`test_output_validator_and_sanitizer_are_traced` now patches the real `generate_expression()` seam rather than the obsolete `generate()` path.

### Fail-closed canonicality

Explicit noncanonical markers veto promotion. `interpretive_belief`, `private_cognition`, renderer output, UI state, avatar state, voice plans, and other structurally noncanonical event families cannot be promoted merely by caller-supplied truth flags.

### Renderer selection is not identity

Legacy `[identity].model_name` is no longer required by the cartridge schema. Old v1 cartridges containing it remain loadable for compatibility, but the field is ignored for renderer selection and produces a migration warning.

Bundled cartridges no longer contain renderer hints. `CoreIdentity.model_name` remains only as an unstored constructor `InitVar` compatibility shim. `InteriorEngine` no longer reads it and now bootstraps its deterministic offline renderer from runtime policy only.

The compatibility InitVar should be removed only through an explicit future schema/API migration so older direct constructor callers are not broken accidentally.

### Ontology is character-scoped

The generic engine no longer assumes that saying `I am an AI`, `as an AI`, or `language model` is universally out of character.

Wayfarer now supports character-scoped `forbidden_self_claims`. Workspace prompts, output validation, and sanitization consult the current character's self-model constraints rather than a universal AI/human ontology rule.

The bundled existing characters explicitly carry their historical self-model restrictions so behavior remains preserved while ownership moves into character data.

Regression tests now prove that the same generic engine can host:

- a human-self character that rejects `I am an AI`, and
- an artificial-self character that may truthfully produce `I am an AI`.

The regression also verifies that character self-model constraints survive renderer replacement.

The current literal `forbidden_self_claims` mechanism is intentionally modest. M2 `.snp` v2 should introduce a more structured self-model/ontology representation rather than expanding this into a large phrase blacklist.

## Architecture features inherited from PythonX

The branch currently contains deterministic or bounded implementations for strict `.snp` cartridge loading, local SQLite persistence, relationship state, emotional pressure state, body state, world state, memory, intentions/open loops, habits, shared symbols, belief ledger, source-traced noncanonical interpretation, World Authority, deterministic Tide idle drift, evidence-backed consolidation hooks, replay/debug utilities, mock-safe audio/vision observations, voice plans, avatar-safe state projection, proactive proposals, optional local Ollama rendering, and deterministic offline rendering.

## Known limitations

The default offline expression path remains linguistically limited compared with a capable generative model. There is no real microphone, camera, TTS, avatar engine, or mobile-native host yet. Local-HF provider support remains scaffolding. Autonomous behavior is limited to existing idle/offscreen hooks rather than the planned event-based life scheduler. Replay does not yet reconstruct every future authoritative event family. There is not yet a formal continuity clock or cross-host single-writer handoff protocol. Social influence and collaboration authority are not yet formally typed. The MatrAIx interoperability phenotype layer is planned, not implemented. The minimum viable individual has not yet been established through ablation.

## Current design decisions

### Continuity ledger

Do not require a per-event cryptographic hash chain for the local single-owner prototype. M3 targets an append-only, sequence-numbered, transactional ledger with event IDs, continuity epochs, schema validation, state digests/checkpoints, causal references where useful, and export/import integrity checks.

Cryptographic tamper evidence is an optional future profile only if the threat model expands to untrusted synchronization, hostile hosts, remote custody, or multi-party administrative boundaries.

### Personality plasticity

Do not introduce large tables of hand-tuned per-trait decimals and treat them as validated psychology. M7 begins with a calibration/identifiability gate: use a small number of shared profiles, define observable consequences, sensitivity-test them, remove unidentifiable parameters, use held-out scenarios, version calibrated parameter sets, and require evidence before adding trait-specific overrides.

## Immediate next work

M1 runtime ownership repair is complete. Before beginning `.snp` v2 implementation:

1. Capture the documented deterministic simulator runs as durable artifacts with commands and outputs.
2. Capture a repeatable deterministic Pretorius transcript package including event/state evidence and renderer status.
3. Confirm the normal Python 3.11/3.12 Wayfarer CI after the M1 code and cleanup/documentation commits.
4. Update `WAYFARER_BASELINE.md` with the evidence locations while preserving the frozen baseline reference.
5. Begin M2 `.snp` v2 design: permanent entity identity, structured self-model/ontology, phenotype namespaces, progressive-fidelity rules, and MatrAIx interoperability planning.

## Required reading

Before modifying Wayfarer behavior, read in this order:

1. `WAYFARER_MASTER_PLAN.md`
2. `WAYFARER_PROGRESS.md`
3. `WAYFARER_CHARTER.md`
4. `AI_DEVELOPER_HANDOFF.md`
5. `AUTHORITY_MATRIX.md`
6. `ARCHITECTURE_LOCK.md`
7. `WAYFARER_BASELINE.md`
8. this file
9. relevant tests

Repository documentation is part of the implementation contract. If documentation and code disagree, establish live behavior through code, history, and tests, then update the documentation in the same work pass.
