# Project Wayfarer

Project Wayfarer is the active next-generation development line of the PythonX Persona Engine.

Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen pre-Wayfarer baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

If you cloned the repository normally, switch branches before evaluating current Wayfarer work:

```bash
git switch wayfarer
```

The `main` branch is intentionally retained as the pre-Wayfarer comparison point.

## What Wayfarer Is

Wayfarer is a reference architecture for a portable, persistent simulated individual.

The project is not fundamentally a chatbot or a role-play prompt. The design target is one continuing individual whose identity, biography, relationships, commitments, memories, affective state, developmental history, and causal consequences live outside any particular language model.

A language model may provide semantic interpretation, proposal generation, or natural-language realization. It is not the authority over who the character is.

The same individual is intended eventually to move among different substrates and expression systems, including:

- deterministic/no-model rendering,
- very small local models,
- larger local models,
- frontier models,
- desktop and phone interfaces,
- game NPC hosts,
- simulated social environments,
- future low-resource P99/C99-compatible runtimes.

Changing the renderer may change fluency, vocabulary, reasoning bandwidth, or style. It must not silently replace the individual's lived history or identity trajectory.

## Current Wayfarer Doctrine

- The persistent subject is the object of design.
- The model is a replaceable semantic/expression substrate.
- Renderer output is not canonical truth.
- Character-specific content belongs in `.snp` data or explicitly character-scoped lived state.
- World Authority owns objective facts.
- The character owns subjective interpretation.
- Social language is experience/evidence, not direct write authority.
- A peer agent, consensus claim, or model suggestion cannot directly become an executable goal.
- Character willingness and host capability/permission are separate gates.
- One individual has one canonical lived history.
- Divergent copies become branches/descendants unless explicit merge semantics are designed later.
- The portable source may be rich while constrained runtimes execute a sparse projection.
- No cognitive subsystem belongs in the minimum runtime until testing shows that it contributes observable character fidelity.

## Current Verified Test State

Latest completed phase-sized production integration:

- Runtime commit: `268739c` (`Preserve slow belief development in canonical continuity`)
- Documentation closeout: `9b4f64a` (`Document developmental continuity contract`)
- Focused developmental/continuity/replay contracts: `18 passed`
- Full Python 3.11 deterministic suite: `330 passed, 1 skipped, 1 warning`
- Changed slow belief trajectory: live `-0.4`, restart `-0.4`, canonical replay `-0.4`
- Two separated no-change repair consolidation boundaries: live `0.0`, canonical replay `0.0`
- Root-only 1,000-turn production SQLite baseline: `2,486,272 B`
- Root-only 5,000-turn production SQLite baseline: `8,581,120 B`
- 5,000-turn active serialized state: approximately `12.8 KB`

The remaining warning is the existing Starlette/httpx TestClient deprecation. This README update intentionally triggers the normal Python 3.11/3.12 Wayfarer CI matrix against the final developmental-continuity branch state.

Run locally with:

```bash
python -m pytest persona_engine/tests -q
```

The historical `171 passed, 1 skipped` figure in the old documentation was stale. The true frozen baseline and its failures are preserved in `persona_engine/docs/WAYFARER_BASELINE.md`.

## Important Baseline Regression That Wayfarer Already Fixed

The pre-Wayfarer test `test_output_validator_and_sanitizer_are_traced` monkeypatched `renderer.generate`, but the production expression path had moved to `renderer.generate_expression`. The test therefore stopped injecting invalid output into the actual renderer seam.

Wayfarer corrected the test to patch `generate_expression()` directly so validator/sanitizer tracing is tested against the live path.

## M1 Work Already Completed

Wayfarer has already:

- added CI on Python 3.11 and 3.12,
- added durable project/handoff documentation,
- made event canonicality fail closed,
- made subjective interpretation/private cognition structurally noncanonical,
- added adversarial canonicality tests,
- made legacy `[identity].model_name` optional,
- prevented cartridge `model_name` from selecting a renderer,
- turned `CoreIdentity.model_name` into compatibility-only constructor input rather than stored identity,
- removed renderer hints from bundled cartridges,
- added renderer/identity authority tests.

M1 ownership/ontology repair is complete. Current continuity work uses minimum-sufficient causal roots while preserving historical v1 compatibility. Slow `BeliefLedger` development now has an explicit digest-verified `belief_consolidation` boundary so replay preserves demonstrated developmental history without restoring verbose per-turn state records.

## Two Design Decisions Added During Review

### Keep the continuity ledger simple until the threat model requires more

The local-first reference implementation does **not** require a cryptographic previous-hash chain for every event.

The default target is an append-only, sequence-numbered, transactional ledger with event IDs, continuity epochs, schema validation, causal references where useful, state digests/checkpoints, and explicit export/import integrity checks.

Cryptographic tamper evidence becomes an optional future profile only if Wayfarer introduces untrusted multi-party synchronization, hostile hosts, remote custody, or another real adversarial-integrity requirement.

### Plasticity numbers must earn their existence

Wayfarer will not assign many per-trait constants simply because they look plausible.

Developmental parameters must be kept parsimonious, tied to observable behavior, sensitivity-tested, evaluated on held-out scenarios, versioned, and supported by experimental evidence before trait-specific overrides are accepted.

## Install

From the repository root:

```bash
python -m pip install -e .
```

For developer/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Ollama is optional. Deterministic tests do not require network access, a GPU, microphone, camera, TTS, avatar engine, or a model download.

## Run the Human UI

```bash
python -m uvicorn "persona_engine.ui:create_app" --factory --reload
```

or:

```bash
persona-engine-ui
```

The current UI supports cartridge selection, session reset, streamed chat, public organism status, current interpretive beliefs, proactive proposals, mock-safe sensor observations, read-only debug details, and local renderer controls.

## Run Simulators

Examples:

```bash
python persona_engine/simulator.py --script persona_engine/simulator_scripts/pretorius_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/organism_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_anchored_misread.yaml --cartridge persona_engine/cartridges/pretorius.snp
```

A dedicated preserved simulator-artifact baseline is still pending and is tracked in the Wayfarer progress file.

## Cartridges

Current `.snp` cartridges live in `persona_engine/cartridges/`.

Wayfarer is preparing these files to become the authored portable source of an individual, with a future MatrAIx-compatible phenotype interoperability layer and runtime-specific projections.

Renderer/model selection is runtime configuration, not identity.

## Project Documentation

AI coding tools and human contributors should read the following before behavior-changing work:

1. `persona_engine/docs/WAYFARER_MASTER_PLAN.md`
2. `persona_engine/docs/WAYFARER_PROGRESS.md`
3. `persona_engine/docs/WAYFARER_CHARTER.md`
4. `persona_engine/docs/AI_DEVELOPER_HANDOFF.md`
5. `persona_engine/docs/AUTHORITY_MATRIX.md`
6. `persona_engine/docs/ARCHITECTURE_LOCK.md`
7. `persona_engine/docs/WAYFARER_BASELINE.md`
8. `persona_engine/docs/CURRENT_STATUS.md`
9. relevant tests

Root `AGENTS.md` contains mandatory instructions for Codex and other automated coding assistants.
