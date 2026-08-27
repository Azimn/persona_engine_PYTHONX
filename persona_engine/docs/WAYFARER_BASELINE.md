# Wayfarer Baseline Manifest

## Provenance

Project Wayfarer was branched from:

- Repository: `Azimn/persona_engine_PYTHONX`
- Branch: `main`
- Commit: `65df9144e7f0876b6e61e28d6446c50f283f9db4`
- Commit message: `Validate cartridge dialogue schema and slots`
- Wayfarer branch: `wayfarer`

This commit is the semantic pre-Wayfarer comparison point. Do not move this baseline reference when later work changes the branch.

## Documented pre-Wayfarer status

`CURRENT_STATUS.md` describes PythonX as the v12 Human UI lineage and the Python package as the reference implementation for a deterministic cartridge-driven character organism. It documents the older expected test result as `171 passed, 1 skipped` and lists deterministic relationship, pressure, body, world, memory, intention, habit, symbol, belief, interpretation, World Authority, Tide, replay/debug, mock sensors, voice/avatar projection, and optional Ollama rendering among the current features.

The repository had accumulated additional tests after that status text was written, so the live baseline contains more tests than the documented count.

## Independent baseline verification

A local clone could not be used from the initiating ChatGPT execution environment because that container could not resolve `github.com`. Rather than treating an unexecuted local command as verification, Wayfarer added a GitHub Actions workflow and used GitHub-hosted clean runners as the independent execution environment.

The first CI commit was `530fc1452ef49c3a6f6c5e6dd1786b3f33047da6`. At that point only Wayfarer documentation and the CI workflow had been added; PythonX runtime behavior was still the baseline code inherited from `65df9144e7f0876b6e61e28d6446c50f283f9db4`.

Command:

```bash
python -m pytest persona_engine/tests -q
```

### Python 3.11 baseline

- Python: CPython 3.11.16
- Platform: GitHub Actions, Ubuntu 24.04.4 LTS
- Result: `177 passed, 2 failed, 1 skipped, 1 warning`
- Duration: approximately 5.00 seconds
- CI run: `33110460947`

Failures:

1. `test_output_validator_and_sanitizer_are_traced`
   - The test monkeypatched `renderer.generate`, but the current expression path uses `renderer.generate_expression`.
   - The assertion therefore did not actually inject invalid renderer output into the active expression seam.
   - Classified as a stale test seam, not evidence that the validator itself was bypassed.

2. `test_anchored_misread_simulator_runs`
   - Turn 4 expected a lexical regex containing `sorry|sincere|unproven|settle|tension|repair`.
   - Actual deterministic/offline response was `I hear the apology. I will let the next action determine its weight.`
   - The semantic behavior was appropriate, but the expected regex omitted `apology`.
   - The same test passed in the Python 3.12 baseline run, so this is recorded as a brittle/nondeterministic baseline test rather than a Wayfarer regression.

### Python 3.12 baseline

- Python: CPython 3.12.14
- Platform: GitHub Actions, Ubuntu 24.04.4 LTS
- Result: `178 passed, 1 failed, 1 skipped, 1 warning`
- Duration: approximately 4.12 seconds
- CI run: `33110460947`

Failure:

1. `test_output_validator_and_sanitizer_are_traced`
   - Same stale test-seam issue described above.

The anchored-misread simulator passed on this run. That cross-version discrepancy is now part of the frozen baseline evidence and should be used when stabilizing simulator determinism later.

## First Wayfarer verification after M1 canonicality repair

After the first authority/canonicality changes and corresponding contract-test updates, GitHub Actions run `33110735888` completed successfully on both Python 3.11 and Python 3.12.

Python 3.11 result:

```text
188 passed, 1 skipped, 1 warning in 2.90s
```

Python 3.12 job also completed successfully.

This successful run includes the new Wayfarer canonicality adversarial tests and the corrected validator test seam.

## Simulator baseline

The existing simulator suite is partially exercised by the pytest suite. The anchored-misread simulator produced the cross-version baseline discrepancy documented above. A dedicated exported simulator artifact package is still pending.

Status: PARTIALLY CAPTURED

Remaining:

- run/export each documented simulator explicitly,
- preserve command lines and outputs as durable artifacts,
- distinguish deterministic failures from lexical expectation brittleness.

## Human-visible baseline

Capture at least one reproducible Pretorius session using the deterministic/offline renderer. Preserve:

- prompts,
- responses,
- event log,
- final state digest,
- renderer status,
- notable fake/canned moments.

Status: NOT YET CAPTURED

If a local Ollama model is available, also capture one representative model-backed session, but model availability must not block completion of the deterministic baseline.

## Known architectural concerns identified before Wayfarer modifications

1. Event canonicality should fail closed when an event/payload explicitly says it is noncanonical. **Addressed in first Wayfarer M1 change; verified by CI.**
2. `interpretive_belief` appeared in a generic canonical event-type set even though architecture/tests define active interpretive beliefs as noncanonical. **Addressed in first Wayfarer M1 change; verified by CI.**
3. `model_name` is currently required inside the `.snp` `[identity]` section, which conflicts with renderer-substrate independence. **Pending.**
4. Generic identity/output guards contain universal AI/language-model ontology assumptions that should instead be character-scoped. **Pending.**
5. Current replay primarily reprocesses `input` events and will need broader canonical event replay before time, migration, tools, and social worlds become authoritative. **Pending later milestone.**
6. Current idle catch-up is useful but is not yet a complete continuity-clock contract. **Pending later milestone.**

These concerns are observations, not permission to change behavior without tests and documentation.
