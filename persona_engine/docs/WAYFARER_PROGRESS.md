# Project Wayfarer Live Progress

This file is the short-form operational status for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`; this file records what is actually true in the repository now so a new ChatGPT, Codex, Claude Code, or human session can resume without trusting stale chat history.

Last updated: 2026-08-27

## Current branch

- Project name: **Project Wayfarer**
- Repository: `Azimn/persona_engine_PYTHONX`
- Development branch: `wayfarer`
- Frozen pre-Wayfarer baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`
- Latest verified documentation checkpoint before this update: `0a05a46efe9d438f7a2692923681c17907864d88`

## Important branch distinction

A clean clone without switching branches still lands on `main`. The `main` branch intentionally remains the frozen pre-Wayfarer comparison point and still contains the historical pre-Wayfarer implementation and documentation.

Use:

```bash
git switch wayfarer
```

before evaluating current Project Wayfarer behavior.

Do not rewrite `main` merely to make it look current. Its purpose is to preserve the before-state.

## Verified baseline findings

The old documentation said `171 passed, 1 skipped`, but that count was stale.

Independent clean GitHub Actions baseline verification found:

- Python 3.11: `177 passed, 2 failed, 1 skipped, 1 warning`
- Python 3.12: `178 passed, 1 failed, 1 skipped, 1 warning`

The common failure was `test_output_validator_and_sanitizer_are_traced`. The test patched `renderer.generate`, while the active expression path had moved to `renderer.generate_expression`, so the invalid test output never entered the real production rendering seam.

The Python 3.11 baseline also exposed a brittle lexical expectation in the anchored-misread simulator. Both findings are preserved in `WAYFARER_BASELINE.md`.

## Latest verified Wayfarer state

Latest completed CI before this progress update:

- Workflow: `Wayfarer CI`
- Run: `33117422415`
- Head: `0a05a46efe9d438f7a2692923681c17907864d88`
- Conclusion: success
- Python 3.11/3.12 matrix: successful

The last fetched detailed Python 3.11 log before the documentation-only commits reported:

```text
194 passed, 1 skipped, 1 warning in 3.46s
```

The subsequent documentation commits also completed green CI. Check GitHub Actions before quoting a newer exact test count after runtime changes.

## Completed work

- [x] Created `wayfarer` from the frozen PythonX baseline.
- [x] Added Wayfarer CI on Python 3.11 and 3.12.
- [x] Added `WAYFARER_CHARTER.md`.
- [x] Added `AI_DEVELOPER_HANDOFF.md`.
- [x] Added `AUTHORITY_MATRIX.md`.
- [x] Added `WAYFARER_BASELINE.md`.
- [x] Added and refreshed `WAYFARER_MASTER_PLAN.md`.
- [x] Added this `WAYFARER_PROGRESS.md` live tracker.
- [x] Branded root `README.md` as Project Wayfarer on this branch.
- [x] Branded `CURRENT_STATUS.md` as Project Wayfarer and removed stale `171 passed` status.
- [x] Updated root `AGENTS.md` so Codex and other coding tools are directed to Wayfarer documents first.
- [x] Corrected `test_output_validator_and_sanitizer_are_traced` so it patches the real `generate_expression()` seam.
- [x] Made canonicality fail closed.
- [x] Removed `belief` and `interpretive_belief` from generic default-canonical event classes.
- [x] Made `interpretive_belief` and `private_cognition` structurally noncanonical.
- [x] Added adversarial canonicality tests.
- [x] Made legacy `[identity].model_name` optional instead of required.
- [x] Added migration warning for legacy cartridge `model_name`.
- [x] Prevented cartridge `model_name` from selecting the renderer.
- [x] Removed renderer hints from bundled `.snp` cartridges.
- [x] Changed `CoreIdentity.model_name` into a compatibility-only `InitVar`, so it is not stored as identity state.
- [x] Added renderer/identity authority tests.
- [x] Revised M3 so a cryptographic hash chain is not mandatory for the local single-owner threat model.
- [x] Added an explicit M7 calibration/validation gate so plasticity does not become arbitrary per-trait decimal tuning.

## Still open in M1

- [~] Remove the remaining execution-path dependency on `identity.model_name` inside `InteriorEngine` bootstrap. The compatibility value no longer represents authored identity, but the engine should not consult identity at all to select its default renderer.
- [ ] Remove universal AI/language-model ontology assumptions from generic identity/output code.
- [ ] Move character-specific self-description conflicts into cartridge/self-model policy rather than engine-wide regexes.
- [ ] Add at least one artificial-self test character and one human-self test character under the same generic engine.
- [ ] Capture the dedicated simulator artifact package.
- [ ] Capture the deterministic Pretorius human-visible baseline transcript package.

## Design decision: continuity ledger simplicity

The original roadmap proposed a hash-chained event ledger. That is stronger than the current threat model requires.

For the local-first single-owner prototype, the default design is now:

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

A per-event cryptographic previous-hash chain is **not required by default**.

Cryptographic chaining may be added later as an optional integrity profile if the product introduces untrusted multi-party synchronization, remote custody, hostile host assumptions, or another real need for adversarial tamper evidence.

Reason: replay, ordering, missing-event detection, and ordinary corruption checks do not require a security mechanism designed for an adversarial threat model the local prototype does not currently have.

## Design decision: plasticity parameters require calibration

The roadmap must not turn personality development into large tables of aesthetically chosen decimals.

Default approach:

1. Start with a small number of shared plasticity profiles by state layer or semantic class, not bespoke constants per trait.
2. Define observable behavioral consequences before tuning parameters.
3. Run sensitivity analysis across plausible ranges.
4. Remove or collapse parameters that are not identifiable from observable behavior.
5. Require per-trait overrides to have a documented reason and experimental provenance.
6. Calibrate against repeated scripted scenarios, longitudinal tests, cross-renderer tests, and human judgments where appropriate.
7. Hold out scenarios from tuning so the system is not merely fitted to its regression suite.
8. Version parameter sets and record which experiments justified them.
9. Treat numerical precision as implementation precision, not scientific certainty.

The goal is a parsimonious developmental model whose parameters earn their existence empirically.

## Immediate next actions

1. Finish renderer/identity decoupling in `InteriorEngine`.
2. Begin M1 ontology decoupling.
3. Add artificial-self and human-self regression fixtures/tests.
4. Re-run CI after runtime changes.
5. Update this file in the same pass.
6. Capture dedicated simulator artifacts and the deterministic Pretorius human-visible baseline before beginning `.snp` v2.

## Rule for future contributors

If this file, `WAYFARER_MASTER_PLAN.md`, and the code disagree, do not guess which is correct. Inspect branch history and tests, establish live behavior, then update the documents in the same change. Repository documentation is part of the implementation contract.