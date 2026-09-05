# DUCK Production Candidate Gate

Status: architecture freeze and release-candidate acceptance criteria for `duck-future-build`.

This document separates code-completeness from research evidence. Passing this gate means the current architecture is coherent enough to freeze for testing. It does not establish consciousness, sentience, or any phenomenal property, and it does not establish that human observers will judge the character continuous across every model or context.

## Freeze rule

No new macro-level cognitive subsystem should be added merely because another architecture names one. After this gate, a new mechanism requires a failing acceptance metric, a reproducible behavioral defect, or evidence that an existing authority cannot represent the required state transition.

The engineering target remains a persistent simulated subject whose identity and lived history are independent of the replaceable language renderer.

## Mandatory invariants

1. **Subject identity authority**: `subject_id`, authored identity, autobiographical history, relationships, beliefs, commitments, and canonical DUCK state are never renderer-owned.
2. **Renderer firewall**: a renderer may realize an already-selected semantic intention, but it may not change the selected action ID/type or directly mutate canonical state.
3. **Same subject across lifecycle operations**: checkpoint/restart, backup/restore, and embodiment transfer preserve the subject identity invariant.
4. **Bounded hot state**: working memory, action/prediction ledgers, delivery receipts, and the expression hot cache remain bounded. Long-horizon evidence may grow append-only on disk.
5. **Historical expression fidelity**: evicted speech remains recoverable from durable execution traces without calling a renderer to invent replacement wording.
6. **Deterministic fallback**: renderer failure must degrade to a usable deterministic expression path rather than breaking the cognitive cycle.
7. **Explicit authority and provenance**: canonical changes pass through typed/authorized reducers or subject APIs; proposal services remain noncanonical until accepted.
8. **Recovery integrity**: corrupted checkpoints/backups and unsupported future schemas fail closed rather than being silently interpreted.

## Hosted acceptance gates

A production-candidate commit must pass on Python 3.11 and 3.12:

```bash
python -m pytest persona_engine/tests -q
python -m pytest persona_engine/tests/test_duck_*.py -q
python tools/run_duck_smoke.py
python tools/run_duck_future_probe.py --cycles 500
python tools/run_duck_acceptance.py --cycles 24 --expression-cache-limit 8
```

The short acceptance probe deliberately shrinks the expression hot cache so CI exercises eviction and cold trace recovery without requiring hundreds of full host interactions.

## Target-machine gates

These are intentionally not faked by hosted CI.

### Real local renderer swap

Use two actually installed Ollama models when possible:

```bash
python tools/run_duck_local_model_probe.py --model-a qwen3:8b --model-b gemma3
```

Acceptance: same subject/organism identity and canonical state semantics across renderer changes; surface realization may differ.

### Long production-boundary soak

Run the real host acceptance probe at its normal cache size:

```bash
python tools/run_duck_acceptance.py --cycles 360
```

For deeper soak testing, increase `--cycles` into the thousands. Record wall time, process memory, state-directory growth, backup size, and any invariant failure. Growth of append-only evidence is expected; unbounded hot JSON/state structures are not.

## Research evidence gates

These are post-freeze evaluation tasks, not reasons to continue adding architecture before testing:

- longitudinal interaction with the same subject over days/weeks;
- blind renderer/model-swap transcript evaluation;
- continuity recognition and character-identity ratings;
- lesion/ablation studies for motivation, memory activation, workspace, simulation, and self-related mechanisms;
- body/environment transfer studies;
- comparison against frozen-renderer and prompt-only baselines.

## Release-candidate interpretation

When every hosted gate is green, the code may be called a **production candidate** for controlled research and local experimentation. A public production release still requires target-machine model execution, longer soak evidence, versioned upgrade/rollback practice, and human continuity evaluation appropriate to the intended deployment.
