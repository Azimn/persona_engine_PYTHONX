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

`CURRENT_STATUS.md` describes PythonX as the v12 Human UI lineage and the Python package as the reference implementation for a deterministic cartridge-driven character organism. It documents the expected test result as `171 passed, 1 skipped` and lists deterministic relationship, pressure, body, world, memory, intention, habit, symbol, belief, interpretation, World Authority, Tide, replay/debug, mock sensors, voice/avatar projection, and optional Ollama rendering among the current features.

That result is documentation evidence only until Wayfarer independently re-runs the suite below.

## Required baseline verification

From the repository root:

```bash
python -m pytest persona_engine/tests -q
```

Record the exact environment, result, failures, and elapsed time below.

### Full test suite

Status: NOT YET RE-RUN FOR WAYFARER

- Python version: pending
- Platform: pending
- Result: pending
- Duration: pending
- Notes: pending

## Simulator baseline

Run the currently documented simulator scripts with the mock/offline renderer. Record exact commands and results here before modifying behavior they exercise.

Status: NOT YET CAPTURED

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

1. Event canonicality should fail closed when an event/payload explicitly says it is noncanonical.
2. `interpretive_belief` appears in a generic canonical event-type set even though architecture/tests define active interpretive beliefs as noncanonical.
3. `model_name` is currently required inside the `.snp` `[identity]` section, which conflicts with renderer-substrate independence.
4. Generic identity/output guards contain universal AI/language-model ontology assumptions that should instead be character-scoped.
5. Current replay primarily reprocesses `input` events and will need broader canonical event replay before time, migration, tools, and social worlds become authoritative.
6. Current idle catch-up is useful but is not yet a complete continuity-clock contract.

These concerns are observations, not permission to change behavior without tests and documentation.
