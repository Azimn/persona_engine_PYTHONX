# Project Wayfarer Live Progress

This file is the short-form operational status for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`; this file records what is actually true in the repository now so a new ChatGPT, Codex, Claude Code, or human session can resume without trusting stale README text or chat history.

Last updated: 2026-08-27

## Current branch

- Project name: **Project Wayfarer**
- Repository: `Azimn/persona_engine_PYTHONX`
- Development branch: `wayfarer`
- Frozen pre-Wayfarer baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`
- Current Wayfarer head at this checkpoint: `fcaf4fd9af2f5c8e6e32b7ab5225ce133cb6c67e`
- Wayfarer is 24 commits ahead of the frozen baseline at this checkpoint.

## Important branch distinction

A clean clone of the repository without switching branches still lands on `main`. The `main` branch intentionally remains the frozen pre-Wayfarer comparison point and still contains the stale historical documentation and the old renderer-test/canonicality behavior.

Therefore:

```bash
git switch wayfarer
```

before evaluating current Project Wayfarer behavior.

Do not "fix" the frozen baseline by rewriting `main`; its value is that it preserves the before-state.

## Verified baseline findings

The old documentation said `171 passed, 1 skipped`, but that count was stale.

Independent clean GitHub Actions baseline verification found:

- Python 3.11: `177 passed, 2 failed, 1 skipped, 1 warning`
- Python 3.12: `178 passed, 1 failed, 1 skipped, 1 warning`

The common failure was `test_output_validator_and_sanitizer_are_traced`. The test patched `renderer.generate`, while the active expression path had moved to `renderer.generate_expression`. That meant the test no longer injected its invalid text into the real production rendering seam.

The Python 3.11 baseline also exposed a brittle lexical expectation in the anchored-misread simulator. That discrepancy is preserved in `WAYFARER_BASELINE.md` rather than being erased from the historical record.

## Verified Wayfarer state

Latest completed Wayfarer CI at this checkpoint:

- Workflow: `Wayfarer CI`
- Run: `33111704143`
- Head: `fcaf4fd9af2f5c8e6e32b7ab5225ce133cb6c67e`
- Python 3.11: `194 passed, 1 skipped, 1 warning in 3.46s`
- Python 3.12: successful

## Completed work

- [x] Created `wayfarer` branch from the frozen PythonX baseline.
- [x] Added Wayfarer CI on Python 3.11 and 3.12.
- [x] Added `WAYFARER_CHARTER.md`.
- [x] Added `AI_DEVELOPER_HANDOFF.md`.
- [x] Added `AUTHORITY_MATRIX.md`.
- [x] Added `WAYFARER_BASELINE.md`.
- [x] Added `WAYFARER_MASTER_PLAN.md`.
- [x] Updated root `AGENTS.md` with Wayfarer rules for AI coding tools.
- [x] Corrected `test_output_validator_and_sanitizer_are_traced` so it patches the real `generate_expression()` seam.
- [x] Made canonicality fail closed.
- [x] Removed `belief` and `interpretive_belief` from generic default-canonical event classes.
- [x] Made `interpretive_belief` and `private_cognition` structurally noncanonical.
- [x] Added adversarial canonicality tests.
- [x] Made legacy `[identity].model_name` optional instead of required.
- [x] Added a migration warning for legacy cartridge `model_name`.
- [x] Prevented cartridge `model_name` from selecting the renderer.
- [x] Removed renderer hints from the bundled `.snp` cartridges.
- [x] Changed `CoreIdentity.model_name` into a compatibility-only `InitVar`, so it is not stored as identity state.
- [x] Added renderer/identity authority tests.

## Still open in M1

- [ ] Remove the remaining execution-path dependency on `identity.model_name` inside `InteriorEngine` bootstrap. The value is now compatibility-only, but the constructor should no longer consult identity at all when creating the default offline renderer.
- [ ] Remove universal AI/language-model ontology assumptions from generic identity/output code.
- [ ] Move character-specific self-description conflicts into cartridge/self-model policy rather than engine-wide regexes.
- [ ] Add at least one artificial-self test character and one human-self test character under the same generic engine.
- [ ] Update `README.md` and `CURRENT_STATUS.md` so the Wayfarer branch visibly identifies itself as Project Wayfarer and no longer reports `171 passed`.
- [ ] Capture the dedicated simulator artifact package.
- [ ] Capture the deterministic Pretorius human-visible baseline transcript package.

## New design decision: continuity ledger simplicity

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

Cryptographic chaining may be added later as an optional integrity profile if the product introduces untrusted multi-party synchronization, remote custody, hostile host assumptions, or a requirement to prove tamper evidence across administrative boundaries.

Reason: replay, ordering, missing-event detection, and ordinary corruption checks do not require a security mechanism designed for adversarial tampering. Avoid making the minimum portable character pay conceptual and implementation complexity for a threat model it does not currently have.

## New design decision: plasticity parameters require calibration

The roadmap must not turn personality development into large tables of aesthetically chosen decimals.

Default approach:

1. Start with a very small number of shared plasticity profiles by state layer or semantic class, not bespoke constants per trait.
2. Define observable behavioral consequences before tuning parameters.
3. Run sensitivity analysis over plausible ranges.
4. Remove parameters that are not identifiable from observable behavior.
5. Require per-trait overrides to have a documented reason and provenance.
6. Calibrate against repeated scripted scenarios, longitudinal tests, cross-renderer tests, and human judgments where appropriate.
7. Hold out scenarios from tuning so the system is not simply fitted to its regression suite.
8. Version parameter sets and record which experiments justified them.
9. Treat numerical precision as implementation precision, not scientific certainty.

The goal is a parsimonious developmental model whose parameters earn their existence empirically.

## Immediate next actions

1. Brand `README.md` and `CURRENT_STATUS.md` as Project Wayfarer on this branch and correct the test status.
2. Finish renderer/identity decoupling in `InteriorEngine`.
3. Begin M1 ontology decoupling.
4. Add the artificial-self/human-self regression pair.
5. Re-run CI.
6. Update this file after each completed step.

## Rule for future contributors

If this file, `WAYFARER_MASTER_PLAN.md`, and the code disagree, do not guess which is correct. Inspect the branch history and tests, establish the live behavior, then update the documents in the same change. Repository documentation is part of the implementation contract.