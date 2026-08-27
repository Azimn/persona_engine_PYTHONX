# Project Wayfarer Current Status

Project Wayfarer is the active development line of `Azimn/persona_engine_PYTHONX` on the `wayfarer` branch.

The frozen pre-Wayfarer comparison point remains `main` at commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`. Do not use the stale `main` documentation as the status of current Wayfarer work.

PythonX remains the reference implementation and experimental laboratory. The long-term objective is not to make Python the minimum runtime. The objective is to discover and validate the minimum semantics required to preserve one portable, believable individual, then project those stabilized contracts into lower-resource runtimes including a future P99/C99-compatible implementation.

## Current Project Definition

Wayfarer is a portable synthetic-individual architecture.

The authoritative character is not the LLM. The individual is represented by authored character data plus lived continuity state, including identity constraints, biography, relationships, memories, commitments, beliefs, affective state, developmental history, time, and causally traceable consequences.

A language model may provide semantic interpretation, proposal generation, or linguistic realization, but model replacement must not silently replace the individual's identity or lived trajectory.

The same individual is intended eventually to inhabit multiple hosts and renderer tiers, including deterministic/no-model rendering, small local models, larger local models, frontier models, games, phone/edge interfaces, and constrained runtimes.

## Current Verified Wayfarer State

Latest completed CI verified before this documentation update:

- Workflow: `Wayfarer CI`
- Run: `33111704143`
- Commit: `fcaf4fd9af2f5c8e6e32b7ab5225ce133cb6c67e`
- Python 3.11: `194 passed, 1 skipped, 1 warning in 3.46s`
- Python 3.12: successful

The current test command is:

```bash
python -m pytest persona_engine/tests -q
```

A later documentation-only commit may have a newer head SHA. Check GitHub Actions for the latest branch result before quoting a newer count.

## Important Frozen-Baseline Finding

The historical documentation said `171 passed, 1 skipped`, but the untouched pre-Wayfarer code actually contained more tests.

Clean GitHub Actions runs of the baseline found:

- Python 3.11: `177 passed, 2 failed, 1 skipped, 1 warning`
- Python 3.12: `178 passed, 1 failed, 1 skipped, 1 warning`

The shared failure was a stale validator test seam: the test patched `renderer.generate`, while active expression routing had moved to `renderer.generate_expression`. Wayfarer corrected the test so it now injects invalid output through the real expression path.

The detailed frozen record is in `WAYFARER_BASELINE.md`.

## Completed Wayfarer Foundation Work

- Dedicated `wayfarer` development branch.
- GitHub Actions CI on Python 3.11 and 3.12.
- `WAYFARER_MASTER_PLAN.md` detailed roadmap.
- `WAYFARER_PROGRESS.md` live operational tracker.
- `WAYFARER_CHARTER.md` project definition.
- `AI_DEVELOPER_HANDOFF.md` multi-agent/multi-developer handoff rules.
- `AUTHORITY_MATRIX.md` state-ownership rules.
- `WAYFARER_BASELINE.md` frozen before-state and verification evidence.
- Root `AGENTS.md` instructions for Codex and other AI coding tools.

## Completed M1 Work So Far

### Validator test routing

`test_output_validator_and_sanitizer_are_traced` now patches the real `generate_expression()` seam instead of the obsolete `generate()` path.

### Fail-closed canonicality

The memory/event authority rules were tightened so explicit noncanonical markers veto promotion. Subjective `interpretive_belief` and `private_cognition` events are structurally noncanonical, and caller-supplied truth flags cannot elevate forbidden event families.

### Renderer/identity decoupling

Legacy `[identity].model_name` is no longer required by the cartridge schema.

Old v1 cartridges containing that field are still accepted for compatibility, but the field is ignored for renderer selection and produces a migration warning.

`CoreIdentity.model_name` is now compatibility-only constructor input rather than stored identity state, and bundled cartridges no longer contain renderer hints.

One cleanup remains: `InteriorEngine` bootstrap still reads the compatibility attribute while creating its default renderer. That path must be changed so the default offline renderer is selected by runtime configuration only, not by identity in any form.

## Active M1 Task

Remove universal ontology assumptions from the generic engine.

Current generic code still contains assumptions such as treating `I am an AI`, `as a language model`, or similar language as inherently out-of-character. Those rules are valid only for characters whose own self-model conflicts with those claims.

Wayfarer must support, under the same generic engine:

- a character who understands itself as artificial,
- a character whose self-model is human,
- fictional/embodied identities with other ontologies.

Character-specific self-model conflicts belong in cartridge/self-model policy, not generic engine regexes.

## Current Architecture Features Inherited From PythonX

The branch currently contains deterministic or bounded implementations for:

- strict `.snp` cartridge loading,
- local SQLite persistence,
- relationship state,
- emotional pressure state,
- body state,
- world state,
- memory,
- intentions and open loops,
- habits,
- shared symbols,
- belief ledger,
- source-traced noncanonical interpretation,
- World Authority,
- deterministic Tide idle drift,
- evidence-backed consolidation hooks,
- replay/debug utilities,
- mock-safe audio and vision observations,
- voice-plan state,
- avatar-safe state projection,
- proactive event proposals,
- optional local Ollama rendering,
- deterministic offline rendering.

## Current Known Limitations

- The default offline expression path is still linguistically limited compared with a capable generative model.
- No real microphone adapter is implemented.
- No real camera adapter is implemented.
- No real TTS output is implemented.
- No real avatar engine is implemented.
- No mobile-native host exists yet.
- Local-HF provider support remains scaffolding.
- Autonomous behavior is limited to current idle/offscreen hooks, not the planned full event-based life scheduler.
- Replay does not yet reconstruct all future authoritative event families.
- There is not yet a formal continuity clock or cross-host single-writer handoff protocol.
- Social influence and collaboration authority are not yet formally typed.
- The MatrAIx interoperability phenotype layer is planned, not implemented.
- The minimum viable individual has not yet been determined by ablation.

## Two Current Design Decisions

### Continuity ledger

Do not require a per-event cryptographic hash chain for the local single-owner prototype.

The default design target is an append-only, sequence-numbered, transactional ledger with event IDs, continuity epochs, schema validation, state digests/checkpoints, causal references where useful, and export/import integrity checks.

Cryptographic tamper evidence becomes an optional profile only if the threat model expands to untrusted synchronization, hostile hosts, remote custody, or multi-party administrative boundaries.

### Personality plasticity

Do not introduce large tables of hand-tuned per-trait decimals and treat them as validated psychology.

Start with a small number of shared plasticity profiles, define observable effects, run sensitivity analysis, remove unidentifiable parameters, use held-out scenarios, version calibrated parameter sets, and require evidence before adding per-trait overrides.

The exact experimental requirements are tracked in `WAYFARER_PROGRESS.md` and should be reflected in the detailed roadmap before M7 implementation begins.

## Immediate Next Work

1. Keep repository status documents current on every substantive Wayfarer change.
2. Finish removal of renderer selection from `InteriorEngine` identity bootstrap.
3. Remove generic AI/language-model ontology assumptions.
4. Add artificial-self and human-self regression characters/tests.
5. Re-run Wayfarer CI.
6. Capture dedicated simulator artifacts and the deterministic Pretorius human-visible baseline.
7. Continue into `.snp` v2 only after M1 ownership contracts are clean.

## Required Reading

Before modifying Wayfarer behavior, read:

1. `WAYFARER_MASTER_PLAN.md`
2. `WAYFARER_PROGRESS.md`
3. `WAYFARER_CHARTER.md`
4. `AI_DEVELOPER_HANDOFF.md`
5. `AUTHORITY_MATRIX.md`
6. `ARCHITECTURE_LOCK.md`
7. `WAYFARER_BASELINE.md`
8. this file
9. relevant tests

Repository documentation is part of the implementation contract. If documentation and code disagree, establish the live behavior through code, history, and tests, then update the documentation in the same work pass.