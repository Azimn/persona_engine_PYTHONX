# DUCK Production Candidate Gate

Status: **HOSTED GATE PASSING / ARCHITECTURE FROZEN** on `duck-future-build` as of the embodiment-feasibility fix at commit `2e2dbf2e6b6fea053ec86fe0c4bb838109532e3f`.

This document separates code-completeness from research evidence. Passing this gate means the current architecture is coherent enough to freeze for controlled testing. It does not establish consciousness, sentience, or any phenomenal property, and it does not establish that human observers will judge the character continuous across every model or context.

## Freeze rule

No new macro-level cognitive subsystem should be added merely because another architecture names one. After this gate, a new mechanism requires a failing acceptance metric, a reproducible behavioral defect, or evidence that an existing authority cannot represent the required state transition.

The engineering target remains a persistent simulated subject whose identity and lived history are independent of the replaceable language renderer.

## Mandatory invariants

1. **Subject identity authority**: `subject_id`, authored identity, autobiographical history, relationships, beliefs, commitments, and canonical DUCK state are never renderer-owned.
2. **Renderer firewall**: a renderer may realize an already-selected semantic intention, but it may not change the selected action ID/type or directly mutate canonical state.
3. **Same subject across lifecycle operations**: checkpoint/restart, backup/restore, and embodiment transfer preserve the subject identity invariant.
4. **Embodiment-feasible intention**: current body capabilities constrain candidate actions before simulation and commitment. If no proposed action is physically available, the organism may commit to `wait` rather than an impossible action. The executor independently rechecks capability as the final enforcement boundary.
5. **Bounded hot state**: working memory, action/prediction ledgers, delivery receipts, and the expression hot cache remain bounded. Long-horizon evidence may grow append-only on disk.
6. **Historical expression fidelity**: evicted speech remains recoverable from durable execution traces without calling a renderer to invent replacement wording.
7. **Deterministic fallback**: renderer failure must degrade to a usable deterministic expression path rather than breaking the cognitive cycle.
8. **Explicit authority and provenance**: canonical changes pass through typed/authorized reducers or subject APIs; proposal services remain noncanonical until accepted.
9. **Recovery integrity**: corrupted checkpoints/backups and unsupported future schemas fail closed rather than being silently interpreted.

## Hosted acceptance gates

A production-candidate commit must pass on Python 3.11 and 3.12:

```bash
python -m pytest persona_engine/tests -q
python -m pytest persona_engine/tests/test_duck_*.py -q
python tools/run_duck_smoke.py
python tools/run_duck_future_probe.py --cycles 500
python tools/run_duck_acceptance.py --cycles 120
python tools/run_duck_acceptance.py --cycles 24 --expression-cache-limit 8 --require-expression-eviction
```

The lifecycle probe does not force speech. A user message is an input event, not a command to speak. Any autonomously selected action must be feasible for the current embodiment and must execute successfully. Language delivery is required only when DUCK itself commits to `communicate`.

The separate short eviction probe deliberately shrinks the expression hot cache so CI proves eviction and cold trace recovery without making "speak hundreds of times" a behavioral requirement.

## Defects exposed by the gate

The first lifecycle run exposed a bad test assumption: repeated user input eventually led DUCK to select `inspect`, showing that the organism was not simply hard-wired to answer every message. The gate was corrected to preserve that autonomy.

The corrected gate then exposed a real architectural defect: the text-channel body supports `communicate` and `wait`, but an exploration drive could still cause DUCK to commit to `inspect`. The executor correctly rejected it as `effector_unavailable`, but capability had entered the pipeline too late. Commit `2e2dbf2e6b6fea053ec86fe0c4bb838109532e3f` moved embodiment feasibility ahead of simulation/selection while retaining the executor's independent check.

This is the intended value of the freeze gate: defects change mechanisms; passing behavior does not trigger speculative subsystem growth.

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

With every hosted gate green, the code may be called a **production candidate for controlled research and local experimentation**. A public production release still requires target-machine model execution, longer soak evidence, versioned upgrade/rollback practice, and human continuity evaluation appropriate to the intended deployment.
