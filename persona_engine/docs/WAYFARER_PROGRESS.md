# Project Wayfarer Live Progress

This file is the short-form operational status for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. This file records what is actually true now so a new ChatGPT, Codex, Claude Code, or human session can resume without reconstructing state from chat history.

Last updated: 2026-08-28

## Current branch

- Project name: **Project Wayfarer**
- Repository: `Azimn/persona_engine_PYTHONX`
- Development branch: `wayfarer`
- Frozen pre-Wayfarer baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`
- M1 renderer-decoupling commit: `c064c3d4fdedfd08668171b26fc9e26cb8443c70`
- M1 ontology-decoupling commit: `ba78a1cfccb1f0e78aa46ea41a5e251f54bdfca0`

A normal clone still lands on `main`. Use:

```bash
git switch wayfarer
```

before evaluating current Wayfarer behavior. Do not rewrite `main` merely to make it current. Its purpose is to preserve the before-state.

## Frozen baseline findings

The old documentation said `171 passed, 1 skipped`, but that count was stale.

Independent clean GitHub Actions verification of the untouched baseline found:

- Python 3.11: `177 passed, 2 failed, 1 skipped, 1 warning`
- Python 3.12: `178 passed, 1 failed, 1 skipped, 1 warning`

The shared failure was `test_output_validator_and_sanitizer_are_traced`. It patched `renderer.generate`, while live expression routing had moved to `renderer.generate_expression`, so the invalid text no longer entered the real production seam. The Python 3.11 baseline also exposed a brittle lexical expectation in the anchored-misread simulator. Both findings are preserved in `WAYFARER_BASELINE.md`.

## Latest verified runtime result

The ordered M1 maintenance run `33174272164` completed successfully and pushed both runtime commits only after compilation, targeted tests, and the complete Python 3.11 suite passed.

Verification inside that run:

```text
Renderer/identity targeted tests: 7 passed
M1 ontology + renderer + engine targeted tests: 21 passed
Full Python 3.11 suite: 198 passed, 1 skipped, 1 warning in 3.47s
```

The normal two-version Wayfarer CI should be treated as the final branch verification after the documentation/cleanup commits in this pass. Check GitHub Actions and update this section if its result differs.

## Completed foundation work

- [x] Created `wayfarer` from the frozen PythonX baseline.
- [x] Added Wayfarer CI on Python 3.11 and 3.12.
- [x] Added `WAYFARER_CHARTER.md`.
- [x] Added `AI_DEVELOPER_HANDOFF.md`.
- [x] Added `AUTHORITY_MATRIX.md`.
- [x] Added `WAYFARER_BASELINE.md`.
- [x] Added `WAYFARER_MASTER_PLAN.md`.
- [x] Added this live progress tracker.
- [x] Branded README/current-status documentation as Project Wayfarer.
- [x] Updated root `AGENTS.md` so AI coding tools are directed to Wayfarer project memory first.

## Completed M1 ownership/authority repair

### Production-path validator coverage

- [x] Corrected `test_output_validator_and_sanitizer_are_traced` to patch `generate_expression()`, the active production expression seam.

### Fail-closed canonicality

- [x] Explicit noncanonical markers veto canonical promotion.
- [x] `interpretive_belief` is not a default-canonical event class.
- [x] `private_cognition` and other output/UI families are structurally noncanonical.
- [x] Added adversarial canonicality tests.

### Renderer is not identity

- [x] Legacy `[identity].model_name` is optional rather than required.
- [x] Legacy cartridge `model_name` cannot select a renderer.
- [x] Legacy cartridge use produces a migration warning.
- [x] Bundled cartridges no longer contain renderer hints.
- [x] `CoreIdentity.model_name` is compatibility-only `InitVar`, not stored identity.
- [x] `InteriorEngine` no longer reads `identity.model_name` at all.
- [x] Default engine renderer bootstrap is explicitly offline host/runtime policy.
- [x] Added a regression that removes the compatibility class attribute and proves `InteriorEngine` still boots correctly.

The `CoreIdentity.model_name` InitVar remains only as a deliberate compatibility shim for pre-Wayfarer constructor callers. Its eventual removal belongs to an explicit schema/API migration, not an incidental refactor.

### Ontology is character-scoped

- [x] Removed universal `I am an AI` / `language model` identity assumptions from generic `identity.py`.
- [x] Removed universal AI/language-model phrase bans from `OutputValidator`.
- [x] Removed the universal `Never say you are an AI or language model` workspace instruction.
- [x] Added character-scoped `forbidden_self_claims` to `CoreIdentity` and v1 cartridge validation.
- [x] Engine prompts, validation, and sanitization now consume the current character's self-model constraints.
- [x] Migrated bundled existing characters to explicit self-model constraints so historical behavior remains character-owned rather than engine-owned.
- [x] Added a human-self/artificial-self regression pair under the same generic engine.
- [x] Verified an artificial character may truthfully render `I am an AI` while a human-self character configured to reject that claim catches and sanitizes the same renderer output.
- [x] Verified character self-model constraints survive renderer replacement.

`forbidden_self_claims` is intentionally a small v1 compatibility mechanism. M2 should replace/extend it with a more structured `.snp` v2 self-model/ontology representation rather than growing a large literal phrase list.

## M1 status

**Runtime ownership work: COMPLETE.**

Remaining pre-M2 housekeeping is evidence capture, not another identity-authority redesign:

- [ ] Capture dedicated simulator artifacts with commands and outputs.
- [ ] Capture a deterministic Pretorius human-visible baseline transcript package.
- [ ] Record final normal Python 3.11/3.12 Wayfarer CI after this pass.

## Design decision: continuity ledger simplicity

The original roadmap proposed a hash-chained event ledger. That is stronger than the current threat model requires.

For the local-first single-owner prototype, the default M3 design is:

- append-only event log,
- monotonically increasing sequence numbers,
- event UUIDs,
- continuity epoch,
- transactional writes,
- schema validation,
- causal-parent references where useful,
- deterministic state digests/checkpoints,
- SQLite/database integrity checks,
- explicit export/import validation.

A per-event cryptographic previous-hash chain is **not required by default**. Cryptographic chaining becomes an optional integrity profile only if Wayfarer later introduces a real requirement such as untrusted multi-party synchronization, remote custody, hostile hosts, or proof of tamper evidence across administrative boundaries.

## Design decision: plasticity parameters require calibration

Wayfarer must not turn personality development into tables of aesthetically chosen decimals.

M7 therefore begins with a calibration gate:

1. Start with a small number of shared plasticity profiles by state layer or semantic class.
2. Define the observable behavioral effect before tuning a parameter.
3. Run sensitivity analysis over plausible ranges.
4. Remove or collapse parameters that are not identifiable from observable behavior.
5. Require per-trait overrides to have a documented reason and experimental provenance.
6. Calibrate against repeated scripted scenarios, longitudinal tests, cross-renderer tests, and human judgments where appropriate.
7. Hold out scenarios from tuning so the model is not simply fitted to regression cases.
8. Version parameter sets and record which experiments justified them.
9. Treat numerical precision as implementation precision, not scientific certainty.

The goal is a parsimonious developmental model whose parameters earn their existence empirically.

## Immediate next actions

1. Capture and preserve all documented deterministic simulator outputs as the remaining M0 evidence package.
2. Capture a repeatable deterministic Pretorius transcript, event log, renderer status, and final state information.
3. Confirm the normal Python 3.11/3.12 Wayfarer CI is green after the M1 code and cleanup commits.
4. Update `WAYFARER_BASELINE.md` with those artifact locations/results without changing the frozen baseline commit.
5. Begin M2 `.snp` v2 design with permanent entity identity, structured self-model/ontology, phenotype namespaces, progressive-fidelity rules, and MatrAIx interoperability crosswalk planning.
6. Before implementing M2 plasticity fields, keep the M7 calibration rule in force: schema expressiveness does not justify arbitrary runtime parameters.

## Rule for future contributors

If this file, `WAYFARER_MASTER_PLAN.md`, and the code disagree, do not guess which is correct. Inspect branch history and tests, establish live behavior, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.
